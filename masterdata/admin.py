from django.contrib import admin
from .models import *

# Register your models here.
class CheckListAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    
class CheckListItemsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'checklist_id', 'created_at')
    list_display_links = ('id', 'name')
    
class TaskCheckListAdmin(admin.ModelAdmin):
    list_display = ('id', 'checklist_id', 'task_id', 'created_at')
    list_display_links = ('id',)

class TaskCheckListItemsAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_checked',  'created_at')
    list_display_links = ('id',)
    
class TabAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    list_display_links = ('id', 'name')
    
class FieldAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'field_type', 'display_order', 'created_at')
    list_display_links = ('id', 'name', 'field_type')
    
class TabFieldAdmin(admin.ModelAdmin):
    list_display = ('id', 'tab_id', 'field_id', 'is_required')
    list_display_links = ('id', 'tab_id', 'field_id', 'is_required')
    
class LocationFieldsAdmin(admin.ModelAdmin):
    list_display = ('id', 'location_id', 'field_id', 'value', 'created_at', 'updated_at')
    list_display_links = ('id', 'location_id')
    search_fields = ('id',)
    
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    
class GroupFieldAdmin(admin.ModelAdmin):
    list_display = ('id', 'group_id', 'field_id', 'order_number', 'created_at', 'updated_at')
    list_display_links = ('id', 'group_id')
    
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'group_id', 'field_id')
    list_display_links = ('id', 'user_id')
    
admin.site.register(CheckList, CheckListAdmin)
admin.site.register(CheckListItems, CheckListItemsAdmin)
admin.site.register(TaskCheckList, TaskCheckListAdmin)
admin.site.register(TaskCheckListItems, TaskCheckListItemsAdmin)
admin.site.register(Tab, TabAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(TabFields, TabFieldAdmin)
admin.site.register(LocationFields,LocationFieldsAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupField, GroupFieldAdmin)
admin.site.register(UserGroup, UserGroupAdmin)
admin.site.register(TaskTemplateCheckList)
admin.site.register(TaskTemplateCheckListItems)
admin.site.register(GroupModule)
admin.site.register(GroupView)
admin.site.register(ViewLocationFieldsLogs)