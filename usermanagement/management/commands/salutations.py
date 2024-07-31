from usermanagement.models import Salutation

salutations = [
    {'id':1, 'name': 'Mr'},
    {'id':2, 'name': 'Mrs'},
]
def create_salutations():
    for salutation_data in salutations:
        salutation_id = salutation_data['id']
        if not Salutation.objects.filter(id = salutation_id).exists():
            Salutation.objects.create(**salutation_data)