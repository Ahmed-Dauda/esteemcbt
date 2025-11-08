from django.contrib.auth import get_user_model

User = get_user_model()

class UsernameOnlyBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            return None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        # Optional: block staff/admins
        if user.is_staff or user.is_superuser:
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
