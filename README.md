# U-Work

Plataforma de microtrabajos universitarios construida con Django. Conecta estudiantes que buscan ingresos flexibles con empleadores que necesitan talento joven para tareas puntuales.
---
**LINK**: https://u-work.vercel.app
---

## Características principales

- **Registro por roles** — Flujo separado para estudiantes y empleadores con campos específicos por rol
- **Gestión de trabajos** — Publicar, buscar, filtrar y postularse a trabajos con categorías, modalidad y urgencia
- **Moderación previa a publicar** — Toda publicación pasa por revisión del personal antes de hacerse visible (Términos §6)
- **Canal de apelación** — El usuario sancionado puede pedir la revisión de su sanción y recibe respuesta
- **Bitácora de sanciones** — Registro de auditoría inmutable: quién sancionó, a quién, cuándo y por qué
- **Panel de soporte** — Cola de tickets que el personal responde y cierra, con aviso al usuario
- **Notificaciones** — Avisos en la app de postulaciones, aceptación, reseñas, sanciones, apelaciones y tickets
- **Ciclo de trabajo completo** — Publicación → Postulación → Asignación → Finalización → Reseña
- **Sistema de reseñas** — Calificación de 1-5 estrellas con comentarios, promedio calculado por usuario
- **Dashboard analítico** — Ingresos/gastos, desglose por categoría, tendencias de 6 meses, contadores de estado
- **Tema claro/oscuro** — Tema claro por defecto, tema oscuro configurable desde la selección de rol o dentro de la app
- **Moneda COP** — Precios y pagos en pesos colombianos con formato local
- **Diseño mobile-first** — Interfaz responsive con Bootstrap 5.3.3

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Django 5.2 / Python 3.11 |
| Base de datos (producción) | Neon PostgreSQL (serverless) |
| Base de datos (desarrollo) | SQLite (fallback automático) |
| Deployment | Vercel (serverless) |
| Static files | WhiteNoise |
| Frontend | Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Inter font |
| Imágenes | Pillow |
| Idioma | Español (es) |
| Zona horaria | America/Bogota |

---

## Estructura del proyecto

```
U-Work/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── uwork/                    # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # Usuarios, autenticación, perfiles
│   ├── models.py             # Modelo User personalizado
│   ├── views.py              # Registro, login, perfil, balance
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── templatetags/
│       └── form_tags.py      # Filtros: add_class, split, cop
├── jobs/                     # Trabajos y postulaciones
│   ├── models.py             # Modelos Job y Application
│   ├── views.py              # CRUD de trabajos, postulaciones
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── reviews/                  # Reseñas y calificaciones
│   ├── models.py             # Modelo Review (1-5 estrellas)
│   ├── signals.py            # Recalcula calificacion_promedio al crear/borrar
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── notifications/            # Avisos dentro de la app
│   ├── models.py             # Modelo Notification
│   ├── views.py              # Listado y contador de no leídas
│   ├── context_processors.py # Badge de la barra superior
│   └── urls.py
├── support/                  # Módulo de soporte
│   ├── models.py             # Modelo SupportTicket
│   ├── views.py              # Crear ticket, mis tickets, panel de staff
│   ├── forms.py
│   └── urls.py
├── legal/                    # Términos y Política de Privacidad (R14, R15)
│   ├── views.py
│   └── urls.py
├── moderation/               # Reportes, sanciones y apelaciones (§6.5.4)
│   ├── models.py             # Reporte, Sancion, Apelacion
│   ├── views.py              # Paneles de staff y canal de apelación
│   ├── forms.py
│   └── urls.py
├── templates/
│   ├── base.html             # Layout principal + sistema de temas
│   ├── accounts/             # Plantillas de cuentas
│   ├── jobs/                 # Plantillas de trabajos
│   ├── reviews/              # Plantillas de reseñas
│   ├── notifications/        # Listado de notificaciones
│   ├── support/              # Tickets de soporte y panel de staff
│   ├── moderation/           # Paneles de moderación y canal de apelación
│   └── legal/                # Documentos legales públicos
├── static/css/               # Estilos adicionales
├── media/                    # Uploads (perfiles, carnets, trabajos)
├── .env.example              # Plantilla de variables de entorno
├── api/index.py              # Entrypoint WSGI para Vercel (no es una API)
└── uwork/
    ├── settings.py
    ├── middleware.py         # CSP con nonce por request
    └── context_processors.py # nonce de la CSP en las plantillas
```

---

## Modelos

### User (accounts)

Extiende `AbstractUser` con campos adicionales:

| Campo | Tipo | Descripción |
|---|---|---|
| `rol` | Choice | ESTUDIANTE o EMPLEADOR |
| `foto` | ImageField | Foto de perfil |
| `cedula` | CharField | Número de identificación |
| `telefono` | CharField | Teléfono de contacto |
| `direccion` | CharField | Ubicación |
| `fecha_nacimiento` | DateField | Fecha de nacimiento |
| `habilidades` | TextField | Habilidades separadas por coma |
| `calificacion_promedio` | DecimalField | Rating promedio (0-5) |
| `universidad` | CharField | Solo estudiantes |
| `carrera` | CharField | Solo estudiantes |
| `semestre` | SmallIntegerField | Solo estudiantes |
| `foto_carnet` | ImageField | Solo estudiantes |

### Job (jobs)

| Campo | Tipo | Descripción |
|---|---|---|
| `titulo` | CharField | Título del trabajo |
| `descripcion` | TextField | Descripción detallada |
| `requisitos` | TextField | Requisitos del trabajo |
| `habilidades_requeridas` | CharField | Habilidades separadas por coma |
| `pago` | DecimalField | Monto en COP |
| `estado` | Choice | DISPONIBLE, EN_PROCESO, FINALIZADO |
| `categoria` | Choice | Académico, Tecnología, Diseño, Redacción, Traducción, Otro |
| `modalidad` | Choice | Presencial, Remoto, Híbrido |
| `ubicacion` | CharField | Ciudad/dirección |
| `urgente` | BooleanField | Trabajo urgente |
| `imagen` | ImageField | Imagen de referencia |
| `creador` | ForeignKey(User) | Empleador que publicó |
| `asignado` | ForeignKey(User) | Estudiante asignado |
| `fecha_limite` | DateField | Fecha límite |

### Application (jobs)

| Campo | Tipo | Descripción |
|---|---|---|
| `usuario` | ForeignKey(User) | Postulante |
| `trabajo` | ForeignKey(Job) | Trabajo al que postula |
| `mensaje` | TextField | Mensaje de postulación |
| `estado` | Choice | PENDIENTE, ACEPTADA, RECHAZADA |

Restricción: un usuario solo puede postularse una vez por trabajo.

### Review (reviews)

| Campo | Tipo | Descripción |
|---|---|---|
| `autor` | ForeignKey(User) | Quien escribe la reseña |
| `receptor` | ForeignKey(User) | Usuario reseñado |
| `trabajo` | ForeignKey(Job) | Trabajo relacionado |
| `puntuacion` | SmallIntegerField | 1-5 estrellas |
| `comentario` | TextField | Comentario opcional |

Restricción: una reseña por combinación autor-receptor-trabajo.

---

## Rutas

### Accounts

| Ruta | Vista | Descripción |
|---|---|---|
| `/` | `role_select` | Selección de rol |
| `/register/student/` | `register_student` | Registro de estudiante |
| `/register/employer/` | `register_employer` | Registro de empleador |
| `/login/` | `LoginView` | Iniciar sesión |
| `/logout/` | `LogoutView` | Cerrar sesión |
| `/profile/` | `profile` | Editar perfil |
| `/balance/` | `balance` | Dashboard analítico |
| `/user/<id>/` | `user_detail` | Perfil público |

### Jobs

| Ruta | Vista | Descripción |
|---|---|---|
| `/jobs/` | `job_list` | Explorar trabajos |
| `/jobs/job/new/` | `job_create` | Crear trabajo |
| `/jobs/job/<id>/` | `job_detail` | Detalle del trabajo |
| `/jobs/job/<id>/edit/` | `job_edit` | Editar trabajo |
| `/jobs/job/<id>/apply/` | `job_apply` | Postularse |
| `/jobs/job/<id>/applicants/` | `job_applicants` | Ver postulantes |
| `/jobs/job/<id>/accept/<app_id>/` | `accept_applicant` | Aceptar postulante |
| `/jobs/job/<id>/finish/` | `job_finish` | Finalizar trabajo |
| `/jobs/my-jobs/` | `my_jobs` | Mis trabajos |

### Reviews

| Ruta | Vista | Descripción |
|---|---|---|
| `/reviews/job/<id>/review/` | `create_review` | Escribir reseña |

### Notificaciones

| Ruta | Vista | Descripción |
|---|---|---|
| `/notificaciones/` | `notification_list` | Bandeja de avisos |
| `/notificaciones/<id>/leer/` | `mark_read` | Marcar como leído |
| `/notificaciones/api/no-leidas/` | `unread_count` | Contador (JSON) |

### Soporte

| Ruta | Vista | Descripción |
|---|---|---|
| `/soporte/` | `ticket_create` | Abrir un reporte |
| `/soporte/mis-reportes/` | `my_tickets` | Historial de tickets |
| `/soporte/panel/` | `panel_tickets` | Cola de tickets (staff) |
| `/soporte/panel/<id>/resolver/` | `resolver_ticket` | Responder y cerrar (staff) |

### Legal

| Ruta | Vista | Descripción |
|---|---|---|
| `/terminos-y-condiciones/` | `terminos` | Términos y Condiciones (R14) |
| `/politica-de-privacidad/` | `privacidad` | Política de Privacidad (R15) |

### Moderación

| Ruta | Vista | Descripción |
|---|---|---|
| `/moderacion/panel/` | `panel_reportes` | Cola de reportes (staff) |
| `/moderacion/panel/publicaciones/` | `panel_publicaciones` | Revisión previa a publicar (staff) |
| `/moderacion/panel/reporte/<id>/resolver/` | `resolver_reporte` | Resolver reporte (staff) |
| `/moderacion/panel/publicacion/<id>/revisar/` | `revisar_trabajo` | Aprobar o rechazar (staff) |
| `/moderacion/bitacora/` | `bitacora_sanciones` | Bitácora de sanciones (staff) |
| `/moderacion/apelaciones/` | `panel_apelaciones` | Apelaciones (staff) |
| `/moderacion/apelacion/` | `apelacion_crear` | Presentar una apelación |
| `/moderacion/apelaciones/mias/` | `mis_apelaciones` | Mis apelaciones |
| `/moderacion/reportar/<id>/` | `reportar_trabajo` | Reportar una publicación |

---

## Instalación

### Requisitos previos

- Python 3.10+

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/Dolopex/Uwork.git
cd U-Work

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env   # (o crear .env manualmente)
# Editar .env con tu DATABASE_URL de Neon y SECRET_KEY

# 6. Aplicar migraciones
python manage.py migrate

# 7. Crear superusuario (opcional)
# Ojo: `createsuperuser` de Django NO sirve aquí. El backend de
# autenticación (accounts.backends.EmailVerifiedBackend) rechaza las
# cuentas sin correo verificado, así que un superusuario creado con
# createsuperuser se queda sin poder iniciar sesión.
#
# Usa el comando del proyecto, que además es idempotente:
python manage.py crear_admin

# Lee la contraseña de DJANGO_SUPERUSER_PASSWORD. Sin esa variable no
# crea nada y avisa por pantalla (preferible a una contraseña
# predecible).

# 8. Cargar datos de prueba (opcional)
python manage.py seed_data

# 9. Iniciar servidor
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000/`.

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto a partir de la plantilla:

```bash
cp .env.example .env
```

Las variables que importan:

```env
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://tu-dominio.vercel.app
SITE_URL=https://tu-dominio.vercel.app
RESEND_API_KEY=re_...
```

- `CSRF_TRUSTED_ORIGINS` y `SITE_URL` son obligatorias en producción: la
  primera para que el token CSRF sea válido detrás del proxy de Vercel y la
  segunda para que los enlaces de verificación, sanción y apelación apunten
  al dominio real.
- Si no se define `DATABASE_URL`, la app usa SQLite automáticamente (útil
  para desarrollo local).
- Si no se define `RESEND_API_KEY`, los correos se imprimen en la consola.

---

## Despliegue en Vercel

1. Importar el repositorio en [vercel.com](https://vercel.com)
2. Agregar las variables de entorno en la configuración del proyecto:
   - `DATABASE_URL` → cadena de conexión de Neon
   - `SECRET_KEY` → clave secreta de Django
   - `DEBUG` → `False`
   - `ALLOWED_HOSTS` → tu dominio de Vercel
   - `CSRF_TRUSTED_ORIGINS` → `https://tu-dominio.vercel.app`
   - `SITE_URL` → `https://tu-dominio.vercel.app`
   - `RESEND_API_KEY` → clave de Resend (para los correos reales)
3. Vercel ejecutará `build_files.sh` automáticamente para colectar estáticos y migrar

Notas de despliegue:

- `SECURE_PROXY_SSL_HEADER` está configurado para que HTTPS funcione detrás
  del proxy de Vercel. Sin él, `SECURE_SSL_REDIRECT` responde 301 en bucle.
- `api/index.py` es el entrypoint WSGI de Vercel. **No es una API**: no hay
  DRF ni endpoints JSON más allá del contador de notificaciones.
- **El almacenamiento de archivos sigue pendiente de contrato.** En Vercel el
  disco local no persiste, así que las fotos de perfil y las imágenes de los
  trabajos se pierden. Hay que definir `STORAGE_BACKEND` con django-storages
  y contratar un proveedor (Vercel Blob, S3 o Cloudinary).

---

## Sistema de temas

La app usa un sistema dual de temas basado en CSS custom properties:

- **Tema claro** — Por defecto. Fondos blancos, texto oscuro, tarjetas sólidas.
- **Tema oscuro** — Activable con toggle. Glassmorphism, fondos translúcidos, animación de partículas.

El tema se persiste en `localStorage` y se puede cambiar desde:

1. La página de selección de rol (antes de iniciar sesión)
2. El topbar o sidebar dentro de la app

---

## Filtros de plantilla personalizados

| Filtro | Uso | Descripción |
|---|---|---|
| `add_class` | `{{ field\|add_class:"form-control" }}` | Agrega clase CSS a un campo de formulario |
| `split` | `{{ texto\|split:"," }}` | Divide un string por delimitador |
| `cop` | `{{ monto\|cop }}` | Formatea número como COP: `$350.000` |

---

## Panel de administración

Accesible en `/admin/` con un superusuario. Registra los modelos User, Job, Application y Review con filtros y fieldsets personalizados.

### El superusuario en producción

El comando `python manage.py crear_admin` crea el superusuario (o repara el que ya existe) y está pensado para correr en cada despliegue:

- Es **idempotente**: si la cuenta ya está, la repara sin tocar la contraseña.
- Pone `is_email_verified=True`, sin lo cual el backend de autenticación no deja entrar ni al superusuario.
- Lee la contraseña de `DJANGO_SUPERUSER_PASSWORD`. Si no está definida, no hace nada y avisa.

El `buildCommand` de `vercel.json` lo ejecuta junto con `migrate` y `collectstatic`, de modo que un despliegue deja la base al día y garantiza que el superusuario existe.

Define estas variables en el panel de Vercel (Settings > Environment Variables), **nunca en el repositorio**:

```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=tu@correo.com
DJANGO_SUPERUSER_PASSWORD=(una contraseña larga)
```

### Los paneles propios

El personal no usa `/admin/`, sino los paneles de la aplicación, que exigen `is_staff`:

| Panel | Ruta |
|---|---|
| Moderación de reportes | `/moderacion/panel/` |
| Moderación previa de publicaciones | `/moderacion/panel/publicaciones/` |
| Bitácora de sanciones | `/moderacion/bitacora/` |
| Apelaciones | `/moderacion/apelaciones/` |
| Cola de soporte | `/soporte/panel/` |

---

## Sistema de diseño

La app usa un sistema de tokens propio, en `static/css/style.css`, cargado por
todas las plantillas (las que heredan `base.html` y las independientes).

| Capa | Dónde |
|---|---|
| Tokens (color, radio, sombra, espaciado, tipografía) | `static/css/style.css` |
| Primitivas (superficie, chip, botón, encabezado de página, vacío) | `static/css/style.css` |
| Maquetado del shell (barra, sidebar, bottom-nav) | `templates/base.html` |
| Filosofía visual | `design/FILOSOFIA.md` |
| Hoja visual del sistema | `design/sistema-visual.png` |

Reglas que gobiernan el sistema:

1. **Un solo acento** (índigo). `--primary` es el acento como texto y
   `--primary-solid` como relleno: en tema oscuro el texto necesita ser claro
   y el relleno saturado.
2. **Una escala de radios** (6/8/12/16/20), **una de elevación** (xs/sm/md/lg),
   **una tipográfica** (32/22/18/16/14/13/12/11).
3. **Sombras neutras** teñidas al fondo. Nunca halos de color.
4. **El color codifica estado**, nunca decora. Verde es correcto, ámbar es
   atención, rojo es peligro, azul es información.
5. **El acento se reserva para actuar**: botones, enlaces activos y foco.

Añadir un color, un radio o una sombra fuera de estas escalas rompe el
sistema: se nota en la primera pantalla.

---

## Seguridad

| Control | Dónde |
|---|---|
| Content-Security-Policy con nonce por request | `uwork/middleware.py` |
| HTTPS detrás del proxy de Vercel | `SECURE_PROXY_SSL_HEADER` |
| Cierre de sesión de usuarios sancionados | `accounts/middleware.py` |
| Rate-limiting por IP en endpoints sensibles | `accounts/middleware.py` |
| Validación MIME y de tamaño real de uploads | `accounts/upload_validators.py` |
| Canal de apelación para el sancionado | `accounts/middleware.py` |

La CSP se emite de verdad: `uwork/middleware.py` genera un nonce por request
y lo inyecta en `script-src` y `style-src`. Los manejadores inline
(`onclick`, `onsubmit`, `onchange`) están prohibidos por esa política, así
que todas las plantillas los registran con `addEventListener` y las
etiquetas `<script>` llevan `nonce="{{ csp_nonce }}"`.
