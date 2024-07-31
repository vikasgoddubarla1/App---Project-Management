import json
# import codecs
from django.core.management.base import BaseCommand
from .models import Timezone, Countries

class command(BaseCommand):
    help = 'import counties and timezone data'
    
    def handle(self, *args, **options):
        json_file = "countries.json"
        
            
        with open(json_file, 'r') as file:
            data = json.load(file)
            
        for item in data:
            country_data = item.copy().pop('timezones', None)
            timezones_data = item.get('timezones', [])
            country = Countries(**country_data)
            country.save()
            
            for timezone_data in timezones_data:
                timezone = Timezone(
                    country = country,
                    **timezone_data
                )
                timezone.save