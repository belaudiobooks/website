from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import FileResponse, Http404, HttpResponseForbidden

from partners.models import Agreement, Partner, PartnerUser


def partner_login_required(view_func):
    """Decorator that redirects to login if user is not a logged-in PartnerUser."""

    def wrapper(request, *args, **kwargs):
        if isinstance(request.user, PartnerUser) and request.user.is_active:
            return view_func(request, *args, **kwargs)
        return redirect("partners:login")

    return wrapper


@partner_login_required
def index(request):
    """Redirect authenticated user to their partner's dashboard."""
    return redirect("partners:dashboard", partner_id=request.user.partner_id)


@partner_login_required
def dashboard(request, partner_id):
    """Partners dashboard page. Requires partner login."""
    partner = get_object_or_404(Partner, id=partner_id)

    # Check that logged-in user belongs to this partner
    if request.user.partner_id != partner.id:
        return HttpResponseForbidden()

    # Count total books and narrations across all agreements
    agreements_count = 0
    for agreement in partner.agreements.prefetch_related("narrations", "books"):
        agreements_count += agreement.narrations.count() + agreement.books.count()

    return render(
        request,
        "partners/dashboard.html",
        {"partner": partner, "agreements_count": agreements_count},
    )


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


@partner_login_required
def agreements(request, partner_id):
    """View all agreements for a partner."""
    partner = get_object_or_404(Partner, id=partner_id)

    # Check that logged-in user belongs to this partner
    if request.user.partner_id != partner.id:
        return HttpResponseForbidden()

    # Build list of items (narrations and books) with royalty
    items = []
    for agreement in partner.agreements.prefetch_related(
        "narrations__book__authors", "books__authors"
    ):
        for narration in agreement.narrations.all():
            authors = [a.name for a in narration.book.authors.all()]
            items.append(
                {
                    "type": "narration",
                    "title": narration.book.title,
                    "authors": authors,
                    "narration": narration,
                    "book_slug": narration.book.slug,
                    "royalty_percent": agreement.royalty_percent,
                    "agreement_id": agreement.id,
                    "has_agreement_file": bool(agreement.agreement_file),
                }
            )
        for book in agreement.books.order_by("title"):
            authors = [a.name for a in book.authors.all()]
            items.append(
                {
                    "type": "book",
                    "title": book.title,
                    "authors": authors,
                    "royalty_percent": agreement.royalty_percent,
                    "agreement_id": agreement.id,
                    "has_agreement_file": bool(agreement.agreement_file),
                }
            )

    return render(
        request,
        "partners/agreements.html",
        {"partner": partner, "items": items},
    )


@partner_login_required
def download_agreement_file(request, partner_id, agreement_id):
    """Serve the agreement PDF file."""
    agreement = get_object_or_404(Agreement, id=agreement_id, partner_id=partner_id)

    # Check that logged-in user belongs to this partner
    if request.user.partner_id != partner_id:
        return HttpResponseForbidden()

    if not agreement.agreement_file:
        raise Http404("Agreement file not found")

    return FileResponse(
        agreement.agreement_file.open("rb"),
        as_attachment=True,
        filename=agreement.agreement_file.name.split("/")[-1],
    )
