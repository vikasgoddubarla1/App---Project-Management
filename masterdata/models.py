from django.db import models
from projectmanagement.models import ProjectPhaseTask, ProjectPhaseTaskTemplate
from usermanagement.models import User
from locations.models import Location
from datetime import datetime

# Create your models here.
class CheckList(models.Model):
    name = models.CharField(max_length=555, unique=True)
    display_order = models.IntegerField(null=True, blank=True)
    is_master = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class CheckListItems(models.Model):
    checklist_id = models.ForeignKey(CheckList, on_delete = models.CASCADE, null=True, blank=True)
    name       = models.CharField(max_length=155)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    
class TaskCheckList(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE)
    checklist_id = models.ForeignKey(CheckList, on_delete=models.PROTECT, null=True, blank=True)
    checklist_item_id = models.ForeignKey(CheckListItems, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # def get_ordered_taskchecklistitems(self):
    #     return self.taskchecklistitems.order_by('id')
    
class TaskCheckListItems(models.Model):
    taskchecklist_id = models.ForeignKey(TaskCheckList, on_delete=models.CASCADE)
    checklistitems_id = models.ForeignKey(CheckListItems, on_delete=models.SET_NULL, null=True, blank=True)
    is_checked = models.BooleanField(default=False, null=True, blank=True)
    checked_by  = models.ForeignKey(User, on_delete = models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    
class Tab(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class Field(models.Model):
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length = 300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    field_type  = models.CharField(max_length=255, choices=[
        ('text', 'TEXT'), 
        ('longtext', 'LONGTEXT'),
        ('dropdown', 'DROPDOWN'),
        ('fileupload', 'FILEUPLOAD'),
        ('datetime', 'DATETIME'),
        ('integer', 'INTEGER'),
        ('decimal', 'DECIMAL'),
        ('date', 'DATE'),
        ('dependency', 'DEPENDENCY')
    ])
    options = models.JSONField(null=True, blank=True)
    display_order = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return self.name
    
class TabFields(models.Model):
    tab_id = models.ForeignKey(Tab, on_delete=models.CASCADE)
    field_id = models.ForeignKey(Field, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) 
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 
    
class LocationFields(models.Model):
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE)
    tab_id = models.ForeignKey(Tab, on_delete=models.SET_NULL, null=True, blank=True)
    field_id = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True)
    value        = models.TextField(null=True, blank=True)
    value_json   = models.JSONField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at   = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.field_id and self.field_id.field_type == 'date':
            self.value = self.convert_date_format(self.value)
        super(LocationFields, self).save(*args, **kwargs)

    def convert_date_format(self, date_str):
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            except ValueError:
                date_obj = None

            if date_obj:
                return date_obj.strftime('%d.%m.%Y')
        return date_str
# ........................................MODULE.................................
class GroupModule(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_pinned = models.BooleanField(default=False, null=True, blank=True)
    is_global = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # def __str__(self):
    #     return self.name
# ...........................................................
class Group(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str_(self):
        return self.name
    
class GroupView(models.Model):
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    group_module_id = models.ForeignKey(GroupModule, on_delete=models.CASCADE, related_name="group_module")
    order_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        ordering = ['order_number']
        
    # def __str__(self):
    #     return self.group_id.name
    
class ViewLocationFieldsLogs(models.Model):
    group_module_id = models.ForeignKey(GroupModule, on_delete=models.CASCADE)
    location_field_id = models.ForeignKey(LocationFields, on_delete=models.CASCADE)
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

class GroupField(models.Model):
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_fields")
    field_id = models.ForeignKey(Field, on_delete=models.CASCADE)
    order_number = models.IntegerField(null=True, blank=True)
    group_module_id = models.ForeignKey(GroupModule, on_delete=models.CASCADE, null=True, blank=True)
    is_hidden = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        ordering = ['order_number']
        
    
class UserGroup(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    field_id = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True)
    group_module_id = models.ForeignKey(GroupModule, on_delete= models.CASCADE, null=True, blank=True)
    field_order = models.IntegerField(null=True, blank=True)
    is_checked = models.BooleanField(default=True, null=True, blank=True)
    is_pinned = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now = True, null=True, blank=True)


#-------------------------------------------------------TEMPLATE CHECKLIST -----------------------------------------------------------------------
class TaskTemplateCheckList(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTaskTemplate, on_delete=models.CASCADE)
    checklist_id = models.ForeignKey(CheckList, on_delete=models.PROTECT, null=True, blank=True)
    checklist_item_id = models.ForeignKey(CheckListItems, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
class TaskTemplateCheckListItems(models.Model):
    tasktemplatechecklist_id = models.ForeignKey(TaskTemplateCheckList, on_delete=models.CASCADE)
    checklistitems_id = models.ForeignKey(CheckListItems, on_delete=models.SET_NULL, null=True, blank=True)
    is_checked = models.BooleanField(default=False, null=True, blank=True)
    checked_by  = models.ForeignKey(User, on_delete = models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

# ----------------------------------------------PROJECT PHASE TASK FIELDS--------------------------------------------------------------------------
class ProjectPhaseTaskFields(models.Model):
    task_id = models.ForeignKey(ProjectPhaseTask, on_delete=models.CASCADE)
    field_id = models.ForeignKey(Field, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)