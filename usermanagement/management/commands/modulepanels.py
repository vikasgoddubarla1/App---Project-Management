from locations.models import ModulePanel, Module

modulepanels = [
   {'id': 1, 'name': 'General', 'slug': 'location-general', 'module_id': 1},
   {'id': 2, 'name': 'Support', 'slug': 'location-support', 'module_id': 1},
   {'id': 3, 'name': 'Sales', 'slug': 'location-sales', 'module_id': 1},
   {'id': 4, 'name': 'Drone image', 'slug':'location-drone-image', 'module_id':1},
   {'id': 5, 'name': 'Prioritization', 'slug':'location-prioritization', 'module_id':1},
   {'id': 6, 'name': 'Snow load factor', 'slug':'location-snow-load-factor', 'module_id':1},
   {'id': 7, 'name': 'State', 'slug':'location-state', 'module_id':1},
   {'id': 8, 'name': 'Pre ratings', 'slug': 'location-pre-ratings', 'module_id': 1},
   {'id': 9, 'name': 'Project Information', 'slug':'location-project-information', 'module_id':1},
   {'id': 10, 'name': 'Drone view channels', 'slug':'location-device-channels', 'module_id':1},
   {'id': 11, 'name': 'Energy data', 'slug':'location-energy-data', 'module_id':1},
   {'id': 12, 'name': 'Devices', 'slug':'location-devices', 'module_id':1},
   {'id': 13, 'name': 'Malo numbers', 'slug':'location-malo-numbers', 'module_id':1},
   {'id': 14, 'name': 'Malo virtual channels', 'slug':'location-malo-virtual-channels', 'module_id':1},
   {'id': 15, 'name': 'EV details', 'slug':'location-ev-details', 'module_id':1},
   {'id': 16, 'name': 'PV details', 'slug':'location-pv-details', 'module_id':1},
   {'id': 17, 'name': 'KPI general details', 'slug':'location-kpi-general-details', 'module_id':1},
   {'id': 18, 'name': 'KPI values', 'slug':'location-kpi-values', 'module_id':1},
   {'id': 19, 'name': 'General', 'slug': 'contract-general', 'module_id': 2},
   {'id': 20, 'name': 'Files', 'slug': 'contract-files', 'module_id': 2},
   {'id': 21, 'name': 'Duration', 'slug': 'contract-duration', 'module_id': 2},
   {'id': 22, 'name': 'Approvals', 'slug': 'contract-approvals', 'module_id': 2},
   {'id': 23, 'name': 'Logs', 'slug': 'contract-logs', 'module_id': 2},
]

def create_modulepanels():
   for modulepanel_data in modulepanels:
       modulepanel_id = modulepanel_data['id']
       module_id = modulepanel_data['module_id']

       if Module.objects.filter(id=module_id).exists():
           module = Module.objects.get(id=module_id)

           del modulepanel_data['module_id']

           # Set the module object as the foreignkey
           modulepanel_data['module_id'] = module

           if not ModulePanel.objects.filter(id=modulepanel_id).exists():
               ModulePanel.objects.create(**modulepanel_data)
       else:
           print(f"Module with id {module_id} does not exist.")