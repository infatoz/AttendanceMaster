from django.contrib import admin
from app.models import Admin, AttendanceBook, AttendanceRecord, Course, CustomUser, Department, Notification, Student, Teacher
from django.urls import path
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from .resources import StudentResource


class CustomAdminSite(admin.AdminSite):
    site_header = _('Your Custom Header')
    site_title = _('Your Custom Title')
    index_title = _('Welcome to Your Admin Site')

admin_site = CustomAdminSite(name='custom_admin')


class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ['usn', 'user', 'course', 'year', 'section', 'gender']

# admin_site.register(Student, StudentAdmin)
# admin_site.register(CustomUser)
# admin_site.register(Admin)
# admin_site.register(Teacher)
# admin_site.register(AttendanceBook)
# admin_site.register(AttendanceRecord)
# admin_site.register(Department)
# admin_site.register(Course)

admin.site.register(Student, StudentAdmin)
admin.site.register(CustomUser)
admin.site.register(Admin)
admin.site.register(Teacher)
# admin.site.register(Student)
admin.site.register(AttendanceBook)
admin.site.register(AttendanceRecord)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Notification)
