from app.models import Student

# Create your tests here.

x = Student.objects.get(usn='S101', dob='1999-10-01')
print(x)