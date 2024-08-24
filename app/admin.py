from django.contrib import admin
from app.models import Admin, AttendanceBook, AttendanceRecord, Course, CustomUser, Department, Student, Teacher
from django.contrib.auth.admin import UserAdmin


admin.site.register(CustomUser)
admin.site.register(Admin)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(AttendanceBook)
admin.site.register(AttendanceRecord)
admin.site.register(Department)
admin.site.register(Course)


