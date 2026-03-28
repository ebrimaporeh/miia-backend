# seeders/base_seeder.py
import random
import string
from datetime import datetime, timedelta
from django.db import transaction
from faker import Faker

# Initialize Faker with multiple locales
fake = Faker(['en_US', 'ar_SA'])  # Add Arabic locale for Islamic names

class BaseSeeder:
    """Base class for all seeders"""
    
    def __init__(self):
        self.created_objects = {}
        self.fake = fake
    
    def run(self):
        """Main method to run the seeder"""
        print(f"\n🌱 Running {self.__class__.__name__}...")
        with transaction.atomic():
            self.seed()
        print(f"✅ {self.__class__.__name__} completed")
    
    def seed(self):
        """Override this method in child classes"""
        raise NotImplementedError
    
    def random_string(self, length=10):
        """Generate random string"""
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    def random_phone(self):
        """Generate random phone number"""
        return f"+{random.randint(1, 99)}{random.randint(100000000, 999999999)}"
    
    def random_date(self, start_date=None, end_date=None):
        """Generate random date"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365*10)
        if not end_date:
            end_date = datetime.now()
        return self.fake.date_between(start_date=start_date, end_date=end_date)
    
    def random_choice(self, choices):
        """Random choice from list"""
        return random.choice(choices)
    
    def random_bool(self):
        """Random boolean"""
        return random.choice([True, False])
    
    def random_int(self, min_val=1, max_val=100):
        """Random integer"""
        return random.randint(min_val, max_val)
    
    def random_float(self, min_val=0, max_val=100, decimals=2):
        """Random float"""
        return round(random.uniform(min_val, max_val), decimals)
    
    def random_islamic_name(self):
        """Generate random Islamic name"""
        islamic_names = [
            'Muhammad', 'Abdullah', 'Omar', 'Ali', 'Hassan', 'Hussein',
            'Fatima', 'Aisha', 'Maryam', 'Zainab', 'Khadija', 'Sofia',
            'Ibrahim', 'Yusuf', 'Musa', 'Isa', 'Yahya', 'Zakariya'
        ]
        return self.random_choice(islamic_names)