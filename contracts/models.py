from django.db import models
from partners.models import *
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from usermanagement.models import User

# Create your models here.
class ContractCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Contract categories"
class ContractSubCategory(models.Model):
    contract_category_id = models.ForeignKey(ContractCategory, on_delete=models.CASCADE)
    name                 = models.CharField(max_length=160, unique=True, null=True )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Contract sub categories"

class Contract(models.Model):
    contract_number     = models.CharField(max_length=100, unique=True)
    name                = models.CharField(max_length=100, unique=True)
    status              = models.CharField(max_length=100, null=True, choices=[
        ('draft', 'Draft'), 
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated')
    ])
    created_by          = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='contract_by', null=True)
    category_id         = models.ForeignKey(ContractCategory, on_delete=models.SET_NULL, null=True)
    sub_category_id     = models.ForeignKey(ContractSubCategory, on_delete=models.SET_NULL, null=True)
    begin_date          = models.DateField(null=True)
    duration            = models.IntegerField(null=True)
    duration_cycle      = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    auto_extended       = models.BooleanField(default=False)
    extend_duration     = models.IntegerField(null=True, blank=True)
    extend_cycle        = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    end_date            = models.DateField(null=True)
    is_terminated       = models.BooleanField(default=False, null=True)
    termination_duration = models.IntegerField(null=True)
    termination_cycle   = models.CharField(max_length=100, null=True, choices=[
        ('days', 'Days'), 
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ])
    termination_date    = models.DateField(null=True)
    terminated_on       = models.DateField(null=True)
    location_id         = models.ForeignKey('locations.Location', on_delete= models.SET_NULL, null=True, blank=True)
    made_by             = models.ForeignKey(Partner, on_delete = models.SET_NULL, null=True, blank=True, related_name='made_by')
    made_by_type        = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'made_by_type')
    made_to             = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='made_to')
    made_to_type        = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True, related_name='made_to_type')
    approval_status     = models.CharField(max_length=100, default='draft', choices=[
        ('draft', 'DRAFT'), 
        ('review', 'REVIEW'),
        ('published', 'PUBLISHED')
    ])
    previous_status     = models.CharField(max_length=100, null=True, blank=True)
    previous_status_comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True, null=True)
    is_active = models.BooleanField(default = True)
    
    
    
    
    def __str__(self):
        return f"{self.name} - {self.contract_number}"
    

@receiver(pre_save, sender=Contract)
def update_contract_status(sender, instance, **kwargs):
    today = timezone.now().date()
    start_date = instance.begin_date
    end_date = instance.end_date

    if start_date is None or end_date is None:
        instance.status = 'draft'
    elif start_date > today:
        instance.status = 'draft'
    elif start_date <= today <= end_date:
        instance.status = 'active'
    else:
        instance.status = 'inactive'


class ContractFramework(models.Model):
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='contract', null=True) #category_id 2
    individual_contract_id = models.ManyToManyField(Contract, related_name='induvidual_contract')


    
class ContractPartner(models.Model):
    contract_id = models.ManyToManyField(Contract, related_name='contract_id')
    partner_id  = models.ManyToManyField(Partner)
    is_main     = models.BooleanField(default=False)


class ContractFile(models.Model):
    contract_id     = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True)
    file_url        = models.FileField(upload_to='files/contractfiles/', null=True)
    created_at      = models.DateTimeField(auto_now_add=True, null=True)

class ContractLogs(models.Model):
    contract_id = models.ForeignKey(Contract, on_delete= models.CASCADE, null=True)
    user_id     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    column_name = models.CharField(max_length=255, null=True)
    updated_at  = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Contract logs"


class ContractApprovals(models.Model):
    contract_id = models.ForeignKey(Contract, on_delete = models.CASCADE)
    partner_id = models.ForeignKey(Partner, on_delete = models.CASCADE, null=True)
    type_id     = models.ForeignKey(Type, on_delete=models.CASCADE, null=True, blank=True)
    is_approved = models.CharField(max_length=100, null=True, blank=True, choices=[('approve', 'APPROVE'), ('reject', 'REJECT')])
    comments    = models.TextField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Contract approvals"