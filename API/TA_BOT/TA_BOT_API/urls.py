from django.contrib import admin
from django.urls import path, include
from .views import AuthView

auth_send_otp = AuthView.as_view({
    'post': 'register_user'
})

account_activition = AuthView.as_view({
    'post': 'activate_account'
})

urlpatterns = [
    path('auth/send-otp/', auth_send_otp),
    path('auth/activate-account', account_activition)
]
