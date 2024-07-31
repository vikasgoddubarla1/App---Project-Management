from django.contrib import admin
from .models import *

# Register your models here.
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'location_id', 'name')
    list_display_links = ('id', 'location_id', 'name')
    ordering    = ('id',)
    
class ProjectPhaseAdmin(admin.ModelAdmin):
    list_display =  ('id', 'project_id', 'phase_name', 'start_date', 'end_date')
    list_display_links = ('id', 'project_id', 'phase_name')
    ordering    = ('id',)
    
class ProjectPhaseTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent_id', 'title', 'assigned_by', 'assigned_at', 'status', 'is_dependent', 'priority_level')
    list_display_links = ('id', 'parent_id', 'title')
    ordering    = ('id',)
    
class ProjectPhasesTaskFileAdmin(admin.ModelAdmin):
    list_display = ('id',)
    ordering    = ('id',)
    
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'template_type')
    ordering    = ('id',)
    
class ProjectTemplatePhaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'phase_name', 'template_id')
    ordering    = ('id',)

class ProjectTemplatePhaseTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    ordering    = ('id',)

class PhasesUpdateAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'column_name')
    ordering = ('id',)
    
class TaskUpdateAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'column_name')
    ordering = ('id',)
    
class ProjectPhaseTaskDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'condition')
    ordering = ('id',)

class ProjectPhaseTaskTemplateDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'condition')
    ordering = ('id',)

admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectPhase, ProjectPhaseAdmin)
admin.site.register(ProjectPhaseTask, ProjectPhaseTaskAdmin)
admin.site.register(ProjectPhasesTaskFile, ProjectPhasesTaskFileAdmin)
admin.site.register(ProjectTemplate, ProjectTemplateAdmin)
admin.site.register(ProjectPhaseTemplate, ProjectTemplatePhaseAdmin)
admin.site.register(ProjectPhaseTaskTemplate, ProjectTemplatePhaseTaskAdmin)
admin.site.register(PhaseUpdate, PhasesUpdateAdmin)
admin.site.register(TaskUpdate, TaskUpdateAdmin)
admin.site.register(ProjectPhaseTaskDependency, ProjectPhaseTaskDependencyAdmin)
admin.site.register(ProjectPhaseTaskTemplateDependency, ProjectPhaseTaskTemplateDependencyAdmin)
admin.site.register(ProjectPhaseTaskMentions)
admin.site.register(TaskAssignedUsers)
admin.site.register(TaskFields)
admin.site.register(TemplateTaskFields)
