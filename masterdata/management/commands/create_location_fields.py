from django.core.management.base import BaseCommand
from masterdata.models import LocationFields, Field, Location

class Command(BaseCommand):
    help = 'Create or update records for all existing fields to all existing locations'

    def handle(self, *args, **options):
        field_name_mapping = {
            'Project-No.': 'project_number',
            'City': 'city',
            'Zip Code': 'zipcode',
            'Street': 'address_line_1',
            'Expected kWp PV': 'expected_kWp_pv',
            'Expected Spec Yield(kWh/kWp)': 'expected_spec_yield_pv',
            'Expected Installation Date PV': 'exp_installation_date_pv',
            'Planned Installation Date PV': 'planned_installation_date_pv',
            'Expected oper. Date PV': 'exp_operation_date_pv',
            'Offtakers PV': 'offtakers_pv',
            'Lead Manger PV': 'lead_manager_pv',
            'Prioritization': 'prioritisation',
            'Snow Load Factor':'snowweight_load_factor',
        }

        # Get all existing fields and locations
        fields = Field.objects.all()
        locations = Location.objects.all()

        for location in locations:
            for field in fields:
                location_field_name = field_name_mapping.get(field.name) 
                if location_field_name:
                    field_value = getattr(location, location_field_name, None)
                else:
                    field_value = None
                location_field, created = LocationFields.objects.get_or_create(
                    location_id=location,
                    field_id=field,
                    defaults={'value': field_value, 'value_json':None},
                )

                if not created:
                    location_field.value = field_value
                    location_field.save()

        self.stdout.write(self.style.SUCCESS('Records created or updated successfully.'))


# class Command(BaseCommand):
#     help = 'Create or update records for all existing fields to all existing locations'

#     def handle(self, *args, **options):
#         # Get all existing fields and locations
#         fields = Field.objects.all()
#         locations = Location.objects.all()

#         for location in locations:
#             for field in fields:
#                 # Get the corresponding field value from the Location model
#                 value_field_name = field.name.replace(' ', '_').lower()
#                 field_value = getattr(location, value_field_name, None)

#                 # Create or update the LocationFields record
#                 location_field, created = LocationFields.objects.get_or_create(
#                     location_id=location,
#                     field_id=field,
#                     value=field_value if field_value else None                    
#                 )

#                 # If the record was not created (i.e., it already existed), update the value
#                 if not created:
#                     location_field.value = field_value
#                     location_field.save()

#         self.stdout.write(self.style.SUCCESS('Records created or updated successfully.'))

# class Command(BaseCommand):
#     help = 'Create records for all existing fields to all existing locations'

#     def handle(self, *args, **options):
#         # Get all existing fields and locations
#         fields = Field.objects.all()
#         locations = Location.objects.all()

#         for location in locations:
#             for field in fields:
#                 value_field_name = field.name.replace(' ', '_').lower()
#                 field_value = getattr(location, value_field_name, None)
#                 if not LocationFields.objects.filter(location_id=location, field_id=field):
#                     location_field, created = LocationFields.objects.get_or_create(
#                         location_id=location,
#                         field_id=field,
#                         value=field_value,
#                         value_json=None,
#                     )
#                 if not created:
#                     location_field.value = field_value
#                     location_field.save()

#         self.stdout.write(self.style.SUCCESS('Records created successfully.'))


