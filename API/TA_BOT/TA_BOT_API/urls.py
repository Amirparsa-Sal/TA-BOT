from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import AuthView, LoginApiView, MemberCategoryView,AdminCategoryView,AdminResourceView,AdminHomeWorkView

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

last_login = AuthView.as_view({
    'get': 'get_last_login'
})
# Member Category urls

member_category_root = MemberCategoryView.as_view({
    'get': 'get_all_categories'
})

admin_category_with_id = AdminCategoryView.as_view({
    'put': 'change_category_status'
})

admin_category_resources = AdminCategoryView.as_view({
    'get': 'get_all_resources',
    'post': 'add_resource'
})

admin_resource_with_id = AdminResourceView.as_view({
    'put': 'update_resource',
    'delete': 'delete_resource'
})


admin_homeworks_root = AdminHomeWorkView.as_view({
    'get': 'get_all_homeworks',
    'post': 'create_homework'
})

admin_homeworks_with_id = AdminHomeWorkView.as_view({
    'delete': 'delete_homework',
    'patch': 'update_homework',
    'get': 'get_homework'
})

urlpatterns = [
    path('auth/send-otp/', auth_send_otp),
    path('auth/activate-account/', account_activition),
    path('auth/register-admin/', register_admin),
    path('auth/login/', LoginApiView.as_view()),
    path('auth/logout/', logout),
    path('auth/last-login', last_login),

    path('member/categories', member_category_root),
    path('admin/categories/<int:cat_id>/', admin_category_with_id),
    path('admin/categories/<int:cat_id>/resources/', admin_category_resources),

    path('admin/resources/<int:res_id>/', admin_resource_with_id),

    path('admin/homeworks/', admin_homeworks_root),
    path('admin/homeworks/<int:hw_id>/', admin_homeworks_with_id),
]
