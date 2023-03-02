from typing import MutableMapping
from django.contrib import admin

# Register your models here.
from import_export import resources
from TA_BOT_API.models import AuthData, Category, TelegramActiveSessions, User, Grade, HomeWork, Resource
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.hashers import make_password

class AuthDataResource(resources.ModelResource):

    class Meta:
        model = AuthData

class AuthDataAdmin(ImportExportModelAdmin):
    resource_class = AuthDataResource

admin.site.register(AuthData, AuthDataAdmin)
admin.site.register(Category)
admin.site.register(User)
admin.site.register(Grade)
admin.site.register(HomeWork)
admin.site.register(Resource)
admin.site.register(TelegramActiveSessions)