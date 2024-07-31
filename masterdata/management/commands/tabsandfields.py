from masterdata.models import *

tabsandfields= [
   {'id': 1, 'tab_id':1, 'field_id':1, 'is_required':False},
   {'id': 2, 'tab_id':1, 'field_id':2, 'is_required':False},
   {'id': 3, 'tab_id':1, 'field_id':3, 'is_required':False},
   {'id': 4, 'tab_id':1, 'field_id':4, 'is_required':False},
   {'id': 5, 'tab_id':1, 'field_id':5, 'is_required':False},
   {'id': 6, 'tab_id':1, 'field_id':6, 'is_required':False},
   {'id': 7, 'tab_id':1, 'field_id':7, 'is_required':False},
   {'id': 8, 'tab_id':1, 'field_id':8, 'is_required':False},
   {'id': 9, 'tab_id':1, 'field_id':9, 'is_required':False},
   {'id': 10, 'tab_id':1, 'field_id':10, 'is_required':False},
   {'id': 11, 'tab_id':1, 'field_id':11, 'is_required':False},
   {'id': 12, 'tab_id':1, 'field_id':12, 'is_required':False},
   {'id': 13, 'tab_id':1, 'field_id':13, 'is_required':False},
   {'id': 14, 'tab_id':1, 'field_id':14, 'is_required':False},
   {'id': 15, 'tab_id':1, 'field_id':15, 'is_required':False},
   {'id': 16, 'tab_id':1, 'field_id':16, 'is_required':False},
   {'id': 17, 'tab_id':1, 'field_id':17, 'is_required':False},
   {'id': 18, 'tab_id':1, 'field_id':18, 'is_required':False},
   {'id': 19, 'tab_id':1, 'field_id':19, 'is_required':False},
   {'id': 20, 'tab_id':1, 'field_id':20, 'is_required':False},
   {'id': 21, 'tab_id':1, 'field_id':21, 'is_required':False},
   {'id': 22, 'tab_id':1, 'field_id':22, 'is_required':False},
   {'id': 23, 'tab_id':1, 'field_id':23, 'is_required':False},
   {'id': 24, 'tab_id':1, 'field_id':24, 'is_required':False},
   {'id': 25, 'tab_id':1, 'field_id':25, 'is_required':False},
   {'id': 26, 'tab_id':1, 'field_id':26, 'is_required':False},
   {'id': 27, 'tab_id':1, 'field_id':27, 'is_required':False},
   {'id': 28, 'tab_id':1, 'field_id':28, 'is_required':False},
   {'id': 29, 'tab_id':1, 'field_id':29, 'is_required':False},
   {'id': 30, 'tab_id':1, 'field_id':30, 'is_required':False},
   {'id': 31, 'tab_id':1, 'field_id':31, 'is_required':False},
   {'id': 32, 'tab_id':1, 'field_id':32, 'is_required':False},
   {'id': 33, 'tab_id':1, 'field_id':33, 'is_required':False},
   {'id': 34, 'tab_id':1, 'field_id':34, 'is_required':False},
   {'id': 35, 'tab_id':1, 'field_id':35, 'is_required':False},
   {'id': 36, 'tab_id':1, 'field_id':36, 'is_required':False},
   {'id': 37, 'tab_id':1, 'field_id':37, 'is_required':False},
   {'id': 38, 'tab_id':2, 'field_id':38, 'is_required':False},
   {'id': 39, 'tab_id':2, 'field_id':39, 'is_required':False},
   {'id': 40, 'tab_id':2, 'field_id':40, 'is_required':False},
   {'id': 41, 'tab_id':2, 'field_id':41, 'is_required':False},
   {'id': 42, 'tab_id':2, 'field_id':42, 'is_required':False},
   {'id': 43, 'tab_id':2, 'field_id':43, 'is_required':False},
   {'id': 44, 'tab_id':2, 'field_id':44, 'is_required':False},
   {'id': 45, 'tab_id':2, 'field_id':45, 'is_required':False},
   {'id': 46, 'tab_id':2, 'field_id':46, 'is_required':False},
   {'id': 47, 'tab_id':2, 'field_id':47, 'is_required':False},
   {'id': 48, 'tab_id':2, 'field_id':48, 'is_required':False},
   {'id': 49, 'tab_id':2, 'field_id':49, 'is_required':False},
   {'id': 50, 'tab_id':2, 'field_id':50, 'is_required':False},
   {'id': 51, 'tab_id':2, 'field_id':51, 'is_required':False},
   {'id': 52, 'tab_id':2, 'field_id':52, 'is_required':False},
   {'id': 53, 'tab_id':2, 'field_id':53, 'is_required':False},
   {'id': 54, 'tab_id':2, 'field_id':54, 'is_required':False},
   {'id': 55, 'tab_id':2, 'field_id':55, 'is_required':False},
   {'id': 56, 'tab_id':2, 'field_id':56, 'is_required':False},
   {'id': 57, 'tab_id':2, 'field_id':57, 'is_required':False},
   {'id': 58, 'tab_id':2, 'field_id':58, 'is_required':False},
   {'id': 49, 'tab_id':2, 'field_id':59, 'is_required':False},
   {'id': 60, 'tab_id':2, 'field_id':60, 'is_required':False},
   {'id': 61, 'tab_id':2, 'field_id':61, 'is_required':False},
   {'id': 62, 'tab_id':2, 'field_id':62, 'is_required':False},
   
   
]

def create_tabsandfields():
    for tabsandfields_data in tabsandfields:
        tabsandfields_id = tabsandfields_data['id']
        tab_id = tabsandfields_data['tab_id']
        field_id = tabsandfields_data['field_id']

        if not Tab.objects.filter(id=tab_id).exists():
            print(f"Tab with id {tab_id} does not exist.")
            continue
        
        if not Field.objects.filter(id=field_id).exists():
            print(f"Field with id {field_id} does not exist.")
            continue

        tab = Tab.objects.get(id=tab_id)
        field = Field.objects.get(id=field_id)

        tabsandfields_data['tab_id'] = tab
        tabsandfields_data['field_id'] = field

        if not TabFields.objects.filter(id=tabsandfields_id).exists():
            TabFields.objects.create(**tabsandfields_data)
