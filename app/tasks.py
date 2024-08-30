from datetime import timezone
# from multiprocessing.dummy.connection import Client

from celery import shared_task
from app.models import AttendanceRecord
from django.core.mail import send_mass_mail


@shared_task
def send_daily_absent_notifications():
    today = timezone.now().date()
    absentees = AttendanceRecord.objects.filter(date=today, status=False)
    send_notifications(absentees)

def send_notifications(absentees):
    email_messages = []
    sms_messages = []

    for record in absentees:
        student = record.student
        parent_email = student.user.email
        parent_phoneno = student.parent_phoneno
        class_details = f'{record.attendance_book.name} on {record.date}'

        # Prepare Email
        email_subject = f'Absence Notification for {student.usn}'
        email_body = f'Your child was absent for {class_details}.'
        email_messages.append((
            email_subject,
            email_body,
            'no-reply@school.com',
            [parent_email],
        ))

        # Prepare SMS
        # sms_body = f'{student.usn} was absent for {class_details}.'
        # sms_messages.append((parent_phoneno, sms_body))

    # Send all emails
    send_mass_mail(tuple(email_messages))

    # Send all SMS
    # client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')
    # for phone, message in sms_messages:
    #     client.messages.create(
    #         body=message,
    #         from_='+1234567890',  # Your Twilio number
    #         to=phone
    #     )

