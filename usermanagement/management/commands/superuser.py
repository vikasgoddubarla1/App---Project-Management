from usermanagement.models import User
from django.contrib.auth.hashers import make_password

def create_superuser():
   if not User.objects.filter(is_superuser=True).exists():
       user = User.objects.create(
           firstname='firstname',
           lastname='webapp',
           username='solar_project',
           email='welcome@solar.com',
           password=make_password('Solar1234@$'),
           salutation_id=None,
           title_id=None,
           is_admin=True,
           is_staff=True,
           is_active=True,
           is_superuser=True
       )
       print('Superuser created successfully')
   else:
       print('Superuser already exists')