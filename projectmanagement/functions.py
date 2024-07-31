from .models import *
from notifications.models import *
from partners.models import *
from django.utils import timezone
from projectmanagement.serializers import *
def assign_task_to_partner(task, partner, assigned_by_user):
    if partner:
        task.assigned_to = partner
        partner_admin = PartnerTypeRolesUser.objects.filter(
            partner_types_role_id__partner_id=partner,
            is_admin=True
        ).first()
        if partner_admin:
            fullname = f"{assigned_by_user.firstname} {assigned_by_user.lastname}"
            notification = Notification.objects.create(
                user_id=partner_admin.user_id.id,
                subject='Partner - Project Management',
                task_id = task.id,
                body=task.title,
                data_id=task.project_phase_id.project_id.id,
                data_name=task.project_phase_id.project_id.name,
                assigned_by_id=assigned_by_user.id,
                assigned_by_name=fullname,
                location_name=task.project_phase_id.project_id.location_id,
                created_at=timezone.now()
            )



def project_phases_and_tasks(self, response_data):
        project_phases = response_data['project_phases']
        for phase_data in project_phases:
            phase_tasks = ProjectPhaseTask.objects.filter(project_phase_id=phase_data['id']).distinct()
            phase_data['project_phase_tasks'] = ProjectPhaseTaskSerializer(phase_tasks, many=True).data
            
            for task in phase_tasks:
                if task.parent_id:
                    sub_task_index = next((index for index, sub_task in enumerate(phase_data['project_phase_tasks']) if sub_task['id'] == task.id), None)
                    if sub_task_index is not None:
                        del phase_data['project_phase_tasks'][sub_task_index]
        response_data['project_phases'] = project_phases
        return response_data
    
    
# def expected_start_date_calculate(self):
#     tasks = ProjectPhaseTask.objects.filter(status='todo') | Project.objects.filter(start_date__isnull=True)
#     for task in tasks:
#         task.start_date = timezone.now() + timezone.timedelta(days=1)
#         task.save()