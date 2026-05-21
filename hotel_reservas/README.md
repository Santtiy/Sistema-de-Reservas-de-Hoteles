# Sistema de Reservas de Hotel

Plataforma web para la gestión integral de reservas hoteleras: disponibilidad de habitaciones, administración de reservas, control de pagos y panel de analíticas. Desarrollada con Django 5 y pensada para hoteles boutique en Colombia.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 5.0, Python 3.11 |
| Base de datos | PostgreSQL (producción) · SQLite (desarrollo) |
| Frontend | Bootstrap 5.3.3 · Bootstrap Icons 1.11.3 |
| Gráficas | Chart.js 4.4.1 |
| Reportes | ReportLab · openpyxl |
| Static files | WhiteNoise 6.x |
| Servidor WSGI | Gunicorn |
| Despliegue | Render.com |

---

## Estructura del proyecto

```
hotel_reservas/
├── core/                  # Configuración del proyecto
│   ├── settings/
│   │   ├── base.py        # Configuración común
│   │   ├── dev.py         # Desarrollo (SQLite)
│   │   └── prod.py        # Producción (PostgreSQL + seguridad)
│   ├── management/
│   │   └── commands/
│   │       └── seed_all.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/              # Autenticación y usuarios (Santy)
├── rooms/                 # Habitaciones y tipos (Samuel)
├── reservations/          # Flujo de reservas (Santy)
├── dashboard/             # Panel analítico (Pipe)
├── templates/             # Templates globales y parciales
├── static/                # CSS, JS, imágenes estáticas
├── Procfile
├── build.sh
├── requirements.txt
└── runtime.txt
```

---

## Instalación local

### Prerrequisitos
- Python 3.11+
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/<org>/Sistema-de-Reservas-de-Hoteles.git
cd Sistema-de-Reservas-de-Hoteles/hotel_reservas

# 2. Crear entorno virtual y activarlo
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores locales

# 5. Aplicar migraciones
python manage.py migrate

# 6. Cargar datos de prueba
python manage.py seed_all

# 7. Levantar el servidor de desarrollo
python manage.py runserver
```

Abre http://127.0.0.1:8000 en tu navegador.

---

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```env
# .env.example
SECRET_KEY=cambia-esto-por-una-clave-segura
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Base de datos (producción)
DATABASE_URL=postgres://user:password@host:5432/dbname

# Email SMTP
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-correo@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=no-reply@hotel.com
```

---

## Comandos principales

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Seed de datos de prueba (todos los módulos)
python manage.py seed_all

# Solo habitaciones
python manage.py seed_rooms

# Crear superusuario manualmente
python manage.py createsuperuser

# Recolectar archivos estáticos (producción)
python manage.py collectstatic --no-input

# Servidor de desarrollo
python manage.py runserver
```

---

## Despliegue en Render

### Paso 1 — Preparar el repositorio
Asegúrate de tener en la rama `main`:
- `hotel_reservas/build.sh` (ejecutable)
- `render.yaml` en la raíz del repositorio
- `hotel_reservas/Procfile`

### Paso 2 — Crear cuenta y conectar repositorio
1. Ir a [render.com](https://render.com) y registrarse con GitHub.
2. En el dashboard, hacer clic en **New → Blueprint**.
3. Seleccionar el repositorio `Sistema-de-Reservas-de-Hoteles`.
4. Render detectará el `render.yaml` automáticamente.

### Paso 3 — Configurar variables de entorno
En el servicio web dentro de Render, ir a **Environment** y completar:

| Variable | Valor |
|----------|-------|
| `SECRET_KEY` | Generado automáticamente |
| `DATABASE_URL` | Asignado desde la BD gratuita |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DJANGO_SETTINGS_MODULE` | `core.settings.prod` |
| `EMAIL_HOST_USER` | Tu correo Gmail |
| `EMAIL_HOST_PASSWORD` | App Password de Gmail |
| `DEFAULT_FROM_EMAIL` | `no-reply@hotel.com` |

### Paso 4 — Primer deploy
1. Hacer clic en **Manual Deploy → Deploy latest commit**.
2. El proceso ejecuta `build.sh` (instala deps, collectstatic, migrate).
3. Una vez activo, correr el seed en la **Shell** del servicio:
   ```bash
   python manage.py seed_all
   ```

### Paso 5 — URL pública
La URL pública será: `https://hotel-reservas.onrender.com`

> **Nota:** El plan gratuito de Render hiberna el servicio tras 15 min de inactividad. El primer request puede tardar ~30 s.

---

## Credenciales de prueba

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Administrador | admin@hotel.com | admin123 |
| Recepcionista | maria.gonzalez@hotel.com | recep123 |
| Recepcionista | carlos.rodriguez@hotel.com | recep123 |
| Cliente | cliente1@ejemplo.com | cliente123 |
| Cliente | cliente2@ejemplo.com | cliente123 |

---

## Equipo de desarrollo

| Integrante | Módulo(s) asignado(s) | Rol en el equipo |
|------------|----------------------|-----------------|
| **Santy** | Setup inicial, `accounts`, `reservations` | Líder técnico |
| **Samuel** | `rooms` (modelos, vistas, CRUD, seed_rooms) | Desarrollador backend |
| **Pipe** | `dashboard` (analíticas, reportes, Chart.js) | Desarrollador frontend/backend |
| **Juanjo** | Deploy (Render, CI, prod settings, seed_all, docs) | DevOps / documentación |

---

## Licencia

Proyecto académico — Universidad. Todos los derechos reservados © 2025.
