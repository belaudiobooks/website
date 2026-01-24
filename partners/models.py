from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext as _

from books.models import Book, Narration


class Partner(models.Model):
    """Represents a partner organization/company."""

    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PartnerUserManager(BaseUserManager):
    def create_user(self, email, partner, password=None, **extra_fields):
        if not email:
            raise ValueError("PartnerUser must have an email address")
        if not partner:
            raise ValueError("PartnerUser must belong to a partner")
        user = self.model(
            email=self.normalize_email(email), partner=partner, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class PartnerUser(AbstractBaseUser):
    """User account for partner employees. Separate from admin User model."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="users")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PartnerUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["partner"]

    @property
    def is_staff(self):
        """Partner users are never staff."""
        return False

    @property
    def is_superuser(self):
        """Partner users are never superusers."""
        return False

    def has_perm(self, perm, obj=None):
        """Partner users have no admin permissions."""
        return False

    def has_module_perms(self, app_label):
        """Partner users have no admin permissions."""
        return False

    def __str__(self):
        return self.email


class Agreement(models.Model):
    """
    Agreement between us and a partner for recording and publishing audiobooks.
    Contains royalty share percentage and references to narrations (published)
    and books (not yet published as audiobooks).
    """

    partner = models.ForeignKey(
        Partner, on_delete=models.CASCADE, related_name="agreements"
    )
    royalty_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Royalty share percentage (0-100)",
    )
    # For published audiobooks - link to actual Narration records
    narrations = models.ManyToManyField(
        Narration,
        related_name="agreements",
        blank=True,
        verbose_name=_("Narrations (published books)"),
    )
    # For books without narrations yet
    books = models.ManyToManyField(
        Book,
        related_name="agreements",
        blank=True,
        verbose_name=_("Books (unpublished)"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Agreement with {self.partner.name} ({self.royalty_percent}%)"
