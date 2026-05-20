# Hotel Reservas

Sistema de gestion de reservas de hotel desarrollado con Django 5.x.

## Stack tecnologico
- Django 5.x
- Bootstrap 5 + Bootstrap Icons
- PostgreSQL (produccion) / SQLite (desarrollo)
- WhiteNoise para static

## Estructura de carpetas
- core/: configuracion del proyecto y settings por entorno
- accounts/: usuarios, autenticacion y roles
- rooms/: habitaciones
- reservations/: reservas
- dashboard/: panel administrativo
- templates/: templates globales
- static/: assets estaticos
- media/: archivos subidos

## Instalacion
1. Clonar repositorio
2. Crear y activar entorno virtual
3. Instalar dependencias
   - `pip install -r requirements.txt`
4. Crear archivo `.env` basado en `.env.example`
5. Migrar y crear superusuario
   - `python manage.py migrate`
   - `python manage.py createsuperuser`
6. Ejecutar servidor
   - `python manage.py runserver`

## Convenciones del equipo
- Ramas: `feature/nombre`, `fix/nombre`
- Commits: mensajes cortos y descriptivos en presente
- PRs: minimo una revision, checklist de pruebas basicas
