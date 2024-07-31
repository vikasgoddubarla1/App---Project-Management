from django.core.management.base import BaseCommand
from locations.models import Location
import googlemaps

class Command(BaseCommand):
    help = 'Geocode latitude and longitude coordinates for locations one at a time using Google Maps Geocoding API'

    def handle(self, *args, **options):
        api_key = 'AIzaSyBlnDVhQGJz3Jt3LNEr9wto14s3kut72tI'
        gmaps = googlemaps.Client(key=api_key)

        locations = Location.objects.all()#filter(location_latitude__isnull=True, location_longitude__isnull=True)

        for location in locations:
            address = f"{location.address_line_1}, {location.city}, {location.zipcode}"
            geocoded_result = gmaps.geocode(address)

            if geocoded_result:
                latitude = geocoded_result[0]['geometry']['location']['lat']
                longitude = geocoded_result[0]['geometry']['location']['lng']
                location.location_latitude = latitude
                location.location_longitude = longitude
                location.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated coordinates for {location.name}'))

        self.stdout.write(self.style.SUCCESS('Geocoding using Google Maps Geocoding API completed for all locations.'))

