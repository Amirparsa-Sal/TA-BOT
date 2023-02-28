from django.contrib import admin
from django.urls import path, include

from .views import AdminQuestionAnswerView, AuthView, CustomAuthToken, MemberCategoryView, AdminCategoryView, \
    AdminResourceView, AdminHomeWorkView, AdminNotificationsView, MemberHomeworkView, \
    BotMetaDataView, MemberQuestionAnswerView

# Auth urls
auth_send_otp = AuthView.as_view({
    'post': 'register_user'
})

verify_otp = AuthView.as_view({
    'post': 'verify_otp'
})

set_password = AuthView.as_view({
    'post': 'set_password'
})

register_admin = AuthView.as_view({
    'post': 'register_admin'
})

logout = AuthView.as_view({
    'post': 'logout'
})

last_login = BotMetaDataView.as_view({
    'get': 'get_last_login'
})

active_sessions = BotMetaDataView.as_view({
    'get': 'get_all_active_sessions'
})

all_student_sessions = BotMetaDataView.as_view({
    'get': 'get_all_students_sessions'
})

get_all_admin_sessions = BotMetaDataView.as_view({
    'get': 'get_all_admin_sessions'
})
# Member Category urls

member_category_root = MemberCategoryView.as_view({
    'get': 'get_all_categories'
})

member_category_resources = MemberCategoryView.as_view({
    'get': 'get_resources'
})

member_category_questions = MemberCategoryView.as_view({
    'post': 'add_question'
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

admin_question_answer_update = AdminQuestionAnswerView.as_view({
    'put': 'update_redis'
})

admin_answer_question = AdminQuestionAnswerView.as_view({
    'put': 'answer_question'
})

admin_question_answer_with_id = AdminQuestionAnswerView.as_view({
    'put': 'update_question_message',
    'get': 'get_question'
})

admin_chat_question_data = AdminQuestionAnswerView.as_view({
    'get': 'get_questions_in_chat'
})

admin_question_answer_root = AdminQuestionAnswerView.as_view({
    'get': 'get_all_questions'
})

member_question_answer_with_id = MemberQuestionAnswerView.as_view({
    'get': 'get_question_answer'
})

member_my_questions = MemberQuestionAnswerView.as_view({
    'get': 'get_my_questions'
})

urlpatterns = [
    path('auth/send-otp/', auth_send_otp),
    path('auth/verify-otp/', verify_otp),
    path('auth/set-password/', set_password),
    path('auth/register-admin/', register_admin),
    path('auth/login/', CustomAuthToken.as_view()),
    path('auth/logout/', logout),
    path('auth/last-login/', last_login),
    path('auth/active-sessions/', active_sessions),
    path('auth/all-students-sessions/', all_student_sessions),
    path('auth/all-admins-sessions/', get_all_admin_sessions),

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
    path('member/categories/<int:cat_id>/resources/', member_category_resources),
    path('member/categories/<int:cat_id>/questions/', member_category_questions),
    
    path('member/homeworks/', member_homework_root),
    path('member/homeworks/<int:hw_id>/', member_homework_with_id),
    path('member/homeworks/<int:hw_id>/grades/', member_homework_grades),

    path('admin/question-answer/<int:q_id>/answer/', admin_answer_question),
    path('admin/question-answer/<int:q_id>/', admin_question_answer_with_id),
    path('admin/question-answer/get-chat-data/', admin_chat_question_data),
    path('admin/question-answer/', admin_question_answer_root),

    path('member/question-answer/<int:q_id>/', member_question_answer_with_id),
    path('member/question-answer/my-questions/', member_my_questions)
]
