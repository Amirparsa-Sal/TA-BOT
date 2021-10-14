from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import AuthView, CustomAuthToken, MemberCategoryView, AdminCategoryView, \
    AdminResourceView, AdminHomeWorkView, AdminNotificationsView, MemberHomeworkView

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

member_category_resources = MemberCategoryView.as_view({
    'get': 'get_resources'
})

admin_category_root = AdminCategoryView.as_view({
    'get': 'get_all_categories'
})

admin_category_toggle_status = AdminCategoryView.as_view({
    'put': 'change_category_status'
})

admin_category_resources = AdminCategoryView.as_view({
    'get': 'get_all_resources',
    'post': 'add_resource'
})

admin_resource_with_id = AdminResourceView.as_view({
    'get': 'get_resource',
    'patch': 'update_resource',
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

admin_homeworks_grade = AdminHomeWorkView.as_view({
    'put': 'update_grade',
    'delete': 'delete_grade',
    'get': 'get_grade'
})

admin_homeworks_grade_publish = AdminHomeWorkView.as_view({
    'post': 'publish_grade'
})

admin_homeworks_grade_unpublish = AdminHomeWorkView.as_view({
    'post': 'unpublish_grade'
})

admin_notification_enable = AdminNotificationsView.as_view({
    'post': 'enable_notif'
})

admin_notification_disable = AdminNotificationsView.as_view({
    'post': 'disable_notif'
})

admin_get_notif_status = AdminNotificationsView.as_view({
    'get': 'get_incoming_notif_status'
})

member_homework_root = MemberHomeworkView.as_view({
    'get': 'get_published_homeworks'
})

member_homework_with_id = MemberHomeworkView.as_view({
    'get': 'get_homework'
})

member_homework_grades = MemberHomeworkView.as_view({
    'get': 'get_grade'
})

urlpatterns = [
    path('auth/send-otp/', auth_send_otp),
    path('auth/activate-account/', account_activition),
    path('auth/register-admin/', register_admin),
    path('auth/login/', CustomAuthToken.as_view()),
    path('auth/logout/', logout),
    path('auth/last-login', last_login),

    path('member/categories/', member_category_root),
    path('admin/categories/', admin_category_root),
    path('admin/categories/<int:cat_id>/toggle-status/', admin_category_toggle_status),
    path('admin/categories/<int:cat_id>/resources/', admin_category_resources),

    path('admin/resources/<int:res_id>/', admin_resource_with_id),

    path('admin/homeworks/', admin_homeworks_root),
    path('admin/homeworks/<int:hw_id>/', admin_homeworks_with_id),
    path('admin/homeworks/<int:hw_id>/grade/', admin_homeworks_grade),
    path('admin/homeworks/<int:hw_id>/grade/publish/', admin_homeworks_grade_publish),
    path('admin/homeworks/<int:hw_id>/grade/unpublish/', admin_homeworks_grade_unpublish),

    path('admin/incoming-notifs/status/', admin_get_notif_status),
    path('admin/incoming-notifs/enable/', admin_notification_enable),
    path('admin/incoming-notifs/disable/', admin_notification_disable),

    path('member/categories/', member_category_root),
    path('member/categories/<int:cat_id>/resources', member_category_resources),
    
    path('member/homeworks/', member_homework_root),
    path('member/homeworks/<int:hw_id>', member_homework_with_id),
    path('member/homeworks/<int:hw_id>/grades', member_homework_grades),
]
