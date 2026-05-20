from django.shortcuts import render


def placeholder(request):
    return render(request, "reservations/list.html")
