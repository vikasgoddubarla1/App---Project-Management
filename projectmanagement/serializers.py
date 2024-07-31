from .models import *
from rest_framework import serializers
from partners.models import *
from projectmanagement.functions import *
from masterdata.models import ProjectPhaseTaskFields, LocationFields
#-------------------------------PROJECT PHASE TASK FILE CREATE SERIALIZERS --------------------------------------------------------------------
class ProjectPhaseTaskFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhasesTaskFile
        fields = ('id', 'project_phase_id', 'project_phase_task_id', 'file_url', 'created_at', 'updated_at')

        
class ProjectPhaseTaskFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhasesTaskFile
        fields = ('id', 'file_url', 'created_at', 'updated_at')


class ProjectPhaseTaskDependencySerializer(serializers.ModelSerializer):
    dependent_task_name = serializers.ReadOnlyField(source="dependent_task_id.title")
    status = serializers.ReadOnlyField(source = "dependent_task_id.status")
    dependent_task_type = serializers.ReadOnlyField(source = "dependent_task_id.dependent_task_type")

    class Meta:
        model = ProjectPhaseTaskDependency
        fields = ('id', 'task_id', 'condition', 'dependent_task_id', 'dependent_task_name', 'status', 'dependent_task_type') 
        



       
        
#------------------------------------ PROJECT PHASE TASK CREATE ---------------------------------------------------------------------
class ProjectPhaseTaskGetSerializer(serializers.ModelSerializer):
    project_phase_task_files = ProjectPhaseTaskFilesSerializer(source='projectphasestaskfile_set', many=True, read_only=True)
    project_phase_task_dependencies = serializers.SerializerMethodField()
    assigned_by_name = serializers.ReadOnlyField(source="assigned_by.get_full_name")
    completed_by_name = serializers.ReadOnlyField(source = "completed_by.get_full_name")
    parent_name       = serializers.ReadOnlyField(source = "parent_id.title")
    assigned_to_name  = serializers.ReadOnlyField(source = 'assigned_to.name')
    assigned_to_user_name  = serializers.ReadOnlyField(source = 'assigned_to_user.get_full_name')
    class Meta:
        model = ProjectPhaseTask
        fields = ('id', 'title', 'target_count', 'target_duration', 'description', 'project_phase_id', 'parent_id', 'parent_name', 'status','priority_level', 'assigned_by', 'assigned_by_name', 'assigned_to', 'assigned_to_name', 'completed_by', 'completed_by_name', 'order_number', 'cost_estimations_pv', 'is_dependent', 'dependent_task_type', 'dependent_count', 'dependent_duration', 'assigned_to_user', 'assigned_to_user_name',  'start_date', 'end_date', 'project_phase_task_files', 'project_phase_task_dependencies', )
    
    def get_project_phase_task_dependencies(self, obj):
        dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=obj.id).order_by('id')
        dependency_serializer = ProjectPhaseTaskDependencySerializer(dependencies, many=True)
        return dependency_serializer.data

class TaskAssignedUsersSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user_id.get_full_name')
    assigned_by_name = serializers.ReadOnlyField(source='user_id.get_full_name')
    # profile_photo   = serializers.ReadOnlyField(source='user_id.profile_photo.url')
    
    class Meta:
        model = TaskAssignedUsers
        fields = ('id', 'task_id', 'user_id',  'user_name', 'assigned_by', 'assigned_by_name')
class ProjectPhaseTaskSerializer(serializers.ModelSerializer):
    # project_phase_task_dependencies = ProjectPhaseTaskDependencySerializer(source = 'project phase task dependency_set', many=True, read_only=True)
    project_phase_task_files = ProjectPhaseTaskFilesSerializer(source='projectphasestaskfile_set', many=True, read_only=True)
    project_phase_task_users = serializers.SerializerMethodField()
    
    sub_tasks = serializers.SerializerMethodField()
    assigned_by_name = serializers.ReadOnlyField(source="assigned_by.get_full_name")
    completed_by_name = serializers.ReadOnlyField(source = "completed_by.get_full_name")
    parent_name       = serializers.ReadOnlyField(source = "parent_id.title")
    assigned_to_name  = serializers.ReadOnlyField(source = 'assigned_to.name')
    project_phase_task_dependencies = serializers.SerializerMethodField()
    assigned_to_user_name = serializers.ReadOnlyField(source = 'assigned_to_user.get_full_name')
    project_id = serializers.ReadOnlyField(source = 'project_phase_id.project_id.id')
    project_name = serializers.ReadOnlyField(source = 'project_phase_id.project_id.name')
    project_phase_name = serializers.ReadOnlyField(source = 'project_phase_id.phase_name')
    # can_complete = serializers.SerializerMethodField()
    class Meta:
        model = ProjectPhaseTask
        fields = ('id', 'title', 'target_count', 'target_duration', 'dependent_count', 'dependent_duration', 'description', 'project_id', 'project_name', 'project_phase_id', 'project_phase_name', 'parent_id', 'parent_name', 'status','priority_level', 'assigned_by', 'assigned_by_name', 'assigned_to', 'assigned_to_name', 'assigned_to_user', 'assigned_to_user_name', 'completed_by', 'completed_by_name', 'order_number', 'cost_estimations_pv', 'is_dependent', 'dependent_task_type', 'start_date', 'end_date', 'project_phase_task_users', 'project_phase_task_dependencies', 'project_phase_task_files', 'sub_tasks')
    
    # def get_can_complete(self, obj):
    #     project_phase_task_fields = TaskFields.objects.filter(task_id=obj.id)
    #     for field in project_phase_task_fields:
    #         location_field = LocationFields.objects.get(location_id=obj.project_phase_id.project_id.location_id, field_id=field.field_id)
    #         print(location_field)
    #         if location_field.value is None:
    #             return False
    #     return True
    
    def get_sub_tasks(self, obj):
        sub_tasks = ProjectPhaseTask.objects.filter(parent_id=obj.id).order_by('order_number')
        sub_task_serializer = ProjectPhaseTaskSerializer(sub_tasks, many=True)
        return sub_task_serializer.data
    
    def get_project_phase_task_users(self, obj):
        task_users = TaskAssignedUsers.objects.filter(task_id = obj.id).order_by('id')
        task_assign_serializer = TaskAssignedUsersSerializer(task_users, many=True)
        return task_assign_serializer.data

    def get_project_phase_task_dependencies(self, obj):
        dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=obj.id).order_by('id')
        dependency_serializer = ProjectPhaseTaskDependencySerializer(dependencies, many=True)
        return dependency_serializer.data
    
    # def get_queryset(self):
    #     queryset = ProjectPhaseTask.objects.filter(parent_id__isnull=True)
    #     return queryset
    

class ProjectPhaseTaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhaseTask
        fields = ('id', 'title', 'status', 'phase_start_confirmation', 'start_date', 'end_date')
    

    

class ProjectTaskAssigneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhaseTask
        fields = ('id', 'title', 'assigned_to', 'expected_complete_date', 'assigned_at', 'assigned_to_user')
        
        
class ProjectTaskCustomerAssignSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProjectPhaseTask
        fields = ('id', 'assigned_to_user', 'assigned_at')
        

#---------------------------------------- PROJECT PHASE SERIALIZER ------------------------------------------------------------------

class ProjectPhaseSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project_id.name')
    class Meta:
        model = ProjectPhase
        fields = ('id', 'project_id', 'project_name', 'phase_name', 'target_count', 'target_duration', 'order_number', 'created_by')

class ProjectPhaseStartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = ('id', 'start_date')
        
class ProjectPhaseStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = ('id', 'phase_status', 'end_date')
class ProjectPhaseUpdateSerializer(serializers.ModelSerializer):
    start_date = serializers.ReadOnlyField()
    class Meta:
        model = ProjectPhase
        fields = ('id', 'phase_name', 'order_number', 'start_date', 'end_date',  'target_kWp', 'target_count', 'target_duration', 'final_output')

class ProjectPhaseGetSerializer(serializers.ModelSerializer):
    project_phase_tasks = ProjectPhaseTaskSerializer(source='get_ordered_tasks', many=True)
    # project_phase_tasks = serializers.SerializerMethodField() #ProjectPhaseTaskSerializer(source = 'projectphasetask_set', many=True, read_only=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    class Meta:
        model = ProjectPhase
        fields = ('id', 'project_id', 'phase_name', 'order_number', 'phase_status', 'created_by', 'created_by_name', 'start_date', 'end_date', 'target_kWp', 'target_count', 'target_duration', 'final_output', 'phase_estimation', 'project_phase_tasks')
        
    # def get_project_phase_tasks(self, obj):
        # task = obj.projectphasetask_set.all().order_by('order_number')
        # return ProjectPhaseTask(task)

class ProjectPhaseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = ('id', 'phase_name', 'order_number', 'phase_status', 'start_date', 'end_date', 'target_kWp', 'target_count', 'target_duration', 'final_output')
        
class ProjectPhaseEstimationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fileds = ('id', 'phase_estimations')
        
#------------------------------------------- PROJECT SERIALIZERS ------------------------------------------------------------------
        
class ProjectSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'location_id.name')
    location_status = serializers.ReadOnlyField(source='location_id.location_status')
    current_phase   = serializers.ReadOnlyField(source='location_id.current_phase')
    current_phase_status   = serializers.ReadOnlyField(source='location_id.current_phase_status')
    # excpected_start_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ('id', 'location_id', 'name', 'location_name', 'location_status', 'project_status', 'project_estimation', 'current_phase', 'current_phase_status', 'start_date', 'end_date', 'created_at' )
    
    
    
class ProjectUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Project
        fields = ('id', 'name')
        
class ProjectDetailSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'location_id.name')
    location_status = serializers.ReadOnlyField(source='location_id.location_status')
    project_phases = ProjectPhaseGetSerializer(source='get_ordered_phases' , many=True)
    class Meta:
        model = Project
        fields = ('id', 'name', 'location_id','location_name', 'location_status', 'project_status', 'total_target_kWp', 'project_estimation', 'created_at', 'start_date', 'end_date', 'project_phases')


#------------------------------------------- PROJECT TEMPLATE SERIALIZERS ------------------------------------------------------------

        
class ProjectTemplateSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = ProjectTemplate
        fields = ('id', 'name', 'template_type', 'status')
        
#--------------------------------------------------------------------- DEPENDENT TASKS ------------------------------------------------

        
class ProjectPhaseTaskDependencyCreateSerializer(serializers.ModelSerializer):
    dependent_tasks = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProjectPhaseTask.objects.all(),
        required=False
    )

    class Meta:
        model = ProjectPhaseTaskDependency
        fields = ('id', 'task_id', 'condition', 'dependent_tasks')


#-------------------------------------------------------- DEPENDENT TASK ENDS --------------------------------------------------------
class ProjectPhaseTaskDependencyTemplateSerializer(serializers.ModelSerializer):
    dependent_task_name = serializers.ReadOnlyField(source="dependent_task_id.title")

    class Meta:
        model = ProjectPhaseTaskTemplateDependency
        fields = ('task_id', 'condition', 'dependent_task_id', 'dependent_task_name')





class ProjectPhaseTaskTemplateSerializer(serializers.ModelSerializer):
    project_phase_task_template_dependencies = serializers.SerializerMethodField()
    subtasks = serializers.SerializerMethodField()
    parent_name = serializers.ReadOnlyField(source = 'parent_id.title')
    assigned_to_type_name = serializers.ReadOnlyField(source='assigned_to_type.name')
    project_phases_template_name = serializers.ReadOnlyField(source='project_phases_template_id.phase_name')
    template_id = serializers.ReadOnlyField(source='project_phases_template_id.template_id.id')
    template_name = serializers.ReadOnlyField(source='project_phases_template_id.template_id.name')

    class Meta:
        model = ProjectPhaseTaskTemplate
        fields = ('id', 'template_id', 'template_name', 'project_phases_template_id', 'project_phases_template_name', 'parent_id', 'parent_name', 'dependent_count', 'dependent_duration', 'title', 'description', 'assigned_to_type', 'assigned_to_type_name', 'order_number', 'expected_count',  'expected_duration', 'is_dependent', 'dependent_task_type', 'priority_level', 'project_phase_task_template_dependencies', 'subtasks')
        
        
    def get_subtasks(self, obj):
        subtasks = ProjectPhaseTaskTemplate.objects.filter(parent_id=obj.id).order_by('order_number')
        serializer = ProjectPhaseTaskTemplateSerializer(subtasks, many=True)
        return serializer.data
    
    def get_project_phase_task_template_dependencies(self, obj):
        dependencies = ProjectPhaseTaskTemplateDependency.objects.filter(task_id=obj.id)
        dependency_serializer = ProjectPhaseTaskDependencyTemplateSerializer(dependencies, many=True)
        return dependency_serializer.data
    

class ProjectPhaseTemplateCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProjectPhaseTemplate
        fields = ('id', 'template_id', 'phase_name', 'target_count', 'target_duration', 'order_number')
        
    

class ProjectPhaseTemplateSerializer(serializers.ModelSerializer):
    project_phase_task_templates = ProjectPhaseTaskTemplateSerializer(source='get_ordered_tasks', many=True, read_only=True) #projectphasetasktemplate_set
    
    available_phase_templates = serializers.PrimaryKeyRelatedField(
        queryset=ProjectPhaseTemplate.objects.all(),
        many=True,
        required=False
    )

    def create(self, validated_data):
        available_phase_templates = validated_data.pop('available_phase_templates', [])
        project_phase_template = ProjectPhaseTemplate.objects.create(**validated_data)

        for phase_template in available_phase_templates:
            project_phase_template.projectphasetemplate_set.add(phase_template)

        return project_phase_template
    
    class Meta:
        model = ProjectPhaseTemplate
        fields = ('id', 'template_id', 'phase_name', 'order_number', 'target_count', 'target_duration', 'available_phase_templates', 'project_phase_task_templates')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        tasks = representation['project_phase_task_templates']
        filtered_tasks = [task for task in tasks if task['parent_id'] is None]
        representation['project_phase_task_templates'] = filtered_tasks
        return representation
        


class ProjectTemplateDetailSerializer(serializers.ModelSerializer):
    project_phase_templates = ProjectPhaseTemplateSerializer(source='get_ordered_phase_template', many=True)
    class Meta:
        model = ProjectTemplate
        fields = ('id', 'name', 'template_type', 'status', 'project_phase_templates')
        
        
class ProjectTemplateTaskGetSerializer(serializers.ModelSerializer):
    task_template_dependencies = serializers.SerializerMethodField()
    parent_name = serializers.ReadOnlyField(source = 'parent_id.title')
    
    class Meta:
        model = ProjectPhaseTaskTemplate
        fields = ('id', 'parent_id', 'parent_name', 'project_phases_template_id', 'title', 'description', 'order_number', 'is_dependent', 'dependent_task_type', 'priority_level', 'task_template_dependencies')
    
    def get_task_template_dependencies(self, obj):
        dependencies = ProjectPhaseTaskTemplateDependency.objects.filter(task_id=obj.id)
        dependency_serializer = ProjectPhaseTaskDependencyTemplateSerializer(dependencies, many=True)
        return dependency_serializer.data

#-------------------------------------- FOR EXCEL SHEET CREATE ------------------------------------------------------------------------
class projectPhaseExcelSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'project_id.location_id.name')
    location_status = serializers.ReadOnlyField(source = 'project_id.location_id.location_status')
    city          = serializers.ReadOnlyField(source = 'project_id.location_id.city')
    zipcode       = serializers.ReadOnlyField(source = 'project_id.location_id.zipcode')
    country       = serializers.ReadOnlyField(source = 'project_id.location_id.country')
    project_name  = serializers.ReadOnlyField(source = 'project_id.name')
    project_status  = serializers.ReadOnlyField(source = 'project_id.project_status')
    current_phase = serializers.ReadOnlyField(source = 'project_id.location_id.current_phase')
    current_phase_status = serializers.ReadOnlyField(source = 'project_id.location_id.current_phase_status')
    project_estimation = serializers.ReadOnlyField(source = 'project_id.project_estimation')
    class Meta:
        model = ProjectPhase
        fields = ('id', 'project_name', 'project_status', 'phase_estimation', 'project_estimation', 'current_phase', 'current_phase_status', 'location_name', 'location_status', 'city', 'zipcode', 'country', 'target_kWp', 'target_count', 'target_duration')
        

class projectExcelSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'location_id.name')
    location_status = serializers.ReadOnlyField(source = 'location_id.location_status')
    city          = serializers.ReadOnlyField(source = 'location_id.city')
    zipcode       = serializers.ReadOnlyField(source = 'location_id.zipcode')
    country       = serializers.ReadOnlyField(source = 'location_id.country')
    address_line_1       = serializers.ReadOnlyField(source = 'location_id.address_line_1')
    address_line_2       = serializers.ReadOnlyField(source = 'location_id.address_line_2')
    current_phase = serializers.ReadOnlyField(source = 'location_id.current_phase')
    current_phase_status = serializers.ReadOnlyField(source = 'location_id.current_phase_status')
    class Meta:
        model = Project
        fields = ('id', 'name', 'project_status', 'project_estimation', 'current_phase', 'current_phase_status', 'location_name', 'location_status', 'address_line_1', 'address_line_2', 'city', 'zipcode', 'country')
        
#-------------------------------------------------- SORTING LIST SERIALIZERS ----------------------------------------------------------

class TemplateSortingSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()
    parent_name = serializers.ReadOnlyField(source = 'parent_id.title')

    class Meta:
        model = ProjectPhaseTaskTemplate
        fields = ('id', 'project_phases_template_id', 'parent_id', 'parent_name', 'title', 'description', 'order_number', 'is_dependent', 'dependent_task_type', 'priority_level', 'subtasks')
      
    def get_subtasks(self, obj):
        subtasks = ProjectPhaseTaskTemplate.objects.filter(parent_id=obj.id)
        serializer = ProjectPhaseTaskTemplateSerializer(subtasks, many=True)
        return serializer.data
    
    
#----------------------------------------------- PHASE UPDATE LIST SERIALIZERS -----------------------------------------------------
class PhaseUpdateListSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user_id.get_full_name')
    class Meta:
        model = PhaseUpdate
        fields = ('id', 'phase_id', 'user_id', 'user_name', 'column_name', 'updated_date')
        
    
class TaskUpdateListSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user_id.get_full_name')
    class Meta:
        model = TaskUpdate
        fields = ('id', 'task_id', 'user_id', 'user_name', 'column_name', 'updated_date')
        
#-------------------------------------- PROJECT PHASE TASK DEPENDENCY SERIALZIERS ------------------------------------------------------


class ProjectCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Project
        fields = '__all__'
        

class ProjectPhaseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = ('id', 'phase_name', 'order_number', 'phase_status', 'start_date', 'end_date', 'target_kWp', 'target_count', 'target_duration', 'final_output', 'phase_estimation')
        
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation


class ProjectPhaseTaskDepSerializer(serializers.ModelSerializer):
    project_phase_task_users = TaskAssignedUsersSerializer(source='taskassignedusers', many=True, read_only=True)
    assigned_by_name = serializers.ReadOnlyField(source="assigned_by.get_full_name")
    completed_by_name = serializers.ReadOnlyField(source="completed_by.get_full_name")
    parent_name = serializers.ReadOnlyField(source="parent_id.title")
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.name')
    assigned_to_user_name = serializers.ReadOnlyField(source='assigned_to_user.get_full_name')

    class Meta:
        model = ProjectPhaseTask
        fields = ('id', 'title', 'target_count', 'target_duration', 'dependent_count', 'dependent_duration', 'description', 'project_phase_id', 'parent_id', 'parent_name', 'status','priority_level', 'assigned_by', 'assigned_by_name', 'assigned_to', 'assigned_to_name', 'assigned_to_user', 'assigned_to_user_name', 'completed_by', 'completed_by_name', 'order_number', 'cost_estimations_pv', 'is_dependent', 'dependent_task_type', 'start_date', 'end_date', 'project_phase_task_users')
        
    # def get_project_phase_task_users(self, obj):
    #     task_users = TaskAssignedUsers.objects.filter(task_id = obj.id).order_by('id')
    #     task_assign_serializer = TaskAssignedUsersSerializer(task_users, many=True)
    #     return task_assign_serializer.data


#------------------------------------------------------------------ TASK MENTIONS SERIALIZERS -------------------------------------------------

class TaskMentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhaseTaskMentions
        fields = ('id', 'task_id', 'user_id', 'mentioned_by')
        

#------------------------------------------------------------- TASK FIELDS AND TEMPLATE TASK FIELDS ---------------------------------------------------

class TaskFieldSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project_id.name')
    task_name = serializers.ReadOnlyField(source='task_id.title')
    field_name = serializers.ReadOnlyField(source='field_id.name')
    field_type = serializers.ReadOnlyField(source='field_id.field_type')
    field_options = serializers.ReadOnlyField(source='field_id.options')
    
    class Meta:
        model = TaskFields
        fields = ('id', 'project_id', 'is_required', 'project_name', 'task_id', 'task_name', 'field_id', 'field_name', 'field_type', 'field_options')
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        options = representation.get('options', [])
        if options is None:
            options = []
        formatted_options = [{'id': i + 1, 'name': option} for i, option in enumerate(options)]
        representation['options'] = formatted_options
        return representation
        
class UpdateTaskFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskFields
        fields = ('id', 'is_required')
        
class TemplateTaskFieldSerializer(serializers.ModelSerializer):
    
    project_name = serializers.ReadOnlyField(source='project_id.name')
    task_name = serializers.ReadOnlyField(source='task_id.title')
    field_name = serializers.ReadOnlyField(source='field_id.name')
    field_type = serializers.ReadOnlyField(source='field_id.field_type')
    field_options = serializers.ReadOnlyField(source='field_id.options')
    
    class Meta:
        model = TemplateTaskFields
        fields = ('id', 'project_id', 'is_required', 'project_name', 'task_id', 'task_name', 'field_id', 'field_name', 'field_type', 'field_options')
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        options = representation.get('options', [])
        if options is None:
            options = []
        formatted_options = [{'id': i + 1, 'name': option} for i, option in enumerate(options)]
        representation['options'] = formatted_options
        return representation
        
class UpdateTemplateTaskFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateTaskFields
        fields = ('id', 'is_required')