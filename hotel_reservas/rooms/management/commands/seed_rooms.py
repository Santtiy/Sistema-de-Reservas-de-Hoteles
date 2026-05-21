"""Crea datos de prueba para la app rooms: 3 tipos, 8 amenities, 15 habitaciones."""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from rooms.models import Amenity, Room, RoomImage, RoomType

try:
    from faker import Faker
    fake = Faker("es_CO")
except ImportError:
    fake = None


ROOM_TYPES = [
    {
        "name": "Individual",
        "description": "Habitación cómoda para una persona, con todas las comodidades esenciales.",
        "base_price": Decimal("80.00"),
        "capacity": 1,
    },
    {
        "name": "Doble",
        "description": "Espaciosa habitación para dos personas, ideal para parejas o viajeros de negocios.",
        "base_price": Decimal("120.00"),
        "capacity": 2,
    },
    {
        "name": "Suite Premium",
        "description": "Suite de lujo con sala separada, jacuzzi y vistas privilegiadas.",
        "base_price": Decimal("250.00"),
        "capacity": 4,
    },
]

AMENITIES = [
    ("WiFi", "bi-wifi"),
    ("Piscina", "bi-water"),
    ("Desayuno incluido", "bi-cup-hot"),
    ("Estacionamiento", "bi-p-square"),
    ("Aire acondicionado", "bi-snow"),
    ("TV Smart", "bi-tv"),
    ("Caja fuerte", "bi-safe"),
    ("Spa", "bi-flower1"),
]


class Command(BaseCommand):
    help = "Seed inicial de tipos, amenities y habitaciones."

    def add_arguments(self, parser):
        parser.add_argument("--rooms", type=int, default=15)
        parser.add_argument("--reset", action="store_true", help="Borra los datos previos antes.")

    def handle(self, *args, **opts):
        if opts["reset"]:
            RoomImage.objects.all().delete()
            Room.objects.all().delete()
            Amenity.objects.all().delete()
            RoomType.objects.all().delete()
            self.stdout.write(self.style.WARNING("Datos previos eliminados."))

        types = []
        for data in ROOM_TYPES:
            t, _ = RoomType.objects.get_or_create(name=data["name"], defaults=data)
            types.append(t)
        self.stdout.write(self.style.SUCCESS(f"Tipos: {len(types)}"))

        amenities = []
        for name, icon in AMENITIES:
            a, _ = Amenity.objects.get_or_create(name=name, defaults={"icon": icon})
            amenities.append(a)
        self.stdout.write(self.style.SUCCESS(f"Amenities: {len(amenities)}"))

        n_rooms = opts["rooms"]
        existing = Room.objects.count()
        created = 0
        for i in range(existing + 1, existing + n_rooms + 1):
            number = f"{(i // 100) + 1}{i % 100:02d}"
            if Room.objects.filter(number=number).exists():
                continue
            room_type = random.choice(types)
            desc = (
                fake.paragraph(nb_sentences=3)
                if fake
                else f"Habitación {number} acogedora y bien equipada."
            )
            room = Room.objects.create(
                number=number,
                room_type=room_type,
                floor=(i // 5) + 1,
                status=Room.Status.AVAILABLE,
                description=desc,
            )
            room.amenities.set(random.sample(amenities, k=random.randint(3, 6)))

            for j in range(random.randint(2, 3)):
                seed = random.randint(100, 9999)
                RoomImage.objects.create(
                    room=room,
                    image=f"https://picsum.photos/seed/room{room.pk}-{seed}/800/600",
                    caption=f"Vista {j + 1}",
                    is_main=(j == 0),
                )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Habitaciones creadas: {created}"))
        self.stdout.write(self.style.SUCCESS("Seed completado ✅"))
