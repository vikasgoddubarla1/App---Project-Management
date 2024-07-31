from contracts.models import ContractSubCategory, ContractCategory
import logging

sub_categories = [
   {'id': 1, 'contract_category_id':ContractCategory.objects.get(id=1), 'name': 'Strombelieferungsvertrag'}, #Electricity Supply Contract
   {'id':2, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Dachpachtvertrag'}, #roof lease
   {'id':3, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Installationsvertrag bzw. Angebot/AB'}, #Installation contract or offer/AB
   {'id':4, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Betriebsführungsvertrag PV'}, #Operational management contract PV
   {'id':5, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Betriebsführungsvertrag LadeInfraStruktur'}, #Charge infrastructure management agreement
   {'id':6, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Strombezugsvertrag LIS'}, #Electricity purchase agreement LIS
   {'id':7, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Vertrag Messstellenbetrieb'}, #Contract measuring point operation
   {'id':8, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Vertrag Abrechnungsdienstleistungen'}, #Contract Billing Services
   {'id':9, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Direktvermarktungsschnittstellenvertrag'}, #Direct Marketing Interface Agreement
   {'id':10, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Direktvermarktungsvertrag'}, #Direct Marketing Agreement
   {'id':11, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Wartungsvertrag'}, #maintenance contract
   {'id':12, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Reinigungsvertrag'}, #cleaning contract
   {'id':13, 'contract_category_id':ContractCategory.objects.get(id=1), 'name':'Mietvertrag (aktuell nur zwischen Slate und Verbrauchern)'} #Lease Agreement (currently only between Slate and Consumers)
   
]


def create_sub_contract_categories():
    for sub_category_data in sub_categories:
        sub_contract_category_id = sub_category_data['id']
        contract_category_instance = sub_category_data['contract_category_id']

        
        if not ContractSubCategory.objects.filter(id=sub_contract_category_id).exists():
            sub_category_data['contract_category_id'] = contract_category_instance
            ContractSubCategory.objects.create(**sub_category_data)

