from contracts.models import ContractCategory
from contracts.models import ContractSubCategory


categories = [
   {'id': 1, 'name': 'EinzelVertrag'}, #Induvidual contracts
   {'id':2, 'name':'RahmenVertrag'}, #group contracts
   {'id':3, 'name':'Vollmachten'}, #permission contracts
   
]

def create_contract_categories():
   for categories_data in categories:
       contract_category_id = categories_data['id']
       if not ContractCategory.objects.filter(id=contract_category_id).exists():
           ContractCategory.objects.create(**categories_data)
           
