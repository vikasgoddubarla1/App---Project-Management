from partners.models import Type

create_types_list = [
    {'id':1, 'name': 'Land Owner'},
    {'id':2, 'name':'Property Manager'},
    {'id':3, 'name':'Lead Company'},
    {'id':4, 'name': 'Tenant'}
]

def create_types():
    for types_data in create_types_list:
        type_id = types_data['id']
        if not Type.objects.filter(id=type_id).exists():
            Type.objects.create(**types_data)
