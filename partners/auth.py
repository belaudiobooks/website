from partners.models import PartnerUser


class PartnerUserBackend:
    """Authentication backend for PartnerUser model."""

    def authenticate(self, request, email=None, password=None):
        try:
            user = PartnerUser.objects.get(email=email)
            if user.is_active and user.check_password(password):
                return user
        except PartnerUser.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return PartnerUser.objects.get(pk=user_id)
        except PartnerUser.DoesNotExist:
            return None
