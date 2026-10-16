"""Private iCalendar importer for La Escalera, using only the Python standard library."""
from __future__ import annotations

import ipaddress
import json
import logging
import mimetypes
import os
import re
import socket
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from wsgiref.simple_server import make_server, WSGIRequestHandler
from zoneinfo import ZoneInfo

PROJECT_DIR = Path(__file__).resolve().parent.parent
def _load_env_file(path: Path) -> None:
    """Load a small KEY=VALUE .env file without overriding process environment."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value

_load_env_file(PROJECT_DIR / ".env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("la-escalera-calendar")
LOCAL_TZ = ZoneInfo(os.getenv("PROPERTY_TIMEZONE", "Europe/Madrid"))
INTERVAL_MIN = max(5, min(1440, int(os.getenv("SYNC_INTERVAL", "30"))))
MAX_BYTES = 5 * 1024 * 1024

# Cache stores date intervals and sync metadata only, never event titles, names or descriptions.
lock = threading.RLock()
state = {
    "booking": {"intervals": [], "last_success": None, "last_attempt": None, "error": None},
    "airbnb": {"intervals": [], "last_success": None, "last_attempt": None, "error": None},
}


def _allowed_host(host: str) -> bool:
    host = (host or "").lower().rstrip(".")
    return (host == "booking.com" or host.endswith(".booking.com") or host == "airbnb.com" or host.endswith(".airbnb.com") or host == "airbnb.es" or host.endswith(".airbnb.es"))


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not _allowed_host(parsed.hostname or "") or parsed.username or parsed.password:
        raise ValueError("La fuente debe ser una URL HTTPS oficial de Booking.com o Airbnb.")
    # SSRF guard: do not fetch private/local destinations, even if a hostname resolves there.
    for result in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM):
        address = ipaddress.ip_address(result[4][0].split("%", 1)[0])
        if not address.is_global:
            raise ValueError("La URL resuelve a una dirección de red no pública.")
    return url


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _parse_ical_date(prop: str, value: str):
    params = prop.split(";")[1:]
    param_map = {}
    for item in params:
        if "=" in item:
            key, val = item.split("=", 1)
            param_map[key.upper()] = val.strip('"')
    raw = value.strip()
    if param_map.get("VALUE", "").upper() == "DATE" or re.fullmatch(r"\d{8}", raw):
        return datetime.strptime(raw[:8], "%Y%m%d").date()
    fmt = "%Y%m%dT%H%M%S" if len(raw.rstrip("Z")) >= 15 else "%Y%m%dT%H%M"
    clean = raw.rstrip("Z")
    parsed = datetime.strptime(clean, fmt)
    if raw.endswith("Z"):
        parsed = parsed.replace(tzinfo=timezone.utc)
    elif param_map.get("TZID"):
        parsed = parsed.replace(tzinfo=ZoneInfo(param_map["TZID"]))
    else:
        parsed = parsed.replace(tzinfo=LOCAL_TZ)
    return parsed.astimezone(LOCAL_TZ)


def _parse_duration(raw: str) -> timedelta:
    match = re.fullmatch(r"P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", raw.upper())
    if not match:
        raise ValueError("DURATION iCalendar no reconocido")
    weeks, days, hours, minutes, seconds = (int(x or 0) for x in match.groups())
    return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)


def parse_busy_intervals(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    # RFC 5545 line folding: continuation lines begin with one space or tab.
    unfolded = []
    for line in text.split("\n"):
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    events = []
    current = None
    for line in unfolded:
        upper = line.upper()
        if upper == "BEGIN:VEVENT":
            current = {}
        elif upper == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None and ":" in line:
            prop, value = line.split(":", 1)
            key = prop.split(";", 1)[0].upper()
            if key in {"DTSTART", "DTEND", "DURATION", "STATUS", "RRULE", "RDATE", "EXDATE", "TRANSP"}:
                current[key] = (prop, value.strip())
    intervals: set[tuple[date, date]] = set()
    for event in events:
        if any(key in event for key in ("RRULE", "RDATE", "EXDATE")):
            raise ValueError("El calendario contiene recurrencias que requieren tratamiento explícito.")
        if event.get("STATUS", ("", ""))[1].upper() == "CANCELLED":
            continue
        if event.get("TRANSP", ("", ""))[1].upper() == "TRANSPARENT":
            continue
        if "DTSTART" not in event:
            continue
        start_value = _parse_ical_date(*event["DTSTART"])
        start = start_value.date() if isinstance(start_value, datetime) else start_value
        if "DTEND" in event:
            end_value = _parse_ical_date(*event["DTEND"])
            end = end_value.date() if isinstance(end_value, datetime) else end_value
        elif "DURATION" in event:
            duration = _parse_duration(event["DURATION"][1])
            if isinstance(start_value, datetime):
                end = (start_value + duration).astimezone(LOCAL_TZ).date()
            else:
                end = start + duration
        else:
            end = start + timedelta(days=1)
        if end > start:
            intervals.add((start, end))
    return [{"start": a.isoformat(), "end": b.isoformat()} for a, b in sorted(intervals)]


def _fetch_feed(url: str) -> list[dict[str, str]]:
    _validate_url(url)
    request = Request(url, headers={"User-Agent": "LaEscaleraAvailability/1.0", "Accept": "text/calendar, text/plain;q=0.9"})
    with build_opener(SafeRedirect()).open(request, timeout=12) as response:
        _validate_url(response.geturl())
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("El calendario supera el límite permitido de 5 MB.")
    if b"BEGIN:VCALENDAR" not in payload[:4096].upper():
        raise ValueError("La respuesta no parece un calendario iCalendar válido.")
    return parse_busy_intervals(payload)


def sync_once() -> None:
    configured = {"booking": os.getenv("BOOKING_ICAL_URL", "").strip(), "airbnb": os.getenv("AIRBNB_ICAL_URL", "").strip()}
    for source, url in configured.items():
        with lock:
            state[source]["last_attempt"] = datetime.now(timezone.utc).isoformat()
        if not url:
            with lock:
                state[source]["error"] = "not_configured"
            continue
        try:
            intervals = _fetch_feed(url)
            with lock:
                state[source]["intervals"] = intervals
                state[source]["last_success"] = datetime.now(timezone.utc).isoformat()
                state[source]["error"] = None
            log.info("Sincronización correcta de %s (%d intervalos)", source, len(intervals))
        except Exception as exc:
            # Keep the last good copy. The API will mark availability as degraded, not free.
            with lock:
                state[source]["error"] = type(exc).__name__
            log.warning("No se pudo sincronizar %s; se conserva la última copia válida (%s)", source, type(exc).__name__)


def public_snapshot() -> dict:
    with lock:
        snapshot = {name: {key: (list(value) if key == "intervals" else value) for key, value in item.items()} for name, item in state.items()}
    configured = {name: bool(os.getenv(f"{name.upper()}_ICAL_URL", "").strip()) for name in state}
    all_ranges = []
    for source in snapshot.values():
        all_ranges.extend((date.fromisoformat(item["start"]), date.fromisoformat(item["end"])) for item in source["intervals"])
    all_ranges.sort()
    merged: list[list[date]] = []
    for start, end in all_ranges:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    all_configured = all(configured.values())
    now = datetime.now(timezone.utc)
    def fresh(name):
        stamp = snapshot[name]["last_success"]
        if not stamp or snapshot[name]["error"]:
            return False
        try:
            synced_at = datetime.fromisoformat(stamp)
            return now - synced_at <= timedelta(minutes=max(60, INTERVAL_MIN * 2))
        except (TypeError, ValueError):
            return False
    all_fresh = all(fresh(name) for name in state)
    any_success = any(snapshot[name]["last_success"] for name in state)
    status = "synced" if all_configured and all_fresh else "degraded" if any_success else "pending"
    successes = [snapshot[name]["last_success"] for name in state if snapshot[name]["last_success"]]
    return {
        "status": status,
        "busy": [{"start": a.isoformat(), "end": b.isoformat()} for a, b in merged],
        "last_successful_sync": min(successes) if all_fresh and successes else (max(successes) if successes else None),
        "sources": {name: {"configured": configured[name], "last_success": snapshot[name]["last_success"], "state": "ok" if fresh(name) else "stale" if snapshot[name]["last_success"] else "pending"} for name in state},
        "refresh_minutes": INTERVAL_MIN,
        "message": "Fechas ocupadas importadas; confirma siempre con el alojamiento." if status == "synced" else "Disponibilidad pendiente de sincronización. Consulta las fechas por WhatsApp." if status == "pending" else "Sincronización parcial o temporalmente desactualizada. Consulta las fechas por WhatsApp.",
    }


def _response(start_response, status: str, body: bytes, content_type: str = "application/json; charset=utf-8", headers=None):
    base = [("Content-Type", content_type), ("Content-Length", str(len(body))), ("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "SAMEORIGIN"), ("Referrer-Policy", "no-referrer")]
    if headers:
        base.extend(headers)
    start_response(status, base)
    return [body]


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    if method != "GET":
        return _response(start_response, "405 Method Not Allowed", b'{"error":"method_not_allowed"}', headers=[("Allow", "GET")])
    if path == "/api/availability":
        return _response(start_response, "200 OK", json.dumps(public_snapshot(), ensure_ascii=False).encode(), headers=[("Cache-Control", "no-store")])
    if path == "/api/health":
        payload = {"ok": True, "service": "calendar-import", "status": public_snapshot()["status"]}
        return _response(start_response, "200 OK", json.dumps(payload).encode(), headers=[("Cache-Control", "no-store")])
    relative = "index.html" if path == "/" else unquote(path.lstrip("/"))
    target = (PROJECT_DIR / relative).resolve()
    if not target.is_relative_to(PROJECT_DIR) or not target.is_file():
        return _response(start_response, "404 Not Found", b"Not found", "text/plain; charset=utf-8")
    # Never serve secrets or server-only files from the project root.
    if target.name in {".env", ".env.example", "app.py"} or "backend" in target.relative_to(PROJECT_DIR).parts or target.name == ".gitignore":
        return _response(start_response, "404 Not Found", b"Not found", "text/plain; charset=utf-8")
    content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    return _response(start_response, "200 OK", target.read_bytes(), content_type, headers=[("Cache-Control", "no-cache" if target.suffix in {".html", ".js", ".css"} else "public, max-age=3600")])


def _background_sync() -> None:
    while True:
        sync_once()
        time.sleep(INTERVAL_MIN * 60)


if os.getenv("DISABLE_BACKGROUND_SYNC", "0") != "1":
    threading.Thread(target=_background_sync, daemon=True, name="ical-sync").start()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    class QuietHandler(WSGIRequestHandler):
        def log_message(self, fmt, *args):
            log.info("%s - %s", self.address_string(), fmt % args)
    log.info("Web disponible en http://%s:%s", host, port)
    with make_server(host, port, application, handler_class=QuietHandler) as server:
        server.serve_forever()
