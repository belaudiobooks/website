from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from partners.models import Partner, PartnerUser


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
