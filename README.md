# La Escalera · web turística y calendario iCal

Proyecto existente ampliado, no reconstruido desde cero. Conserva galería/lightbox, información del alojamiento y el entorno, mapa, navegación responsive, enlaces a Booking.com, Airbnb e Instagram, formulario y accesos de WhatsApp.

## Mejoras de esta versión

- La marca **LA ESCALERA** aparece sobre el título principal de Zahara de la Sierra; el logotipo muestra **La Escalera** y las iniciales **LE**.
- Bloque principal «RESERVA DIRECTAMENTE Y AHORRA» con «10–15 % DE DESCUENTO» y botón directo a WhatsApp con el mensaje solicitado.
- Booking.com y Airbnb siguen accesibles como alternativas visualmente secundarias.
- Calendario mensual con navegación, selección de entrada/salida y huéspedes, leyenda accesible, validación de intervalos y consulta preparada por WhatsApp.
- Backend privado que importa intervalos iCalendar en el servidor, combina eventos y publica solo las fechas ocupadas y el estado general; no devuelve títulos ni datos de huéspedes.
- El calendario no declara fechas libres si las dos fuentes no están configuradas y sincronizadas correctamente.

## Ejecutar localmente

Se necesita Python 3.9 o posterior. El backend usa la biblioteca estándar, sin instalar paquetes externos.

1. Descomprime el proyecto.
2. Abre una terminal en la carpeta `la-escalera-web`.
3. Ejecuta `python backend/app.py`.
4. Abre `http://127.0.0.1:8000`.

Sin enlaces iCal, el calendario muestra «Disponibilidad pendiente de sincronización. Consulta las fechas por WhatsApp». Esto es lo esperado hasta configurar las fuentes.

## Configurar las fuentes iCal privadas

1. Copia `.env.example` y llámalo `.env` en la carpeta raíz del proyecto.
2. En la cuenta autorizada de **Booking.com**, abre la Extranet del alojamiento y busca **Precios y disponibilidad / Calendario → Sincronizar calendarios (Sync calendars)**. Si aparece la opción, crea una conexión de exportación y copia el enlace de calendario. Si la interfaz permite elegir el contenido exportado, incluye **fechas reservadas y fechas cerradas/bloqueadas**, no solo las reservadas. Booking.com no ofrece esta función a todas las propiedades; depende de la configuración y elegibilidad del alojamiento. Si no aparece, contacta con soporte de Booking.com o usa un gestor de canales compatible.
3. En **Airbnb**, abre el calendario del anuncio concreto → **Disponibilidad → Vincular calendarios / Connect calendars → Exportar calendario** y copia la URL iCal del anuncio. El anuncio público no revela este enlace privado.
4. Pega las URL privadas en `BOOKING_ICAL_URL` y `AIRBNB_ICAL_URL` dentro de `.env`. No las compartas en el HTML, JavaScript, repositorio público, capturas o mensajes públicos.
5. Configura `SYNC_INTERVAL=30` (minutos; mínimo 5) y ejecuta el backend. Reinícialo después de modificar `.env`.
6. Comprueba `http://127.0.0.1:8000/api/health` y `http://127.0.0.1:8000/api/availability`. La respuesta pública no debe incluir las URL privadas. Cuando ambas fuentes hayan importado correctamente, el estado será `synced`; si una falla, el calendario pasa a estado degradado y las fechas no ocupadas se muestran como «sin verificar».

**No se han añadido URL inventadas.** En esta entrega no se recibieron las URL privadas autorizadas, por lo que la sincronización real queda pendiente de configuración y no se afirma que se hayan importado reservas de este anuncio concreto.

## Cómo se interpreta el calendario

- Los eventos iCal se convierten en intervalos `[entrada, salida)`: la noche de entrada está ocupada y el día de salida queda excluido. Una reserva del 10 al 13 bloquea las noches 10, 11 y 12, pero no la noche del 13 por esa misma reserva.
- Los intervalos coincidentes o solapados se combinan para no duplicar fechas.
- Si una fuente falla, se conserva su última copia correcta y se informa de sincronización degradada; no se elimina el histórico ni se presentan las fechas desconocidas como libres.
- La web recibe fechas ocupadas, estado y marca temporal de sincronización, no los nombres, títulos ni descripciones de los eventos.
- La disponibilidad de iCal puede retrasarse. La selección no constituye confirmación ni bloquea una fecha; el propietario debe confirmar precio y disponibilidad.

## Importar frente a sincronizar en ambos sentidos

- **Importar en la web:** el backend lee los calendarios de Booking.com y Airbnb para mostrar ocupación en este sitio. Eso es lo implementado.
- **Sincronizar en ambos sentidos:** requiere además que cada plataforma importe la disponibilidad de las demás, o utilizar un gestor de canales/sistema de reservas autorizado. Este calendario web no crea reservas ni escribe bloqueos en Booking.com/Airbnb; por tanto, una consulta directa por WhatsApp debe registrarse en el sistema de gestión y bloquearse también en las plataformas según sus funciones autorizadas. Para reducir el riesgo de doble reserva, la opción más fiable es centralizar las reservas en un channel manager compatible y conectar ambos canales, en vez de confiar únicamente en importaciones iCal independientes.

## Configuración y seguridad

- `.env` no debe subirse al repositorio ni servirse como archivo público. `.gitignore` ya lo excluye y el servidor niega el acceso HTTP a `.env`, `.env.example` y `backend/`.
- El backend acepta únicamente URLs HTTPS de dominios oficiales de Booking.com/Airbnb, valida redirecciones y rechaza destinos que resuelvan a direcciones privadas/no públicas, limita la descarga a 5 MB y tiene un timeout de red.
- `python backend/app.py` utiliza el servidor WSGI de la biblioteca estándar y es para pruebas/local. En Linux, una opción de despliegue es instalar Gunicorn en el servidor y ejecutar `gunicorn --workers 1 --bind 127.0.0.1:8000 backend.app:application` detrás de un proxy HTTPS. Mantén un solo worker/proceso con esta caché en memoria; un despliegue multiworker necesita mover la caché y la tarea de sincronización a un servicio compartido persistente. El puerto del backend debe ser accesible solo desde el proxy.
- Las URL iCal son secretos de acceso al calendario. Si se filtran, revoca o regenera el enlace desde la plataforma si la opción está disponible.

## Enlaces conservados

- Booking.com: https://www.booking.com/hotel/es/la-escalera-zahara-de-la-sierra.es.html
- Airbnb: https://www.airbnb.es/rooms/1451979739905839541
- Instagram: https://www.instagram.com/alojamiento_rural_la_escalera/
- WhatsApp: https://wa.me/34645471761

## Promoción

El sitio informa de un descuento del 10–15 %, sujeto a confirmación por el alojamiento. El descuento aplicable, el precio final y las condiciones deben confirmarse directamente por WhatsApp antes de reservar. No se garantiza un precio inferior a las plataformas ni se inventan condiciones adicionales.

## Pruebas ejecutadas en esta entrega

- Sintaxis JavaScript (`node --check`) y compilación Python (`py_compile`).
- Parser iCal con un evento de prueba del 10 al 13 de octubre y otro cancelado; el intervalo devuelto fue `[2026-10-10, 2026-10-13)`, sin exponer su título.
- API en estado pendiente sin URL configuradas; respuesta sin URL privada.
- Pruebas del servidor para la página principal, bloqueo de `.env.example`, bloqueo de rutas fuera del proyecto y rechazo de métodos HTTP distintos de GET.
- Comprobación estructural HTML, IDs y referencias a CSS/JS/URLs, más integridad del ZIP.

No se pudo realizar una prueba real de importación de Booking.com/Airbnb porque no se proporcionaron los enlaces iCal autorizados. Tampoco se ha podido verificar el aspecto mediante un navegador automatizado en este entorno. La consulta por WhatsApp se prepara; no se envía automáticamente ni confirma una reserva.

## Referencias oficiales

- Airbnb, sincronización de calendarios: https://es.airbnb.com/help/article/99
- Booking.com Partners, sincronización de calendarios entre canales: https://www.youtube.com/watch?v=Smj-WfWpi4o
- Booking.com Connectivity Portal y limitaciones de integraciones directas: https://connect.booking.com/


## Pulido visual añadido

- Galería ampliada a ocho fotografías del entorno de Zahara de la Sierra (calles blancas, puerta histórica, panorámica del pueblo, vistas nocturnas y embalse), con ampliación en lightbox y leyendas. Las imágenes externas se sirven desde Wikimedia Commons; revisa la ficha individual de cada archivo para confirmar autoría y licencia.
- Diseño de galería tipo editorial, mosaico adaptable a móvil, animaciones suaves y estados hover/focus accesibles.
- Hero con mejor contraste, tipografía responsive, tarjetas con elevación sutil y CTA flotante para consultar la estancia.
- Barra de progreso de lectura y soporte para `prefers-reduced-motion`.
- Las fotografías corresponden al destino, no al interior del alojamiento. Conserva los créditos y consulta las licencias en las fichas enlazadas junto a la galería. Para máxima fiabilidad, descarga las imágenes autorizadas y sírvelas desde tu propio hosting.


## Idiomas y galería del pueblo

- Se ha añadido un selector de idioma con banderas en la parte superior del menú: español (predeterminado), inglés, alemán y francés. La preferencia elegida se guarda localmente en el navegador cuando el almacenamiento está disponible.
- La interfaz traduce las secciones principales, la galería, las opciones de camas y partes relevantes de la consulta/reserva. Algunos textos dinámicos o información de terceros pueden seguir apareciendo en español si no tienen una traducción definida.
- La galería mantiene las categorías «El alojamiento» y «Zahara y su entorno» para no saturar la página. Las fotos del pueblo se cargan desde Wikimedia Commons y requieren conexión a Internet.
