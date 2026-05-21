# Sistema de Reservas de Hotel

Aplicación web completa para gestión de reservas hoteleras, desarrollada con Django 5. Permite a los clientes buscar habitaciones, realizar reservas y recibir confirmaciones por email con código QR, mientras que el personal administrativo cuenta con un panel de control con KPIs, reportes y exportaciones.

## Tabla de contenidos

- [Características](#características)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Instalación local](#instalación-local)
- [Variables de entorno](#variables-de-entorno)
- [Comandos útiles](#comandos-útiles)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Módulos principales](#módulos-principales)
- [Sistema de roles](#sistema-de-roles)
- [Despliegue en Render](#despliegue-en-render)
- [Credenciales de prueba](#credenciales-de-prueba)

---

## Características

**Para clientes:**
- Catálogo de habitaciones con filtros por tipo, capacidad, precio y disponibilidad por fechas
- Reserva online con cálculo automático del precio según noches
- Código de confirmación único y código QR adjunto por email
- Historial de reservas y posibilidad de cancelación (hasta 48h antes del check-in)
- Perfil de usuario con teléfono y documento de identidad

**Para recepcionistas y administradores:**
- Panel de control con KPIs en tiempo real (ocupación, ingresos, reservas activas)
- Gráficas interactivas (reservas por mes, ingresos, habitaciones más solicitadas)
- CRUD completo de habitaciones, tipos y amenidades
- Gestión del ciclo de vida de reservas (check-in, check-out, reembolso)
- Log de cambios de estado por reserva
- Exportación de reportes a PDF y Excel

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 5, Python 3.11.9 |
| Base de datos (prod) | PostgreSQL |
| Base de datos (dev) | SQLite3 |
| Frontend | Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4 |
| Formularios | django-crispy-forms + crispy-bootstrap5 |
| Archivos estáticos | WhiteNoise |
| Servidor | Gunicorn |
| Emails | SMTP (Gmail) / Console (desarrollo) |
| Generación de QR | qrcode |
| Reportes PDF | ReportLab |
| Reportes Excel | openpyxl |
| Imágenes | Pillow |
| Hosting | Render.com |

---

## Arquitectura

El proyecto sigue la arquitectura MVT de Django, organizado en cuatro aplicaciones independientes:

```
accounts       → Autenticación, roles y perfiles de usuario
rooms          → Catálogo y gestión de habitaciones
reservations   → Ciclo completo de reservas y pagos
dashboard      → Análisis, KPIs y exportación de reportes
```

La configuración de Django está dividida en tres archivos (`base.py`, `dev.py`, `prod.py`) para separar los entornos de desarrollo y producción.

---

## Instalación local

**Requisitos previos:** Python 3.11+ y Git.

```bash
# 1. Clonar el repositorio
git clone https://github.com/Santtiy/Sistema-de-Reservas-de-Hoteles.git
cd Sistema-de-Reservas-de-Hoteles

# 2. Crear y activar entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r hotel_reservas/requirements.txt

# 4. Configurar variables de entorno
cp hotel_reservas/.env.example hotel_reservas/.env
# Editar .env con los valores adecuados

# 5. Aplicar migraciones
cd hotel_reservas
python manage.py migrate --settings=core.settings.dev

# 6. Cargar datos de prueba
python manage.py seed_all --settings=core.settings.dev

# 7. Iniciar servidor de desarrollo
python manage.py runserver --settings=core.settings.dev
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000) en tu navegador.

---

## Variables de entorno

Crea el archivo `hotel_reservas/.env` basándote en `.env.example`:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (dev usa SQLite por defecto)
DATABASE_URL=sqlite:///db.sqlite3

# Email (en desarrollo usa 'console' para ver emails en terminal)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-de-google
DEFAULT_FROM_EMAIL=no-reply@hotel.com
```

En producción, `render.yaml` gestiona automáticamente `SECRET_KEY`, `DATABASE_URL` y las variables de email.

---

## Comandos útiles

```bash
# Aplicar migraciones
python manage.py migrate --settings=core.settings.dev

# Crear superusuario
python manage.py createsuperuser --settings=core.settings.dev

# Poblar la base de datos con datos de prueba
python manage.py seed_all --settings=core.settings.dev

# Limpiar y repoblar desde cero
python manage.py seed_all --reset --settings=core.settings.dev

# Solo habitaciones (parametrizable)
python manage.py seed_rooms --rooms 20 --settings=core.settings.dev

# Recolectar archivos estáticos (producción)
python manage.py collectstatic --settings=core.settings.prod
```

---

## Estructura del proyecto

```
Sistema-de-Reservas-de-Hoteles/
├── render.yaml                  # Blueprint de despliegue en Render
└── hotel_reservas/
    ├── core/                    # Configuración del proyecto
    │   ├── settings/
    │   │   ├── base.py
    │   │   ├── dev.py
    │   │   └── prod.py
    │   ├── management/commands/
    │   │   └── seed_all.py      # Datos de prueba completos
    │   ├── urls.py
    │   └── home_urls.py
    ├── accounts/                # Autenticación y perfiles
    ├── rooms/                   # Catálogo de habitaciones
    ├── reservations/            # Reservas y pagos
    ├── dashboard/               # Panel analítico
    ├── templates/               # Templates globales (base, home, partials)
    ├── static/                  # CSS, JS, imágenes
    ├── requirements.txt
    ├── Procfile
    ├── build.sh
    ├── runtime.txt              # python-3.11.9
    └── .env.example
```

---

## Módulos principales

### `accounts` — Usuarios y autenticación

Extiende `AbstractUser` con un campo `role` (ADMIN, RECEPCIONISTA, CLIENTE) y perfil asociado. Incluye registro, login/logout, cambio de contraseña y decoradores de autorización por rol.

### `rooms` — Habitaciones

Modelos: `RoomType`, `Amenity`, `Room`, `RoomImage`.

Cada habitación pertenece a un tipo (Simple, Doble, Suite…), tiene amenidades (WiFi, Piscina, Spa…), estado (AVAILABLE, MAINTENANCE, OUT_OF_SERVICE) e imágenes referenciadas por URL. El catálogo público permite filtrar por tipo, capacidad, precio y disponibilidad en un rango de fechas.

### `reservations` — Reservas

Modelos: `Reservation`, `Payment`, `ReservationStatusLog`.

Flujo completo: selección de habitación → elección de fechas → validación de disponibilidad → cálculo de precio → simulación de pago → confirmación por email con QR. Los cambios de estado quedan registrados en `ReservationStatusLog`.

### `dashboard` — Análisis

Vista de KPIs con tarjetas métricas y gráficas Chart.js alimentadas por APIs JSON propias. Permite exportar reportes de reservas, ingresos y ocupación en formato PDF (ReportLab) y Excel (openpyxl).

---

## Sistema de roles

| Permiso | Cliente | Recepcionista | Admin |
|---------|:-------:|:-------------:|:-----:|
| Ver catálogo de habitaciones | ✓ | ✓ | ✓ |
| Crear y ver sus propias reservas | ✓ | ✓ | ✓ |
| Cancelar sus propias reservas | ✓ | ✓ | ✓ |
| CRUD de habitaciones y amenidades | — | ✓ | ✓ |
| Gestionar reservas de otros usuarios | — | ✓ | ✓ |
| Registrar pagos y reembolsos | — | ✓ | ✓ |
| Ver dashboard y exportar reportes | — | ✓ | ✓ |
| Panel de administración de Django | — | — | ✓ |
| Gestión de usuarios y grupos | — | — | ✓ |

---

## Despliegue en Render

El archivo `render.yaml` define toda la infraestructura como código:

1. **Conecta** tu fork del repositorio en [render.com](https://render.com)
2. Render detecta `render.yaml` y crea el servicio web y la base de datos PostgreSQL automáticamente
3. El build ejecuta `build.sh` (instala dependencias, `collectstatic`, `migrate`)
4. El servidor inicia con `gunicorn core.wsgi:application`

Las siguientes variables de entorno deben configurarse manualmente en el panel de Render (o ya están en `render.yaml`):

```
SECRET_KEY         (generar un valor seguro)
EMAIL_HOST_USER    (cuenta Gmail)
EMAIL_HOST_PASSWORD (contraseña de aplicación de Google)
DEFAULT_FROM_EMAIL
```

---

## Credenciales de prueba

Tras ejecutar `python manage.py seed_all`, se crean los siguientes usuarios:

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Admin | `admin` | `admin1234` |
| Recepcionista | `recepcionista1` | `test1234` |
| Cliente | `cliente1` | `test1234` |
| Cliente | `cliente2` | `test1234` |

El panel de administración de Django está disponible en `/admin/`.

---

## Equipo de desarrollo

Proyecto académico desarrollado como trabajo final de curso.

- **Santtiy** — [GitHub](https://github.com/Santtiy)
- **SamuelMenan** — [GitHub](https://github.com/SamuelMenan)
- **Juanenriquezcc** — [GitHub](https://github.com/Juanenriquezcc)
- **benavides17**— [GitHub](https://github.com/benavides17)
