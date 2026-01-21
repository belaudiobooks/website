from django.shortcuts import render


def index(request):
    """Partners index page."""
    return render(request, "partners/index.html")
