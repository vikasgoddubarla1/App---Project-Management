from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

class SuperUser(BaseCommand):
    help = 'Create superuser with fixed email and password'
    
    def user(self, *args, **options):
        email = 'youremail'
        username = 'username'
        password = 'password@$'
        
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.NOTICE("Super user already exists."))
        else:
            User.objects.create(email, '', username, '', password)
            self.stdout.write(self.style.NOTICE("Super user created successfully!"))
            
