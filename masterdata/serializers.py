from rest_framework import serializers
from .models import *

class CheckListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckListItems
        fields = ('id', 'name', 'checklist_id', 'created_at', 'updated_at')


class CheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckList
        fields = ('id', 'name', 'display_order', 'is_master', 'created_at', 'updated_at')

class CheckListDetailSerializer(serializers.ModelSerializer):
    checklist_items = CheckListItemSerializer(source='checklistitems_set',  many=True, read_only=True)
    class Meta:
        model = CheckList
        fields = ('id', 'name', 'display_order', 'is_master', 'created_at', 'updated_at', 'checklist_items')
        
class CheckListSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckList
        fields = ('id', 'display_order', 'updated_at')
        
#--------------------------------------------------------------------- TASK CHECKLIST --------------------------------------------------------------
class TaskCheckListItemSerializer(serializers.ModelSerializer):
    checklistitem_name = serializers.ReadOnlyField(source='checklistitems_id.name')
    class Meta:
        model = TaskCheckListItems
        fields = ('id', 'taskchecklist_id', 'checklistitems_id', 'checklistitem_name', 'is_checked', 'checked_by', 'created_at', 'updated_at')
        
    
class TaskCheckListItemListSerializer(serializers.ModelSerializer):
    task_id = serializers.ReadOnlyField(source='taskchecklist_id.task_id.id')
    task_title = serializers.ReadOnlyField(source='taskchecklist_id.task_id.title')
    checklistitems_name = serializers.ReadOnlyField(source='checklistitems_id.name')
    checklist_id = serializers.ReadOnlyField(source='checklistitems_id.checklist_id.id')
    checklist_name = serializers.ReadOnlyField(source='checklistitems_id.checklist_id.name')
    class Meta:
        model = TaskCheckListItems
        fields = ('id', 'taskchecklist_id', 'task_id', 'task_title', 'checklistitems_id', 'checklistitems_name', 'checklist_id', 'checklist_name', 'is_checked', 'checked_by', 'created_at', 'updated_at')

class TaskCheckListItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCheckListItems
        fields = ('id', 'is_checked', 'checked_by', 'created_at', 'updated_at')

class TaskCheckListDetailSerializer(serializers.ModelSerializer):
    taskchecklist_items = TaskCheckListItemSerializer(source='taskchecklistitems_set', many=True, read_only=True)
    checklist_name = serializers.ReadOnlyField(source='checklist_id.name')
    class Meta:
        model = TaskCheckList
        fields = ('id', 'task_id', 'checklist_id', 'checklist_name', 'created_at', 'updated_at', 'taskchecklist_items')
    
        
class TaskCheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCheckList
        fields = ('id', 'task_id', 'checklist_id', 'created_at', 'updated_at')

#---------------------------------------------------------- TABS -------------------------------------------------------------------------------
class TabFieldListSerializer(serializers.ModelSerializer):
    field_name = serializers.ReadOnlyField(source='field_id.name')
    options = serializers.ReadOnlyField(source='field_id.options')
    field_type = serializers.ReadOnlyField(source='field_id.field_type')
    class Meta:
        model = TabFields
        fields = ('id', 'field_id', 'field_name', 'field_type', 'options', 'is_required', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        options = representation.get('options', [])
        if options is None:
            options = []
        formatted_options = [{'id': i + 1, 'name': option} for i, option in enumerate(options)]
        representation['options'] = formatted_options
        return representation

class TabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tab
        fields = ('id', 'name', 'created_at', 'updated_at')
class TabListSerializer(serializers.ModelSerializer):
    tab_fields = TabFieldListSerializer(source='tabfields_set', many=True, read_only=True)
    class Meta:
        model = Tab
        fields = ('id', 'name', 'created_at', 'updated_at', 'tab_fields')
        
class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ('id', 'name', 'field_type', 'description', 'options', 'display_order', 'created_at', 'updated_at')
        
    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     options = representation.get('options', [])
    #     if options is None:
    #         options = []
    #     formatted_options = [{'id': option['id'], 'name': option['name']} for option in options]
    #     representation['options'] = formatted_options
    #     return representation
    
# class FieldCSVSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Field
#         fields = ('id', 'name', 'field_type', 'description', 'options', 'display_order', 'created_at', 'updated_at')
        
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         options = representation.get('options', [])
#         if options is None:
#             options = []
#         formatted_options = [{'id': option['id'], 'name': option['name']} for option in options]
#         representation['options'] = formatted_options
#         return representation
    
class UpdateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ('id', 'name', 'field_type', 'description', 'options', 'display_order', 'created_at', 'updated_at')
        
class FieldListSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ('id', 'display_order', 'updated_at')
        
    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     options = representation.get('options', [])
    #     if options is None:
    #         options = []
    #     formatted_options = [{'id': i + 1, 'name': option} for i, option in enumerate(options)]
    #     representation['options'] = formatted_options
    #     return representation
        
class TabFieldSerializer(serializers.ModelSerializer):
    tab_name = serializers.ReadOnlyField(source='tab_id.name')
    field_name = serializers.ReadOnlyField(source='field_id.name')
    class Meta:
        model = TabFields
        fields = ('id', 'tab_id', 'tab_name', 'field_id', 'field_name', 'is_required', 'created_at', 'updated_at')
        
#--------------------------------------------------- LOCATIONFIELDS SERIALIZERS ---------------------------------------------------------------
class LocationFieldSerializer(serializers.ModelSerializer):
    field_name = serializers.ReadOnlyField(source='field_id.name')
    field_type = serializers.ReadOnlyField(source='field_id.field_type')
    field_options = serializers.ReadOnlyField(source='field_id.options')
    order_number = serializers.ReadOnlyField(source='field_id.display_order')
    
    class Meta:
        model = LocationFields
        fields = ('id', 'location_id', 'field_id','field_name', 'order_number', 'field_type', 'field_options', 'value')
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        options = representation.get('options', [])
        if options is None:
            options = []
        formatted_options = [{'id': i + 1, 'name': option} for i, option in enumerate(options)]
        representation['options'] = formatted_options
        return representation
    
class UpdateLocationFieldSerializer(serializers.ModelSerializer):
    tab_name = serializers.ReadOnlyField(source='tab_id.name')
    field_name = serializers.ReadOnlyField(source='field_id.name')
    field_type = serializers.ReadOnlyField(source='field_id.field_type')
    field_options = serializers.ReadOnlyField(source='field_id.options')
    field_description = serializers.ReadOnlyField(source='field_id.description')
    order_number = serializers.ReadOnlyField(source='field_id.display_order')
    
    class Meta:
        model = LocationFields
        fields = ('id', 'location_id', 'tab_id', 'tab_name', 'field_id','field_name', 'field_description', 'order_number', 'field_type', 'field_options', 'value', 'value_json', 'created_at', 'updated_at')
        

#------------------------MODULE -------------------------------------------
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupModule
        fields = ('id', 'name', 'is_pinned', 'created_at', 'updated_at')
        


#-------------------------------------------------------------- GROUPS --------------------------------------------------------------------------
class HiddenGroupFieldUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupField
        fields = ('id', 'is_hidden')

class GroupFieldSerializer(serializers.ModelSerializer):
    group_name = serializers.ReadOnlyField(source='group_id.name')
    field_name = serializers.ReadOnlyField(source='field_id.name')
    field_type= serializers.ReadOnlyField(source='field_id.field_type')
    options = serializers.ReadOnlyField(source='field_id.options')
    group_module_name = serializers.ReadOnlyField(source='group_module_id.name')
    class Meta:
        model = GroupField
        fields = ('id', 'group_id', 'group_name', 'field_id', 'is_hidden', 'is_pinned', 'order_number', 'group_module_id', 'group_module_name', 'field_name', 'field_type', 'options', 'created_at', 'updated_at')
class GroupViewSerializer(serializers.ModelSerializer):
    group_module_name = serializers.ReadOnlyField(source='group_module_id.name')
    group_name = serializers.ReadOnlyField(source='group_id.name')
    class Meta:
        model = GroupView
        fields = ('id', 'group_id', 'group_name', 'group_module_id', 'order_number', 'group_module_name')
    
      
class GroupSerializer(serializers.ModelSerializer):
    groupViews = GroupViewSerializer(source='groupview_set', many=True, read_only=True)
    class Meta:
        model = Group
        fields = ('id', 'name', 'created_at', 'updated_at', 'groupViews')


    
class UserGroupSerializer(serializers.ModelSerializer):
    group_name = serializers.ReadOnlyField(source='group_id.name')
    field_name = serializers.ReadOnlyField(source='field_id.name')
    field_type= serializers.ReadOnlyField(source='field_id.field_type')
    class Meta:
        model = UserGroup
        fields = ('id', 'user_id', 'group_id', 'group_module_id', 'group_name', 'field_id', 'field_name', 'field_type', 'field_order', 'is_checked', 'is_pinned', 'created_at', 'updated_at')
        
class UserGroupSortingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ('id', 'user_id', 'group_id', 'field_id', 'field_order', 'updated_at')
        
class UserGroupIsPinnedUpdate(serializers.ModelSerializer):
        class Meta:
            model = UserGroup
            fields = ('id', 'is_pinned')
#---------------------------------------- TASK TEMPLATE CHECKLISTS -----------------------------------------------------------------------------

class TaskTemplateCheckListItemListSerializer(serializers.ModelSerializer):
    task_id = serializers.ReadOnlyField(source='taskchecklist_id.task_id.id')
    task_title = serializers.ReadOnlyField(source='taskchecklist_id.task_id.title')
    checklistitems_name = serializers.ReadOnlyField(source='checklistitems_id.name')
    checklist_id = serializers.ReadOnlyField(source='checklistitems_id.checklist_id.id')
    checklist_name = serializers.ReadOnlyField(source='checklistitems_id.checklist_id.name')
    class Meta:
        model = TaskTemplateCheckListItems
        fields = ('id', 'tasktemplatechecklist_id', 'task_id', 'task_title', 'checklistitems_id', 'checklistitems_name', 'checklist_id', 'checklist_name', 'is_checked', 'checked_by', 'created_at', 'updated_at')

class TaskTemplateCheckListItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTemplateCheckListItems
        fields = ('id', 'is_checked', 'checked_by', 'created_at', 'updated_at')

class TaskTemplateCheckListDetailSerializer(serializers.ModelSerializer):
    taskchecklist_items = TaskTemplateCheckListItemListSerializer(source='tasktemplatechecklistitems_set', many=True, read_only=True)
    checklist_name = serializers.ReadOnlyField(source='checklist_id.name')
    class Meta:
        model = TaskTemplateCheckList
        fields = ('id', 'task_id', 'checklist_id', 'checklist_name', 'created_at', 'updated_at', 'taskchecklist_items')
        
class TaskTemplateCheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTemplateCheckList
        fields = ('id', 'task_id', 'checklist_id', 'created_at', 'updated_at')


# ------------------------------ PROJECT PHASE TASK FIELDS-----------------------
class ProjectPhaseTaskFieldsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhaseTaskFields
        fields = ('id', 'task_id','field_id', 'is_required', 'created_at', 'updated_at')

class ProjectPhaseTaskFieldsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhaseTaskFields
        fields = ('id', 'is_required', 'created_at', 'updated_at')
#----------------------------------------- VIEWS LOCATION FIELDS LOGS ---------------------------------------------------------------------------

class ViewLocationFieldLogSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ViewLocationFieldsLogs
        fields = ('id', 'group_module_id', 'location_field_id', 'updated_at', 'updated_by')


class GroupViewListSerializer(serializers.ModelSerializer):
    group_module_name = serializers.ReadOnlyField(source='group_module_id.name')
    group_name = serializers.ReadOnlyField(source='group_id.name')
    group_fields = GroupFieldSerializer(many=True, read_only=True, source='group_id.group_fields')
    class Meta:
        model = GroupView
        fields = ('id', 'group_id', 'group_name', 'group_module_id', 'order_number', 'group_module_name', 'group_fields')
     
class ModuleSerializerForGroupList(serializers.ModelSerializer):
    # group_field_list = GroupFieldSerializer(source='groupfield_set', many=True, read_only=True)
    group_field_list = serializers.SerializerMethodField()
    class Meta:
        model = GroupModule
        fields = ('id', 'name', 'is_pinned', 'is_global', 'is_default', 'user_id', 'created_at', 'updated_at', 'group_field_list')
        
    def get_group_field_list(self, obj):
        group_id = self.context.get('group_id')
        group_fields = GroupField.objects.filter(group_id=group_id, group_module_id=obj.id)
        return GroupFieldSerializer(group_fields, many=True).data

class ModuleUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupModule
        fields = ('id', 'name', 'is_pinned', 'is_global', 'is_default', 'user_id', 'updated_at')
        
class GroupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'created_at', 'updated_at')
        
class GroupRetrieveSerializer(serializers.ModelSerializer):
    group_modules = serializers.SerializerMethodField()
    class Meta:
        model = Group
        fields = ('id', 'name', 'created_at', 'updated_at', 'group_modules')
        
    def get_group_modules(self, obj):
        group_views = GroupView.objects.filter(group_id=obj.id)
        group_module_ids = group_views.values_list('group_module_id', flat=True)
        group_modules = GroupModule.objects.filter(id__in=group_module_ids)
        return ModuleSerializerForGroupList(group_modules, many=True, context={'group_id': obj.id}).data
    
class GroupViewSerializerForModule(serializers.ModelSerializer):
    group_module_name = serializers.ReadOnlyField(source='group_module_id.name')
    group_name = serializers.ReadOnlyField(source='group_id.name')
    group_fields = serializers.SerializerMethodField()
    class Meta:
        model = GroupView
        fields = ('id', 'group_id', 'group_name', 'group_module_id', 'order_number', 'group_module_name', 'group_fields')
        
    def get_group_fields(self, obj):
        group_fields = GroupField.objects.filter(group_id=obj.group_id, group_module_id=obj.group_module_id)
        return GroupFieldSerializer(group_fields, many=True).data
    
class ListModuleSerializer(serializers.ModelSerializer):
    group_view_list = serializers.SerializerMethodField()
    class Meta:
        model = GroupModule
        fields = ('id', 'name', 'is_pinned', 'is_global', 'is_default', 'user_id', 'created_at', 'updated_at', 'group_view_list')
        
    def get_group_view_list(self, obj):
        group_views = GroupView.objects.filter(group_module_id=obj)
        return GroupViewSerializerForModule(group_views, many=True, read_only=True).data
    
