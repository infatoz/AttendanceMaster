# Generated by Django 5.1 on 2024-08-25 18:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_attendancerecord_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='attendancerecord',
            unique_together=set(),
        ),
    ]
