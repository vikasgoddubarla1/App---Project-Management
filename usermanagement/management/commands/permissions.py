from locations.models import Permission

permissions = [
   {'id': 1, 'name': 'Read'},
   {'id': 2, 'name': 'Create'},
   {'id': 3, 'name': 'Update'},
   {'id': 4, 'name': 'Delete'},
]

def create_permissions():
   for permissions_data in permissions:
       permission_id = permissions_data['id']
       if not Permission.objects.filter(id=permission_id).exists():
           Permission.objects.create(**permissions_data)