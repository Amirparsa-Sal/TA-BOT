from django.contrib import admin
from django.urls import path, include

from .views import AuthView, LoginApiView, MemberCategoryView

# Auth urls
auth_send_otp = AuthView.as_view({
    'post': 'register_user'
})

account_activition = AuthView.as_view({
    'post': 'activate_account'
})

register_admin = AuthView.as_view({
    'post': 'register_admin'
})

logout = AuthView.as_view({
    'post': 'logout'
})

# Member Category urls

member_category_root = MemberCategoryView.as_view({
    'get': 'get_all_categories'
})

urlpatterns = [
    path('auth/send-otp/', auth_send_otp),
    path('auth/activate-account/', account_activition),
    path('auth/register-admin/', register_admin),
    path('auth/login/', LoginApiView.as_view()),
    path('auth/logout/', logout),

    path('member/categories', member_category_root)
]
