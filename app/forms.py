from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from app.models import Admin, AttendanceBook, CustomUser, Notification, Student, Teacher, Department, Course


# class UserLoginForm(AuthenticationForm):
#     username = forms.CharField(label='User ID', max_length=15,)
#     password = forms.CharField(label='Password', widget=forms.PasswordInput)

from django import forms
from django.contrib.auth.forms import AuthenticationForm

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='User ID',
        max_length=15,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',  # Disables autocomplete
            'autocorrect': 'off',   # Disables autocorrect for some browsers
            'spellcheck': 'false',  # Disables spellcheck
            'autocapitalize': 'none' # Prevents automatic capitalization
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off',  # Disables autocomplete
        })
    )



# class CustomUserCreationForm(UserCreationForm):
#     class Meta(UserCreationForm.Meta):
#         model = CustomUser
#         fields = ['userid', 'fullname', 'password1', 'phone_no','email']
    
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.set_password(self.cleaned_data['password1'])
#         if commit:
#             user.save()
#         return user

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        strip=False,
        help_text='Enter the password for the new user.'
    )

    class Meta:
        model = CustomUser
        fields = ['userid', 'fullname', 'password', 'phone_no', 'email']

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise forms.ValidationError('Password is required.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class TeacherRegistrationForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['department', 'photo_url']


class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['parent_phoneno','course', 'year', 'section', 'gender', 'dob', 'photo_url']

class AdminRegistrationForm(forms.ModelForm):
    class Meta:
        model = Admin
        fields = ['photo_url']

class AddDepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['dept_id','name']

class AddCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_id','name']

class AttendanceBookForm(forms.ModelForm):
    class Meta:
        model = AttendanceBook
        fields = ['name', 'book_code', 'book_type']

class TeacherCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        required=True,
        label="Upload CSV File",  # Custom label
        widget=forms.FileInput(attrs={'class': 'form-control'})  # Custom class
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')

        # Check the file extension
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Only .csv files are allowed.")

        return file

class StudentCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        required=True,
        label="Upload CSV File",  # Custom label
        widget=forms.FileInput(attrs={'class': 'form-control'})  # Custom class
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')

        # Check the file extension
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Only .csv files are allowed.")

        return file


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'description', 'attachment_link']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'attachment_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Attachment Link (optional)'}),
        }

