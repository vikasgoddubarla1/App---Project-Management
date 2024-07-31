from locations.models import Module

modules = [
   {'id': 1, 'name': 'Locations', 'slug': 'locations'},
   {'id':2, 'name':'Contracts', 'slug':'contracts'},
   {'id':3, 'name':'Devices', 'slug':'devices'},
   
]

def create_modules():
   for module_data in modules:
       module_id = module_data['id']
       if not Module.objects.filter(id=module_id).exists():
           Module.objects.create(**module_data)