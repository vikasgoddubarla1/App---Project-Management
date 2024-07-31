from locations.models import LocationStatusEVPV

location_additional_status = [
   {'id':1, 'name':'0 - Early-Stage'},
   {'id':2, 'name':'1 - Lead'},
   {'id':3, 'name':'2 - Pitch'},
   {'id':4, 'name':'3 - Negotiations'},
   {'id':5, 'name':'4 - LOI Signed/Development'},
   {'id':6, 'name':'5 - Construction Ready'},
   {'id':7, 'name':'6 - Construction'},
   {'id':8, 'name':'7 - Installed'},
   {'id':9, 'name':'8 - Operating'},
   {'id':10, 'name':'9 - Discontinued'},
   {'id':11, 'name':'H - On Hold'},   
]

def create_location_additional_status():
   for location_additional_status_data in location_additional_status:
       location_additional_status_id = location_additional_status_data['id']
       if not LocationStatusEVPV.objects.filter(id=location_additional_status_id).exists():
           LocationStatusEVPV.objects.create(**location_additional_status_data)