# models.py
from django import forms
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, userid, password=None, **extra_fields):
        if not userid:
            raise ValueError('The User ID must be set')
        user = self.model(userid=userid, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, userid, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(userid, password, **extra_fields)


# Custom User Model
class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('hod', 'HOD'),
        ('student', 'Student'),
    )

    userid = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    fullname = models.CharField(max_length=50)
    phone_no = models.CharField(max_length=10,unique=True,null=True)
    email = models.EmailField(unique=True,null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['fullname','role']

    objects = CustomUserManager()

    def set_password(self, raw_password):
        super().set_password(raw_password)

    def check_password(self, raw_password):
        return super().check_password(raw_password)

    def __str__(self):
        return self.userid


# Course
class Course(models.Model):
    course_id = models.CharField(max_length=10,primary_key=True,unique=True,blank=False)
    name = models.CharField(max_length=50,blank=False)
    def __str__(self):
        return f'{self.name} - {self.course_id}'


# Department
class Department(models.Model):
    dept_id = models.CharField(max_length=10,primary_key=True,unique=True)
    name = models.CharField(max_length=50,null=False)
    def __str__(self):
        return f'{self.dept_id}'


# Admin Model
class Admin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,primary_key=True,unique=True)
    photo_url = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.fullname}'

# HOD Model
class HOD(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,primary_key=True,unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    photo_url = models.CharField(max_length=100)


# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,primary_key=True,unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    photo_url = models.CharField(max_length=100)
    

# Student Model
class Student(models.Model):
    YEAR_CHOICES = (
        ('1', 'I Year'),
        ('2', 'II Year'),
        ('3', 'III Year'),
        ('4', 'IV Year'),
    )

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,primary_key=True,unique=True)
    usn = models.CharField(max_length=10)
    parent_phoneno = models.CharField(max_length=10,unique=False,null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.CharField(max_length=10, choices=YEAR_CHOICES)
    section = models.CharField(max_length=10)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    dob = models.DateField()
    photo_url = models.CharField(max_length=100)


# Attendance Book Model
class AttendanceBook(models.Model):
    BOOK_TYPE = (
        ('1', 'Theory'),
        ('1', 'Practicle-1 Hr'),
        ('2', 'Practicle-2 Hr'),
        ('3', 'Practicle-3 Hr'),
        ('4', 'Practicle-4 Hr'),
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    book_code = models.CharField(max_length=10)
    book_type = models.CharField(max_length=10, choices=BOOK_TYPE, default='1')
    teachers = models.ManyToManyField(Teacher, blank=False)
    students = models.ManyToManyField(Student, blank=False)
    # created_at = models.DateTimeField(auto_now_add=True)



# # Attendance Records Model
# class AttendanceRecord(models.Model):
#     attendance_book = models.ForeignKey(AttendanceBook, on_delete=models.CASCADE)
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     date = models.DateField()
#     session = models.CharField(max_length=100)
#     status = models.BooleanField(default=False)
#     count = models.IntegerField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)

#     @property
#     def get_status_display(self):
#         return 'P' if self.status else 'A'


class AttendanceRecord(models.Model):
    attendance_book = models.ForeignKey(AttendanceBook, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    session = models.CharField(max_length=100)
    status = models.BooleanField(default=False)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('attendance_book', 'student', 'date', 'session')

    @property
    def get_status_display(self):
        return 'P' if self.status else 'A'

