from django.core.management.base import BaseCommand
from masterdata.models import Field, LocationFields
from locations.models import Location

class Command(BaseCommand):
    help = 'Create records for all existing fields to all existing locations'

    def handle(self, *args, **options):
        field_name_mapping = {
            'City': 'city',
            'Zip-Code': 'zipcode',
        }
        
        fields = Field.objects.all()
        locations = Location.objects.all()
        
        for location in locations:
            for field in fields:
                location_field_name = field_name_mapping.get(field.name) 
                if location_field_name:
                    field_value = getattr(location, location_field_name, None)
                else:
                    field_value = None
                if not LocationFields.objects.filter(location_id=location, field_id=field).exists():
                    LocationFields.objects.create(
                        location_id=location,
                        field_id=field,
                        value = field_value
                    )

        self.stdout.write(self.style.SUCCESS('Records created or updated successfully.'))
