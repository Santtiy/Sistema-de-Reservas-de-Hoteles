from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from rooms.models import Room, RoomType

from .models import Reservation


class ReservationModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="client", password="pass1234", role="CLIENTE"
        )
        self.room_type = RoomType.objects.create(
            name="Deluxe", description="Desc", base_price="120.00", capacity=2
        )
        self.room = Room.objects.create(
            number="101", room_type=self.room_type, floor=1
        )

    def test_clean_validates_dates(self):
        reservation = Reservation(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=2),
            check_out=timezone.localdate() + timedelta(days=1),
            guests_count=1,
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_clean_validates_capacity(self):
        reservation = Reservation(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=2),
            check_out=timezone.localdate() + timedelta(days=4),
            guests_count=3,
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_clean_validates_availability(self):
        Reservation.objects.create(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests_count=1,
        )
        overlapping = Reservation(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=6),
            check_out=timezone.localdate() + timedelta(days=8),
            guests_count=1,
        )
        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_can_be_cancelled(self):
        future = Reservation(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests_count=1,
            status=Reservation.Status.CONFIRMED,
        )
        self.assertTrue(future.can_be_cancelled())

        near = Reservation(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=1),
            check_out=timezone.localdate() + timedelta(days=2),
            guests_count=1,
            status=Reservation.Status.CONFIRMED,
        )
        self.assertFalse(near.can_be_cancelled())

        cancelled = Reservation(
            guest=self.user,
            room=self.room,
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests_count=1,
            status=Reservation.Status.CANCELLED,
        )
        self.assertFalse(cancelled.can_be_cancelled())
