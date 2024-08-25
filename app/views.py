from collections import defaultdict
import csv
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.urls import reverse_lazy
from app.forms import AddCourseForm, AddDepartmentForm, AttendanceBookForm, CustomUserCreationForm, StudentCSVUploadForm, StudentRegistrationForm, TeacherCSVUploadForm, TeacherRegistrationForm,  UserLoginForm
from django.contrib.auth.decorators import login_required
from app.decorators import role_required
from django.db import transaction
from django.contrib import messages
from app.models import Admin, AttendanceBook, AttendanceRecord, Course, CustomUser, Department, Student, Teacher
from django.contrib.auth.forms import PasswordChangeForm


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
    return render(request, 'administrator/dashboard.html')


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
@login_required
@role_required(['admin'])
@transaction.atomic
def view_students(request):
    students = Student.objects.all()
    return render(request, 'administrator/view_students.html',{'students': students})


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


# Upload Students via CSV
@login_required
@role_required(['admin'])
@transaction.atomic
def upload_students_csv(request):
    if request.method == 'POST':
        form = StudentCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                # Process CSV file
                csv_reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
                for row in csv_reader:
                    # print(row)
                    userid = row.get('userid')
                    fullname = row.get('fullname')
                    phone_no = row.get('phone_no')
                    parent_phoneno = row.get('parent_phoneno')
                    email = row.get('email')
                    course_id = row.get('course_id')
                    usn = row.get('usn')
                    year=row.get('year')
                    section=row.get('section')
                    gender=row.get('gender')
                    dob = row.get('dob')
                    photo_url = row.get('photo_url')

                    # Convert date format from DD/MM/YYYY to YYYY-MM-DD
                    try:
                        dob = datetime.strptime(dob, '%d/%m/%Y').strftime('%Y-%m-%d')
                    except ValueError:
                        messages.error(request, f"Error processing date for user {userid}: Invalid date format.")
                        continue
                    
                    # Check if user already exists
                    if CustomUser.objects.filter(userid=userid).exists():
                        continue
                    
                    # Create user
                    user = CustomUser(
                        userid=userid,
                        fullname=fullname,
                        phone_no=phone_no,
                        email=email,
                        role='student'
                    )
                    user.set_password('Welcome@12345')
                    user.save()

                    # Get or create course
                    course, created = Course.objects.get_or_create(course_id=course_id)
                    
                    # Create student
                    Student.objects.create(
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
                    
                messages.success(request, 'Students uploaded successfully!')
            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
            return redirect('view_students')
    else:
        form = StudentCSVUploadForm()
    return render(request, 'administrator/upload_students_csv.html', {'form': form})


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
        print(selected_teachers_objs)
        attendance_book.teachers.set(selected_teachers_objs)
        attendance_book.save()
        return redirect('add_attendance_book_student', pk=attendance_book.pk)
    # teachers = Teacher.objects.all()
    # print(teachers)
    return render(request, 'administrator/add_attendance_book_teacher.html', {
        'attendance_book': attendance_book,
        'teachers': teachers
    })

@login_required
@role_required(['admin'])
def add_attendance_book_student(request, pk):
    attendance_book = get_object_or_404(AttendanceBook, pk=pk)
    students = Student.objects.all()
    if request.method == 'POST':
        # print(request.POST)
        # Process form data
        selected_students = request.POST.getlist('students')
        print(selected_students)
        selected_students_objs = Student.objects.filter(user__userid__in=selected_students)
        print(selected_students_objs)
        attendance_book.students.set(selected_students_objs)
        # res = attendance_book.teachers.set(selected_students)
        # print(res)
        attendance_book.save()
        return redirect('view_attendance_books')
    # teachers = Teacher.objects.all()
    return render(request, 'administrator/add_attendance_book_student.html', {
        'attendance_book': attendance_book,
        'students': students
    })

   
# View All Attendance Book
@login_required
@role_required(['admin'])
def view_attendnace_books(request):
    attendance_books = AttendanceBook.objects.all()
    return render(request, 'administrator/view_attendance_books.html', {
        'attendance_books': attendance_books
    })


@login_required
@role_required(['admin', 'teacher'])
def mark_attendance(request, pk):
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
    student_attendance = {}
    total_sessions = len(set((record.date, record.session) for record in attendance_records))
    increment_value = int(attendance_book.book_type)

    for student in students:
        attendance_count = AttendanceRecord.objects.filter(
            attendance_book=attendance_book, student=student, status=True
        ).count()
        attendance_percentage = (attendance_count / total_sessions) * 100 if total_sessions > 0 else 0
        student_attendance[student.user.userid] = {
            'count': attendance_count,
            'percentage': round(attendance_percentage, 2),
        }
    
    if request.method == 'POST':
        selected_students = request.POST.getlist('attendance')
        current_date = request.POST.get('date')
        session = request.POST.get('session')

        try:
            with transaction.atomic():
                for student in students:
                    status = student.user.userid in selected_students

                    # Determine the increment value based on book_type
                    increment_value = int(attendance_book.book_type)

                    # Check if a record already exists for the same student, date, and session
                    existing_record = AttendanceRecord.objects.filter(
                        attendance_book=attendance_book,
                        student=student,
                        date=current_date,
                        session=session
                    ).first()

                    if existing_record:
                        # Update the existing record's status and count
                        existing_record.status = status
                        existing_record.count = student.attendancerecord_set.filter(status=True).count() + (
                            increment_value if status else 0
                        )
                        existing_record.save()
                    else:
                        # Create a new record if it doesn't exist
                        AttendanceRecord.objects.create(
                            attendance_book=attendance_book,
                            student=student,
                            date=current_date,
                            session=session,
                            status=status,
                            count=student.attendancerecord_set.filter(status=True).count() + (
                                increment_value if status else 0
                            )
                        )
            
            messages.success(request, 'Attendance Marked Successfully')

        except Exception as e:
            # Catch any errors and show a message to the user
            messages.error(request, f'Error occurred while marking attendance: {str(e)}')
        return redirect('view_attendance_records',pk=pk)

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
    student_attendance = {}
    total_sessions = len(set((record.date, record.session) for record in attendance_records))

    for student in students:
        attendance_count = AttendanceRecord.objects.filter(
            attendance_book=attendance_book, student=student, status=True
        ).count()
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


#======================== TEACHER VIEWS ==========================================

# Teacher Dashboard
@login_required
@role_required(['teacher'])
def teacher_dashboard(request):
    return render(request, 'teacher/dashboard.html')

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