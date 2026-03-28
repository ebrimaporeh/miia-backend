# apps/accounts/management/commands/seed_db.py
import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Seed the database with test data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fresh',
            action='store_true',
            help='Delete existing data before seeding',
        )
    
    def handle(self, *args, **options):
        # Add the project root to path
        project_root = settings.BASE_DIR
        if project_root not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Import seeder
        try:
            from seeders.main import run_all_seeders
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error importing seeder: {e}'))
            self.stdout.write('Make sure you have a seeders folder with main.py in the project root')
            return
        
        if options['fresh']:
            self.stdout.write(self.style.WARNING('⚠️  This will delete all existing data!'))
            confirm = input('Are you sure? Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write('Cancelled.')
                return
            
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys=OFF;')
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%';")
                tables = cursor.fetchall()
                
                for table in tables:
                    try:
                        cursor.execute(f'DELETE FROM {table[0]};')
                        self.stdout.write(f'  Deleted data from {table[0]}')
                    except Exception as e:
                        pass
                
                cursor.execute('PRAGMA foreign_keys=ON;')
            
            self.stdout.write(self.style.SUCCESS('✅ Existing data cleared'))
        
        try:
            run_all_seeders()
            self.stdout.write(self.style.SUCCESS('✅ Seeding completed!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during seeding: {e}'))
            import traceback
            traceback.print_exc()