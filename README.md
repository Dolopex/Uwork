# U-Work

Plataforma de microtrabajos universitarios construida con Django. Conecta estudiantes que buscan ingresos flexibles con empleadores que necesitan talento joven para tareas puntuales.

---

## Características principales

- **Registro por roles** — Flujo separado para estudiantes y empleadores con campos específicos por rol
- **Gestión de trabajos** — Publicar, buscar, filtrar y postularse a trabajos con categorías, modalidad y urgencia
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
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── templates/
│   ├── base.html             # Layout principal + sistema de temas
│   ├── accounts/             # 7 plantillas de cuentas
│   ├── jobs/                 # 6 plantillas de trabajos
│   └── reviews/              # 1 plantilla de reseñas
├── static/css/               # Estilos adicionales
└── media/                    # Uploads (perfiles, carnets, trabajos)
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
python manage.py createsuperuser

# 8. Cargar datos de prueba (opcional)
python manage.py seed_data

# 9. Iniciar servidor
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000/`.

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Si no se define `DATABASE_URL`, la app usa SQLite automáticamente (útil para desarrollo local).

---

## Despliegue en Vercel

1. Importar el repositorio en [vercel.com](https://vercel.com)
2. Agregar las variables de entorno en la configuración del proyecto:
   - `DATABASE_URL` → cadena de conexión de Neon
   - `SECRET_KEY` → clave secreta de Django
   - `DEBUG` → `False`
   - `ALLOWED_HOSTS` → tu dominio de Vercel
3. Vercel ejecutará `build_files.sh` automáticamente para colectar estáticos y migrar

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
