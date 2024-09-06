from django.utils import timezone
from app.models import AttendanceRecord
from django.conf import settings
from twilio.rest import Client


def get_absent_details_by_date(selected_date):
    # Fetch all attendance records for the selected date where status is False (absent)
    absentees = AttendanceRecord.objects.filter(date=selected_date, status=False)
    
    absentee_details = {}
    for record in absentees:
        student = record.student
        student_key = student.user.userid
        
        if student_key not in absentee_details:
            absentee_details[student_key] = {
                'full_name': student.user.fullname,
                'parent_phoneno': student.parent_phoneno,
                'absent_sessions': []
            }
        
        absentee_details[student_key]['absent_sessions'].append({
            'subject_code': record.attendance_book.book_code,
            'subject_name': record.attendance_book.name,
            'session': record.session
        })
    
    return absentee_details



def send_sms_to_absentees(absentee_details):

    # print(absentee_details)
    # Initialize Twilio client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    messages = []
    
    for student_id, details in absentee_details.items():
        full_name = details['full_name']
        parent_phoneno = "+91"+details['parent_phoneno']
        absent_sessions = details['absent_sessions']
        
        # Create message content
        session_details = ', '.join(
            f"{session['subject_code']}-Class {session['session']}"
            for session in absent_sessions
        )
        
        message_content = (
            f"Dear Parents, {full_name} (Student ID: {student_id}) was absent on\n"
            f"{session_details}.\n-BCK"
        )

        # print(message_content)

        try:
            if parent_phoneno:  # Check if parent's phone number is available
                message = client.messages.create(
                    body=message_content,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=parent_phoneno
                )
                messages.append(message)
            return messages
        except:
            print("An exception occurred")
            return None
            
