# Django Attendance Management System

![Django](https://img.shields.io/badge/Django-3.0+-green?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [License](#license)

## Introduction
This project is an **Attendance Management System** built with Django. It includes role-based authentication for Admin, Teacher, and HOD, and allows for attendance management through a simple and intuitive interface. Teachers can log in and mark attendance for students, while Admins can manage users and attendance books.

## Features
- Role-based Authentication (Admin, Teacher, HOD, Student)
- Manage Attendance Books
- Mark Attendance for Students
- Responsive User Interface
- Error and Success Message Display

## Technologies Used

- ![Django](https://img.shields.io/badge/-Django-092E20?style=for-the-badge&logo=django&logoColor=white) Django 3.0+
- ![Python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white) Python 3.8+
- ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white) SQLite (default database)
- ![Bootstrap](https://img.shields.io/badge/-Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white) Bootstrap 4 (for responsive design)
- ![HTML](https://img.shields.io/badge/-HTML-E34F26?style=for-the-badge&logo=html5&logoColor=white) HTML5
- ![CSS](https://img.shields.io/badge/-CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white) CSS3

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/django-attendance-system.git
cd django-attendance-system
```

### Step 2: Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Create a Superuser
```bash
python manage.py createsuperuser
```

### Step 6: Run the Development Server
```bash
python manage.py runserver
```

### Step 7: Access the Application
- Open your browser and navigate to `http://127.0.0.1:8000/`.

## Usage

- **Admin**: Manage users, attendance books, and roles.
- **Teacher**: Mark attendance for assigned classes and view attendance records.
- **HOD**: Oversee departmental attendance records.
- **Student**: View their attendance records.

### Login
You can log in using the credentials you created during the superuser setup or create new users through the Django admin interface.

## Screenshots

### Login Page
![Login Page](screenshots/login.png)

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Attendance Management
![Attendance Management](screenshots/attendance.png)

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Note**: Replace the image paths in the "Screenshots" section with actual screenshots from your project.

This `README.md` provides all necessary information for someone to understand, install, and use your Django project. Make sure to adjust the paths, links, and descriptions according to your specific project details.