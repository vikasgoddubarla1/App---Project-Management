from masterdata.models import Tab

tabs = [
   {'id': 1, 'name': 'EV Details'},
   {'id':2, 'name':'PV Details'},
   
]

def create_tabs():
   for tab_data in tabs:
       tab_id = tab_data['id']
       if not Tab.objects.filter(id=tab_id).exists():
           Tab.objects.create(**tab_data)