from django.core.management.base import BaseCommand
from masterdata.management.commands.fields import create_fields
from masterdata.management.commands.tabs import create_tabs
from masterdata.management.commands.tabsandfields import create_tabsandfields

class Command(BaseCommand):
   help = 'tabs, fields, tabs and fields'
   def handle(self, *args, **options):
      #  create_tabs()
       create_fields()
    #    create_tabsandfields()