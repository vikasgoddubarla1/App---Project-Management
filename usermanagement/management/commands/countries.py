import json
from partners.models import Countries, Timezone

def create_countries():
   json_file = r'partners\management\commands\countries.json'

   with open(json_file, 'r', encoding='UTF-8') as file:
       data = json.load(file)

   if Countries.objects.count() == 0:
       for item in data:
           country_data = {
               'name': item['name'],
               'iso3': item['iso3'],
               'iso2': item['iso2'],
               'numeric_code': item['numeric_code'],
               'phone_code': item['phone_code'],
               'capital': item['capital'],
               'currency': item['currency'],
               'currency_symbol': item['currency_symbol'],
               'tld': item['tld'],
               'native': item['native'],
               'region': item['region'],
               'sub_region': item['subregion'],
               'latitude': item['latitude'],
               'longitude': item['longitude'],
               'emoji': item['emoji'],
               'emojiU': item['emojiU'],
               'translations': item['translations'],
           }
           timezones_data = item.get('timezones', [])
           country = Countries.objects.create(**country_data)

           for timezone_data in timezones_data:
               timezone = Timezone.objects.create(
                   zoneName=timezone_data['zoneName'],
                   gmtOffset=timezone_data['gmtOffset'],
                   gmtOffsetName=timezone_data['gmtOffsetName'],
                   abbreviation=timezone_data['abbreviation'],
                   tzName=timezone_data['tzName'],
               )