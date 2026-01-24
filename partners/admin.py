from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from partners.models import Agreement, Partner, PartnerUser


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
        ("Status", {"fields": ("is_active",)}),
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


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = [
        "partner",
        "royalty_percent",
        "narrations_count",
        "books_count",
        "created_at",
    ]
    list_filter = ["partner", "created_at"]
    search_fields = ["partner__name"]
    filter_horizontal = ["narrations", "books"]
    readonly_fields = ["created_at"]

    def narrations_count(self, obj):
        return obj.narrations.count()

    narrations_count.short_description = "Narrations"

    def books_count(self, obj):
        return obj.books.count()

    books_count.short_description = "Books"
