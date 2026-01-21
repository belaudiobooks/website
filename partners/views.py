from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from partners.models import PartnerUser


def partner_login_required(view_func):
    """Decorator that redirects to login if user is not a logged-in PartnerUser."""

    def wrapper(request, *args, **kwargs):
        if isinstance(request.user, PartnerUser) and request.user.is_active:
            return view_func(request, *args, **kwargs)
        return redirect("partners:login")

    return wrapper


@partner_login_required
def index(request):
    """Partners dashboard page. Requires partner login."""
    return render(request, "partners/index.html")


def login_view(request):
    """Login page for partner users."""
    if isinstance(request.user, PartnerUser):
        return redirect("partners:index")

    error = None
    if request.method == "POST":
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        user = authenticate(request, email=email, password=password)
        if user is not None and isinstance(user, PartnerUser):
            login(request, user)
            return redirect("partners:index")
        else:
            error = "Invalid email or password"

    return render(request, "partners/login.html", {"error": error})


def logout_view(request):
    """Logout partner user."""
    logout(request)
    return redirect("partners:login")
