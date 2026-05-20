from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        CLIENTE = "CLIENTE", "Cliente"
        RECEPCIONISTA = "RECEPCIONISTA", "Recepcionista"

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.CLIENTE
    )
    phone = models.CharField(max_length=30, blank=True)
    document_id = models.CharField(max_length=30, blank=True, unique=True, null=True)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=CustomUser)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
