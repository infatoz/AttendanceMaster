from io import StringIO
from django.contrib import admin
from django.shortcuts import redirect, render
from app.forms import StudentCSVUploadForm
from app.models import Admin, AttendanceBook, AttendanceRecord, Course, CustomUser, Department, Student, Teacher
from django.urls import path
import csv
from django.contrib import messages


admin.site.register(CustomUser)
admin.site.register(Admin)
admin.site.register(Teacher)
# admin.site.register(Student)
admin.site.register(AttendanceBook)
admin.site.register(AttendanceRecord)
admin.site.register(Department)
admin.site.register(Course)


from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Student
from .resources import StudentResource

class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ['usn', 'user', 'course', 'year', 'section', 'gender']

admin.site.register(Student, StudentAdmin)