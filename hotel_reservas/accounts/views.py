from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm, ProfileForm
from .models import CustomUser


def _redirect_by_role(user: CustomUser):
    if user.role in (CustomUser.Roles.ADMIN, CustomUser.Roles.RECEPCIONISTA):
        return redirect("dashboard:index")
    return redirect("reservations:list")


def register(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.Roles.CLIENTE
            user.save()
            messages.success(request, "Cuenta creada correctamente.")
            login(request, user)
            return _redirect_by_role(user)
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Bienvenido de nuevo.")
            return _redirect_by_role(user)
    else:
        form = AuthenticationForm(request)
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesion.")
    return redirect("home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
