from django.core.management.base import BaseCommand
from masterdata.models import Group, GroupView, GroupField
from django.db.models import Max


class Command(BaseCommand):
    help = 'Update and create GroupField entries based on GroupView entries'

    def handle(self, *args, **kwargs):
        groups = Group.objects.all()
        
        for group in groups:
            group_views = GroupView.objects.filter(group_id=group)
            existing_group_fields = GroupField.objects.filter(group_id=group, group_module_id__isnull=True)
            
            for group_view in group_views:                
                for group_field in existing_group_fields:
                    if not GroupField.objects.filter(
                        group_id=group_field.group_id,
                        field_id=group_field.field_id,
                        group_module_id=group_view.group_module_id
                    ).exists():
                        max_order_number = GroupField.objects.filter(group_id=group, group_module_id=group_view.group_module_id).aggregate(Max('order_number'))['order_number__max'] or 0
                        new_group_field = GroupField.objects.create(
                            group_id=group_field.group_id,
                            field_id=group_field.field_id,
                            group_module_id=group_view.group_module_id,
                            order_number= max_order_number + 1,
                            is_hidden=group_field.is_hidden,
                            created_at=group_field.created_at,
                            updated_at=group_field.updated_at
                        )
            existing_group_fields.delete()
        
        self.stdout.write(self.style.SUCCESS('Successfully updated and created GroupFields'))

