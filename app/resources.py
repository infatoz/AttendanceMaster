from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import Student, Course
from datetime import datetime

CustomUser = get_user_model()

class StudentResource(resources.ModelResource):
    user = fields.Field(
        column_name='userid',
        attribute='user',
        widget=ForeignKeyWidget(CustomUser, 'userid')
    )
    course = fields.Field(
        column_name='course_id',
        attribute='course',
        widget=ForeignKeyWidget(Course, 'course_id')
    )
    dob = fields.Field(
        column_name='dob',
        attribute='dob'
    )

    class Meta:
        model = Student
        import_id_fields = ['user']
        fields = ('userid', 'usn', 'phone_no', 'parent_phoneno', 'email', 'course_id', 'year', 'section', 'gender', 'dob', 'photo_url')

    def before_import_row(self, row, **kwargs):
        # Convert date format from DD/MM/YYYY to YYYY-MM-DD
        date_str = row.get('dob')
        if date_str:
            try:
                # Convert date string from DD/MM/YYYY to YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                row['dob'] = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                # Handle invalid date format
                row['dob'] = None  # or another appropriate default value

        print(row['dob'])
        userid = row['userid']
        fullname = row['fullname']
        role = 'student'
        password = row.get('password', 'Welcome@12345')  # Use a default password if not provided

        # Create or update CustomUser
        user, created = CustomUser.objects.update_or_create(
            userid=userid,
            defaults={
                'fullname': fullname,
                'role': role,
                'phone_no': row.get('phone_no'),
                'email': row.get('email')
            }
        )

        if created:
            user.set_password(password)
            user.save()

        # Update the row with the user's primary key
        row['user'] = user.pk

    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False, **kwargs):
        if not dry_run:
            users_to_create = []
            students_to_create = []

            # Create a mapping for existing courses to avoid fetching them multiple times
            courses = {course.course_id: course for course in Course.objects.all()}

            for row in dataset.dict:
                # Create CustomUser instance
                user = CustomUser(
                    userid=row['userid'],
                    fullname=row['fullname'],
                    role='student',
                    phone_no=row.get('phone_no'),
                    email=row.get('email')
                )
                users_to_create.append(user)

                # Fetch or create Course instance
                course_id = row.get('course_id')
                course = courses.get(course_id)
                if not course:
                    try:
                        course = Course.objects.get(course_id=course_id)
                        courses[course_id] = course  # Cache the fetched course
                    except ObjectDoesNotExist:
                        # Handle case where the course does not exist
                        continue  # Skip this row or handle it as needed

                # Create Student instance if course is found
                if course:
                    student = Student(
                        user=user,
                        usn=row.get('usn'),
                        parent_phoneno=row.get('parent_phoneno'),
                        course=course,
                        year=row.get('year'),
                        section=row.get('section'),
                        gender=row.get('gender'),
                        dob=row.get('dob'),
                        photo_url=row.get('photo_url')
                    )
                    students_to_create.append(student)

            # Bulk create users and students
            CustomUser.objects.bulk_create(users_to_create, batch_size=1000)
            Student.objects.bulk_create(students_to_create, batch_size=1000)

        # Call the parent method to handle the rest of the import process
        return super().import_data(dataset, dry_run, raise_errors, use_transactions, collect_failed_rows, **kwargs)
