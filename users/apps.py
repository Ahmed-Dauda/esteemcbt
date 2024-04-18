from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

# apps.py

# from django.apps import AppConfig

# class YourAppConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'your_app'

#     def ready(self):
#         import your_app.signals
