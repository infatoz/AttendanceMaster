from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    # path('', views.send_bulk_notifications_view, name='send_bulk_notifications_view'),
    path('login/', views.user_login, name='login'),
    path('student_login/', views.student_login, name='student_login'),
    path('logout/', views.user_logout, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('administrator/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('administrator/dashboard/attendance/<int:pk>/', views.view_attendance_records, name='view_attendance_records'),
    path('administrator/dashboard/attendance/mark/<int:pk>/', views.mark_attendance, name='mark_attendance'),
    path('administrator/dashboard/attendance_books/', views.view_attendnace_books, name='view_attendance_books'),
    path('administrator/dashboard/attendance_report/', views.view_attendnace_report, name='view_attendnace_report'),
    path('administrator/dashboard/send_absentee_sms/', views.send_absentee_sms, name='send_absentee_sms'),
    path('administrator/dashboard/attendance_book/add', views.add_attendance_book, name='add_attendance_book'),
    path('administrator/dashboard/attendance_book/add/teacher/<int:pk>/', views.add_attendance_book_teacher, name='add_attendance_book_teacher'),
    path('administrator/dashboard/attendance_book/add/student/<int:pk>/', views.add_attendance_book_student, name='add_attendance_book_student'),
    path('administrator/dashboard/attendance_book/delete/<int:pk>/', views.delete_attendance_book, name='delete_attendance_book'),
    path('administrator/dashboard/teachers', views.view_teachers, name='view_teachers'),
    path('administrator/dashboard/teacher/add', views.add_teacher, name='add_teacher'),
    path('administrator/dashboard/teacher/upload', views.upload_teachers_csv, name='upload_teachers_csv'),
    path('administrator/dashboard/teacher/edit/<str:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('administrator/dashboard/teacher/delete/<str:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('administrator/dashboard/students', views.view_students, name='view_students'),
    path('administrator/dashboard/students/filter', views.filter_students, name='filter_students'),
    path('administrator/dashboard/student/add', views.add_student, name='add_student'),
    path('administrator/dashboard/student/upload', views.upload_students_csv, name='upload_students_csv'),
    path('administrator/dashboard/student/edit/<str:student_id>/', views.edit_student, name='edit_student'),
    path('administrator/dashboard/student/delete/<str:student_id>/', views.delete_student, name='delete_student'),
    path('administrator/dashboard/departments', views.view_departments, name='view_departments'),
    path('administrator/dashboard/department/add', views.add_department, name='add_department'),
    path('administrator/dashboard/department/edit/<str:dept_id>/', views.edit_department, name='edit_department'),
    path('administrator/dashboard/department/delete/<str:dept_id>/', views.delete_department, name='delete_department'),
    path('administrator/dashboard/courses', views.view_courses, name='view_courses'),
    path('administrator/dashboard/course/add', views.add_course, name='add_course'),
    path('administrator/dashboard/course/edit/<str:course_id>/', views.edit_course, name='edit_course'),
    path('administrator/dashboard/course/delete/<str:course_id>/', views.delete_course, name='delete_course'),
    path('administrator/profile/', views.admin_profile, name='admin_profile'),
    path('administrator/change_password/', views.admin_change_password, name='admin_change_password'),
    path('administrator/send_sms/', views.send_absent_sms_view, name='send_absent_sms_view'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/change_password/', views.teacher_change_password, name='teacher_change_password'),
    path('teacher/dashboard/attendance_books/', views.teacher_view_attendance_books, name='teacher_view_attendance_books'),
    path('teacher/dashboard/attendance/<int:pk>/', views.teacher_view_attendance_records, name='teacher_view_attendance_records'),
    path('teacher/dashboard/attendance/mark/<int:pk>/', views.teacher_mark_attendance, name='teacher_mark_attendance'),
]