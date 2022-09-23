from django.apps import AppConfig


class OperationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operation'

    def ready(self):
        print("Start schedular ...")
        from . import updater
        updater.start()

