from django.shortcuts import render


def placeholder(request):
    return render(request, "rooms/list.html")
