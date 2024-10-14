from itertools import islice
import json
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
import csv
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.urls import reverse, reverse_lazy
import requests
import urllib.request
import urllib.parse

import urllib3
from app.forms import AddCourseForm, AddDepartmentForm, AttendanceBookForm, CustomUserCreationForm, NotificationForm, StudentCSVUploadForm, StudentRegistrationForm, TeacherCSVUploadForm, TeacherRegistrationForm,  UserLoginForm
from django.contrib.auth.decorators import login_required
from app.decorators import role_required
from django.db import transaction
from django.contrib import messages
from app.models import Admin, AttendanceBook, AttendanceRecord, Course, CustomUser, Department, Student, Teacher
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from .models import HOD, AttendanceRecord, Notification
from django.core.paginator import Paginator
from django.db.models import Q
from .tasks import get_absent_details_by_date

# Home Page
def home_view(request):
    return render(request,'index.html')

# All user login [Admin/HOD/Teacher/Student]
def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            print(user.role)
            if user is not None:
                if user.role == 'admin':
                    login(request,user)
                    return redirect('admin_dashboard')
                if user.role == 'teacher':
                    login(request,user)
                    return redirect('teacher_dashboard')
                if user.role == 'student':
                    login(request,user)
                    return redirect('student_dashboard')
            else:
                form.add_error(None, 'Invalid userid or password')
                messages.error(request, 'Invalid userid or password!')
        return render(request, 'login.html', {'form': form})
    form = UserLoginForm()
    return render(request, 'login.html', {'form': form})


# User Logout
def user_logout(request):
    logout(request)
    return redirect('login')

# ======================= ADMIN VIEWS ================================

# Admin Dashboard
@login_required
@role_required(['admin'])
def admin_dashboard(request):
    # Count the total number of each entity
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_admins = Admin.objects.count()
    total_hods = HOD.objects.count()
    total_attendance_books = AttendanceBook.objects.count()
    total_departments = Department.objects.count()
    total_courses = Course.objects.count()
    
    # Get today's date
    today = timezone.now().date()
    
    # Count the number of absent students today
    absent_students_today = AttendanceRecord.objects.filter(
        date=today,
        status=False
    ).values('student').distinct().count()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'total_hods': total_hods,
        'total_attendance_books': total_attendance_books,
        'absent_students_today': absent_students_today,
        'total_departments':total_departments,
        'total_courses':total_courses
    }
    return render(request, 'administrator/dashboard.html',context)


# Admin Profile
@login_required
@role_required(['admin'])
def admin_profile(request):
    # Assuming the logged-in user is an admin
    admin = get_object_or_404(Admin, user=request.user)
    return render(request, 'administrator/admin_profile.html', {'admin': admin})

# Admin Change Password
@login_required
def admin_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Your password was successfully updated!')
            return redirect('admin_change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'administrator/change_password.html', {
        'form': form
    })

# Add Teacher
@login_required
@role_required(['admin'])
@transaction.atomic
def add_teacher(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        teacher_form = TeacherRegistrationForm(request.POST)
        if user_form.is_valid() and teacher_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'teacher'
            user.save()
            teacher = teacher_form.save(commit=False)
            teacher.user = user
            teacher.save()
            # login(request, user)
            messages.success(request, 'Teacher added successfully!')
            return redirect('view_teachers')
    else:
        user_form = CustomUserCreationForm()
        teacher_form = TeacherRegistrationForm()
    return render(request, 'administrator/add_teacher.html', {'user_form': user_form, 'teacher_form': teacher_form})


# View Teachers
@login_required
@role_required(['admin'])
def view_teachers(request):
    teachers = Teacher.objects.all()
    return render(request, 'administrator/view_teachers.html',{'teachers': teachers})

# Edit Teacher
@login_required
@role_required(['admin'])
@transaction.atomic
def edit_teacher(request, teacher_id):
    user = get_object_or_404(CustomUser, userid=teacher_id)
    teacher = get_object_or_404(Teacher, user=user)
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, instance=user)
        teacher_form = TeacherRegistrationForm(request.POST, instance=teacher)
        if user_form.is_valid() and teacher_form.is_valid():
            user = user_form.save()
            teacher = teacher_form.save(commit=False)
            teacher.user = user
            teacher.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('view_teachers')
    else:
        user_form = CustomUserCreationForm(instance=user)
        teacher_form = TeacherRegistrationForm(instance=teacher)
    return render(request, 'administrator/edit_teacher.html', {'user_form': user_form, 'teacher_form': teacher_form})


# Delete Teacher
@login_required
@role_required(['admin'])
def delete_teacher(request, teacher_id):
    user = get_object_or_404(CustomUser, userid=teacher_id)
    teacher = get_object_or_404(Teacher, user=user)
    if request.method == 'POST':
        teacher.delete()
        user.delete()
        messages.success(request, 'Teacher deleted successfully!')
        return redirect('view_teachers')
    return render(request, 'administrator/delete_teacher.html', {'teacher': teacher})


# Upload Teacher via CSV
@login_required
@role_required(['admin'])
@transaction.atomic
def upload_teachers_csv(request):
    if request.method == 'POST':
        form = TeacherCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                # Process CSV file
                csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
                for row in csv_reader:
                    userid = row.get('userid')
                    fullname = row.get('fullname')
                    phone_no = row.get('phone_no')
                    email = row.get('email')
                    dept_id = row.get('dept_id')
                    photo_url = row.get('photo_url')
                    
                    # Check if user already exists
                    if CustomUser.objects.filter(userid=userid).exists():
                        continue
                    
                    # Create user
                    user = CustomUser(
                        userid=userid,
                        fullname=fullname,
                        phone_no=phone_no,
                        email=email,
                        role='teacher'
                    )
                    user.set_password('Welcome@12345')
                    user.save()

                    # Get or create department
                    department, created = Department.objects.get_or_create(dept_id=dept_id)
                    
                    # Create teacher
                    Teacher.objects.create(
                        user=user,
                        department=department,
                        photo_url=photo_url
                    )
                    
                messages.success(request, 'Teachers uploaded successfully!')
            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
            return redirect('view_teachers')
    else:
        form = TeacherCSVUploadForm()
    return render(request, 'administrator/upload_teachers_csv.html', {'form': form})

# @login_required
# @role_required(['admin'])
# @transaction.atomic
# def upload_teachers_csv(request):
#     if request.method == 'POST':
#         form = TeacherCSVUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             csv_file = request.FILES['csv_file']
#             try:
#                 # Decode the CSV file
#                 csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
                
#                 # Fetch existing users in one query
#                 existing_users = set(CustomUser.objects.filter(
#                     userid__in=[row['userid'] for row in csv_reader]
#                 ).values_list('userid', flat=True))

#                 # Reset reader after fetching existing users
#                 csv_file.seek(0)
#                 csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())

#                 users_to_create = []
#                 teachers_to_create = []
#                 departments = {}

#                 for row in csv_reader:
#                     userid = row.get('userid')
                    
#                     # Skip if the user already exists
#                     if userid in existing_users:
#                         continue
                    
#                     fullname = row.get('fullname')
#                     phone_no = row.get('phone_no')
#                     email = row.get('email')
#                     dept_id = row.get('dept_id')
#                     photo_url = row.get('photo_url')

#                     # Create user instance
#                     user = CustomUser(
#                         userid=userid,
#                         fullname=fullname,
#                         phone_no=phone_no,
#                         email=email,
#                         role='teacher'
#                     )
#                     user.set_password('Welcome@12345')  # Setting password for later bulk update
#                     users_to_create.append(user)

#                     # Create or get department
#                     if dept_id not in departments:
#                         department, created = Department.objects.get_or_create(dept_id=dept_id)
#                         departments[dept_id] = department
                    
#                     # Create teacher instance
#                     teachers_to_create.append(
#                         Teacher(
#                             user=user,
#                             department=departments[dept_id],
#                             photo_url=photo_url
#                         )
#                     )

#                 # Bulk create users and teachers
#                 CustomUser.objects.bulk_create(users_to_create, ignore_conflicts=True)
#                 Teacher.objects.bulk_create(teachers_to_create, ignore_conflicts=True)

#                 messages.success(request, 'Teachers uploaded successfully!')
#             except Exception as e:
#                 messages.error(request, f'Error processing file: {e}')
#             return redirect('view_teachers')
#     else:
#         form = TeacherCSVUploadForm()
#     return render(request, 'administrator/upload_teachers_csv.html', {'form': form})


# Add Student
@login_required
@role_required(['admin'])
@transaction.atomic
def add_student(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        student_form = StudentRegistrationForm(request.POST)
        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'student'
            user.save()
            student = student_form.save(commit=False)
            student.user = user
            student.save()
            # login(request, user)
            messages.success(request, 'Student added successfully!')
            return redirect('view_students')
    else:
        user_form = CustomUserCreationForm()
        student_form = StudentRegistrationForm()
    return render(request, 'administrator/add_student.html', {'user_form': user_form, 'student_form': student_form})

# View All Students
# @login_required
# @role_required(['admin'])
# @transaction.atomic
# def view_students(request):
#     students = Student.objects.all()
#     return render(request, 'administrator/view_students.html',{'students': students})

@login_required
@role_required(['admin'])
def view_students(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')

        # Filter and fetch students from the database based on search criteria across multiple fields
        students = Student.objects.filter(
            Q(user__fullname__icontains=search_value) |
            Q(user__userid__icontains=search_value) |
            Q(course__course_id__icontains=search_value) |
            Q(year__icontains=search_value) |
            Q(section__icontains=search_value) |
            Q(user__email__icontains=search_value) |
            Q(parent_phoneno__icontains=search_value) |
            Q(user__phone_no__icontains=search_value)
        ).select_related('user', 'course')

        total_records = students.count()

        # Implement pagination
        paginator = Paginator(students, length)
        page_number = (start // length) + 1
        page_obj = paginator.get_page(page_number)

        # Prepare data for DataTables
        data = [
            {
                "userid": student.user.userid,
                "photo_url": student.photo_url,
                "fullname": student.user.fullname,
                "course": student.course.course_id,
                "year": student.get_year_display(),
                "section": student.section,
                "email": student.user.email,
                "parent_phoneno": student.parent_phoneno,
                "phone_no": student.user.phone_no,
                "edit_url": reverse('edit_student', args=[student.user.userid]),
                "delete_url": reverse('delete_student', args=[student.user.userid])
            }
            for student in page_obj
        ]

        response = {
            "draw": int(request.GET.get('draw', 0)),
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": data,
        }
        return JsonResponse(response)

    # Render the initial HTML page with DataTables setup
    return render(request, 'administrator/view_students.html')

# Edit Student
@login_required
@role_required(['admin'])
@transaction.atomic
def edit_student(request, student_id):
    user = get_object_or_404(CustomUser, userid=student_id)
    student = get_object_or_404(Student, user=user)
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, instance=user)
        student_form = StudentRegistrationForm(request.POST, instance=student)
        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save()
            student = student_form.save(commit=False)
            student.user = user
            student.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('view_students')
    else:
        user_form = CustomUserCreationForm(instance=user)
        student_form = StudentRegistrationForm(instance=student)
    return render(request, 'administrator/edit_student.html', {'user_form': user_form, 'student_form': student_form})


# Delete Student
@login_required
@role_required(['admin'])
def delete_student(request, student_id):
    user = get_object_or_404(CustomUser, userid=student_id)
    student = get_object_or_404(Student, user=user)
    if request.method == 'POST':
        student.delete()
        user.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('view_students')
    return render(request, 'administrator/delete_student.html', {'student': student})


# # Upload Students via CSV
# @login_required
# @role_required(['admin'])
# @transaction.atomic
# def upload_students_csv(request):
#     if request.method == 'POST':
#         form = StudentCSVUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             csv_file = request.FILES['csv_file']
#             try:
#                 # Process CSV file
#                 csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
#                 for row in csv_reader:
#                     # print(row)
#                     userid = row.get('userid')
#                     fullname = row.get('fullname')
#                     phone_no = row.get('phone_no')
#                     parent_phoneno = row.get('parent_phoneno')
#                     email = row.get('email')
#                     course_id = row.get('course_id')
#                     usn = row.get('usn')
#                     year=row.get('year')
#                     section=row.get('section')
#                     gender=row.get('gender')
#                     dob = row.get('dob')
#                     photo_url = row.get('photo_url')

#                     # Convert date format from DD/MM/YYYY to YYYY-MM-DD
#                     try:
#                         dob = datetime.strptime(dob, '%d/%m/%Y').strftime('%Y-%m-%d')
#                     except ValueError:
#                         messages.error(request, f"Error processing date for user {userid}: Invalid date format.")
#                         continue
                    
#                     # Check if user already exists
#                     if CustomUser.objects.filter(userid=userid).exists():
#                         continue
                    
#                     # Create user
#                     user = CustomUser(
#                         userid=userid,
#                         fullname=fullname,
#                         phone_no=phone_no,
#                         email=email,
#                         role='student'
#                     )
#                     user.set_password('Welcome@12345')
#                     user.save()

#                     # Get or create course
#                     course, created = Course.objects.get_or_create(course_id=course_id)
                    
#                     # Create student
#                     Student.objects.create(
#                         user=user,
#                         usn=usn,
#                         parent_phoneno=parent_phoneno,
#                         course=course,
#                         year=year,
#                         section=section,
#                         gender=gender,
#                         dob=dob,
#                         photo_url=photo_url
#                     )
                    
#                 messages.success(request, 'Students uploaded successfully!')
#             except Exception as e:
#                 messages.error(request, f'Error processing file: {e}')
#             return redirect('view_students')
#     else:
#         form = StudentCSVUploadForm()
#     return render(request, 'administrator/upload_students_csv.html', {'form': form})

# @login_required
# @role_required(['admin'])
# @transaction.atomic
# def upload_students_csv(request):
#     if request.method == 'POST':
#         form = StudentCSVUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             csv_file = request.FILES['csv_file']
#             try:
#                 # Read the CSV file
#                 csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
#                 users_to_create = []
#                 students_to_create = []
#                 course_cache = {}  # Cache to avoid repeated DB hits for courses

#                 for row in csv_reader:
#                     userid = row.get('userid')
#                     fullname = row.get('fullname')
#                     phone_no = row.get('phone_no')
#                     parent_phoneno = row.get('parent_phoneno')
#                     email = row.get('email')
#                     course_id = row.get('course_id')
#                     usn = row.get('usn')
#                     year = row.get('year')
#                     section = row.get('section')
#                     gender = row.get('gender')
#                     dob = row.get('dob')
#                     photo_url = row.get('photo_url')

#                     # Convert date format from DD/MM/YYYY to YYYY-MM-DD
#                     try:
#                         dob = datetime.strptime(dob, '%d/%m/%Y').date()
#                     except ValueError:
#                         messages.error(request, f"Invalid date format for user {userid}. Expected DD/MM/YYYY.")
#                         continue

#                     # Skip if user already exists
#                     if CustomUser.objects.filter(userid=userid).exists():
#                         messages.warning(request, f"User {userid} already exists. Skipping.")
#                         continue

#                     # Get or create course, using a cache to reduce DB hits
#                     if course_id not in course_cache:
#                         course, created = Course.objects.get_or_create(course_id=course_id)
#                         course_cache[course_id] = course
#                     else:
#                         course = course_cache[course_id]

#                     # Prepare user and student objects for bulk creation
#                     user = CustomUser(
#                         userid=userid,
#                         fullname=fullname,
#                         phone_no=phone_no,
#                         email=email,
#                         role='student'
#                     )
#                     user.set_password('Welcome@12345')
#                     users_to_create.append(user)

#                     student = Student(
#                         user=user,
#                         usn=usn,
#                         parent_phoneno=parent_phoneno,
#                         course=course,
#                         year=year,
#                         section=section,
#                         gender=gender,
#                         dob=dob,
#                         photo_url=photo_url
#                     )
#                     students_to_create.append(student)

#                 # Bulk create users and students
#                 if users_to_create:
#                     CustomUser.objects.bulk_create(users_to_create, batch_size=100)
#                     Student.objects.bulk_create(students_to_create, batch_size=100)

#                 messages.success(request, 'Students uploaded successfully!')

#             except Exception as e:
#                 messages.error(request, f'Error processing file: {e}')
#             return redirect('view_students')
#     else:
#         form = StudentCSVUploadForm()
#     return render(request, 'administrator/upload_students_csv.html', {'form': form})

@login_required
@role_required(['admin'])
@transaction.atomic
def upload_students_csv(request):
    if request.method == 'POST':
        form = StudentCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
                users_to_create = []
                students_to_create = []
                course_cache = {}  # Cache to avoid repeated DB hits for courses

                for i, row in enumerate(csv_reader):
                    userid = row.get('userid')
                    fullname = row.get('fullname')
                    phone_no = row.get('phone_no')
                    parent_phoneno = row.get('parent_phoneno')
                    email = row.get('email')
                    course_id = row.get('course_id')
                    usn = row.get('usn')
                    year = row.get('year')
                    section = row.get('section')
                    gender = row.get('gender')
                    dob = row.get('dob')
                    photo_url = row.get('photo_url')

                    try:
                        dob = datetime.strptime(dob, '%d/%m/%Y').date()
                    except ValueError:
                        messages.error(request, f"Invalid date format for user {userid}. Expected DD/MM/YYYY.")
                        continue

                    if CustomUser.objects.filter(userid=userid).exists():
                        messages.warning(request, f"User {userid} already exists. Skipping.")
                        continue

                    if course_id not in course_cache:
                        course, created = Course.objects.get_or_create(course_id=course_id)
                        course_cache[course_id] = course
                    else:
                        course = course_cache[course_id]

                    user = CustomUser(
                        userid=userid,
                        fullname=fullname,
                        phone_no=phone_no,
                        email=email,
                        role='student'
                    )
                    user.set_password('Welcome@12345')
                    users_to_create.append(user)

                    student = Student(
                        user=user,
                        usn=usn,
                        parent_phoneno=parent_phoneno,
                        course=course,
                        year=year,
                        section=section,
                        gender=gender,
                        dob=dob,
                        photo_url=photo_url
                    )
                    students_to_create.append(student)

                    # Insert in batches of 1000
                    if len(users_to_create) == 100:
                        CustomUser.objects.bulk_create(users_to_create)
                        for j, student in enumerate(students_to_create):
                            student.user = users_to_create[j]
                        Student.objects.bulk_create(students_to_create)
                        users_to_create.clear()
                        students_to_create.clear()

                # Insert remaining records if less than 1000
                if users_to_create:
                    CustomUser.objects.bulk_create(users_to_create)
                    for j, student in enumerate(students_to_create):
                        student.user = users_to_create[j]
                    Student.objects.bulk_create(students_to_create)

                messages.success(request, 'Students uploaded successfully!')

            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
            return redirect('view_students')
    else:
        form = StudentCSVUploadForm()
    return render(request, 'administrator/upload_students_csv.html', {'form': form})


# Add Admin Notifications
def create_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('notification_list')
    else:
        form = NotificationForm()
    return render(request, 'create_notification.html', {'form': form})


#===================== ATTENDANCE BOOKS ================================

# Add New Attendance Books
@login_required
@role_required(['admin'])
def add_attendance_book(request):
    if request.method == 'POST':
        form = AttendanceBookForm(request.POST)
        if form.is_valid():
            # Save the book to get an ID for the next step
            attendance_book = form.save(commit=False)
            attendance_book.save()
            # Redirect to the teacher selection step
            return redirect('add_attendance_book_teacher', pk=attendance_book.pk)
    else:
        form = AttendanceBookForm()
    return render(request, 'administrator/add_attendance_book.html', {'form': form})


@login_required
@role_required(['admin'])
def add_attendance_book_teacher(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    teachers = Teacher.objects.all()
    if request.method == 'POST':
        # Process form data
        selected_teachers = request.POST.getlist('teachers')
        selected_teachers_objs = Teacher.objects.filter(user__userid__in=selected_teachers)
        # print(selected_teachers_objs)
        attendance_book.teachers.set(selected_teachers_objs)
        attendance_book.save()
        return redirect('add_attendance_book_student', pk=attendance_book.pk)
    # teachers = Teacher.objects.all()
    # print(teachers)
    return render(request, 'administrator/add_attendance_book_teacher.html', {
        'attendance_book': attendance_book,
        'teachers': teachers
    })

# @login_required
# @role_required(['admin'])
# def add_attendance_book_student(request, pk):
#     attendance_book = get_object_or_404(AttendanceBook, pk=pk)
#     students = Student.objects.all()
#     if request.method == 'POST':
#         # print(request.POST)
#         # Process form data
#         selected_students = request.POST.getlist('students')
#         print(selected_students)
#         selected_students_objs = Student.objects.filter(user__userid__in=selected_students)
#         print(selected_students_objs)
#         attendance_book.students.set(selected_students_objs)
#         # res = attendance_book.teachers.set(selected_students)
#         # print(res)
#         attendance_book.save()
#         return redirect('view_attendance_books')
#     # teachers = Teacher.objects.all()
#     return render(request, 'administrator/add_attendance_book_student.html', {
#         'attendance_book': attendance_book,
#         'students': students
#     })


@login_required
@role_required(['admin'])
def add_attendance_book_student(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    students = Student.objects.all()[:150]  # Initial load with a limit for performance

    if request.method == 'POST':
        # Get selected students as a comma-separated string and split into a list
        selected_students = request.POST.get('students', '').split(',')
        
        # Filter students by their user ID and update attendance book
        selected_students_objs = Student.objects.filter(user__userid__in=selected_students)
        
        # Check if the selected students were found
        if not selected_students_objs.exists():
            print(f"No students found with the given IDs: {selected_students}")
        
        attendance_book.students.set(selected_students_objs)
        attendance_book.save()
        return redirect('view_attendance_books')

    return render(request, 'administrator/add_attendance_book_student.html', {
        'attendance_book': attendance_book,
        'students': students
    })



@login_required
@role_required(['admin'])
def filter_students(request):
    query = request.GET.get('query', '')
    queryCourse = request.GET.get('queryCourse', '')
    queryYear = request.GET.get('queryYear', '')
    querySection = request.GET.get('querySection', '')

    # Adjusted filtering logic to apply multiple filters correctly
    students = Student.objects.all()

    # Apply the search filters based on input fields
    if query:
        students = students.filter(
            Q(user__fullname__icontains=query) |
            Q(user__userid__icontains=query)
        )

    if queryCourse:
        students = students.filter(course__name__icontains=queryCourse)

    if queryYear:
        students = students.filter(year__icontains=queryYear)

    if querySection:
        students = students.filter(section__icontains=querySection)

    # Paginate the filtered results
    paginator = Paginator(students, 150)  # Show 50 students per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Prepare data for JSON response
    students_data = [
        {
            'userid': student.user.userid,
            'fullname': student.user.fullname,
            'photo_url': student.photo_url,
            'course': student.course.name,  # Assuming course has a name field
            'year': student.get_year_display(),
            'section': student.section,
        } for student in page_obj
    ]

    return JsonResponse({'students': students_data, 'has_next': page_obj.has_next()})
   
# View All Attendance Books
@login_required
@role_required(['admin'])
def view_attendnace_books(request):
    attendance_books = AttendanceBook.objects.all()
    return render(request, 'administrator/view_attendance_books.html', {
        'attendance_books': attendance_books
    })


# # Admin Mark Attendance
# @login_required
# @role_required(['admin'])
# def mark_attendance(request, pk):
#     attendance_book = get_object_or_404(AttendanceBook, pk=pk)
#     students = attendance_book.students.all()
#     attendance_records = AttendanceRecord.objects.filter(attendance_book=attendance_book).order_by('date', 'session')

#     # Create a dictionary to organize records by date and session
#     records_by_date_session = {}
#     for record in attendance_records:
#         if record.date not in records_by_date_session:
#             records_by_date_session[record.date] = {}
#         if record.session not in records_by_date_session[record.date]:
#             records_by_date_session[record.date][record.session] = {}
#         records_by_date_session[record.date][record.session][record.student.user.userid] = record.get_status_display

#     # Calculate total sessions and attendance count for each student
#     increment_value = int(attendance_book.book_type)
#     # print(increment_value)
#     student_attendance = {}
#     total_sessions = len(set((record.date, record.session) for record in attendance_records))*increment_value
#     # total_sessions = (total_sessions*increment_value)

#     for student in students:
#         attendance_count = AttendanceRecord.objects.filter(
#             attendance_book=attendance_book, student=student, status=True
#         ).count()
#         attendance_count = (attendance_count * increment_value)
#         # print(attendance_count)
#         attendance_percentage = (attendance_count / total_sessions) * 100 if total_sessions > 0 else 0
#         student_attendance[student.user.userid] = {
#             'count': attendance_count,
#             'percentage': round(attendance_percentage, 2),
#         }
    
#     if request.method == 'POST':
#         selected_students = request.POST.getlist('attendance')
#         current_date = request.POST.get('date')
#         session = request.POST.get('session')

#         try:
#             with transaction.atomic():
#                 for student in students:
#                     status = student.user.userid in selected_students

#                     # Determine the increment value based on book_type
#                     increment_value = int(attendance_book.book_type)

#                     # Check if a record already exists for the same student, date, and session
#                     existing_record = AttendanceRecord.objects.filter(
#                         attendance_book=attendance_book,
#                         student=student,
#                         date=current_date,
#                         session=session
#                     ).first()

#                     if existing_record:
#                         # Update the existing record's status and count
#                         existing_record.status = status
#                         existing_record.count = student.attendancerecord_set.filter(status=True).count() + (
#                             increment_value if status else 0
#                         )
#                         existing_record.save()
#                     else:
#                         # Create a new record if it doesn't exist
#                         AttendanceRecord.objects.create(
#                             attendance_book=attendance_book,
#                             student=student,
#                             date=current_date,
#                             session=session,
#                             status=status,
#                             count=student.attendancerecord_set.filter(status=True).count() + (
#                                 increment_value if status else 0
#                             )
#                         )
            
#             messages.success(request, 'Attendance Marked Successfully')

#         except Exception as e:
#             # Catch any errors and show a message to the user
#             messages.error(request, f'Error occurred while marking attendance: {str(e)}')
#         return redirect('view_attendance_records',pk=pk)

#     return render(request, 'administrator/mark_attendance.html', {
#         'attendance_book': attendance_book,
#         'students': students,
#         'attendance_records': attendance_records,
#         'records_by_date_session': records_by_date_session,
#         'student_attendance': student_attendance,
#         'total_sessions': total_sessions,
#     })

# Admin Mark Attendance
@login_required
@role_required(['admin'])
def mark_attendance(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    students = attendance_book.students.all()
    attendance_records = AttendanceRecord.objects.filter(attendance_book=attendance_book).order_by('date', 'session')

    # Create a dictionary to organize records by date and session
    records_by_date_session = {}
    for record in attendance_records:
        records_by_date_session.setdefault(record.date, {}).setdefault(record.session, {})[record.student.user.userid] = record.get_status_display

    # Calculate total sessions and attendance count for each student
    increment_value = int(attendance_book.book_type)
    total_sessions = len(set((record.date, record.session) for record in attendance_records)) * increment_value

    student_attendance = {
        student.user.userid: {
            'count': AttendanceRecord.objects.filter(
                attendance_book=attendance_book,
                student=student,
                status=True
            ).count() * increment_value,
            'percentage': round(
                (AttendanceRecord.objects.filter(
                    attendance_book=attendance_book,
                    student=student,
                    status=True
                ).count() * increment_value / total_sessions) * 100, 2) if total_sessions > 0 else 0
        }
        for student in students
    }

    if request.method == 'POST':
        selected_students = set(request.POST.getlist('attendance'))
        current_date = request.POST.get('date')
        session = request.POST.get('session')

        # Prepare bulk create and update data
        update_data = []
        create_data = []
        
        for student in students:
            status = student.user.userid in selected_students

            record_data = {
                'attendance_book': attendance_book,
                'student': student,
                'date': current_date,
                'session': session,
                'status': status,
                'count': student.attendancerecord_set.filter(status=True).count() + (increment_value if status else 0)
            }
            
            if AttendanceRecord.objects.filter(
                attendance_book=attendance_book,
                student=student,
                date=current_date,
                session=session
            ).exists():
                # Collect data for bulk updates
                update_data.append(AttendanceRecord(
                    id=AttendanceRecord.objects.get(
                        attendance_book=attendance_book,
                        student=student,
                        date=current_date,
                        session=session
                    ).id,
                    **record_data
                ))
            else:
                # Collect data for bulk creation
                create_data.append(AttendanceRecord(**record_data))

        try:
            with transaction.atomic():
                # Perform bulk update and create operations
                if update_data:
                    AttendanceRecord.objects.bulk_update(update_data, ['status', 'count'])
                if create_data:
                    AttendanceRecord.objects.bulk_create(create_data)

            messages.success(request, 'Attendance Marked Successfully')

        except Exception as e:
            messages.error(request, f'Error occurred while marking attendance: {str(e)}')

        return redirect('view_attendance_records', pk=pk)

    return render(request, 'administrator/mark_attendance.html', {
        'attendance_book': attendance_book,
        'students': students,
        'attendance_records': attendance_records,
        'records_by_date_session': records_by_date_session,
        'student_attendance': student_attendance,
        'total_sessions': total_sessions,
    })



@login_required
@role_required(['admin', 'teacher'])
def view_attendance_records(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    students = attendance_book.students.all()
    attendance_records = AttendanceRecord.objects.filter(attendance_book=attendance_book).order_by('date', 'session')

    # Create a dictionary to organize records by date and session
    records_by_date_session = {}
    for record in attendance_records:
        if record.date not in records_by_date_session:
            records_by_date_session[record.date] = {}
        if record.session not in records_by_date_session[record.date]:
            records_by_date_session[record.date][record.session] = {}
        records_by_date_session[record.date][record.session][record.student.user.userid] = record.get_status_display

    # Calculate total sessions and attendance count for each student
    increment_value = int(attendance_book.book_type)
    # print(increment_value)
    student_attendance = {}
    total_sessions = len(set((record.date, record.session) for record in attendance_records))*increment_value
    # total_sessions = (total_sessions*increment_value)

    for student in students:
        attendance_count = AttendanceRecord.objects.filter(
            attendance_book=attendance_book, student=student, status=True
        ).count()
        attendance_count = (attendance_count * increment_value)
        # print(attendance_count)
        attendance_percentage = (attendance_count / total_sessions) * 100 if total_sessions > 0 else 0
        student_attendance[student.user.userid] = {
            'count': attendance_count,
            'percentage': round(attendance_percentage, 2),
        }
    return render(request, 'administrator/view_attendance_records.html', {
        'attendance_book': attendance_book,
        'students': students,
        'records_by_date_session': records_by_date_session,
        'student_attendance': student_attendance,
        'total_sessions':total_sessions
    })


# Delete Attendance Book
def delete_attendance_book(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    
    if request.method == 'POST':
        attendance_book.delete()
        messages.success(request, 'Attendance book deleted successfully.')
        return redirect(reverse_lazy('view_attendance_books')) 
    
    return render(request, 'administrator/delete_attendance_book.html', {'attendance_book': attendance_book})


# Add New Department
@login_required
@role_required(['admin'])
def add_department(request):
    if request.method == 'POST':
        form = AddDepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department added successfully!')
            return redirect('view_departments')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddDepartmentForm()
    return render(request, 'administrator/add_department.html',{'form': form})

# View All Departments
@login_required
@role_required(['admin'])
def view_departments(request):
    departments = Department.objects.all()
    return render(request, 'administrator/view_departments.html',{'departments': departments})

# Edit Department
def edit_department(request, dept_id):
    department = get_object_or_404(Department, dept_id=dept_id)
    if request.method == 'POST':
        form = AddDepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('view_departments')
    else:
        form = AddDepartmentForm(instance=department)
    return render(request, 'administrator/edit_department.html', {'form': form})

# Delete Department
def delete_department(request, dept_id):
    department = get_object_or_404(Department, dept_id=dept_id)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully!')
        return redirect('view_departments')
    return render(request, 'administrator/delete_department.html', {'department': department})


# Add Course
@login_required
@role_required(['admin'])
def add_course(request):
    if request.method == 'POST':
        form = AddCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added successfully!')
            return redirect('view_courses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddCourseForm()
    return render(request, 'administrator/add_course.html',{'form': form})

# View Courses
@login_required
@role_required(['admin'])
def view_courses(request):
    courses = Course.objects.all()
    return render(request, 'administrator/view_courses.html',{'courses': courses})


# Edit Course
def edit_course(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    if request.method == 'POST':
        form = AddCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('view_courses')
    else:
        form = AddCourseForm(instance=course)
    return render(request, 'administrator/edit_course.html', {'form': form})

# Delete Course
def delete_course(request, course_id):
    course = get_object_or_404(Course, course_id=course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('view_courses')
    return render(request, 'administrator/delete_course.html', {'course': course})


# USED
def send_sms(phone_number, message):
    """Send SMS via Textlocal API."""
    url = "https://api.textlocal.in/send/"
    payload = {
        'apikey': settings.TEXTLOCAL_API_KEY,
        'numbers': phone_number,
        'message': message,
        'sender': settings.TEXTLOCAL_SENDER_ID,
    }
    
    response = requests.post(url, data=payload)
    return response.json()

# Helper function to send SMS via Textlocal API
#USED
# def send_bulk_sms(absentee_details, selected_date):
#     api_key = settings.TEXTLOCAL_API_KEY
#     sender = settings.TEXTLOCAL_SENDER_ID  # Ensure you are using a registered sender ID
#     messages = []

#     for student_id, student_data in absentee_details.items():
#         sessions_info = '\n'.join(
#             [f"Subject Code: {s['subject_code']}, Session: {s['session']}" for s in student_data['absent_sessions']]
#         )
#         # message = f"Dear Parents,\n{student_data['full_name']} ({student_id}) was absent on {selected_date} for:\n{sessions_info}\nPrincipal, BCK"
        
#         absent_class_count = 7
#         message = (
#             f"Dear Parent,\n"
#             f"This is to inform you that {student_data['full_name']} ({student_id}) was absent for {absent_class_count} classes on {selected_date}.\n"
#             f"Regards,\n"
#             f"Principal, BCK"
#         )

#         print(message)

#         messages.append({
#             'recipient': "91" + student_data['parent_phoneno'],
#             'message': message
#         })


#     # Send messages
#     sent_count = 0
#     for msg in messages:
#         # response = requests.post('https://api.textlocal.in/send/', {
#         #     'apikey': api_key,
#         #     'numbers': msg['recipient'],
#         #     'message': msg['message'],
#         #     'sender': sender
#         # })

#         # response_json = response.json()

#         data =  urllib3.parse.urlencode({'apikey': api_key, 'numbers': msg['recipient'],
#         'message' : msg['message'], 'sender': sender})
#         data = data.encode('utf-8')
#         request = urllib3.request.Request("https://api.textlocal.in/send/?")
#         f = urllib.request.urlopen(request, data)
#         fr = f.read()
#         print(fr)
#         # return(fr)


#         # if response_json.get('status') == 'success':
#         if response_json.get('status') == 'success':
#             sent_count += 1
#         else:
#             return False, response_json.get('errors', [{'message': 'Unknown error'}])[0]['message']

#     return True, sent_count



# def send_bulk_sms(absentee_details, selected_date):
#     api_key = settings.TEXTLOCAL_API_KEY
#     sender = settings.TEXTLOCAL_SENDER_ID  # Ensure you are using a registered sender ID
#     messages = []

#     for student_id, student_data in absentee_details.items():
#         # Dynamically calculate the number of absent sessions (classes)
#         absent_class_count = len(student_data['absent_sessions'])

#         sessions_info = '\n'.join(
#             [f"Subject Code: {s['subject_code']}, Session: {s['session']}" for s in student_data['absent_sessions']]
#         )
        
#         # Construct the message
#         # message = (
#         #     f"Dear Parent,\n"
#         #     f"This is to inform you that {student_data['full_name']} ({student_id}) was absent for {absent_class_count} classes on {selected_date}.\n"
#         #     f"Regards,\n"
#         #     f"Principal, BCK"
#         # )

#         message = (
#             f"Dear Parent,\nThis is to inform you that {student_data['full_name']} ({student_id}) was absent for {absent_class_count} classes on {selected_date}.\nRegards,\nPrincipal, BCK"
#         )

#         print(message)

#         # Append the message and recipient details
#         messages.append({
#             'recipient': "91" + student_data['parent_phoneno'],
#             'message': message
#         })

#     # Send messages
#     sent_count = 0
#     for msg in messages:
#         # Prepare the data for the POST request
#         data = urllib.parse.urlencode({
#             'apikey': api_key,
#             'numbers': msg['recipient'],
#             'message': msg['message'],
#             'sender': sender
#         }).encode('utf-8')
        
#         # Make the POST request to Textlocal API
#         request = urllib.request.Request("https://api.textlocal.in/send/")
#         try:
#             with urllib.request.urlopen(request, data) as response:
#                 response_text = response.read().decode('utf-8')
#                 response_json = json.loads(response_text)
                
#                 # Check the status of the response
#                 if response_json.get('status') == 'success':
#                     sent_count += 1
#                 else:
#                     error_message = response_json.get('errors', [{'message': 'Unknown error'}])[0]['message']
#                     return False, error_message
#         except Exception as e:
#             return False, str(e)

#     return True, sent_count

def send_bulk_sms(absentee_details, selected_date):
    api_key = settings.TEXTLOCAL_API_KEY
    sender = settings.TEXTLOCAL_SENDER_ID  # Ensure you are using a registered sender ID
    messages = []

    # Convert selected_date from '2024-10-31' to '31/10/24'
    formatted_date = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%d/%m/%Y')
    print(formatted_date)

    for student_id, student_data in absentee_details.items():
        # Dynamically calculate the number of absent sessions (classes)
        absent_class_count = len(student_data['absent_sessions'])

        # print(student_data['absent_sessions'])
        absent_sessions = ",".join(
                    [f"{session['session']}"
                    for session in student_data['absent_sessions']]
                )

        # absent_class_count = 7
        print(absent_sessions)
        
        # Construct the message
        # message = (
        #     f"Dear Parent,\nThis is to inform you that {student_data['full_name']} ({student_id}) was absent for {absent_class_count} classes on {formatted_date}.\nRegards,\nPrincipal, BCK"
        # )

        message = (
            f"Dear Parent,\nThis is to inform you that {student_data['full_name'][:20]} ( {student_id[:15]}) was absent for {str(absent_class_count)[:1]} classes ( {absent_sessions[:14]}) on {formatted_date[:8]}.\nRegards,\nPrincipal, BCK"
        )

        print(message)

        # Append the message and recipient details
        messages.append({
            'recipient': "91" + student_data['parent_phoneno'],
            'message': message
        })

    # Send messages
    sent_count = 0
    # for msg in islice(messages, 100):
    for msg in messages:
        # Prepare the data for the GET request by constructing the query string
        params = {
            'message': msg['message']
        }
        
        # URL encode the parameters
        query_string = urllib.parse.urlencode(params)
        url = f" https://api.textlocal.in/send/?apiKey={api_key}&sender={sender}&numbers={msg['recipient']}&{query_string}"
        # url = f"test"
        # print(url)

        # Make the GET request to Textlocal API
        try:
            with urllib.request.urlopen(url) as response:
                response_text = response.read().decode('utf-8')
                response_json = json.loads(response_text)
                
                # Check the status of the response
                if response_json.get('status') == 'success':
                    sent_count += 1
                else:
                    error_message = response_json.get('errors', [{'message': 'Unknown error'}])[0]['message']
                    return False, error_message
        except Exception as e:
            return False, str(e)

    return True, sent_count

# USED
def send_absentee_sms(request):
    if request.method == 'POST':
        selected_date = request.POST.get('selected_date')
        absentee_details = get_absent_details_by_date(selected_date)

        # Call the helper function to send SMS
        success, result = send_bulk_sms(absentee_details, selected_date)

        if success:
            return JsonResponse({'success': True, 'sent_count': result})
        else:
            return JsonResponse({'success': False, 'error': result})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# USED
def view_attendnace_report(request):
    absentee_details = None
    selected_date = None
    sms_sent_count = 0

    if request.method == 'POST':
        selected_date = request.POST.get('selected_date')
        # Convert selected_date from '2024-10-31' to '31/10/24'
        formatted_date = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%d/%m/%y')
        
        # Get absentees by selected date
        absentee_details = get_absent_details_by_date(selected_date)
        
        # Check if the 'send_sms' button was clicked
        if 'send_sms' in request.POST and absentee_details:
            for student_id, student_data in absentee_details.items():
                # Create SMS message
                absent_sessions = "\n".join(
                    [f"{session['subject_name']} (Code: {session['subject_code']}) Session: {session['session']}"
                    for session in student_data['absent_sessions']]
                )

                absent_class_count = 7
                message = (
                    f"Dear Parent,\n"
                    f"This is to inform you that {student_data['full_name']} ({student_id}) was absent for {absent_class_count} classes on {selected_date}.\n"
                    f"Regards,\n"
                    f"Principal, BCK"
                )

                print(message)
                
                # Send SMS
                response = send_sms("91"+student_data['parent_phoneno'], message)
                if response['status'] == 'success':
                    sms_sent_count += 1
                else:
                    messages.error(request, f"Failed to send SMS to {student_data['full_name']}.")

            # Display success message
            if sms_sent_count:
                messages.success(request, f"SMS sent to {sms_sent_count} parents successfully.")
            else:
                messages.error(request, "No SMS was sent due to errors.")

    context = {
        'absentee_details': absentee_details,
        'selected_date': selected_date,
    }
    return render(request, 'administrator/view_attendance_report.html', context)


def send_absent_sms_view(request):
    if request.method == 'POST':
        selected_date = request.POST.get('selected_date')  # Assume date input in 'YYYY-MM-DD' format
        absentee_details = get_absent_details_by_date(selected_date)
        print(absentee_details)
        abcount = int(len(absentee_details))
        
        if absentee_details:
            # res = send_sms_to_absentees(absentee_details,selected_date)
            res = None
            print(res)
            if res is None:
                messages.error(request, f'Error while sending SMS, Not sent to {abcount} Absentees')
            else:
                messages.success(request, f'SMS sent to {abcount} Absentees')
            return render(request, 'administrator/send_sms.html')
        else:
            messages.error(request, f'No Absentees found')
            return render(request, 'administrator/send_sms.html')
    
    return render(request, 'administrator/send_sms.html')



def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)


#======================== TEACHER VIEWS ==========================================

# Teacher Dashboard
@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    userid = request.user.userid
    total_attendance_books = AttendanceBook.objects.filter(teachers__user__userid=userid).count()
    notifications = Notification.objects.all().order_by('-created_at')

    context = {
        'total_attendance_books':total_attendance_books,
        'notifications':notifications
    }
    return render(request, 'teacher/dashboard.html',context)

# Teacher Profile
@login_required
@role_required(['teacher'])
def teacher_profile(request):
    # Assuming the logged-in user is an teacher
    teacher = get_object_or_404(Teacher, user=request.user)
    return render(request, 'teacher/teacher_profile.html', {'teacher': teacher})


# Teacher Change Password
@login_required
def teacher_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Your password was successfully updated!')
            return redirect('teacher_change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'teacher/change_password.html', {
        'form': form
    })

# View Teacher Attendance Books
@login_required
@role_required(['teacher'])
def teacher_view_attendance_books(request):
    userid = request.user.userid
    # print(userid)
    attendance_books = AttendanceBook.objects.filter(teachers__user__userid=userid)
    # print(attendance_books)
    return render(request, 'teacher/view_attendance_books.html', {
        'attendance_books': attendance_books
    })


# Teacher Mark Attendance
@login_required
@role_required(['teacher'])
def teacher_mark_attendance(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    students = attendance_book.students.all()
    attendance_records = AttendanceRecord.objects.filter(attendance_book=attendance_book).order_by('date', 'session')

    # Create a dictionary to organize records by date and session
    records_by_date_session = {}
    for record in attendance_records:
        records_by_date_session.setdefault(record.date, {}).setdefault(record.session, {})[record.student.user.userid] = record.get_status_display

    # Calculate total sessions and attendance count for each student
    increment_value = int(attendance_book.book_type)
    total_sessions = len(set((record.date, record.session) for record in attendance_records)) * increment_value

    student_attendance = {
        student.user.userid: {
            'count': AttendanceRecord.objects.filter(
                attendance_book=attendance_book,
                student=student,
                status=True
            ).count() * increment_value,
            'percentage': round(
                (AttendanceRecord.objects.filter(
                    attendance_book=attendance_book,
                    student=student,
                    status=True
                ).count() * increment_value / total_sessions) * 100, 2) if total_sessions > 0 else 0
        }
        for student in students
    }

    if request.method == 'POST':
        selected_students = set(request.POST.getlist('attendance'))
        current_date = request.POST.get('date')
        session = request.POST.get('session')

        # Prepare bulk create and update data
        update_data = []
        create_data = []
        
        for student in students:
            status = student.user.userid in selected_students

            record_data = {
                'attendance_book': attendance_book,
                'student': student,
                'date': current_date,
                'session': session,
                'status': status,
                'count': student.attendancerecord_set.filter(status=True).count() + (increment_value if status else 0)
            }
            
            if AttendanceRecord.objects.filter(
                attendance_book=attendance_book,
                student=student,
                date=current_date,
                session=session
            ).exists():
                # Collect data for bulk updates
                update_data.append(AttendanceRecord(
                    id=AttendanceRecord.objects.get(
                        attendance_book=attendance_book,
                        student=student,
                        date=current_date,
                        session=session
                    ).id,
                    **record_data
                ))
            else:
                # Collect data for bulk creation
                create_data.append(AttendanceRecord(**record_data))

        try:
            with transaction.atomic():
                # Perform bulk update and create operations
                if update_data:
                    AttendanceRecord.objects.bulk_update(update_data, ['status', 'count'])
                if create_data:
                    AttendanceRecord.objects.bulk_create(create_data)

            messages.success(request, 'Attendance Marked Successfully')

        except Exception as e:
            messages.error(request, f'Error occurred while marking attendance: {str(e)}')

        return redirect('teacher_view_attendance_records', pk=pk)

    return render(request, 'teacher/mark_attendance.html', {
        'attendance_book': attendance_book,
        'students': students,
        'attendance_records': attendance_records,
        'records_by_date_session': records_by_date_session,
        'student_attendance': student_attendance,
        'total_sessions': total_sessions,
    })


@login_required
@role_required(['teacher'])
def teacher_view_attendance_records(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    students = attendance_book.students.all()
    attendance_records = AttendanceRecord.objects.filter(attendance_book=attendance_book).order_by('date', 'session')

    # Create a dictionary to organize records by date and session
    records_by_date_session = {}
    for record in attendance_records:
        if record.date not in records_by_date_session:
            records_by_date_session[record.date] = {}
        if record.session not in records_by_date_session[record.date]:
            records_by_date_session[record.date][record.session] = {}
        records_by_date_session[record.date][record.session][record.student.user.userid] = record.get_status_display

    # Calculate total sessions and attendance count for each student
    increment_value = int(attendance_book.book_type)
    print(increment_value)
    student_attendance = {}
    total_sessions = len(set((record.date, record.session) for record in attendance_records))*increment_value
    # total_sessions = (total_sessions*increment_value)

    for student in students:
        attendance_count = AttendanceRecord.objects.filter(
            attendance_book=attendance_book, student=student, status=True
        ).count()
        attendance_count = (attendance_count * increment_value)
        print(attendance_count)
        attendance_percentage = (attendance_count / total_sessions) * 100 if total_sessions > 0 else 0
        student_attendance[student.user.userid] = {
            'count': attendance_count,
            'percentage': round(attendance_percentage, 2),
        }
    return render(request, 'teacher/view_attendance_records.html', {
        'attendance_book': attendance_book,
        'students': students,
        'records_by_date_session': records_by_date_session,
        'student_attendance': student_attendance,
        'total_sessions':total_sessions
    })



# def send_absent_sms_view(request):
#     if request.method == 'POST':
#         selected_date = request.POST.get('selected_date')  # Assume date input in 'YYYY-MM-DD' format
#         absentee_details = get_absent_details_by_date(selected_date)
#         abcount = int(len(absentee_details))
        
#         if absentee_details:
#             res = send_sms_to_absentees(absentee_details,selected_date)
#             print(res)
#             if res is None:
#                 messages.error(request, f'Error while sending SMS, Not sent to {abcount} Absentees')
#             else:
#                 messages.success(request, f'SMS sent to {abcount} Absentees')
#             return render(request, 'administrator/send_sms.html')
#         else:
#             messages.error(request, f'No Absentees found')
#             return render(request, 'administrator/send_sms.html')
    
#     return render(request, 'administrator/send_sms.html')


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)


# View Notifications
@login_required
@role_required(['admin','teacher'])
def notification_list(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'teacher/notifications.html', {'notifications': notifications})



#====================== STUDENT MODULE ===================================================

def student_login(request):
    if request.method == 'POST':
        usn = request.POST.get('usn')
        dob = request.POST.get('dob')

        try:
            # Fetch the student using USN and DOB
            student = Student.objects.get(usn=usn, dob=dob)
            
            # Retrieve all attendance books assigned to this student
            attendance_books = student.attendancebook_set.all()
            
            # Calculate total, attended classes, and percentage for each book
            attendance_data = []
            for book in attendance_books:
                total_classes = AttendanceRecord.objects.filter(attendance_book=book, student=student).count()
                attended_classes = AttendanceRecord.objects.filter(attendance_book=book, student=student, status=True).count()
                percentage = (attended_classes / total_classes) * 100 if total_classes > 0 else 0

                attendance_data.append({
                    'book': book,
                    'total_classes': total_classes,
                    'attended_classes': attended_classes,
                    'percentage': round(percentage, 2),
                })
            
            # Add success message
            messages.success(request, f'Welcome {student.user.fullname}, your attendance records have been loaded successfully.')

            return render(request, 'student/attendance.html', {'attendance_data': attendance_data, 'student': student})
        
        except Student.DoesNotExist:
            # Add error message
            messages.error(request, 'No student found with the provided USN and DOB. Please try again.')
            return render(request, 'student/login.html')
    
    return render(request, 'student/login.html')