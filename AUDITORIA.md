# Auditoría y cambios — La Escalera

Fecha: 4 de noviembre de 2026. Alcance: proyecto estático HTML/CSS/JavaScript y backend Python incluido en el ZIP recibido.

## Cambios implementados

- Conservada la URL y la fotografía original del hero (`Zahara de la Sierra, Spain.jpg`). Se mantiene en HTML, con `loading="eager"`, `fetchpriority="high"` y `decoding="async"`; no se añadió `preload` para evitar una segunda descarga. Se ajustaron las dimensiones declaradas a las dimensiones publicadas en Wikimedia Commons (4608 × 3072) y se corrigió el texto alternativo para que describa la fortificación que identifica la ficha del archivo.
- Corregido el marcado inválido del hero: había un `h1` anidado dentro de un párrafo y dos encabezados principales. Ahora hay un solo `h1` con clase responsive.
- Sustituida la fotografía de la tarjeta «Pueblo, agua y montaña» por `Zahara-3.jpg`, cuya ficha describe expresamente Zahara, el embalse de Zahara-El Gastor y la Sierra de Grazalema.
- Sustituida la imagen que se presentaba como nocturna aunque su ficha describía una panorámica por el archivo de Commons titulado `Zahara de la Sierra - vista nocturna.jpg`. La licencia de esta ficha no se pudo confirmar con las herramientas disponibles; se indica explícitamente en los créditos y debe comprobarse antes de alojar una copia local.
- Cambiado `preload="metadata"` por `preload="none"` en los dos vídeos locales. Se conservan controles, `playsinline`, posters, fuentes y archivos MP4.
- Añadido un bloque desplegable de créditos con autoría/licencia para las fotografías cuyas fichas se verificaron y enlaces a las fichas originales. No se atribuye una licencia confirmada al archivo nocturno. La tarjeta de la Puerta de la Villa ahora declara expresamente que la imagen disponible en Commons es una reconstrucción documental, no una fotografía del monumento conservado; encontrar una foto real con licencia reutilizable sigue pendiente.
- Añadidas reglas responsive de apoyo, comportamiento para movimiento reducido y estilos legibles para créditos largos.
- Añadida una batería de 8 pruebas de regresión estática en `tests/test_site.py`.

## Fuentes de las fotografías del entorno

| Tarjeta | Archivo | Autoría | Licencia observada en la ficha |
|---|---|---|---|
| Panorámica del embalse | [Embalse de Zahara (1).jpg](https://commons.wikimedia.org/wiki/File:Embalse_de_Zahara_(1).jpg) | Vanbasten 23 | CC BY-SA 3.0 |
| Pueblo, agua y montaña | [Zahara-3.jpg](https://commons.wikimedia.org/wiki/File:Zahara-3.jpg) | Sergio T. Serrano Hernández | CC BY-SA 4.0 |
| Vistas desde el castillo | [Zahara Sierra Desde Castillo.jpg](https://commons.wikimedia.org/wiki/File:Zahara_Sierra_Desde_Castillo.jpg) | El Pantera | CC BY-SA; la ficha ofrece CC BY-SA 4.0 entre las licencias seleccionables |
| Calles blancas | [Calle en Zahara de la Sierra.jpeg](https://commons.wikimedia.org/wiki/File:Calle_en_Zahara_de_la_Sierra.jpeg) | Agustin Piñero | CC0 |
| Puerta de la Villa (reconstrucción documental, no foto) | [Puerta de la Villa.jpg](https://commons.wikimedia.org/wiki/File:Puerta_de_la_Villa.jpg) | Bocaleones | Dominio público; no satisface el requisito de una fotografía del monumento conservado |
| El pueblo desde lejos | [Panorama of Zahara de la Sierra, Cádiz.jpg](https://commons.wikimedia.org/wiki/File:Panorama_of_Zahara_de_la_Sierra,_C%C3%A1diz.jpg) | Alexwing | CC BY 2.5 ES |
| Zahara al anochecer | [Zahara de la Sierra - vista nocturna.jpg](https://commons.wikimedia.org/wiki/File:Zahara_de_la_Sierra_-_vista_nocturna.jpg) | Pendiente de verificar | No confirmada en esta auditoría; revisar la ficha exacta antes de redistribuir |
| Agua y montaña | [Zahara embalse.jpg](https://commons.wikimedia.org/wiki/File:Zahara_embalse.jpg) | soyignatius | CC BY 2.0 |
| Hero original | [Zahara de la Sierra, Spain.jpg](https://commons.wikimedia.org/wiki/File:Zahara_de_la_Sierra,_Spain.jpg) | Epithemeus | CC BY-SA 4.0 |

Las imágenes del entorno siguen cargándose desde Wikimedia Commons. No se han descargado a `assets/` porque la conexión saliente del entorno de ejecución falló al intentar comprobar/descargar los archivos. Por tanto, no se afirma que los recursos remotos hayan pasado una comprobación HTTP en vivo ni que se haya eliminado la dependencia externa.

## Pruebas ejecutadas

### Correctas

- `node --check js/main.js`
- `node --check js/i18n.js`
- `python -m py_compile backend/app.py`
- `python -m unittest discover -s tests -v`: 8 pruebas superadas.
- Servidor local del backend: `GET /`, `/css/styles.css` y `/js/main.js` devolvieron HTTP 200.
- `GET /api/health` devolvió HTTP 200 con estado `pending`.
- `GET /api/availability` devolvió HTTP 200, sin URLs privadas, con ambas fuentes (`booking`, `airbnb`) sin configurar y estado `pending`. No se simularon fechas libres ni reservas.
- `/ .env.example` (ruta real `/.env.example`) y `/backend/app.py` devolvieron HTTP 404.

### Pendientes / limitaciones reales

- La comprobación de red hacia Wikimedia Commons desde el contenedor falló por falta de conectividad saliente; no se pudo verificar el estado HTTP de las imágenes ni alojarlas localmente. La foto real de la Puerta de la Villa con licencia reutilizable y la licencia exacta de la fotografía nocturna siguen pendientes, y no se declaran criterios completados.
- Chromium headless no terminó la captura de pantalla en el límite de ejecución del entorno. No se declara validación visual real en navegador ni se entregan puntuaciones Lighthouse inventadas.
- No se dispone de las URLs privadas iCal de Booking.com/Airbnb; la disponibilidad de producción no se pudo comprobar. El backend local permanece correctamente en `pending`.
- No se han medido LCP, CLS, INP ni datos de producción antes/después. No hay base real para reportar esas métricas.
- Las 8 pruebas responsive comprueban reglas y estructura, no sustituyen una prueba visual completa en 320, 360, 390, 430, 768, 1024 y 1366 px.

## Publicación en GitHub Pages

1. Descomprime el ZIP y abre la carpeta `La-Escalera-Zahara-edited`.
2. Sube el contenido de esa carpeta al repositorio que publica la web, conservando las carpetas `assets/`, `css/` y `js/`.
3. En GitHub, abre **Settings → Pages** y configura la rama y carpeta de publicación que utiliza actualmente el proyecto (por ejemplo, `main` y `/root`).
4. No publiques `.env`, URLs iCal privadas ni secretos. La carpeta `backend/` no sustituye al servicio de Render: el calendario consulta la API indicada en `js/config.js`.
5. Tras publicar, abre la web en móvil y escritorio, revisa la consola y la pestaña Network; confirma que cada imagen externa responde correctamente y que `https://la-escalera-calendar.onrender.com/api/availability` informa el estado real esperado.
6. Antes de alojar localmente las fotos del entorno, descarga solo las que tengan licencia verificada, guarda los créditos/licencias correspondientes y actualiza `src` y `data-full` en el mismo cambio.
