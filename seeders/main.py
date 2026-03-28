# seeders/main.py
import os
import sys
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miiabackend.settings')
django.setup()

# Import models
from apps.accounts.models import User, Teacher, Student, Parent, Staff
from apps.applications.models import Application

# Import seeders
from seeders.auth_seeder import AuthSeeder
from seeders.academic_seeder import AcademicSeeder

def run_all_seeders():
    """Run all seeders"""
    print("\n" + "="*50)
    print("🌱 STARTING DATABASE SEEDING")
    print("="*50)
    
    try:
        # Run auth seeder
        auth_seeder = AuthSeeder()
        auth_seeder.run()
        
        # Run academic seeder
        academic_seeder = AcademicSeeder()
        academic_seeder.run()
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print("\n" + "="*50)
    print("✅ SEEDING COMPLETED SUCCESSFULLY!")
    print("="*50)
    
    # Print summary
    print("\n📊 Summary:")
    print(f"  - Admin users: {User.objects.filter(role='admin').count()}")
    print(f"  - Teacher users: {User.objects.filter(role='teacher').count()}")
    print(f"  - Student users: {User.objects.filter(role='student').count()}")
    print(f"  - Parent users: {User.objects.filter(role='parent').count()}")
    print(f"  - Staff users: {User.objects.filter(role='staff').count()}")
    print(f"  - Applications: {Application.objects.count()}")

if __name__ == "__main__":
    run_all_seeders()