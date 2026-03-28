# MIIA Academic Information System - Backend

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.2.7-green.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.14.0-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📚 Table of Contents
- [Project Overview](#-project-overview)
- [Technology Stack](#-technology-stack)
- [System Requirements](#-system-requirements)
- [Installation Guide](#-installation-guide)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Documentation](#-api-documentation)
- [Authentication & Authorization](#-authentication--authorization)
- [User Roles & Permissions](#-user-roles--permissions)
- [Seeders & Data Management](#-seeders--data-management)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [API Endpoints Reference](#-api-endpoints-reference)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Project Overview

MIIA Backend is a robust Django REST Framework (DRF) application that serves as the API backend for the MIIA Academic Information System, an Islamic school management platform. It provides a comprehensive, secure, and scalable set of endpoints for managing the entire school ecosystem, from student registration to fee collection.

### ✨ Key Features

- **🔐 JWT Authentication** with role-based access control and token refresh.
- **👥 Multi-role System**: Admin, Teacher, Student, Parent, Staff.
- **📝 Student Registration Workflow** with a multi-step form and admin approval process.
- **📚 Academic Management**: Courses, subjects, enrollments, grading, and progress tracking.
- **📅 Attendance Tracking** with daily records and reporting.
- **💰 Fee Management**: Structures, invoices, payment tracking, and receipts.
- **💬 Communication**: Announcements, direct messages, and in-app notifications.
- **🛡️ Granular Permissions** enforced via Django's groups and custom permission classes.
- **📄 Auto-generated API Documentation** (Swagger/OpenAPI) for easy exploration.
- **🧪 Comprehensive Seeders** for populating the database with realistic test data.

---

## 🛠️ Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Programming Language |
| Django | 4.2.7 | High-level Python web framework |
| Django REST Framework | 3.14.0 | Toolkit for building Web APIs |
| DRF SimpleJWT | 5.3.0 | JSON Web Token authentication for DRF |
| Django CORS Headers | 4.3.1 | Cross-Origin Resource Sharing (CORS) management |
| Django Filter | 23.5 | Dynamic queryset filtering for APIs |
| DRF Spectacular | 0.26.5 | OpenAPI schema generation and documentation |
| SQLite | - | Default database for development |
| MySQL | 8.0+ | Production database |
| Faker | 28.0.0 | Python library for generating fake data (seeders) |

---

## 💻 System Requirements

- **Python**: 3.11 or higher
- **pip**: Python package manager
- **Database**: SQLite (development) or MySQL 8.0+ (production)
- **Git**: For version control

---

## 🔧 Installation Guide

Follow these steps to get the development environment running.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/miia-backend.git
cd miia-backend
2. Create and Activate Virtual Environment
bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate      # On Linux/Mac
# or
venv\Scripts\activate        # On Windows
3. Install Dependencies
bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the project root and add the following configuration. Adjust the values as needed.

env
# Django Settings
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:8080

# Email Configuration (for password resets, etc.)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@miia.edu
SUPPORT_EMAIL=support@miia.edu

# Site Configuration
SITE_NAME=MIIA Academy
5. Run Database Migrations
bash
python manage.py migrate
6. Create a Superuser
bash
python manage.py createsuperuser
Follow the prompts to set up your admin account. Example:

Email: admin@miia.edu

Username: admin_miia

Password: Admin@123456

7. Seed the Database (Optional)
Populate the database with test data.

bash
# Run all seeders
python manage.py seed_db

# Clear existing data and reseed (useful for a fresh start)
python manage.py seed_db --fresh
8. Run the Development Server
bash
python manage.py runserver
The API will be available at http://localhost:8000. You can now explore the endpoints!

📁 Project Structure
The project follows a modular, app-based architecture for maintainability and scalability.

text
miiabackend/
├── apps/                           # All Django applications
│   ├── accounts/                   # User management (accounts, profiles)
│   │   ├── models/                 # User, Teacher, Student, Parent, Staff models
│   │   ├── serializers/            # Data serializers for auth and users
│   │   ├── views/                  # API views for authentication and user management
│   │   ├── urls/                   # URL routing for accounts
│   │   ├── permissions.py          # Custom permission classes
│   │   ├── signals.py              # Django signals (e.g., post-save actions)
│   │   └── admin.py                # Admin interface customization
│   ├── academics/                  # Courses, subjects, enrollments, grades
│   ├── applications/               # Student registration applications
│   ├── attendance/                 # Attendance tracking
│   ├── communication/              # Messages and announcements
│   ├── finance/                    # Fee structures, invoices, payments
│   ├── resources/                  # Study materials
│   └── core/                       # Abstract base models and shared utilities
│       └── models.py               # Base model classes (e.g., TimeStampedModel)
├── config/                         # Django project configuration
│   ├── settings/
│   │   ├── base.py                 # Base settings (common to all environments)
│   │   ├── development.py          # Overrides for development
│   │   └── production.py           # Overrides for production
│   └── urls.py                     # Main URL routing
├── seeders/                        # Database seeder scripts
│   ├── base_seeder.py              # Abstract base seeder class
│   ├── auth_seeder.py              # Seeder for users, groups, permissions
│   └── academic_seeder.py          # Seeder for academic data (courses, enrollments)
├── requirements/                   # Dependency files
│   ├── base.txt                    # Core dependencies
│   ├── development.txt             # Dependencies for development (testing, linting)
│   └── production.txt              # Dependencies for production (e.g., gunicorn, mysqlclient)
├── media/                          # User-uploaded files (managed by Django)
├── static/                         # Collected static files
├── .env                            # Environment variables (gitignored)
├── .gitignore
├── manage.py
└── README.md

📖 API Documentation
Interactive API documentation is automatically generated and available once the server is running.

Swagger UI: http://localhost:8000/api/docs/

ReDoc: http://localhost:8000/api/redoc/

OpenAPI Schema (JSON): http://localhost:8000/api/schema/

Base URL
text
http://localhost:8000/api/
📨 Standard API Response Format
Success Response

json
{
  "status": "success",
  "data": { ... },
  "message": "Optional success message"
}
Error Response

json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "field_errors": {
    "field_name": ["Specific error message"]
  }
}
🔐 Authentication & Authorization
The API uses JWT (JSON Web Token) for authentication.

JWT Authentication Flow
Login: Send a POST request to /api/auth/login/ with your email and password.

Receive Tokens: The server returns access and refresh tokens.

Authenticate Requests: Include the access token in the Authorization header: Bearer <access_token>.

Refresh Token: When the access token expires, send a POST request to /api/auth/token/refresh/ with the refresh token to get a new pair.

Login Example
Request

http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "teacher@miia.edu",
  "password": "yourpassword"
}
Response

json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "teacher@miia.edu",
    "name": "Jane Doe",
    "role": "teacher",
    "permissions": ["course:view", "grade:edit"]
  },
  "profile": {
    "user_id": "uuid",
    "full_name": "Jane Doe",
    "department": "Mathematics"
  }
}
👥 User Roles & Permissions
The permission system is designed around groups and Django's built-in permissions, with a custom has_permission check.

Roles Overview
Role	Description	Key Access
Admin	System-wide administrator	Full access to all resources and settings.
Teacher	Classroom instructor	Manage courses, assignments, grades, and attendance for their classes.
Student	Enrolled learner	View courses, submit assignments, check grades and attendance.
Parent	Student guardian	Monitor child's progress, view reports, and pay fees.
Staff	Administrative staff	Manage student records, process applications, and handle fees.
Permission Structure
Permissions follow a resource:action naming convention. They are assigned to groups, and users inherit permissions based on their role group.

Course Permissions

course:view - View courses

course:create - Create courses

course:edit - Edit courses

course:delete - Delete courses

course:enroll - Enroll students in a course

Grade Permissions

grade:view - View grades

grade:edit - Edit/assign grades

Student Permissions

student:view - View student profiles

student:edit - Edit student profiles

student:progress:view - View student progress reports

Fee Permissions

fees:view - View fee structures and invoices

fees:pay - Make a payment

fees:create - Create fee structures (staff/admin)

🌱 Seeders & Data Management
The project includes a powerful seeder system to quickly populate the database with realistic test data for development and testing.

Running Seeders
bash
# Run all seeders
python manage.py seed_db

# Clear existing data and reseed
python manage.py seed_db --fresh
Seeder Structure
auth_seeder.py: Creates user groups, permissions, and test users for all roles (admins, teachers, students, parents, staff). It also creates a set of student applications.

academic_seeder.py: Creates academic years, terms, subjects, courses, and enrollments linking students to courses.

Creating a Custom Seeder
To create a new seeder for a specific app:

Create a new file, e.g., seeders/my_app_seeder.py.

Inherit from BaseSeeder.

Implement the seed() method.

python
# seeders/my_app_seeder.py
from .base_seeder import BaseSeeder

class MyAppSeeder(BaseSeeder):
    def seed(self):
        print("  🌱 Seeding MyApp data...")
        # Your seeding logic using models
Then, add it to seeders/main.py to be included in the main command.

🧪 Testing
A comprehensive test suite ensures the reliability of the API.

Running Tests
bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test apps.accounts

# Run a specific test file
python manage.py test apps.accounts.tests.test_models

# Run with higher verbosity
python manage.py test --verbosity=2
Test Structure
Tests are organized within each app, mirroring the project structure.

text
apps/accounts/tests/
├── __init__.py
├── test_models.py
├── test_serializers.py
├── test_views.py
└── test_permissions.py
🚀 Deployment
This section outlines the key steps for deploying the application to a production environment.

Prerequisites
A production-grade database (e.g., MySQL, PostgreSQL)

A web server (e.g., Nginx)

An application server (e.g., Gunicorn, uWSGI)

Domain name (optional but recommended)

1. Set Production Settings
Ensure your DJANGO_SETTINGS_MODULE environment variable points to the production settings:

bash
export DJANGO_SETTINGS_MODULE=config.settings.production
2. Update Environment Variables
Your production .env file should contain:

env
DEBUG=False
SECRET_KEY=your-strong-production-secret-key
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

Issue	Solution
ModuleNotFoundError: No module named 'pkg_resources'	Run pip install --upgrade setuptools wheel
UNIQUE constraint failed: users.username	Run python manage.py shell and delete conflicting user(s).
Database is locked (SQLite)	Stop the development server and run python manage.py migrate.
Migration dependencies error	Delete migration files (except __init__.py) and run makemigrations and migrate again.
Permission denied for media files	Ensure the web server user (e.g., www-data) has read/write permissions: chown -R www-data:www-data media/
📍 API Endpoints Reference

Reference for the main API endpoints. See the Swagger documentation for full details.

🤝 Contributing
We welcome contributions! Please follow this workflow:

Fork the repository.

Create a feature branch: git checkout -b feature/amazing-feature.

Make your changes, ensuring they are well-tested and follow the code style.

Run the tests to make sure nothing breaks.

Commit your changes: git commit -m 'feat: Add some amazing feature'.

Push to the branch: git push origin feature/amazing-feature.

Open a Pull Request.

Code Style
Follow PEP 8 guidelines.

Use Black for code formatting.

Use isort for import sorting.

bash
# Format code
black apps/
isort apps/

# Check style
flake8 apps/
📄 License
Distributed under the MIT License. See LICENSE for more information.

📞 Contact & Support
Project Repository: GitHub

Report Issues: GitHub Issues

Support Email: support@miia.edu

