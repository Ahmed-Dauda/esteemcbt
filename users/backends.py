from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class UsernameOnlyBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            return None
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # If multiple users share the same email, fall back to username only
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.is_staff or user.is_superuser:
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None