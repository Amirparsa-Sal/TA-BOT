from typing import MutableMapping
from django.contrib import admin

# Register your models here.
from import_export import resources
from TA_BOT_API.models import AuthData
from import_export.admin import ImportExportModelAdmin
from django.dispatch import receiver
from import_export.signals import post_import
from django.contrib.auth.hashers import make_password

class AuthDataResource(resources.ModelResource):

    class Meta:
        model = AuthData

    def after_save_instance(self, instance: AuthData, using_transactions: bool, dry_run: bool):
        super().after_save_instance(instance, using_transactions, dry_run)
        if dry_run is False:
            instance.password = make_password(instance.password)
            instance.save()

class AuthDataAdmin(ImportExportModelAdmin):
    resource_class = AuthDataResource

admin.site.register(AuthData, AuthDataAdmin)