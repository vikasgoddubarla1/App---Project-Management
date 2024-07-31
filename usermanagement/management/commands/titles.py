from usermanagement.models import Title

titles = [
    {'id':1, 'name': 'Dr'},
    {'id':2, 'name': 'Prof'},
    {'id':3, 'name': 'Prof. Dr.'},
]
def create_titles():
    for title_data in titles:
        title_id = title_data['id']
        if not Title.objects.filter(id = title_id).exists():
            Title.objects.create(**title_data)