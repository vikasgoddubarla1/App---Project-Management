from django.core.management.base import BaseCommand
from usermanagement.management.commands.salutations import create_salutations
from usermanagement.management.commands.titles import create_titles
from usermanagement.management.commands.superuser import create_superuser
from usermanagement.management.commands.modules import create_modules
from usermanagement.management.commands.modulepanels import create_modulepanels
from usermanagement.management.commands.permissions import create_permissions
from usermanagement.management.commands.countries import create_countries
from usermanagement.management.commands.contract_categories import create_contract_categories
from usermanagement.management.commands.contract_sub_categories import create_sub_contract_categories
from usermanagement.management.commands.location_additional_status import create_location_additional_status
from usermanagement.management.commands.create_types import create_types

#python manage.py create_data
class Command(BaseCommand):
   help = 'Create users, salutations, titles, super user, modules, modulepanels, permissions, countries, contractcategories and location additioanl status'

   def handle(self, *args, **options):
       create_salutations()
       create_titles()
       create_superuser()
       create_modules()
       create_modulepanels()
       create_permissions()
       create_countries()
       create_contract_categories()
       create_sub_contract_categories()
       create_location_additional_status()
       create_types()