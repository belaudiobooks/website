from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.decorators import display

from partners.models import Agreement, AgreementFile, Partner, PartnerUser, SaleRecord


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(PartnerUser)
class PartnerUserAdmin(BaseUserAdmin):
    # Override inherited settings that don't apply to PartnerUser
    filter_horizontal = ()
    ordering = ["id"]
    list_display = ["email", "name", "partner", "is_active"]
    list_filter = ["is_active", "partner"]
    search_fields = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "partner")}),
        ("Status", {"fields": ("is_active", "login_uuid")}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "partner", "password1", "password2"),
            },
        ),
    )


class AgreementFileInline(admin.TabularInline):
    model = AgreementFile
    extra = 1


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    inlines = [AgreementFileInline]
    list_display = [
        "get_books_names",
        "partner",
        "royalty_percent",
        "created_at",
    ]
    list_filter = ["partner", "created_at"]
    autocomplete_fields = ["narrations", "books"]
    search_fields = ["partner__name", "books__title", "narrations__book__title"]
    filter_horizontal = ["narrations", "books"]
    readonly_fields = ["created_at"]

    @display(description="Books")
    def get_books_names(self, obj):
        all_books = list(obj.books.all()) + [
            narration.book for narration in obj.narrations.all()
        ]
        return ", ".join([book.title for book in all_books])


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "month_of_sale",
        "isbn",
        "retailer",
        "quantity",
        "amount",
        "amount_currency",
    )
    list_filter = ("month_of_sale", "retailer", "sales_type", "amount_currency")
    search_fields = ["title", "isbn__code", "retailer"]
    autocomplete_fields = ["isbn"]
    date_hierarchy = "month_of_sale"
