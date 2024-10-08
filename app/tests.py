from django.test import TestCase
from app.models import Department

# Create your tests here.

x = Department.objects.all()
print(x)
x.delete()