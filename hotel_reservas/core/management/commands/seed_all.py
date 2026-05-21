"""
Seed command: crea datos de prueba completos para el sistema hotelero.

Uso:
    python manage.py seed_all            # crea datos sin borrar los existentes
    python manage.py seed_all --reset    # borra todo y recrea desde cero
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from reservations.models import Payment, Reservation, ReservationStatusLog
from rooms.models import Amenity, Room, RoomImage, RoomType

User = get_user_model()
fake = Faker("es_CO")


class Command(BaseCommand):
    help = "Carga datos de prueba completos (usuarios, habitaciones, reservas)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina todos los datos existentes antes de crear los nuevos",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Eliminando datos existentes...")
            Payment.objects.all().delete()
            ReservationStatusLog.objects.all().delete()
            Reservation.objects.all().delete()
            RoomImage.objects.all().delete()
            Room.objects.all().delete()
            Amenity.objects.all().delete()
            RoomType.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()
            Group.objects.filter(name__in=["Cliente", "Recepcionista", "Admin"]).delete()
            self.stdout.write(self.style.WARNING("Datos anteriores eliminados."))

        self._seed_groups_and_permissions()
        self._seed_users()
        amenities = self._seed_amenities()
        room_types = self._seed_room_types()
        rooms = self._seed_rooms(room_types, amenities)
        self._seed_reservations(rooms)

        self.stdout.write(self.style.SUCCESS("¡Seed completado exitosamente!"))

    # ── Grupos y permisos ─────────────────────────────────────────────────────

    def _seed_groups_and_permissions(self):
        self.stdout.write("Creando grupos y asignando permisos...")

        # Garantiza que todos los permisos existan antes de buscarlos
        from django.apps import apps as django_apps
        from django.contrib.auth.management import create_permissions
        for app_config in django_apps.get_app_configs():
            create_permissions(app_config, verbosity=0)

        def get_perms(pairs):
            result = []
            for app_label, codename in pairs:
                try:
                    result.append(
                        Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename,
                        )
                    )
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"  Permiso no encontrado: {app_label}.{codename}")
                    )
            return result

        # ── Cliente ───────────────────────────────────────────────────────────
        cliente_group, _ = Group.objects.get_or_create(name="Cliente")
        cliente_group.permissions.set(get_perms([
            # Profile (cambios restringidos a "solo suyo" en las vistas)
            ("accounts", "change_profile"),
            ("accounts", "view_profile"),
            # Rooms — solo lectura
            ("rooms", "view_roomtype"),
            ("rooms", "view_room"),
            ("rooms", "view_roomimage"),
            ("rooms", "view_amenity"),
            # Reservations (filtrado a "solo suyas" en las vistas)
            ("reservations", "add_reservation"),
            ("reservations", "change_reservation"),  # cancelar si >48h — validado en vista
            ("reservations", "view_reservation"),
        ]))

        # ── Recepcionista ─────────────────────────────────────────────────────
        recep_group, _ = Group.objects.get_or_create(name="Recepcionista")
        recep_group.permissions.set(get_perms([
            # Accounts
            ("accounts", "view_customuser"),
            ("accounts", "change_profile"),
            ("accounts", "view_profile"),
            # Room Types
            ("rooms", "add_roomtype"),
            ("rooms", "change_roomtype"),
            ("rooms", "delete_roomtype"),
            ("rooms", "view_roomtype"),
            # Rooms
            ("rooms", "add_room"),
            ("rooms", "change_room"),
            ("rooms", "delete_room"),
            ("rooms", "view_room"),
            # Room Images
            ("rooms", "add_roomimage"),
            ("rooms", "change_roomimage"),
            ("rooms", "delete_roomimage"),
            ("rooms", "view_roomimage"),
            # Amenities
            ("rooms", "add_amenity"),
            ("rooms", "change_amenity"),
            ("rooms", "delete_amenity"),
            ("rooms", "view_amenity"),
            # Reservations
            ("reservations", "change_reservation"),  # cambiar estado — validado en vista
            ("reservations", "view_reservation"),
            # Payments
            ("reservations", "add_payment"),
            ("reservations", "change_payment"),  # reembolsos — validado en vista
            ("reservations", "view_payment"),
            # Status Log
            ("reservations", "add_reservationstatuslog"),
            ("reservations", "view_reservationstatuslog"),
        ]))

        # ── Admin ─────────────────────────────────────────────────────────────
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        admin_group.permissions.set(get_perms([
            # Accounts — acceso total
            ("accounts", "add_customuser"),
            ("accounts", "change_customuser"),
            ("accounts", "delete_customuser"),
            ("accounts", "view_customuser"),
            ("accounts", "add_profile"),
            ("accounts", "change_profile"),
            ("accounts", "delete_profile"),
            ("accounts", "view_profile"),
            # Room Types
            ("rooms", "add_roomtype"),
            ("rooms", "change_roomtype"),
            ("rooms", "delete_roomtype"),
            ("rooms", "view_roomtype"),
            # Rooms
            ("rooms", "add_room"),
            ("rooms", "change_room"),
            ("rooms", "delete_room"),
            ("rooms", "view_room"),
            # Room Images
            ("rooms", "add_roomimage"),
            ("rooms", "change_roomimage"),
            ("rooms", "delete_roomimage"),
            ("rooms", "view_roomimage"),
            # Amenities
            ("rooms", "add_amenity"),
            ("rooms", "change_amenity"),
            ("rooms", "delete_amenity"),
            ("rooms", "view_amenity"),
            # Reservations
            ("reservations", "change_reservation"),
            ("reservations", "delete_reservation"),
            ("reservations", "view_reservation"),
            # Payments
            ("reservations", "add_payment"),
            ("reservations", "change_payment"),
            ("reservations", "delete_payment"),
            ("reservations", "view_payment"),
            # Status Log
            ("reservations", "add_reservationstatuslog"),
            ("reservations", "change_reservationstatuslog"),
            ("reservations", "delete_reservationstatuslog"),
            ("reservations", "view_reservationstatuslog"),
            # Solo Admin: panel /admin/ de Django
            ("admin", "add_logentry"),
            ("admin", "change_logentry"),
            ("admin", "delete_logentry"),
            ("admin", "view_logentry"),
            ("auth", "add_group"),
            ("auth", "change_group"),
            ("auth", "delete_group"),
            ("auth", "view_group"),
            ("auth", "add_permission"),
            ("auth", "change_permission"),
            ("auth", "delete_permission"),
            ("auth", "view_permission"),
            ("contenttypes", "view_contenttype"),
            ("sessions", "add_session"),
            ("sessions", "change_session"),
            ("sessions", "delete_session"),
            ("sessions", "view_session"),
        ]))

        self.stdout.write("  Grupos listos: Cliente, Recepcionista, Admin")

    # ── Usuarios ──────────────────────────────────────────────────────────────

    def _seed_users(self):
        self.stdout.write("Creando usuarios...")

        # Superusuario / admin
        if not User.objects.filter(email="admin@hotel.com").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@hotel.com",
                password="admin123",
                first_name="Admin",
                last_name="Hotel",
            )
            admin.role = "ADMIN"
            admin.phone = "3001234567"
            admin.document_id = "1000000001"
            admin.save()
            self.stdout.write(f"  Superusuario: admin@hotel.com / admin123")

        # Recepcionistas
        recepcionistas = [
            {
                "username": "maria.gonzalez",
                "email": "maria.gonzalez@hotel.com",
                "first_name": "María",
                "last_name": "González",
                "phone": "3112345678",
                "document_id": "52345678",
            },
            {
                "username": "carlos.rodriguez",
                "email": "carlos.rodriguez@hotel.com",
                "first_name": "Carlos",
                "last_name": "Rodríguez",
                "phone": "3209876543",
                "document_id": "79876543",
            },
        ]
        for data in recepcionistas:
            if not User.objects.filter(email=data["email"]).exists():
                u = User.objects.create_user(
                    username=data["username"],
                    email=data["email"],
                    password="recep123",
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                )
                u.role = "RECEPCIONISTA"
                u.phone = data["phone"]
                u.document_id = data["document_id"]
                u.save()
                self.stdout.write(f"  Recepcionista: {data['email']}")

        # Clientes
        self.clientes = []
        for i in range(5):
            email = f"cliente{i+1}@ejemplo.com"
            if not User.objects.filter(email=email).exists():
                u = User.objects.create_user(
                    username=f"cliente{i+1}",
                    email=email,
                    password="cliente123",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                )
                u.role = "CLIENTE"
                u.phone = fake.numerify("3#########")
                u.document_id = fake.numerify("##########")
                u.save()
            self.clientes.append(User.objects.get(email=email))
        self.stdout.write(f"  5 clientes creados")

        # Asignar grupos según rol (idempotente: add ignora duplicados)
        role_group_map = {
            "ADMIN": "Admin",
            "RECEPCIONISTA": "Recepcionista",
            "CLIENTE": "Cliente",
        }
        for role, group_name in role_group_map.items():
            try:
                group = Group.objects.get(name=group_name)
                for user in User.objects.filter(role=role):
                    user.groups.add(group)
            except Group.DoesNotExist:
                pass
        self.stdout.write("  Usuarios asignados a sus grupos")

    # ── Amenidades ────────────────────────────────────────────────────────────

    def _seed_amenities(self):
        self.stdout.write("Creando amenidades...")
        amenities_data = [
            ("WiFi", "bi bi-wifi"),
            ("Piscina", "bi bi-droplet-fill"),
            ("Desayuno incluido", "bi bi-egg-fried"),
            ("Estacionamiento", "bi bi-car-front-fill"),
            ("Aire acondicionado", "bi bi-thermometer-snow"),
            ("Smart TV", "bi bi-tv-fill"),
            ("Caja fuerte", "bi bi-safe-fill"),
            ("Spa", "bi bi-flower1"),
        ]
        amenities = []
        for name, icon in amenities_data:
            obj, created = Amenity.objects.get_or_create(name=name, defaults={"icon": icon})
            amenities.append(obj)
        self.stdout.write(f"  {len(amenities)} amenidades listas")
        return amenities

    # ── Tipos de habitación ───────────────────────────────────────────────────

    def _seed_room_types(self):
        self.stdout.write("Creando tipos de habitación...")
        types_data = [
            {
                "name": "Individual",
                "base_price": 80,
                "capacity": 1,
                "description": "Habitación individual con vista al jardín, perfecta para viajeros de negocios.",
            },
            {
                "name": "Doble",
                "base_price": 120,
                "capacity": 2,
                "description": "Amplia habitación doble con cama queen size y balcón privado.",
            },
            {
                "name": "Suite",
                "base_price": 250,
                "capacity": 4,
                "description": "Suite de lujo con sala de estar, jacuzzi y vistas panorámicas de la ciudad.",
            },
        ]
        room_types = []
        for data in types_data:
            rt, _ = RoomType.objects.get_or_create(
                name=data["name"],
                defaults={
                    "base_price": data["base_price"],
                    "capacity": data["capacity"],
                    "description": data["description"],
                },
            )
            room_types.append(rt)
        self.stdout.write(f"  {len(room_types)} tipos de habitación listos")
        return room_types

    # ── Habitaciones ──────────────────────────────────────────────────────────

    def _seed_rooms(self, room_types, amenities):
        self.stdout.write("Creando habitaciones e imágenes...")
        # Distribución: 7 individuales, 8 dobles, 5 suites = 20
        distribution = [
            (room_types[0], 7, 1),   # Individual, pisos 1-2
            (room_types[1], 8, 2),   # Doble, pisos 2-3
            (room_types[2], 5, 4),   # Suite, pisos 4-5
        ]
        rooms = []
        room_number = 101
        statuses = ["AVAILABLE"] * 8 + ["MAINTENANCE"] + ["OUT_OF_SERVICE"]

        for rt, count, base_floor in distribution:
            for i in range(count):
                floor = base_floor + (i % 2)
                number = str(room_number)
                room_number += 1

                if Room.objects.filter(number=number).exists():
                    rooms.append(Room.objects.get(number=number))
                    continue

                room = Room.objects.create(
                    number=number,
                    room_type=rt,
                    floor=floor,
                    status=random.choice(statuses),
                    description=fake.paragraph(nb_sentences=2),
                )
                # Asignar 3-5 amenidades aleatorias
                room.amenities.set(random.sample(amenities, k=random.randint(3, 5)))

                # 2-3 imágenes por habitación
                img_count = random.randint(2, 3)
                seed_ids = random.sample(range(10, 999), img_count)
                for idx, seed_id in enumerate(seed_ids):
                    RoomImage.objects.create(
                        room=room,
                        image=f"https://picsum.photos/seed/{seed_id}/800/600",
                        caption=f"Habitación {number} - vista {idx + 1}",
                        is_main=(idx == 0),
                    )

                rooms.append(room)

        self.stdout.write(f"  {len(rooms)} habitaciones listas")
        return rooms

    # ── Reservas y pagos ──────────────────────────────────────────────────────

    def _seed_reservations(self, rooms):
        self.stdout.write("Creando reservas y pagos...")
        available_rooms = [r for r in rooms if r.status == "AVAILABLE"]
        if not available_rooms:
            available_rooms = rooms

        clientes = list(User.objects.filter(role="CLIENTE"))
        if not clientes:
            clientes = self.clientes

        recepcionistas = list(User.objects.filter(role="RECEPCIONISTA"))
        admin = User.objects.filter(role="ADMIN").first()
        staff = recepcionistas + ([admin] if admin else [])

        statuses = [
            "CONFIRMED", "CONFIRMED", "CONFIRMED",
            "CHECKED_IN", "CHECKED_IN",
            "CHECKED_OUT", "CHECKED_OUT", "CHECKED_OUT",
            "CANCELLED",
            "PENDING",
        ]
        payment_methods = ["CARD", "CARD", "TRANSFER", "CASH"]

        now = timezone.now()
        created_count = 0

        for i in range(30):
            room = random.choice(available_rooms)
            guest = random.choice(clientes)
            status = statuses[i % len(statuses)]

            # Fechas distribuidas en los últimos 6 meses
            days_ago = random.randint(1, 180)
            check_in = (now - timedelta(days=days_ago)).date()
            nights = random.randint(1, 7)
            check_out = check_in + timedelta(days=nights)

            # Para reservas futuras o en curso
            if status in ("PENDING", "CONFIRMED"):
                check_in = (now + timedelta(days=random.randint(1, 30))).date()
                check_out = check_in + timedelta(days=random.randint(1, 5))

            total = room.room_type.base_price * nights

            reservation = Reservation.objects.create(
                guest=guest,
                room=room,
                check_in=check_in,
                check_out=check_out,
                guests_count=random.randint(1, room.room_type.capacity),
                total_price=total,
                status=status,
                notes=fake.sentence() if random.random() > 0.6 else "",
            )

            # Pago (COMPLETED para reservas terminadas o en curso)
            pay_status = "COMPLETED" if status in ("CONFIRMED", "CHECKED_IN", "CHECKED_OUT") else "PENDING"
            method = random.choice(payment_methods)
            Payment.objects.create(
                reservation=reservation,
                amount=total,
                method=method,
                status=pay_status,
                transaction_id=fake.bothify(text="TXN-????-########"),
                paid_at=timezone.now() - timedelta(days=days_ago) if pay_status == "COMPLETED" else None,
                card_last4=fake.numerify(text="####") if method == "CARD" else "",
            )

            # Log de estado inicial
            if staff:
                ReservationStatusLog.objects.create(
                    reservation=reservation,
                    previous_status="PENDING",
                    new_status=status,
                    changed_by=random.choice(staff),
                    notes="Estado inicial asignado por seed.",
                )

            created_count += 1

        self.stdout.write(f"  {created_count} reservas y pagos creados")
