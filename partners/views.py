from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db import models
from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import TruncMonth
from django.http import FileResponse, HttpResponseForbidden

from books.models import Book, Narration
from partners.models import Agreement, AgreementFile, Partner, PartnerUser, SaleRecord


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

    return render(
        request,
        "partners/dashboard.html",
        {"partner": partner},
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


def login_by_uuid(request, login_uuid):
    """Log in a partner user via their unique login UUID."""
    user = get_object_or_404(PartnerUser, login_uuid=login_uuid, is_active=True)
    login(request, user, backend="partners.auth.PartnerUserBackend")
    return redirect("partners:index")


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
        "narrations__book__authors", "books__authors", "files"
    ):
        agreement_files = list(agreement.files.all())
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
                    "agreement_files": agreement_files,
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
                    "agreement_files": agreement_files,
                }
            )

    return render(
        request,
        "partners/agreements.html",
        {"partner": partner, "items": items},
    )


@partner_login_required
def download_agreement_file(request, partner_id, agreement_file_id):
    """Serve an agreement file."""
    agreement_file = get_object_or_404(
        AgreementFile, id=agreement_file_id, agreement__partner_id=partner_id
    )

    # Check that logged-in user belongs to this partner
    if request.user.partner_id != partner_id:
        return HttpResponseForbidden()

    return FileResponse(
        agreement_file.file.open("rb"),
        as_attachment=True,
        filename=agreement_file.file.name.split("/")[-1],
    )


# Month names in Belarusian for display
MONTH_NAMES_BE = {
    1: "Студзень",
    2: "Люты",
    3: "Сакавік",
    4: "Красавік",
    5: "Травень",
    6: "Чэрвень",
    7: "Ліпень",
    8: "Жнівень",
    9: "Верасень",
    10: "Кастрычнік",
    11: "Лістапад",
    12: "Снежань",
}


@partner_login_required
def sales(request, partner_id):
    """View sales data aggregated by book and month."""
    partner = get_object_or_404(Partner, id=partner_id)

    # Check that logged-in user belongs to this partner
    if request.user.partner_id != partner.id:
        return HttpResponseForbidden()

    # Get narration IDs for this partner's agreements
    narration_ids = Narration.objects.filter(agreements__partner=partner).values_list(
        "uuid", flat=True
    )

    # Subquery to get royalty_percent for each narration from partner's agreement
    royalty_subquery = Agreement.objects.filter(
        partner=partner,
        narrations=OuterRef("isbn__narration"),
    ).values("royalty_percent")[:1]

    # Aggregate sales by book, royalty rate, and month
    sales_data = (
        SaleRecord.objects.filter(isbn__narration__uuid__in=narration_ids)
        .annotate(
            month=TruncMonth("month_of_sale"),
            royalty_percent=Subquery(royalty_subquery),
        )
        .values(
            "month",
            "royalty_percent",
            book_title=models.F("isbn__narration__book__title"),
            book_slug=models.F("isbn__narration__book__slug"),
            book_uuid=models.F("isbn__narration__book__uuid"),
        )
        .annotate(
            total_quantity=Sum("quantity"),
            total_amount=Sum("amount"),
        )
        .order_by("-month", "book_title")
    )

    # Fetch authors separately (M2M can't be aggregated directly)
    book_uuids = {row["book_uuid"] for row in sales_data}
    books_with_authors = Book.objects.filter(uuid__in=book_uuids).prefetch_related(
        "authors"
    )
    author_map = {
        book.uuid: ", ".join(a.name for a in book.authors.all())
        for book in books_with_authors
    }

    # Build table data for JSON serialization
    table_data = []
    for row in sales_data:
        month_date = row["month"]
        year = month_date.year
        royalty_percent = row["royalty_percent"] or 0
        original_amount = float(row["total_amount"])
        payable_royalty = original_amount * float(royalty_percent) / 100

        table_data.append(
            {
                "book_title": row["book_title"],
                "book_slug": row["book_slug"],
                "author": author_map.get(row["book_uuid"], ""),
                "month": month_date.strftime("%Y-%m"),
                "month_name": MONTH_NAMES_BE[month_date.month],
                "year": year,
                "quantity": row["total_quantity"],
                "original_amount": original_amount,
                "royalty_share": float(royalty_percent),
                "payable_royalty": payable_royalty,
            }
        )

    return render(
        request,
        "partners/sales.html",
        {
            "partner": partner,
            "sales_data_json": table_data,
        },
    )
