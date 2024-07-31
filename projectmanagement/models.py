from django.db import models
from locations.models import Location
from usermanagement.models import User
from partners.models import Partner, Type
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from datetime import datetime, timedelta
# from masterdata.models import LocationFields


def validate_file_size(value):
    max_size = 25 * 1024 * 1024 
    if value.size > max_size:
        raise ValidationError(("attachment must be less than 25MB"))

class Project(models.Model):
    location_id = models.OneToOneField(Location, on_delete=models.CASCADE, null=True)
    name        = models.CharField(max_length=160, null=True, blank=True)
    project_id  = models.CharField(max_length=155, unique=True, blank=True, null=True)
    project_status = models.CharField(max_length=100, default='todo', choices=[
        ('todo', 'TODO'), 
        ('inprogress', 'INPROGRESS'),
        ('complete', 'COMPLETE')
    ])
    start_date  = models.DateField(null=True)
    end_date    = models.DateField(null=True)
    project_estimation = models.IntegerField(null=True)
    total_target_kWp = models.CharField(max_length=160, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    # def __str__(self):
    #     return self.name
    
    def get_ordered_phases(self):
        return self.projectphase_set.all().order_by('order_number')
    
    # def calculate_start_date(self):
    #     if not self.start_date or self.project_status=="todo":
    #         return datetime.now() + timedelta(days=1)
    #     else:
    #         return self.start_date

    # def calculate_expected_end_date(self):
    #     if not self.end_date:
    #         return self.calculate_expected_start_date() + timedelta(days=self.project_estimation)
    #     else:
    #         return self.end_date

       

class ProjectPhase(models.Model):
    project_id  = models.ForeignKey(Project, on_delete=models.CASCADE)
    phase_name  = models.CharField(max_length=160)
    start_date  = models.DateField(null=True,blank=True)
    end_date    = models.DateField(null=True,blank=True)
    target_kWp      = models.CharField(max_length=160, null=True,blank=True)
    phase_status = models.CharField(max_length=100, default='todo', choices=[
        ('todo', 'TODO'), 
        ('inprogress', 'INPROGRESS'),
        ('complete', 'COMPLETE')
    ])
    
    target_count        = models.IntegerField(null=True, blank=True)
    target_duration      = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    final_output    = models.CharField(max_length=55, null=True,blank=True)
    order_number    = models.IntegerField(null=True, blank=True)
    phase_estimation = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.phase_name
    def get_ordered_tasks(self):
        return self.projectphasetask_set.all().order_by('order_number')
    
        
class ProjectPhaseTask(models.Model):
    parent_id           = models.ForeignKey('self', on_delete=models.CASCADE, null=True, to_field='id', related_name='parent')
    project_phase_id    = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, null=True, blank=True)
    title               = models.CharField(max_length=160)
    description         = models.TextField(null=True, blank=True)
    assigned_by         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_by')
    assigned_at         = models.DateTimeField(null=True)
    assigned_to         = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to_user    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    expected_complete_date = models.DateField(null=True, blank=True)
    status              = models.CharField(max_length=100, default='todo',  choices=[
        ('todo', 'TODO'), 
        ('inprogress', 'INPROGRESS'),
        ('review', 'REVIEW'),
        ('complete', 'COMPLETE')
    ])
    completed_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='completed_by')
    order_number        = models.IntegerField(null=True) #remove null in production
    is_dependent     = models.BooleanField(default=False)
    dependent_task_type = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('phasestarttime', 'PHASESTARTTIME'), 
        ('task', 'TASK')
    ])
    dependent_count = models.IntegerField(null=True, blank=True)
    dependent_duration = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    priority_level      = models.CharField(max_length=100, default='low', choices=[
        ('low', 'LOW'), 
        ('medium', 'MEDIUM'),
        ('high', 'HIGH')
    ])
    cost_estimations_pv    = models.IntegerField(null=True)
    start_date          = models.DateField(null=True, blank=True)
    end_date            = models.DateField(null=True, blank=True)
    target_count        = models.IntegerField(null=True, blank=True)
    target_duration      = models.CharField(max_length=100, null=True, blank=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    phase_start_confirmation = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    
    
class ProjectPhaseTaskDependency(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE, null=True, related_name='dependent')
    dependent_task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE, null=True, related_name='dependent_tasks')
    condition = models.CharField(max_length=100, null=True, choices=[
        ('and', 'AND'), 
        ('or', 'OR')
    ])
    class Meta:
        verbose_name_plural = "Project phase task dependencies"
 
    
class ProjectPhasesTaskFile(models.Model):
    project_phase_id        = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, null=True, blank=True)
    project_phase_task_id   = models.ForeignKey(ProjectPhaseTask, on_delete=models.SET_NULL, null=True, blank=True)
    file_url                = models.FileField(upload_to='files/projectphasetaskfiles', blank=True, null=True, validators=[validate_file_size])
    created_at              = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at              = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    #maxsizefilefield
    
class TaskAssignedUsers(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assign_to_user')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_by_user')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class TaskFields(models.Model):
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE)
    field_id = models.ForeignKey('masterdata.Field', on_delete=models.CASCADE, null=True)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

#--------------------------------------------------- PROJECT TASK TEMPLATES ----------------------------------------------------------
class ProjectTemplate(models.Model):
    name            = models.CharField(max_length=255)
    template_type   = models.CharField(max_length=100, choices=[
        ('project', 'PROJECT'), 
        ('phase', 'PHASE')
    ])
    status          = models.CharField(max_length=100, null=True, choices=[
        ('draft', 'draft'), 
        ('published', 'published'),
    ])
    def get_ordered_phase_template(self):
        return self.projectphasetemplate_set.all().order_by('order_number')
    
class ProjectPhaseTemplate(models.Model):
    template_id     = models.ForeignKey(ProjectTemplate, on_delete=models.CASCADE)
    phase_name      = models.CharField(max_length=255)
    target_count        = models.IntegerField(null=True)
    target_duration      = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    order_number        = models.IntegerField(null=True)
    
    def get_ordered_tasks(self):
        return self.projectphasetasktemplate_set.all().order_by('order_number')
    
    
class ProjectPhaseTaskTemplate(models.Model):
    parent_id       = models.ForeignKey('self', on_delete=models.CASCADE, null=True, to_field='id', related_name='parenttemplate')
    project_phases_template_id = models.ForeignKey(ProjectPhaseTemplate, on_delete=models.CASCADE)
    title           = models.CharField(max_length=160)
    description     = models.TextField(null=True)
    order_number        = models.IntegerField(null=True)
    is_dependent     = models.BooleanField(default=False)
    dependent_task_type = models.CharField(max_length=100, null=True, choices=[
        ('phasestarttime', 'PHASESTARTTIME'), 
        ('task', 'TASK')
    ])
    dependent_count = models.IntegerField(null=True, blank=True)
    dependent_duration = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    priority_level      = models.CharField(max_length=100, null=True, choices=[
        ('low', 'LOW'), 
        ('medium', 'MEDIUM'),
        ('high', 'HIGH')
    ])
    expected_count        = models.IntegerField(null=True, blank=True)
    expected_duration      = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    assigned_to_type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True)
    
class ProjectPhaseTaskTemplateDependency(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTaskTemplate, on_delete=models.CASCADE, null=True, related_name='task_templates')
    dependent_task_id = models.ForeignKey(ProjectPhaseTaskTemplate, on_delete = models.CASCADE, null=True, related_name='dependent_tasks_template')
    condition = models.CharField(max_length=100, null=True, choices=[
        ('and', 'AND'), 
        ('or', 'OR')
    ])

    
    class Meta:
        verbose_name_plural = "Project phase task template dependencies"

class TemplateTaskFields(models.Model):
    project_id = models.ForeignKey(ProjectTemplate, on_delete=models.CASCADE)
    task_id = models.ForeignKey(ProjectPhaseTaskTemplate, on_delete=models.CASCADE)
    field_id = models.ForeignKey('masterdata.Field', on_delete=models.CASCADE, null=True)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

#------------------------------------ PHASES AND TASK UPDATES -------------------------------------------------------------------------

class PhaseUpdate(models.Model):
    phase_id = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, null=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    column_name = models.CharField(max_length=55, null=True)
    updated_date = models.DateTimeField()
    
    
class TaskUpdate(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE, null=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    column_name = models.CharField(max_length=55, null=True)
    updated_date = models.DateTimeField()
    
    
class ProjectPhaseTaskMentions(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentioned_to')
    mentioned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentioned_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Project phase task mentions"