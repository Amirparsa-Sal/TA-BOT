from django.apps import AppConfig


class TaBotApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TA_BOT_API'

    def ready(self) -> None:
        from django.contrib.auth import get_user_model
        import environ
        import sys

        if 'runserver' in sys.argv:
            env = environ.Env()
            environ.Env.read_env()

            superuser_email = env('DJANGO_SUPERUSER_EMAIL')
            superuser_pass = env('DJANGO_SUPERUSER_PASSWORD')

            user_model = get_user_model()
            try:
                user = user_model.objects.get(email__iexact=superuser_email)
                user.is_superuser = True
                user.set_password(superuser_pass)
                user.save()
            except user_model.DoesNotExist:
                user_model.objects.create_superuser(email=superuser_email, password=superuser_pass)
