from .models import *
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from rest_framework.exceptions import ValidationError
from notifications.models import Notification

def create_contract_approvals(self, contract_id, made_by, made_by_type, made_to, made_to_type):
    made_by = Partner.objects.get(pk=made_by)
    made_to = Partner.objects.get(pk=made_to)
    made_by_type = Type.objects.get(pk=made_by_type)
    made_to_type = Type.objects.get(pk=made_to_type)
    
    ContractApprovals.objects.bulk_create([
        ContractApprovals(
            contract_id = contract_id,
            partner_id = made_by,
            type_id = made_by_type,
            is_approved = None,
            approved_by = None,
            created_at = timezone.now()
        ),
        ContractApprovals(
            contract_id = contract_id,
            partner_id = made_to,
            type_id = made_to_type,
            is_approved = None,
            approved_by = None,
            created_at = timezone.now()
        )
    ])
    
    
def create_contract_logs(self, contract_id, user_id, column_name):
    ContractLogs.objects.create(
        contract_id = contract_id,
        user_id = user_id,
        column_name = column_name,
        updated_at = timezone.now()
    )
    
def create_contract_notifications(self, user_id, user_name, subject, body, data_id, data_name, assigned_by, assigned_by_name, location_name, source, status_type):
    Notification.objects.create(
        user_id = user_id,
        user_name = user_name,
        subject = subject,
        task_id = None,
        body =body,
        data_id = data_id,
        data_name = data_name,
        assigned_by_id = assigned_by,
        assigned_by_name = assigned_by_name,
        location_name = location_name,
        source = source,
        status_type = status_type,
        created_at = timezone.now()    
    )

    

def calculate_end_date(self, instance, begin_date, duration, duration_cycle):
        if duration_cycle == 'days':
            instance.end_date = begin_date + timedelta(days=duration)
        elif duration_cycle == 'weeks':
            instance.end_date = begin_date + timedelta(weeks=duration)
        elif duration_cycle == 'months':
            instance.end_date = begin_date + relativedelta(months=duration) - timedelta(days=1)
        elif duration_cycle == 'years':
            instance.end_date = begin_date + relativedelta(years=duration) - timedelta(days=1)
        else:
            raise ValidationError('Duration and duration cycle are required.')

def auto_extend_end_date(self, instance, extend_duration, extend_cycle):
    today = timezone.now().date()
    while today >= instance.end_date:
        if extend_cycle == 'days':
            instance.end_date += timedelta(days=extend_duration)
        elif extend_cycle == 'weeks':
            instance.end_date += timedelta(weeks=extend_duration)
        elif extend_cycle == 'months':
            instance.end_date += relativedelta(months=extend_duration)
        elif extend_cycle == 'years':
            instance.end_date += relativedelta(years=extend_duration)

def calculate_termination_date(self, instance, termination_duration, termination_cycle):
    if termination_cycle == 'days':
        instance.termination_date = instance.end_date - timedelta(days=termination_duration)
    elif termination_cycle == 'weeks':
        instance.termination_date = instance.end_date - timedelta(weeks=termination_duration)
    elif termination_cycle == 'months':
        instance.termination_date = instance.end_date - relativedelta(months=termination_duration)
    elif termination_cycle == 'years':
        instance.termination_date = instance.end_date - relativedelta(years=termination_duration)