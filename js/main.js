(() => {
  'use strict';
  const config = window.SITE_CONFIG || {};
  const urls = {
    booking: config.bookingUrl || 'https://www.booking.com/hotel/es/la-escalera-zahara-de-la-sierra.es.html',
    airbnb: config.airbnbUrl || 'https://www.airbnb.es/rooms/1451979739905839541',
    instagram: config.instagramUrl || 'https://www.instagram.com/alojamiento_rural_la_escalera/'
  };
  const whatsappNumber = String(config.whatsappNumber || '').replace(/\D/g, '');
  const makeWhatsAppUrl = (message = '¡Hola! Me gustaría consultar disponibilidad y el descuento por reserva directa para La Escalera, en Zahara de la Sierra. ¡Muchas gracias!') => {
    return `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
  };

  document.querySelectorAll('[data-external]').forEach(link => {
    const key = link.dataset.external;
    if (urls[key]) link.href = urls[key];
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  });
  document.querySelectorAll('[data-whatsapp-link]').forEach(link => {
    link.href = makeWhatsAppUrl();
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  });
  const promoMessage = '¡Hola! Estoy interesado/a en alojarme en La Escalera, en Zahara de la Sierra. Me gustaría consultar la disponibilidad y el descuento promocional de entre el 10 % y el 15 % por reserva directa. ¿Podríais informarme de las condiciones y el precio de mi estancia?';
  document.querySelectorAll('[data-promo-whatsapp]').forEach(link => {
    link.href = makeWhatsAppUrl(promoMessage);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  });

  const menuButton = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#main-nav');
  menuButton?.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
  });
  nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    nav.classList.remove('open');
    menuButton?.setAttribute('aria-expanded', 'false');
    menuButton?.setAttribute('aria-label', 'Abrir menú');
  }));
  const year = document.querySelector('#year');
  if (year) year.textContent = new Date().getFullYear();

  const checkin = document.querySelector('#checkin');
  const checkout = document.querySelector('#checkout');
  const form = document.querySelector('#contact-form');
  const status = document.querySelector('#form-status');
  const today = new Date();
  today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
  const todayString = today.toISOString().slice(0, 10);
  if (checkin && checkout) {
    checkin.min = todayString;
    checkout.min = todayString;
    checkin.addEventListener('change', () => {
      checkout.min = checkin.value ? nextDay(checkin.value) : todayString;
      if (checkout.value && checkout.value <= checkin.value) checkout.value = '';
    });
  }
  function nextDay(dateString) {
    const d = new Date(`${dateString}T12:00:00`);
    d.setDate(d.getDate() + 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  function formatDate(value) {
    if (!value) return '';
    const [y, m, d] = value.split('-');
    return `${d}/${m}/${y}`;
  }
  form?.addEventListener('submit', event => {
    event.preventDefault();
    if (status) status.textContent = '';
    if (!checkin.value || !checkout.value) {
      status.textContent = 'Selecciona las fechas de entrada y salida.';
      (!checkin.value ? checkin : checkout).focus();
      return;
    }
    if (checkin.value < todayString) {
      status.textContent = 'La fecha de entrada no puede estar en el pasado.';
      checkin.focus();
      return;
    }
    if (checkout.value <= checkin.value) {
      status.textContent = 'La salida debe ser posterior a la entrada.';
      checkout.focus();
      return;
    }
    if (!whatsappNumber || whatsappNumber.length < 10) {
      status.textContent = 'El teléfono de WhatsApp no está configurado correctamente. Revisa js/config.js.';
      return;
    }
    const data = new FormData(form);
    const lines = [
      '¡Hola! Estoy interesado/a en reservar La Escalera, en Zahara de la Sierra.',
      '',
      `Fecha de entrada: ${formatDate(data.get('checkin'))}`,
      `Fecha de salida: ${formatDate(data.get('checkout'))}`,
      `Número de huéspedes: ${data.get('guests')}`,
      data.get('name')?.trim() ? `Nombre: ${data.get('name').trim()}` : '',
      data.get('message')?.trim() ? `Mensaje adicional: ${data.get('message').trim()}` : '',
      '',
      'Me gustaría consultar la disponibilidad, el precio de la estancia y las condiciones del descuento promocional de entre un 10 % y un 15 % por reserva directa.',
      'Entiendo que el descuento está sujeto a confirmación y que este mensaje no confirma una reserva.',
      '',
      '¡Muchas gracias!'
    ].filter(Boolean).join('\n');
    window.open(makeWhatsAppUrl(lines), '_blank', 'noopener,noreferrer');
    status.textContent = 'Se ha preparado el mensaje en WhatsApp. Revísalo y envíalo desde la aplicación; el alojamiento debe confirmar disponibilidad, precio y condiciones.';
  });

  const tiles = [...document.querySelectorAll('.gallery-tile')];
  const dialog = document.querySelector('#lightbox');
  const lightboxImage = document.querySelector('#lightbox-image');
  const caption = document.querySelector('#lightbox-caption');
  let current = 0;
  function showImage(index) {
    if (!tiles.length) return;
    current = (index + tiles.length) % tiles.length;
    const tile = tiles[current];
    lightboxImage.src = tile.dataset.full;
    lightboxImage.alt = tile.querySelector('img')?.alt || '';
    caption.textContent = tile.dataset.caption || '';
  }
  tiles.forEach((tile, index) => tile.addEventListener('click', () => {
    showImage(index);
    if (dialog && typeof dialog.showModal === 'function') dialog.showModal();
  }));
  document.querySelector('.lightbox-close')?.addEventListener('click', () => dialog?.close());
  document.querySelector('.lightbox-prev')?.addEventListener('click', () => showImage(current - 1));
  document.querySelector('.lightbox-next')?.addEventListener('click', () => showImage(current + 1));
  dialog?.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog?.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') showImage(current - 1);
    if (event.key === 'ArrowRight') showImage(current + 1);
  });

  // Calendar UI: no date is called available unless both authorized feeds synced successfully.
  const calendar = document.querySelector('#availability-calendar');
  if (calendar) {
    const monthLabel = document.querySelector('#calendar-month');
    const calendarStatus = document.querySelector('#calendar-status');
    const validation = document.querySelector('#calendar-validation');
    const inputIn = document.querySelector('#calendar-checkin');
    const inputOut = document.querySelector('#calendar-checkout');
    const guestsInput = document.querySelector('#calendar-guests');
    const whatsappLink = document.querySelector('#calendar-whatsapp');
    const prev = document.querySelector('#calendar-prev');
    const next = document.querySelector('#calendar-next');
    const now = new Date();
    let monthCursor = new Date(now.getFullYear(), now.getMonth(), 1);
    let availability = { status: 'pending', busy: [], message: 'Disponibilidad pendiente de sincronización. Consulta las fechas por WhatsApp.' };
    const dateString = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const parseDate = value => value ? new Date(`${value}T12:00:00`) : null;
    const formatDate = value => value ? new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(parseDate(value)) : '';
    const todayValue = dateString(now);
    inputIn.min = todayValue;
    inputOut.min = todayValue;

    function isBusy(value) {
      return availability.busy.some(range => value >= range.start && value < range.end);
    }
    function intervalIsBusy(start, end) {
      return availability.busy.some(range => start < range.end && end > range.start);
    }
    function selectionState() {
      const start = inputIn.value;
      const end = inputOut.value;
      if (!start || !end) return 'incomplete';
      if (end <= start) return 'invalid';
      if (intervalIsBusy(start, end)) return 'busy';
      return availability.status === 'synced' ? 'clear' : 'unknown';
    }
    function updateSelectionMessage() {
      const state = selectionState();
      const valid = state === 'clear' || state === 'unknown';
      whatsappLink.setAttribute('aria-disabled', String(!valid));
      whatsappLink.classList.toggle('is-disabled', !valid);
      if (state === 'incomplete') validation.textContent = 'Selecciona una fecha de entrada y otra de salida.';
      else if (state === 'invalid') validation.textContent = 'La salida debe ser posterior a la entrada.';
      else if (state === 'busy') validation.textContent = 'Ese intervalo coincide con fechas ocupadas en los calendarios importados. Elige otras fechas.';
      else if (state === 'unknown') validation.textContent = 'Fechas seleccionadas, pero la disponibilidad aún no está verificada. Puedes consultarla por WhatsApp.';
      else validation.textContent = 'No se detectan eventos ocupados en ese intervalo en los calendarios sincronizados. La confirmación final depende del alojamiento.';
      renderCalendar();
      if (valid) {
        const message = [
          '¡Hola! Quiero consultar una estancia en La Escalera.',
          '',
          `Entrada: ${formatDate(start)}`,
          `Salida: ${formatDate(end)}`,
          `Huéspedes: ${guestsInput.value}`,
          '',
          'Me gustaría confirmar la disponibilidad y conocer el precio final con el descuento promocional por reserva directa.',
          ...(state === 'unknown' ? ['La disponibilidad del calendario web no está sincronizada/verificada.'] : []),
          '¡Gracias!'
        ].join('\n');
        whatsappLink.href = makeWhatsAppUrl(message);
      }
    }
    function chooseDate(value) {
      if (value < todayValue) return;
      if (!inputIn.value || inputOut.value || value <= inputIn.value) {
        if (isBusy(value)) {
          validation.textContent = 'Esta fecha de entrada figura como ocupada en los calendarios importados. Elige otra fecha.';
          return;
        }
        inputIn.value = value;
        inputOut.value = '';
        inputOut.min = nextDay(value);
      } else {
        inputOut.value = value;
      }
      updateSelectionMessage();
    }
    function renderCalendar() {
      if (!calendar) return;
      monthLabel.textContent = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' }).format(monthCursor);
      monthLabel.textContent = monthLabel.textContent.charAt(0).toLocaleUpperCase('es-ES') + monthLabel.textContent.slice(1);
      calendar.replaceChildren();
      const firstDay = new Date(monthCursor.getFullYear(), monthCursor.getMonth(), 1);
      const offset = (firstDay.getDay() + 6) % 7;
      const daysInMonth = new Date(monthCursor.getFullYear(), monthCursor.getMonth() + 1, 0).getDate();
      for (let blank = 0; blank < offset; blank++) {
        const spacer = document.createElement('span');
        spacer.className = 'calendar-empty';
        spacer.setAttribute('aria-hidden', 'true');
        calendar.append(spacer);
      }
      for (let day = 1; day <= daysInMonth; day++) {
        const d = new Date(monthCursor.getFullYear(), monthCursor.getMonth(), day);
        const value = dateString(d);
        const busy = isBusy(value);
        const selected = value === inputIn.value || value === inputOut.value;
        const within = inputIn.value && inputOut.value && value > inputIn.value && value < inputOut.value;
        const past = value < todayValue;
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'calendar-day';
        if (availability.status === 'synced') button.classList.add(busy ? 'day-busy' : 'day-free');
        else button.classList.add(busy ? 'day-busy' : 'day-unknown');
        if (selected) button.classList.add('day-selected');
        if (within) button.classList.add('day-in-range');
        if (past) button.classList.add('day-past');
        button.textContent = String(day);
        button.disabled = past;
        const stateText = busy ? 'ocupado' : availability.status === 'synced' ? 'sin evento ocupado importado' : 'disponibilidad sin verificar';
        button.setAttribute('aria-label', `${day} de ${monthLabel.textContent}, ${stateText}${selected ? ', seleccionado' : ''}`);
        button.setAttribute('aria-pressed', String(Boolean(selected)));
        button.addEventListener('click', () => chooseDate(value));
        calendar.append(button);
      }
    }
    inputIn.addEventListener('change', () => {
      if (inputIn.value < todayValue || (inputOut.value && inputOut.value <= inputIn.value) || (inputIn.value && isBusy(inputIn.value))) {
        validation.textContent = 'La entrada debe ser futura y no coincidir con una fecha ocupada.';
        inputIn.value = '';
        inputOut.value = '';
      }
      inputOut.min = inputIn.value ? nextDay(inputIn.value) : todayValue;
      updateSelectionMessage();
    });
    inputOut.addEventListener('change', () => updateSelectionMessage());
    guestsInput.addEventListener('change', () => updateSelectionMessage());
    prev.addEventListener('click', () => { monthCursor = new Date(monthCursor.getFullYear(), monthCursor.getMonth() - 1, 1); renderCalendar(); });
    next.addEventListener('click', () => { monthCursor = new Date(monthCursor.getFullYear(), monthCursor.getMonth() + 1, 1); renderCalendar(); });
    whatsappLink.addEventListener('click', event => {
      const state = selectionState();
      if (state !== 'clear' && state !== 'unknown') {
        event.preventDefault();
        updateSelectionMessage();
        validation.focus?.();
      }
    });
    renderCalendar();
    updateSelectionMessage();
    fetch('/api/availability', { headers: { 'Accept': 'application/json' }, cache: 'no-store' })
      .then(response => { if (!response.ok) throw new Error('API no disponible'); return response.json(); })
      .then(data => {
        if (!data || !['synced', 'degraded', 'pending'].includes(data.status) || !Array.isArray(data.busy)) throw new Error('Respuesta no válida');
        availability = data;
        calendarStatus.textContent = data.message || 'Disponibilidad pendiente de sincronización. Consulta las fechas por WhatsApp.';
        calendarStatus.dataset.state = data.status;
        updateSelectionMessage();
      })
      .catch(() => {
        availability = { status: 'pending', busy: [], message: 'Disponibilidad pendiente de sincronización. Consulta las fechas por WhatsApp.' };
        calendarStatus.textContent = availability.message;
        calendarStatus.dataset.state = 'pending';
        updateSelectionMessage();
      });
  }

  // Interacciones sutiles: progreso de lectura y acceso rápido a reservas.
  const progressBar = document.querySelector('#scroll-progress-bar');
  const floatingBooking = document.querySelector('.floating-booking');
  const updateScrollUI = () => {
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    if (progressBar) progressBar.style.width = `${scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0}%`;
    if (floatingBooking) floatingBooking.classList.toggle('visible', window.scrollY > 520);
  };
  window.addEventListener('scroll', updateScrollUI, { passive: true });
  window.addEventListener('resize', updateScrollUI, { passive: true });
  updateScrollUI();

  // Evita que una fotografía externa rota deje un hueco vacío.
  document.querySelectorAll('.gallery-tile img').forEach(img => {
    img.addEventListener('error', () => {
      if (img.dataset.fallbackTried) return;
      img.dataset.fallbackTried = '1';
      img.src = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zahara%20de%20la%20Sierra%2C%20Spain.jpg';
    });
  });
})();
