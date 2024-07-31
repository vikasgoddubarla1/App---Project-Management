from django.shortcuts import render
from rest_framework import generics, status
from .serializers import *
from .models import *
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from usermanagement.exceptions import *
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F, Max
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.db import transaction
from datetime import datetime
from notifications.models import Notification
from notifications.create_notifications import *
from locations.models import *
from .functions import *
from partners.models import *
from dateutil.relativedelta import relativedelta
from masterdata.models import * 

# Create your views here.
#------------------------------------------------------ PROJECT VIEWS -------------------------------------------------------------
class ProjectCreate(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    

    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        serializer.save()
        

    def create(self, request, *args, **kwargs):
        template_id = request.data.get('template_id')
        location_id = request.data.get('location_id')
        location = Location.objects.get(pk=location_id)
        if not self.request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        try:
            if template_id:
                project_template = ProjectTemplate.objects.get(pk=template_id)
            # else:
            #     # location_id = request.data.get('location_id')
            #     # location = Location.objects.get(pk=location_id)
            #     existing_project = Project.objects.filter(location_id=location_id).exists()
            #     if existing_project:
            #         existing_project.delete()
            #         # return Response({'error':'Project already exist for this location please choose another one'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            #     else:
            #         location = Location.objects.get(pk=location_id)
            #         project_name = request.data.get('name')
            #         new_project = Project(name=project_name, location_id=location)
            #         new_project.save()

            #         serializer = self.get_serializer(new_project)
            #         response_data = serializer.data
            #         return Response({'projectDetails': response_data}, status=status.HTTP_201_CREATED)

            # location_id = request.data.get('location_id')
            existing_project = Project.objects.filter(location_id=location_id).delete()
            # location = Location.objects.get(pk=location_id)
            project_name = request.data.get('name')
            new_project = Project(name=project_name, location_id=location)
            new_project.save()
           
            task_template_mapping = {}
            parent_task_mapping = {}

            for phase_template in project_template.projectphasetemplate_set.all():
                new_phase = ProjectPhase(
                    phase_name=phase_template.phase_name,
                    project_id=new_project,
                    order_number=phase_template.order_number,
                    target_count=phase_template.target_count,
                    target_duration=phase_template.target_duration
                )
                new_phase.save()
                
                task_templates = phase_template.projectphasetasktemplate_set.all()
                for task_template in task_templates:
                    new_task = ProjectPhaseTask(
                        title=task_template.title,
                        description=task_template.description,
                        project_phase_id=new_phase,
                        priority_level=task_template.priority_level,
                        dependent_task_type = task_template.dependent_task_type,
                        target_count=task_template.expected_count,
                        target_duration=task_template.expected_duration,
                        order_number = task_template.order_number,
                        dependent_count = task_template.dependent_count,
                        dependent_duration= task_template.dependent_duration,
                        assigned_by=self.request.user
                    )
                    assigned_to_type = task_template.assigned_to_type
                    partner_id = Partner.objects.filter(locationpartnertype__location_id = location_id, locationpartnertype__type_id=assigned_to_type).first()
                    assign_task_to_partner(new_task, partner_id, self.request.user)
                    
                    if task_template.parent_id:
                        parent_task = parent_task_mapping.get(task_template.parent_id.id)
                        if parent_task:
                            new_task.parent_id = parent_task
                    new_task.save()
                    task_template_mapping[task_template.id] = new_task.id
                    parent_task_mapping[task_template.id] = new_task
                    task_template_checklists = TaskTemplateCheckList.objects.filter(task_id=task_template)
                    for checklist in task_template_checklists:
                       new_checklist = TaskCheckList(
                           task_id=new_task,
                           checklist_id=checklist.checklist_id,
                           checklist_item_id=checklist.checklist_item_id
                       )
                       new_checklist.save()
                       checklist_items = TaskTemplateCheckListItems.objects.filter(tasktemplatechecklist_id=checklist)
                       for item in checklist_items:
                           new_item = TaskCheckListItems(
                               taskchecklist_id=new_checklist,
                               checklistitems_id=item.checklistitems_id,
                               is_checked=item.is_checked,
                               checked_by=item.checked_by
                           )
                           new_item.save()
                    
                    task_template_fields = TemplateTaskFields.objects.filter(task_id=task_template)
                    for taskfields in task_template_fields:
                       task_fields = TaskFields.objects.create(
                           task_id=new_task,
                           project_id=new_task.project_phase_id.project_id,
                           field_id=taskfields.field_id,
                           is_required = taskfields.is_required
                       )

            for phase_template in project_template.projectphasetemplate_set.all():
                for task_template in phase_template.projectphasetasktemplate_set.all():
                    if task_template.parent_id:
                        new_parent_id = task_template_mapping.get(task_template.parent_id.id)
                        if new_parent_id:
                            ProjectPhaseTask.objects.filter(id=task_template_mapping[task_template.id]).update(
                                parent_id=new_parent_id)

            for phase_template in project_template.projectphasetemplate_set.all():
                for task_template in phase_template.projectphasetasktemplate_set.all():
                    new_task = ProjectPhaseTask.objects.get(id=task_template_mapping[task_template.id])
                    for dependency in task_template.task_templates.all():
                        dependent_task = task_template_mapping.get(dependency.dependent_task_id.id)
                        if dependent_task:
                            ProjectPhaseTaskDependency.objects.create(
                                task_id=new_task,
                                dependent_task_id=ProjectPhaseTask.objects.get(id=dependent_task),
                                condition=dependency.condition
                            )

            serializer = self.get_serializer(new_project)
            response_data = serializer.data

            return Response({'message': 'Project created from template', 'projectDetails': response_data},
                            status=status.HTTP_201_CREATED)

        except (ProjectTemplate.DoesNotExist, Location.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectUpdate(generics.UpdateAPIView):
   queryset = Project.objects.all().order_by('id')
   serializer_class = ProjectUpdateSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           if user.is_admin:
               instance = serializer.save()
               return Response({'projectDetails':serializer.data})
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       

       
#---------------------------------------- PROJECT PHASE VIEWS ------------------------------------------------------------------------
class ProjectPhaseCreate(generics.CreateAPIView):
    serializer_class = ProjectPhaseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        project_id = kwargs.get('project_id')
        try:
            if project_id:
                try:
                    project = Project.objects.get(pk=project_id)
                except Project.DoesNotExist:
                    return Response({'error': 'Project not found'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Please provide project_id'}, status=status.HTTP_400_BAD_REQUEST)

            phase_name = request.data.get('phase_name')
            order_number = request.data.get('order_number')
            target_count = request.data.get('target_count')
            target_duration = request.data.get('target_duration')

            if not order_number:
                
                existing_phases = ProjectPhase.objects.filter(project_id=project)
                max_order_number = existing_phases.aggregate(models.Max('order_number'))['order_number__max']
                order_number = (max_order_number or 0) + 1


            template_id = request.data.get('template_id')
            if not phase_name and not template_id:
                return Response({'error':'project name or template required'}, status=500)
            if template_id:
                try:
                    project_template = ProjectTemplate.objects.get(pk=template_id)
                    phase_templates = project_template.projectphasetemplate_set.all()
                    task_template_mapping = {}
                    parent_task_mapping = {}
                    
                    for phase_template in phase_templates:
                        new_phase = ProjectPhase(
                            project_id = project,
                            phase_name = phase_template.phase_name,
                            target_count = phase_template.target_count,
                            target_duration = phase_template.target_duration,
                            order_number = order_number,
                            created_by = request.user
                        )
                        new_phase.save()
                        
                        task_templates = phase_template.projectphasetasktemplate_set.all()
                        for task_template in task_templates:
                            new_task = ProjectPhaseTask(
                                title=task_template.title,
                                description=task_template.description,
                                project_phase_id=new_phase,
                                order_number = task_template.order_number,
                                dependent_task_type = task_template.dependent_task_type,
                                target_count=task_template.expected_count,
                                target_duration=task_template.expected_duration,
                                priority_level = task_template.priority_level,
                                dependent_count = task_template.dependent_count,
                                dependent_duration = task_template.dependent_duration,
                                assigned_by=self.request.user
                            )
                            assigned_to_type = task_template.assigned_to_type
                            location_id = project.location_id.id
                            partner_id = Partner.objects.filter(locationpartnertype__location_id = location_id, locationpartnertype__type_id=assigned_to_type).first()
                            assign_task_to_partner(new_task, partner_id, self.request.user)                               

                            if task_template.parent_id:
                                parent_task = parent_task_mapping.get(task_template.parent_id.id)
                                if parent_task:
                                    new_task.parent_id = parent_task
                            new_task.save()
                            task_template_mapping[task_template.id] = new_task.id
                            parent_task_mapping[task_template.id] = new_task
                            
                            task_template_checklists = TaskTemplateCheckList.objects.filter(task_id=task_template)
                            for checklist in task_template_checklists:
                                new_checklist = TaskCheckList(
                                    task_id=new_task,
                                    checklist_id=checklist.checklist_id,
                                    checklist_item_id=checklist.checklist_item_id
                                )
                                new_checklist.save()
                                checklist_items = TaskTemplateCheckListItems.objects.filter(tasktemplatechecklist_id=checklist)
                                for item in checklist_items:
                                    new_item = TaskCheckListItems(
                                        taskchecklist_id=new_checklist,
                                        checklistitems_id=item.checklistitems_id,
                                        is_checked=item.is_checked,
                                        checked_by=item.checked_by
                                    )
                                    new_item.save()
                                    
                            task_template_fields = TemplateTaskFields.objects.filter(task_id=task_template)
                            for taskfields in task_template_fields:
                                task_fields = TaskFields.objects.create(
                                    task_id=new_task,
                                    project_id=new_task.project_phase_id.project_id,
                                    field_id=taskfields.field_id,
                                    is_required = taskfields.is_required
                                )

                    for phase_template in project_template.projectphasetemplate_set.all():
                        for task_template in phase_template.projectphasetasktemplate_set.all():
                            if task_template.parent_id:
                                new_parent_id = task_template_mapping.get(task_template.parent_id.id)
                                if new_parent_id:
                                    ProjectPhaseTask.objects.filter(id=task_template_mapping[task_template.id]).update(
                                        parent_id=new_parent_id)

                    for phase_template in project_template.projectphasetemplate_set.all():
                        for task_template in phase_template.projectphasetasktemplate_set.all():
                            new_task = ProjectPhaseTask.objects.get(id=task_template_mapping[task_template.id])
                            for dependency in task_template.task_templates.all():
                                dependent_task = task_template_mapping.get(dependency.dependent_task_id.id)
                                if dependent_task:
                                    ProjectPhaseTaskDependency.objects.create(
                                        task_id=new_task,
                                        dependent_task_id=ProjectPhaseTask.objects.get(id=dependent_task),
                                        condition=dependency.condition
                                    )

                    serializer = self.get_serializer(new_phase)
                    response_data = serializer.data
                    
                    return Response({'message': 'Phase created', 'phaseDetails': response_data}, status=status.HTTP_201_CREATED)

                except ProjectTemplate.DoesNotExist:
                    return Response({'error': 'ProjectTemplate not found'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                new_phase = ProjectPhase(phase_name=phase_name, target_count=target_count, target_duration=target_duration, order_number=order_number, project_id=project, created_by=request.user)
                new_phase.save()
                serializer = self.get_serializer(new_phase)
                response_data = serializer.data
                return Response({'message': 'Phase created', 'phaseDetails': response_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectPhaseUpdate(generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            
            user = self.request.user
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
            instance = self.get_object()

            updated_fields = []
           
            if 'target_kWp' in request.data:
                new_target_kWp = request.data['target_kWp'] if request.data['target_kWp'] else None
                if instance.target_kWp != new_target_kWp:
                    updated_fields.append('target_kWp')
            if 'target_count' in request.data:
                new_target_count = int(request.data['target_count']) if request.data['target_count'] else None
                if instance.target_count != new_target_count:
                    updated_fields.append('target_count')
            if 'target_duration' in request.data:
                new_target_duration = request.data['target_duration'] if request.data['target_duration'] else None
                if instance.target_duration != new_target_duration:
                    updated_fields.append('target_duration')
            if 'final_output' in request.data:
                new_final_output = request.data['final_output'] if request.data['final_output'] else None
                if instance.final_output != new_final_output:
                    updated_fields.append('final_output')

            if updated_fields:
                user_instance = user
                updated_at = timezone.now()
                
                
                for field in updated_fields:
                    phase_update = PhaseUpdate.objects.create(
                        phase_id=instance, user_id=user_instance, column_name=field, updated_date=updated_at
                    )
             
            if 'order_number' in request.data and instance.order_number != int(request.data['order_number']):
                new_order_number = int(request.data['order_number'])

                if instance.order_number is not None: 
                    old_order_number = instance.order_number

                    with transaction.atomic():
                        if new_order_number < old_order_number:
                            
                            ProjectPhase.objects.filter(
                                project_id=instance.project_id,
                                order_number__gte=new_order_number,
                                order_number__lt=old_order_number
                            ).exclude(id=instance.id).update(order_number=models.F('order_number') + 1)
                        else:
                            
                            ProjectPhase.objects.filter(
                                project_id=instance.project_id,
                                order_number__gt=old_order_number,
                                order_number__lte=new_order_number
                            ).exclude(id=instance.id).update(order_number=models.F('order_number') - 1)

                instance.order_number = new_order_number

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            if user.is_admin or partner_admin_user:
                instance = serializer.save()
                print(serializer.data)
                return Response({'projectPhaseDetails': serializer.data})
                
            else:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
            
            if not self.request.user.is_admin and not partner_admin_user:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            deleted_order_number = instance.order_number

            with transaction.atomic():
                self.perform_destroy(instance)
                
                ProjectPhase.objects.filter(
                    project_id=instance.project_id,
                    order_number__gt=deleted_order_number
                ).update(order_number=F('order_number') - 1)

            return Response({'message': 'ProjectPhase deleted successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


       
class ProjectPhaseStatus(generics.UpdateAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseStatusSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            user = request.user
            if not user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()

            
            user_instance = request.user
            column_name = 'phase_status'
            updated_at = datetime.now()

            phase_update = PhaseUpdate.objects.create(phase_id=instance, user_id=user_instance, column_name=column_name, updated_date=updated_at)
                      
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            if 'phase_status' in request.data:
                new_status = request.data['phase_status']
                if new_status == 'complete':
                    instance.end_date = datetime.now().date()
                elif new_status == 'todo':
                    instance.start_date = None
                    instance.end_date = None
                              
            self.perform_update(serializer)
            
            return Response({'projectPhaseStatus': serializer.data})
        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ProjectPhaseStart(generics.UpdateAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseStartSerializer
    permission_classes = (IsAuthenticated,)
   
    def update(self, request, *args, **kwargs):
        try:
            project_phase = self.get_object()
           
            if not project_phase.start_date:
                with transaction.atomic():
                    project_phase.start_date = datetime.now().date()
                    project_phase.phase_status = 'inprogress'
                    project_phase.save()

                    
                    phase_start_tasks = ProjectPhaseTask.objects.filter(
                        project_phase_id=project_phase.id,
                        dependent_task_type='phasestarttime'
                    )
                    
                    for task in phase_start_tasks:
                        if not task.dependent_count and not task.dependent_duration:
                            parent_dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task.parent_id)

                            if not parent_dependencies.exists() or all(
                                ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete'
                                for dep in parent_dependencies
                            ):
                                task.status = 'inprogress'
                                task.start_date = datetime.now().date()
                                task.save()

                    
                    user_id = request.user
                    column_name = 'start_date'
                    updated_at = datetime.now()
                    phase_update = PhaseUpdate.objects.create(
                        phase_id=project_phase,
                        user_id=user_id,
                        column_name=column_name,
                        updated_date=updated_at
                    )

                    
                    project = project_phase.project_id
                    project.project_status = 'inprogress'
                    start_date = project.start_date
                    if not start_date:
                        project.start_date = datetime.now().date()
                    project.save()

                    location = project.location_id
                    location.location_status = 'projectmanagement'
                    location.current_phase_id = project_phase
                    location.current_phase = project_phase.phase_name
                    location.current_phase_status = project_phase.phase_status
                    location.operating_date = timezone.now().date()
                    location.save()

                    serializer = self.get_serializer(project_phase)
                    return Response({'message': 'start_date updated successfully'})
            else:
                return Response({'message': 'start_date already set'}, status=status.HTTP_400_BAD_REQUEST)
        except ProjectPhase.DoesNotExist:
            return Response({'error': 'ProjectPhase not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class ProjectPhaseDetail(generics.RetrieveAPIView):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseGetSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        
        phase_updates = instance.phaseupdate_set.all()
        phase_update_serializer = PhaseUpdateListSerializer(phase_updates, many=True)
        serializer.data['phase_updates'] = phase_update_serializer.data
        response_data = serializer.data.copy()  
        response_data['phase_updates'] = phase_update_serializer.data
       
        return Response(response_data)
    
  
       
#------------------------------------------- PROJECT PHASE TASK VIEWS ----------------------------------------------------------------- 


class ProjectPhaseTaskCreate(generics.CreateAPIView):
    queryset = ProjectPhaseTask.objects.all()
    serializer_class = ProjectPhaseTaskSerializer
    permission_classes = (IsAuthenticated,)

    
    def create(self, request, *args, **kwargs):
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
        if not request.user.is_admin and not partner_admin_user:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        try:
            project_phase_id = kwargs.get('project_phase_id')
            max_order_number = ProjectPhaseTask.objects.filter(project_phase_id=project_phase_id).aggregate(Max('order_number'))['order_number__max']
            new_order_number = 1 if max_order_number is None else max_order_number + 1

            mutable_request_data = request.data.copy()
            mutable_request_data['project_phase_id'] = project_phase_id
            mutable_request_data['assigned_by'] = request.user.id
            mutable_request_data['order_number'] = new_order_number

            
            serializer = self.get_serializer(data=mutable_request_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            task_id = serializer.data['id'] 
            dependent_task_ids = mutable_request_data.get('dependent_task_id', [])
            condition = mutable_request_data.get('condition')
            if condition == 'or' and len(dependent_task_ids) < 2:
                return Response({'status_code':655, 'error': 'Please add at least two tasks for "or" condition.'}, status=status.HTTP_400_BAD_REQUEST)
            
            dependency_instances = []
            for dependent_task_id in dependent_task_ids:
                dependency_data = {
                    'task_id': task_id,
                    'dependent_task_id': dependent_task_id,
                    'condition': condition,
                }
                dependency_serializer = ProjectPhaseTaskDependencySerializer(data=dependency_data)
                dependency_serializer.is_valid(raise_exception=True)
                dependency_instance = dependency_serializer.save()
                dependency_instances.append(dependency_instance)

            response_data = {'projectPhaseTaskDetails': serializer.data}

            if dependency_instances:
                    dependency_details = [{
                        'dependent_task_id': dependency.dependent_task_id_id,
                        'dependent_task_name':dependency.dependent_task_id.title,
                        'condition': dependency.condition,
                    } for dependency in dependency_instances]

                    response_data['projectPhaseTaskDetails']['project_phase_task_dependencies'] = dependency_details

            return Response(response_data)
        except ValidationError as e:
            return Response({'error': e.detail}, status=500)
        except Exception as e:
            return Response({'error': str(e)})


class ProjectPhaseSubTaskCreate(generics.CreateAPIView):
   queryset = ProjectPhaseTask.objects.all()
   serializer_class = ProjectPhaseTaskSerializer
   permission_classes = (IsAuthenticated,)

   def create(self, request, *args, **kwargs):
       partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
       if not request.user.is_admin and not partner_admin_user:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       try:
           parent_id = kwargs.get('parent_id') 
           parent_task = ProjectPhaseTask.objects.get(id=parent_id)
           project_phase_id = parent_task.project_phase_id_id
           
           max_order_number = ProjectPhaseTask.objects.filter(project_phase_id=project_phase_id, parent_id=parent_id).aggregate(
               Max('order_number'))['order_number__max']
           new_order_number = 1 if max_order_number is None else max_order_number + 1
           
           mutable_request_data = request.data.copy()
           mutable_request_data['parent_id'] = parent_id
           mutable_request_data['assigned_by'] = request.user.id
           mutable_request_data['project_phase_id'] = project_phase_id
           mutable_request_data['order_number'] = new_order_number
           
           serializer = self.get_serializer(data=mutable_request_data)
           serializer.is_valid(raise_exception=True)
           self.perform_create(serializer)
           task_id = serializer.data['id'] 
           dependent_task_ids = mutable_request_data.get('dependent_task_id', []) 
           condition = mutable_request_data.get('condition')
           if condition == 'or' and len(dependent_task_ids) < 2:
                return Response({'status_code':655, 'error': 'Please add at least two tasks for "or" condition.'}, status=status.HTTP_400_BAD_REQUEST)

           
           dependency_instances = []
           for dependent_task_id in dependent_task_ids:
               dependency_data = {
                   'task_id': task_id,
                   'dependent_task_id': dependent_task_id,
                   'condition': mutable_request_data.get('condition'), 
               }
               dependency_serializer = ProjectPhaseTaskDependencySerializer(data=dependency_data)
               dependency_serializer.is_valid(raise_exception=True)
               dependency_instance = dependency_serializer.save()
               dependency_instances.append(dependency_instance)

           response_data = {'projectPhaseTaskDetails': serializer.data}

           if dependency_instances:
                dependency_details = [{
                    'dependent_task_id': dependency.dependent_task_id_id,
                    'dependent_task_name':dependency.dependent_task_id.title,
                    'condition': dependency.condition,
                } for dependency in dependency_instances]

                response_data['projectPhaseTaskDetails']['project_phase_task_dependencies'] = dependency_details

           return Response({'projectPhaseSubTaskDetails': response_data})
       except ValidationError as e:
           return Response({'error': e.detail}, status=500)
       except Exception as e:
           return Response({'error': str(e)})

class ProjectPhaseTaskStatus(generics.UpdateAPIView):
    serializer_class = ProjectPhaseTaskStatusSerializer
    permission_classes = (IsAuthenticated,)  

    def get_object(self):
        task_id = self.kwargs.get('pk')
        try:
            instance = ProjectPhaseTask.objects.get(pk=task_id)
            return instance
        except ProjectPhaseTask.DoesNotExist:
            return None
 

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        try:
            if instance is None:
                return Response({'error': 'Task not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            user = request.user
            assigned_user = ProjectPhaseTask.objects.filter(taskassignedusers__user_id = user)
            # if not user.is_admin and (not partner_admin_user and assigned_user != user): #(not user.partner_admin and instance.assigned_to_user != user):
            #     return Response({'status_code':657, 'error':'This task is not assigned to you or your partner.'}, status = 400)
            if not user.is_admin and (not partner_admin_user and not assigned_user):
                return Response({'status_code':657, 'error':'This task is not assigned to you or your partner.'}, status = 400)


            old_status = instance.status
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            if 'status' in request.data and request.data['status'] != old_status:
                user_instance = request.user
                column_name = 'status'
                updated_at = timezone.now()
                task_update = TaskUpdate.objects.create(
                    task_id=instance,
                    user_id=user_instance,
                    column_name=column_name,
                    updated_date=updated_at
                )

            if 'status' in request.data:
                new_status = request.data['status']
                
                if new_status == 'inprogress':
                    if instance.status == 'inprogress':
                        
                        instance.start_date = datetime.now().date()
                        instance.end_date = None

                        
                        parent_task = instance.parent_id
                        if parent_task:
                            parent_task.status = 'inprogress'
                            if not parent_task.start_date:
                                parent_task.start_date = datetime.now().date()
                            parent_task.save()
                            
                parent_task = instance.parent_id
                    
                parent_dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=parent_task)
                
                if parent_dependencies.exists():
                    parent_dependencies_complete = all(
                        ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete'
                        for dep in parent_dependencies
                    )

                    if not parent_dependencies_complete:
                        return Response({'status_code':654, 'error': 'Please complete parent task dependencies first'}, status=status.HTTP_400_BAD_REQUEST)
                    
                
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=instance)
                if dependencies.exists():
                    condition = dependencies.first().condition
                    dependent_task_ids = dependencies.values_list('dependent_task_id', flat=True)
                    dependent_task_info  = ProjectPhaseTask.objects.filter(id__in=dependent_task_ids).values('id', 'title', 'status')
                    if condition == 'and':
                        incomplete_dependent_tasks = [{'id':task['id'], 'title':task['title'], 'status':task['status']} for task in dependent_task_info if task['status'] != 'complete']
                        if incomplete_dependent_tasks:
                            return Response({'status_code':651, 'error':'Please complete these dependent tasks first:', 'taskDetail':incomplete_dependent_tasks}, status = 400)
                    elif condition == 'or':
                        completed_dependent_tasks = [{'id':task['id'], 'title':task['title'], 'status':task['status']} for task in dependent_task_info if task['status']=='complete']
                        if not completed_dependent_tasks:
                            return Response({'status_code': 651, 'error':'Please complete any one of these tasks first:', 'taskDetail': dependent_task_info}, status=400)
                            
                if new_status == 'complete':
                    required_tasks = TaskFields.objects.filter(task_id=instance.id, is_required=True)
                    print("Line 783",required_tasks)
                    for task in required_tasks:
                        location_id = instance.project_phase_id.project_id.location_id.id
                        fields = LocationFields.objects.get(location_id=location_id, field_id= task.field_id)
                        print("Line 787",fields)
                        print("Line 790",fields)
                        if not fields.value:
                            return Response({'status_code':659, 'error':'Please fill the required task fields'}, status=500)
                    subtasks = ProjectPhaseTask.objects.filter(parent_id=instance)
                    complete_all_subtasks = all(subtask.status == 'complete' for subtask in subtasks)
                    if not complete_all_subtasks:
                        return Response({'status_code':652, 'error':'Please complete subtasks first'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                                     
                    
                    instance.status = new_status
                    instance.save()
                    # --------------------------------------- Parent task dependency status update -----------------------------------------
                    parent_task = instance.parent_id
                    if parent_task:
                        subtasks = ProjectPhaseTask.objects.filter(parent_id=parent_task)
                        complete_all_subtasks =  all(subtask.status == 'complete' for subtask in subtasks)
                        if complete_all_subtasks:
                            parent_task.status = 'complete'
                            parent_task.end_date = datetime.now().date()
                            parent_task.save()
                                
                            dependent_tasks = ProjectPhaseTaskDependency.objects.filter(dependent_task_id=parent_task)
                            for dep_task in dependent_tasks:
                                condition = dep_task.condition
                                dependent_task = ProjectPhaseTask.objects.get(id=dep_task.task_id.id)
                                dependencies_for_task = ProjectPhaseTaskDependency.objects.filter(task_id=dependent_task)

                                if condition == 'and':
                                    if all(ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete' for dep in dependencies_for_task):
                                        if dependent_task.status == 'todo':
                                            dependent_task.status = 'inprogress'
                                            dependent_task.start_date = datetime.now().date()
                                            dependent_task.save()
                                            print(f'Changed status of the task{dependent_task.id} due to and comdition')
                                        phase_start_subtasks = ProjectPhaseTask.objects.filter(
                                            parent_id=dependent_task,
                                            dependent_task_type='phasestarttime'
                                        )
                                        print(phase_start_subtasks, "These are the phase start subtasks")

                                        
                                        for subtask in phase_start_subtasks:
                                            if subtask.status != 'complete':
                                                subtask.status = 'inprogress'
                                                subtask.start_date = timezone.now().date()
                                                subtask.save()
                                        

                                elif condition == 'or':
                                    if any(ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete' for dep in dependencies_for_task):
                                        if dependent_task.status == 'todo':
                                            dependent_task.status = 'inprogress'
                                            dependent_task.start_date = datetime.now().date()
                                            dependent_task.save()
                                            print(f'Changed status of the task{dependent_task.id} due to or comdition')
                                
                                        phase_start_subtasks = ProjectPhaseTask.objects.filter(
                                            parent_id=dependent_task,
                                            dependent_task_type='phasestarttime'
                                        )
                                        print(phase_start_subtasks, "These are the phase start subtasks")

                                        
                                        for subtask in phase_start_subtasks:
                                            if subtask.status != 'complete':
                                                subtask.status = 'inprogress'
                                                subtask.start_date = timezone.now().date()
                                                subtask.save()
                            
                             
                    #---------------------------------- All tasks dependency status auto update ------------------------------------
                    dependent_tasks = ProjectPhaseTaskDependency.objects.filter(dependent_task_id=instance)

                    for dep_task in dependent_tasks:
                        condition = dep_task.condition
                        dependent_task = ProjectPhaseTask.objects.get(id=dep_task.task_id.id)
                        dependencies_for_task = ProjectPhaseTaskDependency.objects.filter(task_id=dependent_task)

                        if condition == 'and':
                            if all(ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete' for dep in dependencies_for_task):
                                if dependent_task.status == 'todo':
                                    dependent_task.status = 'inprogress'
                                    dependent_task.start_date = datetime.now().date()
                                    dependent_task.save()
                                    print(f'Changed status of the task{dependent_task.id} due to and comdition')
                            
                                phase_start_subtasks = ProjectPhaseTask.objects.filter(
                                    parent_id=dependent_task,
                                    dependent_task_type='phasestarttime'
                                )
                                print(phase_start_subtasks, "These are the phase start subtasks")

                                
                                for subtask in phase_start_subtasks:
                                    if subtask.status != 'complete':
                                        subtask.status = 'inprogress'
                                        subtask.start_date = timezone.now().date()
                                        subtask.save()
                    
                        elif condition == 'or':
                            if any(ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete' for dep in dependencies_for_task):
                                if dependent_task.status == 'todo':
                                    dependent_task.status = 'inprogress'
                                    dependent_task.start_date = datetime.now().date()
                                    dependent_task.save()
                                    print(f'Changed status of the task{dependent_task.id} due to or comdition')
                                phase_start_subtasks = ProjectPhaseTask.objects.filter(
                                    parent_id=dependent_task,
                                    dependent_task_type='phasestarttime'
                                )
                                print(phase_start_subtasks, "These are the phase start subtasks")

                                
                                for subtask in phase_start_subtasks:
                                    if subtask.status != 'complete':
                                        subtask.status = 'inprogress'
                                        subtask.start_date = timezone.now().date()
                                        subtask.save()

                #------------------------ TASK INPROGRESS ------------------------------------------------------
                            
                if new_status == 'inprogress':
                    phase_start_subtasks = ProjectPhaseTask.objects.filter(
                        parent_id=instance,
                        dependent_task_type='phasestarttime'
                    )
                    print(phase_start_subtasks, "These are the phase start subtasks")

                    
                    for subtask in phase_start_subtasks:
                        if subtask.status != 'complete':
                            subtask.status = 'inprogress'
                            subtask.start_date = timezone.now().date()
                            subtask.save()
                    print("phase start subtasks", phase_start_subtasks)
                    instance.start_date = datetime.now().date()
                    instance.end_date = None
                    parent_task = instance.parent_id           
                    if parent_task:
                        parent_task.status = 'inprogress'
                        start_date = parent_task.start_date
                        if not start_date:
                            parent_task.start_date = datetime.now().date()
                        parent_task.save()
                    

                    phase_start_confirmation = self.request.data.get('phase_start_confirmation')

                    if phase_start_confirmation == 'True':
                        project_phase = instance.project_phase_id
                        project = instance.project_phase_id.project_id

                        if project_phase:
                            with transaction.atomic():
                                project_phase.start_date = datetime.now().date()
                                project_phase.phase_status = 'inprogress'
                                project_start_date = project.start_date
                                if not project_start_date:
                                    project.start_date = timezone.now()
                                project_phase.save()

                                
                                phase_start_tasks = ProjectPhaseTask.objects.filter(
                                    project_phase_id=project_phase.id,
                                    dependent_task_type='phasestarttime'
                                )

                                for task in phase_start_tasks:
                                    parent_dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task.parent_id)

                                    if not parent_dependencies.exists() or all(
                                        ProjectPhaseTask.objects.get(id=dep.dependent_task_id.id).status == 'complete'
                                        for dep in parent_dependencies
                                    ):
                                        task.status = 'inprogress'
                                        task.start_date = timezone.now().date()
                                        task.save()

                    else:
                        instance.status = 'inprogress'
                        instance.project_phase_id.phase_status = 'inprogress'
                        phase_start_date = instance.project_phase_id.start_date
                        if not phase_start_date:
                            instance.project_phase_id.start_date = datetime.now().date()
                
                elif new_status == 'complete':
                    required_tasks = TaskFields.objects.filter(task_id=instance.id, is_required=True)
                    print("Line 975",required_tasks)
                    for task in required_tasks:
                        location_id = instance.project_phase_id.project_id.location_id.id
                        fields = LocationFields.objects.get(location_id=location_id, field_id= task.field_id)
                        print("Line 979",fields)
                        print("Line 981",fields)
                        if not fields.value:
                            return Response({'status_code':659, 'error':'Please fill the required task fields'}, status=500)
                            
                    instance.end_date = datetime.now().date()
                    instance.completed_by = user
                else:
                    instance.start_date = None
                    instance.end_date = None
                    
                if new_status == 'complete':
                    required_tasks = TaskFields.objects.filter(task_id=instance.id, is_required=True)
                    print("Line 981",required_tasks)
                    for task in required_tasks:
                        location_id = instance.project_phase_id.project_id.location_id.id
                        fields = LocationFields.objects.get(location_id=location_id, field_id= task.field_id)
                        print("Line 985",fields)
                        print("Line 987",fields)
                        if not fields.value:
                            return Response({'status_code':659, 'error':'Please fill the required task fields'}, status=500)

                self.perform_update(serializer)
                phase = instance.project_phase_id
                all_tasks_complete = phase.projectphasetask_set.filter(status='complete').count() == phase.projectphasetask_set.count()

                phase.phase_status = 'complete' if all_tasks_complete else 'inprogress'
                phase.end_date = None if not all_tasks_complete else datetime.now().date()
                if not all_tasks_complete and phase.phase_status == "inprogress":
                    phase.start_date = phase.start_date
                    phase.end_date = None
                phase.save()

                project = instance.project_phase_id.project_id
                all_phase_complete = project.projectphase_set.filter(phase_status='complete').count() == project.projectphase_set.count()

                project.project_status = 'complete' if all_phase_complete else 'inprogress'
                project.end_date = None if not all_phase_complete else datetime.now().date() #newly added
                if not all_phase_complete and project.project_status == "inprogress":
                    project.end_date = None
                project.save()

                location = instance.project_phase_id.project_id.location_id
                projects_in_location = Project.objects.filter(location_id=location)
                project_complete = projects_in_location.filter(project_status='complete')

                location.location_status = 'operating' if project_complete else 'projectmanagement'
                location.current_phase_id = phase
                location.current_phase = phase.phase_name
                location.current_phase_status = phase.phase_status
                location.operating_date = timezone.now().date()
                location.save()

                return Response({'projectPhaseTaskStatus': serializer.data})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)



class ProjectPhaseTaskAssignee(generics.UpdateAPIView):
    queryset = ProjectPhaseTask.objects.all()
    serializer_class = ProjectTaskAssigneeSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            user = request.user
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
            if not user.is_admin and not partner_admin_user:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.validated_data['assigned_at'] = timezone.now()
            self.perform_update(serializer)

            
            assigned_to_partner = instance.assigned_to
            if assigned_to_partner:
                partner_admins = assigned_to_partner.user_set.filter(partner_admin=True)
                for partner_admin in partner_admins:
                    assigned_task_name = instance.title
                    fullname = f"{request.user.firstname} {request.user.lastname}"
                    notification = Notification(
                        user_id=partner_admin.id,
                        subject='Partner - Project Management',
                        body=assigned_task_name,
                        data_id=instance.project_phase_id.project_id.id,  
                        data_name=instance.project_phase_id.project_id.name, 
                        assigned_by_id=request.user.id,
                        assigned_by_name=fullname,
                        location_name=instance.project_phase_id.project_id.location_id.name, 
                        created_at=timezone.now()
                    )
                    notification.save()

            return Response({'projectPhaseTaskAssignDetails': serializer.data})
        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class ProjectPhaseTaskCustomerAssign(generics.UpdateAPIView):
   queryset = ProjectPhaseTask.objects.all()
   serializer_class = ProjectTaskCustomerAssignSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = request.user
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
           if not user.is_admin and not partner_admin_user:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           
           instance = self.get_object()
           if not user.is_admin:
               partner = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
               if instance.assigned_to != partner:
                   return Response({"error":"This task is not assigned to your partner"}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           serializer.validated_data['assigned_at'] = timezone.now()
           self.perform_update(serializer)
           
           assigned_to_user = instance.assigned_to_user
           if assigned_to_user:
                assigned_task_name = instance.title
                fullname = f"{request.user.firstname} {request.user.lastname}"
                notification = Notification(
                    user_id=assigned_to_user.id,
                    subject='Customer - Project Management',
                    body=assigned_task_name,
                    data_id=instance.project_phase_id.project_id.id,  
                    data_name=instance.project_phase_id.project_id.name, 
                    assigned_by_id=request.user.id,
                    assigned_by_name=fullname,
                    location_name=instance.project_phase_id.project_id.location_id.name, 
                    created_at=timezone.now()
                )
                notification.save()
           return Response({'projectPhaseTaskCustomerAssignDetails':serializer.data})
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class ProjectPhaseTaskGeneral(generics.UpdateAPIView):
    queryset = ProjectPhaseTask.objects.all()
    serializer_class = ProjectPhaseTaskSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            user = request.user
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id =user, is_admin=True)
            if not user.is_admin and not partner_admin_user:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()
            updated_fields = []

            if 'title' in request.data and instance.title != request.data['title']:
                updated_fields.append('title')

            if 'description' in request.data and instance.description != request.data['description']:
                updated_fields.append('description')

            if updated_fields:
                user_instance = user
                updated_at = datetime.now()

                for field_name in updated_fields:
                    column_name = field_name
                    task_update = TaskUpdate.objects.create(task_id=instance,user_id=user_instance, column_name=column_name, updated_date=updated_at)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            response_data = {
                'title': instance.title,
                'description': instance.description,
                'priority_level':instance.priority_level,
            }

            return Response({'projectPhaseGeneralDetails': response_data})
        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ProjectPhaseTaskEstimation(generics.UpdateAPIView):
    queryset = ProjectPhaseTask.objects.all()
    serializer_class = ProjectPhaseTaskSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            user = request.user
            if not user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            
            phase = instance.project_phase_id
            total_cost = phase.projectphasetask_set.aggregate(models.Sum('cost_estimations_pv'))['cost_estimations_pv__sum']

            
            phase.phase_estimation = total_cost
            phase.save()
            
            project = instance.project_phase_id.project_id
            project_cost = project.projectphase_set.aggregate(models.Sum('phase_estimation'))['phase_estimation__sum']

            
            project.project_estimation = project_cost
            project.save()

            response_data = {
                'cost_estimations_pv': instance.cost_estimations_pv,
            }
            return Response({'projectPhaseEstimationDetails': response_data})
        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class ProjectPhaseTaskDependencyUpdate(generics.UpdateAPIView):
    queryset = ProjectPhaseTask.objects.all()
    serializer_class = ProjectPhaseTaskSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        user = request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin=True)
        if not user.is_admin and not partner_admin_user:
            return Response({'status_code':605, 'error':'you do not have permission to perform this action'}, status=500)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            dependent_task_ids = request.data.get('dependent_task_id', [])
            condition = request.data.get('condition')       
            if condition == 'or' and len(dependent_task_ids) < 2:
                return Response({'status_code':655, 'error': 'Please add at least two tasks for "or" condition.'}, status=status.HTTP_400_BAD_REQUEST)

            ProjectPhaseTaskDependency.objects.filter(task_id=instance).delete()

            dependency_instances = [] 

            for task_id in dependent_task_ids:
                dependency_data = {
                    'task_id': instance.id,
                    'dependent_task_id': task_id,
                    'condition': condition,
                }
                dependency_serializer = ProjectPhaseTaskDependencySerializer(data=dependency_data)
                dependency_serializer.is_valid(raise_exception=True)
                dependency_instance = dependency_serializer.save()
                dependency_instances.append(dependency_instance)

            return Response({'projectPhaseTaskDetails': serializer.data})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectPhaseTaskDelete(generics.DestroyAPIView):
   queryset = ProjectPhaseTask.objects.all()
   serializer_class = ProjectPhaseTaskSerializer
   permission_classes = (IsAuthenticated,)
    
   def destroy(self, request, *args, **kwargs):
        try:
            user = request.user
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin=True)
            instance = self.get_object()
            if not user.is_admin and not partner_admin_user:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            
            
            dependent_tasks = ProjectPhaseTaskDependency.objects.filter(dependent_task_id=instance.id)
            
            if dependent_tasks.count() > 0:
                dependent_task_info = [{'id': dep.task_id.id, 'name': dep.task_id.title} for dep in dependent_tasks]
                message = f"This task has been added as a dependent task. Please remove the dependencies and try again."
                return Response({'status_code': 653, 'error': message, 'taskDetail': dependent_task_info}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            
            self.perform_destroy(instance)
            
            ProjectPhaseTask.objects.filter(parent_id=instance.parent_id, order_number__gt=instance.order_number).update(
                order_number=F('order_number') - 1
            )
            return Response({'message': 'ProjectPhaseTask deleted successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectPhaseTaskDetail(generics.RetrieveAPIView):
    queryset = ProjectPhaseTask.objects.all()
    serializer_class = ProjectPhaseTaskSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    

    
# class ProjectPhaseTaskDetail(generics.RetrieveAPIView):
#     queryset = ProjectPhaseTask.objects.all()
#     serializer_class = ProjectPhaseTaskSerializer
#     permission_classes = (IsAuthenticated,)

#     def retrieve(self, request, *args, **kwargs):
#         user = request.user
#         queryset = self.get_queryset()
#         partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
#         partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
#         if user.is_customer:
#             if partner_admin_user:
#                 task_ids = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('id', flat=True).distinct()
#                 queryset = self.get_queryset().filter(id__in = task_ids)
#                 serializer = ProjectPhaseTaskSerializer(queryset, many=True)
#                 return Response(serializer.data)
#             else:
#                 project_id = ProjectPhaseTask.objects.filter(assigned_to_user=user).values_list('project_phase_id__project_id', flat=True).distinct()
#                 queryset = self.get_queryset().filter(id__in = project_id)
#                 serializer = ProjectPhaseTaskSerializer(queryset, many=True)
#                 return Response(serializer.data)
            
#         elif user.is_admin:
#             instance = self.get_object()
#             serializer = self.get_serializer(instance)
#             task_updates = instance.taskupdate_set.all()
#             task_update_serializer = TaskUpdateListSerializer(task_updates, many=True)
#             serializer.data['task_updates'] = task_update_serializer.data
#             response_data = serializer.data.copy()
#             response_data['task_updates'] = task_update_serializer.data
#             return Response(response_data)
#         else:
#             raise PermissionDenied()
#------------------------------------------- Project phase task files ----------------------------------------------------------------


class ProjectPhasesTaskFileCreate(generics.CreateAPIView):
    queryset = ProjectPhasesTaskFile.objects.all()
    serializer_class = ProjectPhaseTaskFileSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        project_phase_id = self.kwargs.get('project_phase_id')
        project_phase_task_id = self.kwargs.get('project_phase_task_id')

        try:
            project_phase = ProjectPhase.objects.get(id=project_phase_id)
            project_phase_task = ProjectPhaseTask.objects.get(id=project_phase_task_id)
        except ProjectPhase.DoesNotExist:
            return Response({'error': f"Project Phase with ID {project_phase_id} does not exist."}, status=400)
        except ProjectPhaseTask.DoesNotExist:
            return Response({'error': f"Project Phase Task with ID {project_phase_task_id} does not exist."}, status=400)

        if project_phase_task.project_phase_id != project_phase:
            return Response({'status_code': 656, 'error': "Project Phase and Task are not assigned to each other."}, status=400)

        response_data = []
        max_file_size = 25 *1024 *1024
        for file_data in request.data.getlist('file_url'):
            file_size = file_data.size if hasattr(file_data, 'size') else len(file_data)
            if file_size > max_file_size:
                return Response({'status_code':657, 'error':'File size should be less than 25MB'}, status = 400)
                
            mutable_request_data = request.data.copy()
            mutable_request_data['project_phase_id'] = project_phase_id
            mutable_request_data['project_phase_task_id'] = project_phase_task_id
            mutable_request_data['file_url'] = file_data
            
            

            serializer = self.get_serializer(data=mutable_request_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)


            user_instance = request.user
            column_name = 'file_upload'
            updated_at = timezone.now()
            task_update = TaskUpdate.objects.create(
                task_id=project_phase_task,
                user_id=user_instance,
                column_name=column_name,
                updated_date=updated_at
            )

            response_data.append(serializer.data)

        return Response({'projectPhasesTaskFileDetails': response_data})

class ProjectPhasesTaskFileDelete(generics.DestroyAPIView):
   queryset = ProjectPhasesTaskFile.objects.all()
   permission_classes = (IsAuthenticated,)

   def delete(self, request, *args, **kwargs):
       project_phase_id = self.kwargs.get('project_phase_id')
       project_phase_task_id = self.kwargs.get('project_phase_task_id')
       file_id = self.kwargs.get('file_id')

       project_phases_task_file = get_object_or_404(ProjectPhasesTaskFile, id=file_id, project_phase_id=project_phase_id, project_phase_task_id=project_phase_task_id)
       user_instance = request.user
       column_name = 'file_delete'
       updated_at = timezone.now()
       task_id = ProjectPhaseTask.objects.get(id=project_phase_task_id)
       task_update = TaskUpdate.objects.create(
            task_id=task_id,
            user_id=user_instance,
            column_name=column_name,
            updated_date=updated_at
        )
       project_phases_task_file.delete()
       

       return Response({'message': 'File deleted successfully'})
   

# #-------------------------------------- PROJECT TEMPLATES VIEWS ----------------------------------------------------------------------
class ProjectTemplateCreate(generics.CreateAPIView):
    serializer_class = ProjectTemplateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       
        template_type = serializer.validated_data.get('template_type')
        instance = serializer.save()
        target_count = self.request.data.get('target_count')
        target_duration = self.request.data.get('target_duration')
       
        if template_type == 'phase':
            ProjectPhaseTemplate.objects.create(template_id=instance, target_count= target_count, target_duration=target_duration,  phase_name="Phase-1",  order_number=1)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        project_phases = request.data.get('project_phases', [])
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                instance = serializer.save()
                
                max_order_number = ProjectPhaseTemplate.objects.filter(template_id=instance).aggregate(Max('order_number'))
                order_number_counter = max_order_number['order_number__max'] + 1 if max_order_number['order_number__max'] is not None else 1


                
                task_id_mapping = {}
                parent_task_mapping ={}

                
                for phase_id in project_phases:
                    source_template = ProjectTemplate.objects.get(id=phase_id)

                    for source_phase in source_template.projectphasetemplate_set.all():
                        project_phase_template = ProjectPhaseTemplate.objects.create(
                            template_id=instance,
                            phase_name=source_phase.phase_name,
                            order_number=order_number_counter,
                            target_count = source_phase.target_count,
                            target_duration = source_phase.target_duration
                        )
                        order_number_counter += 1

                        for source_task_template in source_phase.projectphasetasktemplate_set.all():
                            project_phase_task_template = ProjectPhaseTaskTemplate(
                                project_phases_template_id=project_phase_template,
                                title=source_task_template.title,
                                description=source_task_template.description,
                                order_number=source_task_template.order_number,
                                is_dependent=source_task_template.is_dependent,
                                dependent_task_type=source_task_template.dependent_task_type,
                                priority_level=source_task_template.priority_level,
                                expected_count=source_task_template.expected_count,
                                expected_duration=source_task_template.expected_duration,
                                dependent_count = source_task_template.dependent_count,
                                dependent_duration = source_task_template.dependent_duration,
                                assigned_to_type = source_task_template.assigned_to_type if source_task_template.assigned_to_type else None
                            )
                            if source_task_template.parent_id:
                                parent_task = parent_task_mapping.get(source_task_template.parent_id.id)
                                if parent_task:
                                    project_phase_task_template.parent_id = parent_task
                            project_phase_task_template.save()
                            task_id_mapping[source_task_template.id] = project_phase_task_template.id
                            parent_task_mapping[source_task_template.id] = project_phase_task_template
                            task_template_checklists = TaskTemplateCheckList.objects.filter(task_id=source_task_template)
                            for checklist in task_template_checklists:
                                new_checklist = TaskTemplateCheckList(
                                    task_id=project_phase_task_template,
                                    checklist_id=checklist.checklist_id,
                                    checklist_item_id=checklist.checklist_item_id
                                )
                                new_checklist.save()
                                checklist_items = TaskTemplateCheckListItems.objects.filter(tasktemplatechecklist_id=checklist)
                                for item in checklist_items:
                                    new_item = TaskTemplateCheckListItems(
                                        taskchecklist_id=new_checklist,
                                        checklistitems_id=item.checklistitems_id,
                                        is_checked=item.is_checked,
                                        checked_by=item.checked_by
                                    )
                                    new_item.save()
                                
                                task_template_fields = TemplateTaskFields.objects.filter(task_id=source_task_template)
                                for taskfields in task_template_fields:
                                    task_fields = TemplateTaskFields.objects.create(
                                        task_id=project_phase_task_template,
                                        project_id=project_phase_task_template.project_phases_template_id.template_id,
                                        field_id=taskfields.field_id,
                                        is_required = taskfields.is_required
                                    )
                            
                        for source_phase in source_template.projectphasetemplate_set.all():
                            for source_task_template in source_phase.projectphasetasktemplate_set.all():
                                if source_task_template.parent_id:
                                    new_parent_id = task_id_mapping.get(source_task_template.parent_id.id)
                                    if new_parent_id:
                                        ProjectPhaseTaskTemplate.objects.filter(id=task_id_mapping[source_task_template.id]).update(
                                            parent_id=new_parent_id)
                                        
                                new_task_id = task_id_mapping.get(source_task_template.id)

                                if new_task_id is not None:
                                    for source_dependency in source_task_template.task_templates.all():
                                        new_dependent_task_id = task_id_mapping.get(source_dependency.dependent_task_id.id)

                                        if new_dependent_task_id is not None:
                                            ProjectPhaseTaskTemplateDependency.objects.get_or_create(
                                                task_id=ProjectPhaseTaskTemplate.objects.get(id=new_task_id),
                                                dependent_task_id=ProjectPhaseTaskTemplate.objects.get(id=new_dependent_task_id),
                                                condition=source_dependency.condition
                                            )
            self.perform_create(serializer)
            return Response({'projectTemplateDetails':serializer.data})
        except ValidationError as error:
           return Response({'error':error.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectTemplateUpdate(generics.UpdateAPIView):
   queryset = ProjectTemplate.objects.all()
   serializer_class = ProjectTemplateSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           if user.is_admin:
               instance = serializer.save()
               return Response({'projectTemplateDetails':serializer.data})
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       

class ProjectTemplateList(generics.CreateAPIView):
    serializer_class = ProjectTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        template_type = self.request.data.get('template_type')
        queryset = ProjectTemplate.objects.all().order_by('id')

        if template_type:
            queryset = queryset.filter(template_type=template_type, status='published')

        return queryset

    def post(self, request, *args, **kwargs):
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        user = request.user
        if not user.is_admin and not partner_admin_user:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectTemplateList': serializer.data}
        return Response(response_data)



    
class ProjectTemplateDetail(generics.RetrieveDestroyAPIView):
   queryset = ProjectTemplate.objects.all()
   serializer_class = ProjectTemplateDetailSerializer
   permission_classes = (IsAuthenticated,)

   def retrieve(self, request, *args, **kwargs):
       partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
       if not request.user.is_admin and not partner_admin_user:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({'projectTemplateDetails':serializer.data})
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           self.perform_destroy(instance)
           return Response({'message': 'Project template deleted successfully'})
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
       
#---------------------------------------- PROJECT TEMPLATE PHASE VIEWS ---------------------------------------------------------------

class ProjectPhaseTemplateCreate(generics.CreateAPIView):
    serializer_class = ProjectPhaseTemplateCreateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        try:
            template_id = self.kwargs.get('template_id')

            phase_name = request.data.get('phase_name')
            target_count = request.data.get('target_count')
            target_duration = request.data.get('target_duration')
            template_ids = request.data.get('project_phases', [])

            target_template, created = ProjectTemplate.objects.get_or_create(id=template_id)
            if created:
                target_template.name = phase_name
                target_template.save()

            source_templates = ProjectTemplate.objects.filter(id__in=template_ids)
            source_phase_templates = ProjectPhaseTemplate.objects.filter(template_id__in=template_ids)

            max_order_number = target_template.projectphasetemplate_set.aggregate(models.Max('order_number'))['order_number__max']
            if max_order_number is None:
                max_order_number = 0

            created_phase_templates = []

            task_id_mapping = {}
            parent_task_mapping = {}

            for source_template in source_templates:
                source_phase_templates = ProjectPhaseTemplate.objects.filter(template_id=source_template.id)
                for source_phase_template in source_phase_templates:
                    max_order_number += 1  
                    phase_template = ProjectPhaseTemplate.objects.create(
                        template_id=target_template,
                        phase_name=source_phase_template.phase_name,
                        target_count=source_phase_template.target_count,
                        target_duration=source_phase_template.target_duration,
                        order_number=max_order_number
                    )
                    created_phase_templates.append(phase_template)

                    source_task_templates = ProjectPhaseTaskTemplate.objects.filter(
                        project_phases_template_id=source_phase_template.id)

                    for source_task_template in source_task_templates:
                        project_phase_task_template = ProjectPhaseTaskTemplate(
                            project_phases_template_id=phase_template,
                            title=source_task_template.title,
                            description=source_task_template.description,
                            order_number=source_task_template.order_number,
                            is_dependent=source_task_template.is_dependent,
                            dependent_task_type=source_task_template.dependent_task_type,
                            priority_level=source_task_template.priority_level,
                            expected_count=source_task_template.expected_count,
                            expected_duration=source_task_template.expected_duration,
                            dependent_count = source_task_template.dependent_count,
                            dependent_duration = source_task_template.dependent_duration,
                            assigned_to_type=source_task_template.assigned_to_type if source_task_template.assigned_to_type else None
                        )

                        if source_task_template.parent_id:
                            parent_task = parent_task_mapping.get(source_task_template.parent_id.id)
                            if parent_task:
                                project_phase_task_template.parent_id = parent_task
                        project_phase_task_template.save()
                        task_id_mapping[source_task_template.id] = project_phase_task_template.id
                        parent_task_mapping[source_task_template.id] = project_phase_task_template
                        task_template_checklists = TaskTemplateCheckList.objects.filter(task_id=source_task_template)
                        for checklist in task_template_checklists:
                            new_checklist = TaskTemplateCheckList(
                                task_id=project_phase_task_template,
                                checklist_id=checklist.checklist_id,
                                checklist_item_id=checklist.checklist_item_id
                            )
                            new_checklist.save()
                            checklist_items = TaskTemplateCheckListItems.objects.filter(tasktemplatechecklist_id=checklist)
                            for item in checklist_items:
                                new_item = TaskTemplateCheckListItems(
                                    taskchecklist_id=new_checklist,
                                    checklistitems_id=item.checklistitems_id,
                                    is_checked=item.is_checked,
                                    checked_by=item.checked_by
                                )
                                new_item.save()
                            
                            task_template_fields = TemplateTaskFields.objects.filter(task_id=source_task_template)
                            for taskfields in task_template_fields:
                                task_fields = TemplateTaskFields.objects.create(
                                    task_id=project_phase_task_template,
                                    project_id=project_phase_task_template.project_phases_template_id.template_id,
                                    field_id=taskfields.field_id,
                                    is_required = task_fields.is_required
                                )
                        
                    for source_phase in source_template.projectphasetemplate_set.all():
                        for source_task_template in source_phase.projectphasetasktemplate_set.all():
                            if source_task_template.parent_id:
                                new_parent_id = task_id_mapping.get(source_task_template.parent_id.id)
                                if new_parent_id:
                                    ProjectPhaseTaskTemplate.objects.filter(id=task_id_mapping[source_task_template.id]).update(
                                        parent_id=new_parent_id)
                                    
                            new_task_id = task_id_mapping.get(source_task_template.id)

                            if new_task_id is not None:
                                for source_dependency in source_task_template.task_templates.all():
                                    new_dependent_task_id = task_id_mapping.get(source_dependency.dependent_task_id.id)

                                    if new_dependent_task_id is not None:
                                        ProjectPhaseTaskTemplateDependency.objects.get_or_create(
                                            task_id=ProjectPhaseTaskTemplate.objects.get(id=new_task_id),
                                            dependent_task_id=ProjectPhaseTaskTemplate.objects.get(id=new_dependent_task_id),
                                            condition=source_dependency.condition
                                        )

            if not template_ids:
                max_order_number += 1  
                phase_template = ProjectPhaseTemplate.objects.create(
                    template_id=target_template,
                    phase_name=phase_name,
                    target_count=target_count,
                    target_duration=target_duration,
                    order_number=max_order_number
                )
                created_phase_templates.append(phase_template)

            serializer = self.get_serializer(created_phase_templates, many=True)

            return Response({'projectPhaseTemplateDetails': serializer.data}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
class ProjectPhaseTemplateUpdate(generics.UpdateAPIView):
   queryset = ProjectPhaseTemplate.objects.all().order_by('id')
   serializer_class = ProjectPhaseTemplateSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           if 'order_number' in request.data and instance.order_number != int(request.data['order_number']):
                new_order_number = int(request.data['order_number'])

                if instance.order_number is not None:
                    old_order_number = instance.order_number

                    with transaction.atomic():
                        if new_order_number < old_order_number:
                            ProjectPhaseTemplate.objects.filter(
                                template_id=instance.template_id,
                                order_number__gte=new_order_number,
                                order_number__lt=old_order_number
                            ).exclude(id=instance.id).update(order_number=models.F('order_number') + 1)
                        else:
                            ProjectPhaseTemplate.objects.filter(
                                template_id=instance.template_id,
                                order_number__gt=old_order_number,
                                order_number__lte=new_order_number
                            ).exclude(id=instance.id).update(order_number=models.F('order_number') - 1)

                instance.order_number = new_order_number
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           if user.is_admin:
               instance = serializer.save()
               return Response({'projectPhaseTemplateDetails':serializer.data})
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)



class ProjectPhaseTemplateDelete(generics.DestroyAPIView):
   queryset = ProjectPhaseTemplate.objects.all()
   permission_classes = (IsAuthenticated,)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           
           deleted_order_number = instance.order_number

           with transaction.atomic():
                self.perform_destroy(instance)
                
                ProjectPhaseTemplate.objects.filter(
                    template_id=instance.template_id,
                    order_number__gt=deleted_order_number
                ).update(order_number=F('order_number') - 1)
           return Response({'message': 'Project template deleted successfully'})
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
       
class ProjectPhaseTemplateDetail(generics.RetrieveAPIView):
    queryset = ProjectPhaseTemplate.objects.all()
    serializer_class = ProjectPhaseTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = serializer.data

       
        return Response(response_data)
       
#--------------------------------------------- PROJECT PHASE TASK TEMPLATE VIEWS ------------------------------------------------------

class ProjectPhaseTaskTemplateCreate(generics.CreateAPIView):
    queryset = ProjectPhaseTaskTemplate.objects.all()
    serializer_class = ProjectPhaseTaskTemplateSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        try:
            project_phases_template_id = kwargs.get('project_phases_template_id')
            parent_id = request.data.get('parent_id')

            if parent_id:
                max_order_number = ProjectPhaseTaskTemplate.objects.filter(
                    project_phases_template_id=project_phases_template_id,
                    parent_id=parent_id
                ).aggregate(Max('order_number'))['order_number__max']
                new_order_number = 1 if max_order_number is None else max_order_number + 1
            else:
                max_order_number = ProjectPhaseTaskTemplate.objects.filter(
                    project_phases_template_id=project_phases_template_id
                ).aggregate(Max('order_number'))['order_number__max']
                new_order_number = 1 if max_order_number is None else max_order_number + 1

            mutable_request_data = request.data.copy()
            mutable_request_data['project_phases_template_id'] = project_phases_template_id
            mutable_request_data['order_number'] = new_order_number
            serializer = self.get_serializer(data=mutable_request_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            task_id = serializer.data['id']  # Get the newly created task_id
            dependent_task_ids = mutable_request_data.get('dependent_task_id', [])
            condition = mutable_request_data.get('condition')
            
            if condition == 'or' and len(dependent_task_ids) < 2:
                return Response({'status_code':655, 'error': 'Please add at least two tasks for "or" condition.'}, status=status.HTTP_400_BAD_REQUEST)

            dependency_instances = []

            for dependent_task_id in dependent_task_ids:
                dependency_data = {
                    'task_id': task_id,
                    'condition': condition,
                    'dependent_task_id': dependent_task_id,
                }
                dependency_serializer = ProjectPhaseTaskDependencyTemplateSerializer(data=dependency_data)
                dependency_serializer.is_valid(raise_exception=True)
                dependency_instance = dependency_serializer.save()
                dependency_instances.append(dependency_instance)

            response_data = {'projectPhaseTaskDetails': serializer.data}

            if dependency_instances:
                dependency_details = []
                for dependency_instance in dependency_instances:
                    dependency_details.append({
                        'id': dependency_instance.id,
                        'task_id': dependency_instance.task_id.id,
                        'condition': dependency_instance.condition,
                        'dependent_task_id': dependency_instance.dependent_task_id.id,
                    })
                response_data['dependencyDetails'] = dependency_details

            return Response({'projectPhaseTaskTemplateDetails': response_data})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

 
class ProjectPhaseTaskTemplateUpdate(generics.UpdateAPIView):
    queryset = ProjectPhaseTaskTemplate.objects.all()
    serializer_class = ProjectPhaseTaskTemplateSerializer
    permission_classes = (IsAuthenticated,)


    def update(self, request, *args, **kwargs):
        user = self.request.user
        if not user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        # try:
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        dependent_task_ids = request.data.get('dependent_task_id', [])
        condition = request.data.get('condition')
            
        if condition == 'or' and len(dependent_task_ids) < 2:
            return Response({'status_code':655, 'error': 'Please add at least two tasks for "or" condition.'}, status=status.HTTP_400_BAD_REQUEST)

        ProjectPhaseTaskTemplateDependency.objects.filter(task_id=instance).delete()

        dependency_instances = []
        for task_id in dependent_task_ids:
            dependency_data = {
                'task_id': instance.id,
                'dependent_task_id': task_id,
                'condition': request.data.get('condition'), 
            }
            dependency_serializer = ProjectPhaseTaskDependencyTemplateSerializer(data=dependency_data)
            dependency_serializer.is_valid(raise_exception=True)
            dependency_instance = dependency_serializer.save()
            dependency_instances.append(dependency_instance)

        return Response({'projectPhaseTaskTemplateDetails': serializer.data})



class ProjectPhaseTaskTemplateDelete(generics.DestroyAPIView):
   queryset = ProjectPhaseTaskTemplate.objects.all()
   permission_classes = (IsAuthenticated,)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           
           dependent_tasks = ProjectPhaseTaskTemplateDependency.objects.filter(dependent_task_id=instance.id)
             
           if dependent_tasks.count() > 0:
                    dependent_task_info = [{'id': dep.task_id.id, 'name': dep.task_id.title} for dep in dependent_tasks]
                    message = f"This task has been added as a dependent task. Please remove the dependencies and try again."
                    return Response({'status_code': 653, 'error': message, 'taskDetail': dependent_task_info}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
           self.perform_destroy(instance)
           ProjectPhaseTaskTemplate.objects.filter(parent_id=instance.parent_id, order_number__gt=instance.order_number).update(
                    order_number=F('order_number') - 1
                )
        
           return Response({'message': 'Template Task deleted successfully'})
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
       
       
class ProjectPhaseTaskTemplateDetail(generics.RetrieveAPIView):
    queryset = ProjectPhaseTaskTemplate.objects.all()
    serializer_class = ProjectPhaseTaskTemplateSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

#-------------------------------- CREATE PROJECT PHASE AND TASKS AFTER CREATING THE PROJECT -----------------------------------------
class ProjectTemplateCreateAfterProject(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, project_id, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_id)
        template_id = request.data.get('template_id')

        try:
            project_template = ProjectTemplate.objects.get(pk=template_id)
        except ProjectTemplate.DoesNotExist:
            return Response({'error': 'Template not found'}, status=status.HTTP_400_BAD_REQUEST)

        phase_templates = project_template.projectphasetemplate_set.all()
        for phase_template in phase_templates:
            new_phase = ProjectPhase(phase_name=phase_template.phase_name, project_id=project)
            new_phase.save()

            task_templates = phase_template.projectphasetasktemplate_set.all()
            for task_template in task_templates:
                new_task = ProjectPhaseTask(
                    title=task_template.title,
                    description=task_template.description,
                    project_phase_id=new_phase,
                    assigned_by = self.request.user 
                )
                new_task.save()

        serializer = ProjectSerializer(project)
        response_data = serializer.data

        return Response({'message': 'Project phases and tasks created from template', 'projectDetails': response_data}, status=status.HTTP_201_CREATED)


#------------------------------------------------ CREATE PHASES TEMPLATE AND TASKS GET LIST --------------------------------------------

class ProjectTemplateTaskList(generics.ListAPIView):
    serializer_class = ProjectTemplateTaskGetSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        template_id = self.kwargs['template_id']
        return ProjectPhaseTaskTemplate.objects.filter(project_phases_template_id__template_id=template_id).order_by('order_number')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectTaskTemplateList': serializer.data}
        return Response(response_data)
    
class PhaseTemplateTaskList(generics.ListAPIView):
    serializer_class = ProjectTemplateTaskGetSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        phase_template_id = self.kwargs['phase_id']
        return ProjectPhaseTaskTemplate.objects.filter(project_phases_template_id=phase_template_id).order_by('order_number')

    def list(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectTaskTemplateList': serializer.data}
        return Response(response_data)
    

class ProjectTaskGetList(generics.ListAPIView):
    serializer_class = ProjectPhaseTaskGetSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        user = self.request.user 
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        if user.is_admin:
            return ProjectPhaseTask.objects.filter(project_phase_id__project_id=project_id).order_by('order_number')
        elif user.is_customer:
            if partner_admin_user:
                return ProjectPhaseTask.objects.filter(project_phase_id__project_id=project_id, assigned_to__in=partner_ids)
            else:
                return ProjectPhaseTask.objects.filter(project_phase_id__project_id=project_id, taskassignedusers__user_id=user).order_by('order_number')
        else:
            raise PermissionDenied()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectTaskList': serializer.data}
        return Response(response_data)

class PhaseTaskGetList(generics.ListAPIView):
    serializer_class = ProjectPhaseTaskGetSerializer
    permission_classes = (IsAuthenticated,)

    
    def get_queryset(self):
        phase_id = self.kwargs['phase_id']
        user = self.request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        if user.is_admin:
            return ProjectPhaseTask.objects.filter(project_phase_id=phase_id)
        elif user.is_customer:
            if partner_admin_user:
                return ProjectPhaseTask.objects.filter(project_phase_id= phase_id, assigned_to__in=partner_ids)
            else:
                return ProjectPhaseTask.objects.filter(project_phase_id=phase_id, taskassignedusers__user_id=user).order_by('order_number')
        else:
            raise PermissionDenied()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectTaskList': serializer.data}
        return Response(response_data)
    
#-------------------------------------------------- PROJECT PHASE EXCEL LIST --------------------------------------------------------
    
# class ProjectPhaseExcelList(generics.ListAPIView):
#     queryset = Project.objects.all().order_by('id')
#     serializer_class = projectExcelSerializer
#     permission_classes = (IsAuthenticated,)
    
#     def list(self, request, *args, **kwargs): 
#         if not request.user.is_admin:
#             return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
#         queryset = self.filter_queryset(self.get_queryset())
#         serializer = self.get_serializer(queryset, many = True)
#         response_data = {'projectPhaseExcelList':serializer.data}
#         return Response(response_data)


class ProjectPhaseExcelList(generics.ListAPIView):
    serializer_class = projectExcelSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return Project.objects.all().order_by('id')

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user
        if not user.is_admin:
            raise PermissionDenied()
        project_status = self.request.data.get('project_status')
        location_id = self.request.data.get('location_id')
        location_status = self.request.data.get('location_status')
        #EV Filters
        status_ev_id   = self.request.data.get('status_ev_id')
        milestone_date = self.request.data.get('milestone_date')
        parking_spots = self.request.data.get('parking_spots')
        planned_ac = self.request.data.get('planned_ac')
        ac_speed = self.request.data.get('ac_speed')
        planned_dc = self.request.data.get('planned_dc')
        dc_speed = self.request.data.get('dc_speed')
        planned_battery = self.request.data.get('planned_battery')
        battery_speed = self.request.data.get('battery_speed')
        construction_year = self.request.data.get('construction_year')
        exp_installation_date = self.request.data.get('exp_installation_date')
        planned_installation_date = self.request.data.get('planned_installation_date')
        exp_operation_date = self.request.data.get('exp_operation_date')
        gep_ev = self.request.data.get('gep_ev')
        capex_spent_to_date = self.request.data.get('capex_spent_to_date')
        capex_total_expected = self.request.data.get('capex_total_expected')
        #PV Filters
        status_pv_id = self.request.data.get('status_pv_id')
        cos_pv = self.request.data.get('cos_pv')
        milestone_date_pv = self.request.data.get('milestone_date_pv')
        expected_kWp_pv = self.request.data.get('expected_kWp_pv')
        construction_year_pv = self.request.data.get('construction_year_pv')
        exp_installation_date_pv = self.request.data.get('exp_installation_date_pv')
        planned_installation_date_pv = self.request.data.get('planned_installation_date_pv')
        exp_operation_date_pv = self.request.data.get('exp_operation_date_pv')
        capex_spent_to_date_pv = self.request.data.get('capex_spent_to_date_pv')
        capex_total_expected_pv = self.request.data.get('capex_total_expected_pv')
        
        if project_status:
            queryset = queryset.filter(project_status=project_status)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        if location_status:
            queryset = queryset.filter(location_id__location_status=location_status)
        if status_ev_id:
            queryset = queryset.filter(location_id__status_ev_id=status_ev_id)

        if milestone_date:
            milestone_date_condition = self.request.data.get('milestone_date_condition')
            if milestone_date_condition:
                milestone_date = datetime.strptime(milestone_date, '%Y-%m-%d')
                milestone_date_condition = datetime.strptime(milestone_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__milestone_date__range=[milestone_date, milestone_date_condition])
            else:
                queryset = queryset.filter(location_id__milestone_date=milestone_date)
                
        if parking_spots:
            parking_spots_condition = self.request.data.get('parking_spots_condition')
            if parking_spots_condition == '<':
                queryset = queryset.filter(location_id__parking_spots__lt=parking_spots)
            elif parking_spots_condition == '>':
                queryset = queryset.filter(location_id__parking_spots__gt=parking_spots)
            elif parking_spots_condition == '<=':
                queryset = queryset.filter(location_id__parking_spots__lte=parking_spots)
            elif parking_spots_condition == '>=':
                queryset = queryset.filter(location_id__parking_spots__gte=parking_spots)
            else:
                queryset = queryset.filter(location_id__parking_spots=parking_spots)
                
        if planned_ac:
            planned_ac_condition = self.request.data.get('planned_ac_condition')
            if planned_ac_condition == '<':
                queryset = queryset.filter(location_id__planned_ac__lt=planned_ac)
            elif planned_ac_condition == '>':
                queryset = queryset.filter(location_id__planned_ac__gt=planned_ac)
            elif planned_ac_condition == '<=':
                queryset = queryset.filter(location_id__planned_ac__lte=planned_ac)
            elif planned_ac_condition == '>=':
                queryset = queryset.filter(location_id__planned_ac__gte=planned_ac)
            else:
                queryset = queryset.filter(location_id__planned_ac=planned_ac)
                
        if ac_speed:
            ac_speed_condition = self.request.data.get('ac_speed_condition')
            if ac_speed_condition == '<':
                queryset = queryset.filter(location_id__ac_speed__lt=ac_speed)
            elif ac_speed_condition == '>':
                queryset = queryset.filter(location_id__ac_speed__gt=ac_speed)
            elif ac_speed_condition == '<=':
                queryset = queryset.filter(location_id__ac_speed__lte=ac_speed)
            elif ac_speed_condition == '>=':
                queryset = queryset.filter(location_id__ac_speed__gte=ac_speed)
            else:
                queryset = queryset.filter(location_id__ac_speed=ac_speed)
                
        if planned_dc:
            planned_dc_condition = self.request.data.get('planned_dc_condition')
            if planned_dc_condition == '<':
                queryset = queryset.filter(location_id__planned_dc__lt=planned_dc)
            elif planned_dc_condition == '>':
                queryset = queryset.filter(location_id__planned_dc__gt=planned_dc)
            elif planned_dc_condition == '<=':
                queryset = queryset.filter(location_id__planned_dc__lte=planned_dc)
            elif planned_dc_condition == '>=':
                queryset = queryset.filter(location_id__planned_dc__gte=planned_dc)
            else:
                queryset = queryset.filter(location_id__planned_dc=planned_dc)
                
        if dc_speed:
            dc_speed_condition = self.request.data.get('dc_speed_condition')
            if dc_speed_condition == '<':
                queryset = queryset.filter(location_id__dc_speed__lt=dc_speed)
            elif dc_speed_condition == '>':
                queryset = queryset.filter(location_id__dc_speed__gt=dc_speed)
            elif dc_speed_condition == '<=':
                queryset = queryset.filter(location_id__dc_speed__lte=dc_speed)
            elif dc_speed_condition == '>=':
                queryset = queryset.filter(location_id__dc_speed__gte=dc_speed)
            else:
                queryset = queryset.filter(location_id__dc_speed=dc_speed)
                
        if planned_battery:
            planned_battery_condition = self.request.data.get('planned_battery_condition')
            if planned_battery_condition == '<':
                queryset = queryset.filter(location_id__planned_battery__lt=planned_battery)
            elif planned_battery_condition == '>':
                queryset = queryset.filter(location_id__planned_battery__gt=planned_battery)
            elif planned_battery_condition == '<=':
                queryset = queryset.filter(location_id__planned_battery__lte=planned_battery)
            elif planned_battery_condition == '>=':
                queryset = queryset.filter(location_id__planned_battery__gte=planned_battery)
            else:
                queryset = queryset.filter(location_id__planned_battery=planned_battery)
        if battery_speed:
            battery_speed_condition = self.request.data.get('planned_battery_condition')
            if battery_speed_condition == '<':
                queryset = queryset.filter(location_id__battery_speed__lt=battery_speed)
            elif battery_speed_condition == '>':
                queryset = queryset.filter(location_id__battery_speed__gt=battery_speed)
            elif battery_speed_condition == '<=':
                queryset = queryset.filter(location_id__battery_speed__lte=battery_speed)
            elif battery_speed_condition == '>=':
                queryset = queryset.filter(location_id__battery_speed__gte=battery_speed)
            else:
                queryset = queryset.filter(location_id__battery_speed=battery_speed)
            
        if construction_year:
            construction_year_condition = self.request.data.get('construction_year_condition')
            if construction_year_condition == '<':
                queryset = queryset.filter(location_id__construction_year__lt=construction_year)
            elif construction_year_condition == '>':
                queryset = queryset.filter(location_id__construction_year__gt=construction_year)
            elif construction_year_condition == '<=':
                queryset = queryset.filter(location_id__construction_year__lte=construction_year)
            elif construction_year_condition == '>=':
                queryset = queryset.filter(location_id__construction_year__gte=construction_year)
            else:
                queryset = queryset.filter(location_id__construction_year=construction_year)
                
        if exp_installation_date:
            exp_installation_date_condition = self.request.data.get('exp_installation_date_condition')
            if exp_installation_date_condition:
                exp_installation_date = datetime.strptime(exp_installation_date, '%Y-%m-%d')
                exp_installation_date_condition = datetime.strptime(exp_installation_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__exp_installation_date__range=[exp_installation_date, exp_installation_date_condition])
            else:
                queryset = queryset.filter(location_id__exp_installation_date=exp_installation_date)
                
        if planned_installation_date:
            planned_installation_date_condition = self.request.data.get('planned_installation_date_condition')
            if planned_installation_date_condition:
                exp_installation_date = datetime.strptime(planned_installation_date, '%Y-%m-%d')
                planned_installation_date_condition = datetime.strptime(planned_installation_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__planned_installation_date__range=[planned_installation_date, planned_installation_date_condition])
            else:
                queryset = queryset.filter(location_id__planned_installation_date=planned_installation_date)
                
        if exp_operation_date:
            exp_operation_date_condition = self.request.data.get('exp_operation_date_condition')
            if exp_operation_date_condition:
                exp_operation_date = datetime.strptime(exp_operation_date, '%Y-%m-%d')
                exp_operation_date_condition = datetime.strptime(exp_operation_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__exp_operation_date__range=[exp_operation_date, exp_operation_date_condition])
            else:
                queryset = queryset.filter(location_id__exp_operation_date=exp_operation_date)
        
        if gep_ev:
            gep_ev_condition = self.request.data.get('gep_ev_condition')
            if gep_ev_condition == '<':
                queryset = queryset.filter(location_id__gep_ev__lt = gep_ev)
            elif gep_ev_condition == '>':
                queryset = queryset.filter(location_id__gep_ev__gt = gep_ev)
            elif gep_ev_condition == '<=':
                queryset = queryset.filter(location_id__gep_ev__lte = gep_ev)
            elif gep_ev_condition == '>=':
                queryset = queryset.filter(location_id__gep_ev__gte = gep_ev)
            else:
                queryset = queryset.filter(location_id__gep_ev=gep_ev)
            
        if capex_spent_to_date:
            capex_spent_to_date_condition = self.request.data.get('capex_spent_to_date_condition')
            if capex_spent_to_date_condition:
                capex_spent_to_date = datetime.strptime(capex_spent_to_date, '%Y-%m-%d')
                capex_spent_to_date_condition = datetime.strptime(capex_spent_to_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__capex_spent_to_date__range=[capex_spent_to_date, capex_spent_to_date_condition])
            else:
                queryset = queryset.filter(location_id__capex_spent_to_date=capex_spent_to_date)
                
        if capex_total_expected:
            capex_total_expected_condition = self.request.data.get('capex_total_expected_condition')
            if capex_total_expected_condition == '<':
                queryset = queryset.filter(location_id__capex_total_expected__lt=capex_total_expected)
            elif capex_total_expected_condition == '>':
                queryset = queryset.filter(location_id__capex_total_expected__gt=capex_total_expected)
            elif capex_total_expected_condition == '<=':
                queryset = queryset.filter(location_id__capex_total_expected__lte=capex_total_expected)
            elif capex_total_expected_condition == '>=':
                queryset = queryset.filter(location_id__capex_total_expected__gte=capex_total_expected)
            else:
                queryset = queryset.filter(location_id__capex_total_expected=capex_total_expected)
        
        #PV FILTERS
        
        if status_pv_id:
            queryset = queryset.filter(location_id__status_pv_id=status_pv_id)
        if cos_pv:
            queryset = queryset.filter(location_id__cos_pv=cos_pv)
            
        if milestone_date_pv:
            milestone_date_pv_condition = self.request.data.get('milestone_date_pv_condition')
            if milestone_date_pv_condition:
                milestone_date_pv = datetime.strptime(milestone_date_pv, '%Y-%m-%d')
                milestone_date_pv_condition = datetime.strptime(milestone_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__milestone_date_pv__range=[milestone_date_pv, milestone_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__milestone_date_pv=milestone_date_pv)
                
        if expected_kWp_pv:
            expected_kWp_pv_condition = self.request.data.get('expected_kWp_pv_condition')
            if expected_kWp_pv_condition == '<':
                queryset = queryset.filter(location_id__expected_kWp_pv__lt=expected_kWp_pv)
            elif expected_kWp_pv_condition == '>':
                queryset = queryset.filter(location_id__expected_kWp_pv__gt=expected_kWp_pv)
            elif expected_kWp_pv_condition == '<=':
                queryset = queryset.filter(location_id__expected_kWp_pv__lte=expected_kWp_pv)
            elif expected_kWp_pv_condition == '>=':
                queryset = queryset.filter(location_id__expected_kWp_pv__gte=expected_kWp_pv)
            else:
                queryset = queryset.filter(location_id__expected_kWp_pv=expected_kWp_pv)
                
        if construction_year_pv:
            construction_year_pv_condition = self.request.data.get('construction_year_pv_condition')
            if construction_year_pv_condition == '<':
                queryset = queryset.filter(location_id__construction_year_pv__lt=construction_year_pv)
            elif construction_year_pv_condition == '>':
                queryset = queryset.filter(location_id__construction_year_pv__gt=construction_year_pv)
            elif construction_year_pv_condition == '<=':
                queryset = queryset.filter(location_id__construction_year_pv__lte=construction_year_pv)
            elif construction_year_pv_condition == '>=':
                queryset = queryset.filter(location_id__construction_year_pv__gte=construction_year_pv)
            else:
                queryset = queryset.filter(location_id__construction_year_pv=construction_year_pv)
                
        if exp_installation_date_pv:
            exp_installation_date_pv_condition = self.request.data.get('exp_installation_date_pv_condition')
            if exp_installation_date_pv_condition:
                exp_installation_date_pv = datetime.strptime(exp_installation_date_pv, '%Y-%m-%d')
                exp_installation_date_pv_condition = datetime.strptime(exp_installation_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__eexp_installation_date_pv__range=[exp_installation_date_pv, exp_installation_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__exp_installation_date_pv=exp_installation_date_pv)
                
        if planned_installation_date_pv:
            planned_installation_date_pv_condition = self.request.data.get('planned_installation_date_pv_condition')
            if planned_installation_date_pv_condition:
                planned_installation_date_pv = datetime.strptime(planned_installation_date_pv, '%Y-%m-%d')
                planned_installation_date_pv_condition = datetime.strptime(planned_installation_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__planned_installation_date_pv__range=[planned_installation_date_pv, planned_installation_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__planned_installation_date_pv=planned_installation_date_pv)
        
        if exp_operation_date_pv:
            exp_operation_date_pv_condition = self.request.data.get('exp_operation_date_pv_condition')
            if exp_operation_date_pv_condition:
                exp_operation_date_pv = datetime.strptime(exp_operation_date_pv, '%Y-%m-%d')
                exp_operation_date_pv_condition = datetime.strptime(exp_operation_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__exp_operation_date_pv__range=[exp_operation_date_pv, exp_operation_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__exp_operation_date_pv=exp_operation_date_pv)
                
        if capex_spent_to_date_pv:
            capex_spent_to_date_pv_condition = self.request.data.get('capex_spent_to_date_pv_condition')
            if capex_spent_to_date_pv_condition:
                capex_spent_to_date_pv = datetime.strptime(capex_spent_to_date_pv, '%Y-%m-%d')
                capex_spent_to_date_pv_condition = datetime.strptime(capex_spent_to_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__capex_spent_to_date_pv__range=[capex_spent_to_date_pv, capex_spent_to_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__capex_spent_to_date_pv=capex_spent_to_date_pv)
                
        if capex_total_expected_pv:
            capex_total_expected_pv_condition = self.request.data.get('capex_total_expected_pv_condition')
            if capex_total_expected_pv_condition == '<':
                queryset = queryset.filter(location_id__capex_total_expected_pv__lt=capex_total_expected_pv)
            elif capex_total_expected_pv_condition == '>':
                queryset = queryset.filter(location_id__capex_total_expected_pv__gt=capex_total_expected_pv)
            elif capex_total_expected_pv_condition == '<=':
                queryset = queryset.filter(location_id__capex_total_expected_pv__lte=capex_total_expected_pv)
            elif capex_total_expected_pv_condition == '>=':
                queryset = queryset.filter(location_id__capex_total_expected_pv__gte=capex_total_expected_pv)
            else:
                queryset = queryset.filter(location_id__capex_total_expected_pv=capex_total_expected_pv)
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectPhaseExcelList': serializer.data}
        return Response(response_data)
    
#------------------------------------------------------------ TEMPLATE SORTING ------------------------------------------------------------
class TemplateTaskSorting(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        try:
            task_updates = request.data.get('updated_task_order', [])  # Assuming the array key is 'task_updates'

            for updated_task_data in task_updates:
                task_id = updated_task_data.get('id')
                new_order_number = updated_task_data.get('order_number')
                new_parent_id = updated_task_data.get('parent_id')
               
                task = ProjectPhaseTaskTemplate.objects.get(id=task_id)

                if new_parent_id is None:
                    if task.parent_id_id is not None:
                        ProjectPhaseTaskTemplate.objects.filter(
                            parent_id_id=task.parent_id_id,
                            order_number__gt=task.order_number
                        ).update(order_number=models.F('order_number') - 1)
                        task.parent_id_id = None
                else:
                    if new_parent_id != task.parent_id_id:
                        new_parent = ProjectPhaseTaskTemplate.objects.get(id=new_parent_id)
                        task.parent_id_id = new_parent_id
                        ProjectPhaseTaskTemplate.objects.filter(
                            parent_id_id=new_parent_id,
                            order_number__gte=new_order_number
                        ).update(order_number=models.F('order_number') + 1)
                    else:
                        if new_order_number > task.order_number:
                            ProjectPhaseTaskTemplate.objects.filter(
                                parent_id_id=new_parent_id,
                                order_number__gt=task.order_number,
                                order_number__lte=new_order_number
                            ).update(order_number=models.F('order_number') - 1)
                        elif new_order_number < task.order_number:
                            ProjectPhaseTaskTemplate.objects.filter(
                                parent_id_id=new_parent_id,
                                order_number__lt=task.order_number,
                                order_number__gte=new_order_number
                            ).update(order_number=models.F('order_number') + 1)

                task.order_number = new_order_number
                task.save()

            return Response({'message': 'Tasks reordered successfully'})
        except ProjectPhaseTaskTemplate.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectTaskSorting(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        try:
            task_updates = request.data.get('updated_task_order', [])  

            for updated_task_data in task_updates:
                task_id = updated_task_data.get('id')
                new_order_number = updated_task_data.get('order_number')
                new_parent_id = updated_task_data.get('parent_id')
               
                task = ProjectPhaseTask.objects.get(id=task_id)

                if new_parent_id is None:
                    if task.parent_id_id is not None:
                        ProjectPhaseTask.objects.filter(
                            parent_id_id=task.parent_id_id,
                            order_number__gt=task.order_number
                        ).update(order_number=models.F('order_number') - 1)
                        task.parent_id_id = None
                else:
                    if new_parent_id != task.parent_id_id:
                        new_parent = ProjectPhaseTask.objects.get(id=new_parent_id)
                        task.parent_id_id = new_parent_id
                        ProjectPhaseTask.objects.filter(
                            parent_id_id=new_parent_id,
                            order_number__gte=new_order_number
                        ).update(order_number=models.F('order_number') + 1)
                    else:
                        if new_order_number > task.order_number:
                            ProjectPhaseTask.objects.filter(
                                parent_id_id=new_parent_id,
                                order_number__gt=task.order_number,
                                order_number__lte=new_order_number
                            ).update(order_number=models.F('order_number') - 1)
                        elif new_order_number < task.order_number:
                            ProjectPhaseTask.objects.filter(
                                parent_id_id=new_parent_id,
                                order_number__lt=task.order_number,
                                order_number__gte=new_order_number
                            ).update(order_number=models.F('order_number') + 1)

                task.order_number = new_order_number
                task.save()

            return Response({'message': 'Tasks reordered successfully'})
        except ProjectPhaseTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------- PHASE UPDATES AND TASKS LIST --------------------------------------------------------------
class PhaseUpdateList(generics.ListAPIView):
    queryset = PhaseUpdate.objects.all().order_by('id')
    serializer_class = PhaseUpdateListSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        phase_id = self.kwargs['phase_id']
        queryset = PhaseUpdate.objects.filter(phase_id=phase_id).order_by('id')
        return queryset

    def list(self, request, *args, **kwargs):
        # if not request.user.is_admin:
        #     return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'phaseUpdatedList': serializer.data}
        return Response(response_data)
    
class TaskUpdateList(generics.ListAPIView):
    queryset = TaskUpdate.objects.all().order_by('id')
    serializer_class = TaskUpdateListSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        task_id = self.kwargs['task_id']
        queryset = TaskUpdate.objects.filter(task_id=task_id).order_by('id')
        return queryset

    def list(self, request, *args, **kwargs):
        user = request.user
        task_id = self.kwargs['task_id']
        
        try:
            task = ProjectPhaseTask.objects.get(id=task_id)
        except ProjectPhaseTask.DoesNotExist:
            return Response({'status_code': 404, 'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'taskUpdatedList': serializer.data}
        return Response(response_data)


#------------------------------------------ PROJECT DUPLICATE VIEWS -------------------------------------------------------------------
class ProjectTemplateDuplicate(generics.CreateAPIView):
    serializer_class = ProjectTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        original_template_id = self.kwargs.get('template_id')
        original_template = ProjectTemplate.objects.get(id=original_template_id)

        new_template = ProjectTemplate.objects.create(
            name=self._generate_unique_name(original_template.name),
            template_type=original_template.template_type,
            status=original_template.status
        )

        task_id_mapping = {}
        parent_id_mapping = {}

        for phase_template in original_template.projectphasetemplate_set.all():
            new_phase_template = ProjectPhaseTemplate.objects.create(
                template_id=new_template,
                phase_name=phase_template.phase_name,
                target_count=phase_template.target_count,
                target_duration=phase_template.target_duration,
                order_number=phase_template.order_number
            )

            for task_template in phase_template.projectphasetasktemplate_set.all():
                new_task_template = ProjectPhaseTaskTemplate.objects.create(
                    project_phases_template_id=new_phase_template,
                    title=task_template.title,
                    description=task_template.description,
                    order_number=task_template.order_number,
                    is_dependent=task_template.is_dependent,
                    dependent_task_type=task_template.dependent_task_type,
                    priority_level=task_template.priority_level,
                    assigned_to_type = task_template.assigned_to_type,
                    expected_count = task_template.expected_count,
                    expected_duration = task_template.expected_duration,
                    dependent_count = task_template.dependent_count,
                    dependent_duration = task_template.dependent_duration
                    
                )
                task_id_mapping[task_template.id] = new_task_template.id
                
                if task_template.parent_id:
                    parent_task = parent_id_mapping.get(task_template.parent_id.id)
                    
                    if parent_task:
                        new_task_template.parent_id = parent_task
                new_task_template.save()
                parent_id_mapping[task_template.id] = new_task_template
                task_template_checklists = TaskTemplateCheckList.objects.filter(task_id=task_template)
                for checklist in task_template_checklists:
                    new_checklist = TaskTemplateCheckList(
                        task_id=new_task_template,
                        checklist_id=checklist.checklist_id,
                        checklist_item_id=checklist.checklist_item_id
                    )
                    new_checklist.save()
                    checklist_items = TaskTemplateCheckListItems.objects.filter(tasktemplatechecklist_id=checklist)
                    for item in checklist_items:
                        new_item = TaskTemplateCheckListItems(
                            taskchecklist_id=new_checklist,
                            checklistitems_id=item.checklistitems_id,
                            is_checked=item.is_checked,
                            checked_by=item.checked_by
                        )
                        new_item.save()
                
                task_template_fields = TemplateTaskFields.objects.filter(task_id=new_task_template)
                for taskfields in task_template_fields:
                    task_fields = TemplateTaskFields.objects.create(
                        task_id=new_task_template,
                        project_id=new_task_template.project_phases_template_id.template_id,
                        field_id=taskfields.field_id,
                        is_required = taskfields.is_required
                    )

                for dependency in task_template.task_templates.all():
                    source_dependency_id = dependency.dependent_task_id.id
                    new_dependency_id = task_id_mapping.get(source_dependency_id)

                    if new_dependency_id is not None:
                        ProjectPhaseTaskTemplateDependency.objects.create(
                            task_id=new_task_template,
                            dependent_task_id=ProjectPhaseTaskTemplate.objects.get(id=new_dependency_id),
                            condition=dependency.condition
                        )

        return Response(self.serializer_class(new_template).data)

    def _generate_unique_name(self, base_name):
        if not ProjectTemplate.objects.filter(name=base_name).exists():
            return base_name

        count = 1
        while True:
            new_name = f"{base_name}-copy({count})"
            if not ProjectTemplate.objects.filter(name=new_name).exists():
                return new_name
            count += 1

class ProjectPhaseTemplateDuplicate(generics.CreateAPIView):
    serializer_class = ProjectPhaseTemplateSerializer
    permission_classes = (IsAuthenticated,)
   
    def create(self, request, *args, **kwargs):
        original_phase_template_id = self.kwargs.get('phase_template_id')
        original_phase_template = ProjectPhaseTemplate.objects.get(id=original_phase_template_id)
       
        
        new_phase_template = ProjectPhaseTemplate.objects.create(
            template_id=original_phase_template.template_id,
            phase_name=self._generate_unique_name(original_phase_template.phase_name),
            target_count=original_phase_template.target_count,
            target_duration=original_phase_template.target_duration,
            order_number=original_phase_template.order_number
        )
        
        task_id_mapping = {}
        parent_id_mapping = {}
        
        for task_template in original_phase_template.projectphasetasktemplate_set.all():
            new_task_template = ProjectPhaseTaskTemplate.objects.create(
                project_phases_template_id=new_phase_template,
                title=task_template.title,
                description=task_template.description,
                order_number=task_template.order_number,
                is_dependent=task_template.is_dependent,
                dependent_task_type=task_template.dependent_task_type,
                priority_level=task_template.priority_level,
                assigned_to_type = task_template.assigned_to_type.id if task_template.assigned_to_type else None,
                expected_count = task_template.expected_count,
                expected_duration = task_template.expected_duration
            )

            task_id_mapping[task_template.id] = new_task_template.id

            if task_template.parent_id:
                parent_task = parent_id_mapping.get(task_template.parent_id.id)
                
                if parent_task:
                    new_task_template.parent_id = parent_task
            new_task_template.save()
            parent_id_mapping[task_template.id] = new_task_template
            task_template_checklists = TaskTemplateCheckList.objects.filter(task_id=task_template)
            for checklist in task_template_checklists:
                new_checklist = TaskTemplateCheckList(
                    task_id=new_task_template,
                    checklist_id=checklist.checklist_id,
                    checklist_item_id=checklist.checklist_item_id
                )
                new_checklist.save()
                checklist_items = TaskTemplateCheckListItems.objects.filter(tasktemplatechecklist_id=checklist)
                for item in checklist_items:
                    new_item = TaskTemplateCheckListItems(
                        taskchecklist_id=new_checklist,
                        checklistitems_id=item.checklistitems_id,
                        is_checked=item.is_checked,
                        checked_by=item.checked_by
                    )
                    new_item.save()
            
            task_template_fields = TemplateTaskFields.objects.filter(task_id=new_task_template)
            for taskfields in task_template_fields:
                task_fields = TemplateTaskFields.objects.create(
                    task_id=new_task_template,
                    project_id=new_task_template.project_phases_template_id.template_id,
                    field_id=taskfields.field_id,
                    is_required = taskfields.is_required
                )

            for dependency in task_template.task_templates.all():
                source_dependency_id = dependency.dependent_task_id.id
                new_dependency_id = task_id_mapping.get(source_dependency_id)

                if new_dependency_id is not None:
                    ProjectPhaseTaskTemplateDependency.objects.create(
                        task_id=new_task_template,
                        dependent_task_id=ProjectPhaseTaskTemplate.objects.get(id=new_dependency_id),
                        condition=dependency.condition
                    )

        return Response(self.serializer_class(new_phase_template).data)
   
    def _generate_unique_name(self, base_name):
        if not ProjectPhaseTemplate.objects.filter(phase_name=base_name).exists():
            return base_name
       
        count = 1
        while True:
            new_name = f"{base_name}-copy({count})"
            if not ProjectPhaseTemplate.objects.filter(phase_name=new_name).exists():
                return new_name
            count += 1

class ProjectList(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return Project.objects.all()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user
        
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        
        if user.is_customer:
            if partner_admin_user:
                # project_ids = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id', flat=True).distinct()
                project_id = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id', flat=True).distinct()
                mentioned_ids = ProjectPhaseTask.objects.filter(projectphasetaskmentions__user_id=user).values_list('project_phase_id__project_id', flat=True).distinct()
                project_ids = project_id | mentioned_ids
                queryset = queryset.filter(id__in = project_ids).order_by('id')
            else:
                # project_ids = ProjectPhaseTask.objects.filter(assigned_to_user=user).values_list('project_phase_id__project_id', flat=True).distinct()
                project_id = ProjectPhaseTask.objects.filter(taskassignedusers__user_id=user).values_list('project_phase_id__project_id', flat=True).distinct()
                mentioned_ids = ProjectPhaseTask.objects.filter(projectphasetaskmentions__user_id=user).values_list('project_phase_id__project_id', flat=True).distinct()
                project_ids = project_id | mentioned_ids
                queryset = queryset.filter(id__in = project_ids).order_by('id')
        project_status = self.request.data.get('project_status')
        location_id = self.request.data.get('location_id')
        location_status = self.request.data.get('location_status')
        #EV Filters
        status_ev_id   = self.request.data.get('status_ev_id')
        milestone_date = self.request.data.get('milestone_date')
        parking_spots = self.request.data.get('parking_spots')
        planned_ac = self.request.data.get('planned_ac')
        ac_speed = self.request.data.get('ac_speed')
        planned_dc = self.request.data.get('planned_dc')
        dc_speed = self.request.data.get('dc_speed')
        planned_battery = self.request.data.get('planned_battery')
        battery_speed = self.request.data.get('battery_speed')
        construction_year = self.request.data.get('construction_year')
        exp_installation_date = self.request.data.get('exp_installation_date')
        planned_installation_date = self.request.data.get('planned_installation_date')
        exp_operation_date = self.request.data.get('exp_operation_date')
        gep_ev = self.request.data.get('gep_ev')
        capex_spent_to_date = self.request.data.get('capex_spent_to_date')
        capex_total_expected = self.request.data.get('capex_total_expected')
        #PV Filters
        status_pv_id = self.request.data.get('status_pv_id')
        cos_pv = self.request.data.get('cos_pv')
        milestone_date_pv = self.request.data.get('milestone_date_pv')
        expected_kWp_pv = self.request.data.get('expected_kWp_pv')
        construction_year_pv = self.request.data.get('construction_year_pv')
        exp_installation_date_pv = self.request.data.get('exp_installation_date_pv')
        planned_installation_date_pv = self.request.data.get('planned_installation_date_pv')
        exp_operation_date_pv = self.request.data.get('exp_operation_date_pv')
        capex_spent_to_date_pv = self.request.data.get('capex_spent_to_date_pv')
        capex_total_expected_pv = self.request.data.get('capex_total_expected_pv')
        
        if project_status:
            queryset = queryset.filter(project_status=project_status)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        if location_status:
            queryset = queryset.filter(location_id__location_status=location_status)
        if status_ev_id:
            queryset = queryset.filter(location_id__status_ev_id=status_ev_id)

        if milestone_date:
            milestone_date_condition = self.request.data.get('milestone_date_condition')
            if milestone_date_condition:
                milestone_date = datetime.strptime(milestone_date, '%Y-%m-%d')
                milestone_date_condition = datetime.strptime(milestone_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__milestone_date__range=[milestone_date, milestone_date_condition])
            else:
                queryset = queryset.filter(location_id__milestone_date=milestone_date)
                
        if parking_spots:
            parking_spots_condition = self.request.data.get('parking_spots_condition')
            if parking_spots_condition == '<':
                queryset = queryset.filter(location_id__parking_spots__lt=parking_spots)
            elif parking_spots_condition == '>':
                queryset = queryset.filter(location_id__parking_spots__gt=parking_spots)
            elif parking_spots_condition == '<=':
                queryset = queryset.filter(location_id__parking_spots__lte=parking_spots)
            elif parking_spots_condition == '>=':
                queryset = queryset.filter(location_id__parking_spots__gte=parking_spots)
            else:
                queryset = queryset.filter(location_id__parking_spots=parking_spots)
                
        if planned_ac:
            planned_ac_condition = self.request.data.get('planned_ac_condition')
            if planned_ac_condition == '<':
                queryset = queryset.filter(location_id__planned_ac__lt=planned_ac)
            elif planned_ac_condition == '>':
                queryset = queryset.filter(location_id__planned_ac__gt=planned_ac)
            elif planned_ac_condition == '<=':
                queryset = queryset.filter(location_id__planned_ac__lte=planned_ac)
            elif planned_ac_condition == '>=':
                queryset = queryset.filter(location_id__planned_ac__gte=planned_ac)
            else:
                queryset = queryset.filter(location_id__planned_ac=planned_ac)
                
        if ac_speed:
            ac_speed_condition = self.request.data.get('ac_speed_condition')
            if ac_speed_condition == '<':
                queryset = queryset.filter(location_id__ac_speed__lt=ac_speed)
            elif ac_speed_condition == '>':
                queryset = queryset.filter(location_id__ac_speed__gt=ac_speed)
            elif ac_speed_condition == '<=':
                queryset = queryset.filter(location_id__ac_speed__lte=ac_speed)
            elif ac_speed_condition == '>=':
                queryset = queryset.filter(location_id__ac_speed__gte=ac_speed)
            else:
                queryset = queryset.filter(location_id__ac_speed=ac_speed)
                
        if planned_dc:
            planned_dc_condition = self.request.data.get('planned_dc_condition')
            if planned_dc_condition == '<':
                queryset = queryset.filter(location_id__planned_dc__lt=planned_dc)
            elif planned_dc_condition == '>':
                queryset = queryset.filter(location_id__planned_dc__gt=planned_dc)
            elif planned_dc_condition == '<=':
                queryset = queryset.filter(location_id__planned_dc__lte=planned_dc)
            elif planned_dc_condition == '>=':
                queryset = queryset.filter(location_id__planned_dc__gte=planned_dc)
            else:
                queryset = queryset.filter(location_id__planned_dc=planned_dc)
                
        if dc_speed:
            dc_speed_condition = self.request.data.get('dc_speed_condition')
            if dc_speed_condition == '<':
                queryset = queryset.filter(location_id__dc_speed__lt=dc_speed)
            elif dc_speed_condition == '>':
                queryset = queryset.filter(location_id__dc_speed__gt=dc_speed)
            elif dc_speed_condition == '<=':
                queryset = queryset.filter(location_id__dc_speed__lte=dc_speed)
            elif dc_speed_condition == '>=':
                queryset = queryset.filter(location_id__dc_speed__gte=dc_speed)
            else:
                queryset = queryset.filter(location_id__dc_speed=dc_speed)
                
        if planned_battery:
            planned_battery_condition = self.request.data.get('planned_battery_condition')
            if planned_battery_condition == '<':
                queryset = queryset.filter(location_id__planned_battery__lt=planned_battery)
            elif planned_battery_condition == '>':
                queryset = queryset.filter(location_id__planned_battery__gt=planned_battery)
            elif planned_battery_condition == '<=':
                queryset = queryset.filter(location_id__planned_battery__lte=planned_battery)
            elif planned_battery_condition == '>=':
                queryset = queryset.filter(location_id__planned_battery__gte=planned_battery)
            else:
                queryset = queryset.filter(location_id__planned_battery=planned_battery)
        if battery_speed:
            battery_speed_condition = self.request.data.get('planned_battery_condition')
            if battery_speed_condition == '<':
                queryset = queryset.filter(location_id__battery_speed__lt=battery_speed)
            elif battery_speed_condition == '>':
                queryset = queryset.filter(location_id__battery_speed__gt=battery_speed)
            elif battery_speed_condition == '<=':
                queryset = queryset.filter(location_id__battery_speed__lte=battery_speed)
            elif battery_speed_condition == '>=':
                queryset = queryset.filter(location_id__battery_speed__gte=battery_speed)
            else:
                queryset = queryset.filter(location_id__battery_speed=battery_speed)
            
        if construction_year:
            construction_year_condition = self.request.data.get('construction_year_condition')
            if construction_year_condition == '<':
                queryset = queryset.filter(location_id__construction_year__lt=construction_year)
            elif construction_year_condition == '>':
                queryset = queryset.filter(location_id__construction_year__gt=construction_year)
            elif construction_year_condition == '<=':
                queryset = queryset.filter(location_id__construction_year__lte=construction_year)
            elif construction_year_condition == '>=':
                queryset = queryset.filter(location_id__construction_year__gte=construction_year)
            else:
                queryset = queryset.filter(location_id__construction_year=construction_year)
                
        if exp_installation_date:
            exp_installation_date_condition = self.request.data.get('exp_installation_date_condition')
            if exp_installation_date_condition:
                exp_installation_date = datetime.strptime(exp_installation_date, '%Y-%m-%d')
                exp_installation_date_condition = datetime.strptime(exp_installation_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__exp_installation_date__range=[exp_installation_date, exp_installation_date_condition])
            else:
                queryset = queryset.filter(location_id__exp_installation_date=exp_installation_date)
                
        if planned_installation_date:
            planned_installation_date_condition = self.request.data.get('planned_installation_date_condition')
            if planned_installation_date_condition:
                exp_installation_date = datetime.strptime(planned_installation_date, '%Y-%m-%d')
                planned_installation_date_condition = datetime.strptime(planned_installation_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__planned_installation_date__range=[planned_installation_date, planned_installation_date_condition])
            else:
                queryset = queryset.filter(location_id__planned_installation_date=planned_installation_date)
                
        if exp_operation_date:
            exp_operation_date_condition = self.request.data.get('exp_operation_date_condition')
            if exp_operation_date_condition:
                exp_operation_date = datetime.strptime(exp_operation_date, '%Y-%m-%d')
                exp_operation_date_condition = datetime.strptime(exp_operation_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__exp_operation_date__range=[exp_operation_date, exp_operation_date_condition])
            else:
                queryset = queryset.filter(location_id__exp_operation_date=exp_operation_date)
        
        if gep_ev:
            gep_ev_condition = self.request.data.get('gep_ev_condition')
            if gep_ev_condition == '<':
                queryset = queryset.filter(location_id__gep_ev__lt = gep_ev)
            elif gep_ev_condition == '>':
                queryset = queryset.filter(location_id__gep_ev__gt = gep_ev)
            elif gep_ev_condition == '<=':
                queryset = queryset.filter(location_id__gep_ev__lte = gep_ev)
            elif gep_ev_condition == '>=':
                queryset = queryset.filter(location_id__gep_ev__gte = gep_ev)
            else:
                queryset = queryset.filter(location_id__gep_ev=gep_ev)
            
        if capex_spent_to_date:
            capex_spent_to_date_condition = self.request.data.get('capex_spent_to_date_condition')
            if capex_spent_to_date_condition:
                capex_spent_to_date = datetime.strptime(capex_spent_to_date, '%Y-%m-%d')
                capex_spent_to_date_condition = datetime.strptime(capex_spent_to_date_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__capex_spent_to_date__range=[capex_spent_to_date, capex_spent_to_date_condition])
            else:
                queryset = queryset.filter(location_id__capex_spent_to_date=capex_spent_to_date)
                
        if capex_total_expected:
            capex_total_expected_condition = self.request.data.get('capex_total_expected_condition')
            if capex_total_expected_condition == '<':
                queryset = queryset.filter(location_id__capex_total_expected__lt=capex_total_expected)
            elif capex_total_expected_condition == '>':
                queryset = queryset.filter(location_id__capex_total_expected__gt=capex_total_expected)
            elif capex_total_expected_condition == '<=':
                queryset = queryset.filter(location_id__capex_total_expected__lte=capex_total_expected)
            elif capex_total_expected_condition == '>=':
                queryset = queryset.filter(location_id__capex_total_expected__gte=capex_total_expected)
            else:
                queryset = queryset.filter(location_id__capex_total_expected=capex_total_expected)
        
        #PV FILTERS
        
        if status_pv_id:
            queryset = queryset.filter(location_id__status_pv_id=status_pv_id)
        if cos_pv:
            queryset = queryset.filter(location_id__cos_pv=cos_pv)
            
        if milestone_date_pv:
            milestone_date_pv_condition = self.request.data.get('milestone_date_pv_condition')
            if milestone_date_pv_condition:
                milestone_date_pv = datetime.strptime(milestone_date_pv, '%Y-%m-%d')
                milestone_date_pv_condition = datetime.strptime(milestone_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__milestone_date_pv__range=[milestone_date_pv, milestone_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__milestone_date_pv=milestone_date_pv)
                
        if expected_kWp_pv:
            expected_kWp_pv_condition = self.request.data.get('expected_kWp_pv_condition')
            if expected_kWp_pv_condition == '<':
                queryset = queryset.filter(location_id__expected_kWp_pv__lt=expected_kWp_pv)
            elif expected_kWp_pv_condition == '>':
                queryset = queryset.filter(location_id__expected_kWp_pv__gt=expected_kWp_pv)
            elif expected_kWp_pv_condition == '<=':
                queryset = queryset.filter(location_id__expected_kWp_pv__lte=expected_kWp_pv)
            elif expected_kWp_pv_condition == '>=':
                queryset = queryset.filter(location_id__expected_kWp_pv__gte=expected_kWp_pv)
            else:
                queryset = queryset.filter(location_id__expected_kWp_pv=expected_kWp_pv)
                
        if construction_year_pv:
            construction_year_pv_condition = self.request.data.get('construction_year_pv_condition')
            if construction_year_pv_condition == '<':
                queryset = queryset.filter(location_id__construction_year_pv__lt=construction_year_pv)
            elif construction_year_pv_condition == '>':
                queryset = queryset.filter(location_id__construction_year_pv__gt=construction_year_pv)
            elif construction_year_pv_condition == '<=':
                queryset = queryset.filter(location_id__construction_year_pv__lte=construction_year_pv)
            elif construction_year_pv_condition == '>=':
                queryset = queryset.filter(location_id__construction_year_pv__gte=construction_year_pv)
            else:
                queryset = queryset.filter(location_id__construction_year_pv=construction_year_pv)
                
        if exp_installation_date_pv:
            exp_installation_date_pv_condition = self.request.data.get('exp_installation_date_pv_condition')
            if exp_installation_date_pv_condition:
                exp_installation_date_pv = datetime.strptime(exp_installation_date_pv, '%Y-%m-%d')
                exp_installation_date_pv_condition = datetime.strptime(exp_installation_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__eexp_installation_date_pv__range=[exp_installation_date_pv, exp_installation_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__exp_installation_date_pv=exp_installation_date_pv)
                
        if planned_installation_date_pv:
            planned_installation_date_pv_condition = self.request.data.get('planned_installation_date_pv_condition')
            if planned_installation_date_pv_condition:
                planned_installation_date_pv = datetime.strptime(planned_installation_date_pv, '%Y-%m-%d')
                planned_installation_date_pv_condition = datetime.strptime(planned_installation_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__planned_installation_date_pv__range=[planned_installation_date_pv, planned_installation_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__planned_installation_date_pv=planned_installation_date_pv)
        
        if exp_operation_date_pv:
            exp_operation_date_pv_condition = self.request.data.get('exp_operation_date_pv_condition')
            if exp_operation_date_pv_condition:
                exp_operation_date_pv = datetime.strptime(exp_operation_date_pv, '%Y-%m-%d')
                exp_operation_date_pv_condition = datetime.strptime(exp_operation_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__exp_operation_date_pv__range=[exp_operation_date_pv, exp_operation_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__exp_operation_date_pv=exp_operation_date_pv)
                
        if capex_spent_to_date_pv:
            capex_spent_to_date_pv_condition = self.request.data.get('capex_spent_to_date_pv_condition')
            if capex_spent_to_date_pv_condition:
                capex_spent_to_date_pv = datetime.strptime(capex_spent_to_date_pv, '%Y-%m-%d')
                capex_spent_to_date_pv_condition = datetime.strptime(capex_spent_to_date_pv_condition, '%Y-%m-%d')
                queryset = queryset.filter(location_id__capex_spent_to_date_pv__range=[capex_spent_to_date_pv, capex_spent_to_date_pv_condition])
            else:
                queryset = queryset.filter(location_id__capex_spent_to_date_pv=capex_spent_to_date_pv)
                
        if capex_total_expected_pv:
            capex_total_expected_pv_condition = self.request.data.get('capex_total_expected_pv_condition')
            if capex_total_expected_pv_condition == '<':
                queryset = queryset.filter(location_id__capex_total_expected_pv__lt=capex_total_expected_pv)
            elif capex_total_expected_pv_condition == '>':
                queryset = queryset.filter(location_id__capex_total_expected_pv__gt=capex_total_expected_pv)
            elif capex_total_expected_pv_condition == '<=':
                queryset = queryset.filter(location_id__capex_total_expected_pv__lte=capex_total_expected_pv)
            elif capex_total_expected_pv_condition == '>=':
                queryset = queryset.filter(location_id__capex_total_expected_pv__gte=capex_total_expected_pv)
            else:
                queryset = queryset.filter(location_id__capex_total_expected_pv=capex_total_expected_pv)
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'projectList': serializer.data}
        return Response(response_data)
    
     
class TaskListByUser(generics.ListAPIView):
    queryset = ProjectPhaseTask.objects.all().order_by('order_number') #ProjectPhaseTask.objects.filter(parent_id__isnull=True).order_by('id')
    serializer_class = ProjectPhaseTaskDepSerializer #ProjectPhaseTaskDepSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_start_date(self, task):
        if task.start_date:
            return task.start_date
        else:
            if task.project_phase_id:
                phase = task.project_phase_id
                if phase.start_date:
                    return phase.start_date
                else:
                    project = phase.project_id
                    if project.start_date:
                        return project.start_date
                    else:
                        return datetime.now().date() + timedelta(days=1)
            else:
                return None
    
    def calculate_end_date(self, start_date, target_count, target_duration):
        if not start_date:
            return None

        if target_duration == 'days':
            end_date = start_date + timedelta(days=target_count)
        elif target_duration == 'weeks':
            end_date = start_date + timedelta(weeks=target_count)
        elif target_duration == 'months':
            end_date = start_date + relativedelta(months=target_count) - timedelta(days=1)
        elif target_duration == 'years':
            end_date = start_date + relativedelta(months=target_count) - timedelta(days=1)
        else:
            end_date = None
        
        return end_date
      
    def list(self, request, *args, **kwargs):
        if request.user.is_admin:
            queryset = self.get_queryset()
            task_list = []
            for task in queryset:
                dependent_end_dates = []
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task)
                if dependencies.exists():
                    for dependency in dependencies:
                        dependent_task = dependency.dependent_task_id
                        dependent_end_date = self.calculate_end_date(
                            self.get_start_date(dependent_task),
                            dependent_task.target_count,
                            dependent_task.target_duration
                        )
                        dependent_end_dates.append(dependent_end_date)
                    
                    
                    start_date = max(dependent_end_dates) #max(end_date, max(dependent_end_dates))
                else:
                    start_date = self.get_start_date(task)
                
                end_date = self.calculate_end_date(start_date, task.target_count, task.target_duration)
                
                subtasks = ProjectPhaseTask.objects.filter(parent_id=task.id)
                # if subtasks.exists():
                #     subtasks_end_dates = [self.calculate_end_date(self.get_start_date(subtask), subtask.target_count, subtask.target_duration) for subtask in subtasks]
                #     end_date = max(end_date, max(subtasks_end_dates))
                if subtasks.exists():
                    subtasks_end_dates = [self.calculate_end_date(self.get_start_date(subtask), subtask.target_count, subtask.target_duration) for subtask in subtasks]
                    subtasks_end_dates = [date for date in subtasks_end_dates if date is not None]
                    if subtasks_end_dates:
                        end_date = max(end_date, max(subtasks_end_dates))

                task_data = {
                    'id': task.id,
                    'project_id': task.project_phase_id.project_id.id if task.project_phase_id else None,
                    'project_name': task.project_phase_id.project_id.name if task.project_phase_id else None,
                    'phase_id': task.project_phase_id.id if task.project_phase_id else None,
                    'phase_name': task.project_phase_id.phase_name if task.project_phase_id else None,
                    'location_id': task.project_phase_id.project_id.location_id.id if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_name': task.project_phase_id.project_id.location_id.name if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_status': task.project_phase_id.project_id.location_id.location_status if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'title': task.title,
                    'target_count': task.target_count,
                    'target_duration': task.target_duration,
                    'prority_level': task.priority_level,
                    'status': task.status,
                    'start_date': task.start_date if task.start_date else start_date,
                    'end_date': task.end_date if task.end_date else end_date
                }
                task_list.append(task_data)

            return Response({'taskList': task_list})
        
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
        if partner_admin_user.exists():
            task_list = []
            partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
            assigned_tasks = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids)
            for task in assigned_tasks:
                dependent_end_dates = []
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task)
                if dependencies.exists():
                    for dependency in dependencies:
                        dependent_task = dependency.dependent_task_id
                        dependent_end_date = self.calculate_end_date(
                            self.get_start_date(dependent_task),
                            dependent_task.target_count,
                            dependent_task.target_duration
                        )
                        dependent_end_dates.append(dependent_end_date)
                    
                    
                    start_date = max(dependent_end_dates) #max(end_date, max(dependent_end_dates))
                else:
                    start_date = self.get_start_date(task)
                
                end_date = self.calculate_end_date(start_date, task.target_count, task.target_duration)
                
                task_data = {
                    'id': task.id,
                    'project_id': task.project_phase_id.project_id.id if task.project_phase_id else None,
                    'project_name': task.project_phase_id.project_id.name if task.project_phase_id else None,
                    'phase_id': task.project_phase_id.id if task.project_phase_id else None,
                    'phase_name': task.project_phase_id.phase_name if task.project_phase_id else None,
                    'location_id': task.project_phase_id.project_id.location_id.id if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_name': task.project_phase_id.project_id.location_id.name if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_status': task.project_phase_id.project_id.location_id.location_status if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'title': task.title,
                    'target_count': task.target_count,
                    'target_duration': task.target_duration,
                    'prority_level': task.priority_level,
                    'status': task.status,
                    'start_date': task.start_date if task.start_date else start_date,
                    'end_date': task.end_date if task.end_date else end_date
                }
                task_list.append(task_data)

            return Response({'taskList': task_list})
        
        elif request.user.is_customer:
            partner_ids = PartnerTypeRolesUser.objects.filter(user_id=request.user).values_list('partner_types_role_id__partner_id', flat=True)
            # assigned_tasks = ProjectPhaseTask.objects.filter(assigned_to_user__in=partner_ids)
            assigned_tasks = ProjectPhaseTask.objects.filter(taskassignedusers__user_id=request.user)
            task_list = []
            for task in assigned_tasks:
                dependent_end_dates = []
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task)
                if dependencies.exists():
                    for dependency in dependencies:
                        dependent_task = dependency.dependent_task_id
                        dependent_end_date = self.calculate_end_date(
                            self.get_start_date(dependent_task),
                            dependent_task.target_count,
                            dependent_task.target_duration
                        )
                        dependent_end_dates.append(dependent_end_date)
                    
                    
                    start_date = max(dependent_end_dates) #max(end_date, max(dependent_end_dates))
                else:
                    start_date = self.get_start_date(task)
                
                end_date = self.calculate_end_date(start_date, task.target_count, task.target_duration)
                
                task_data = {
                    'id': task.id,
                    'project_id': task.project_phase_id.project_id.id if task.project_phase_id else None,
                    'project_name': task.project_phase_id.project_id.name if task.project_phase_id else None,
                    'phase_id': task.project_phase_id.id if task.project_phase_id else None,
                    'phase_name': task.project_phase_id.phase_name if task.project_phase_id else None,
                    'location_id': task.project_phase_id.project_id.location_id.id if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_name': task.project_phase_id.project_id.location_id.name if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_status': task.project_phase_id.project_id.location_id.location_status if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'title': task.title,
                    'target_count': task.target_count,
                    'target_duration': task.target_duration,
                    'prority_level': task.priority_level,
                    'status': task.status,
                    'start_date': task.start_date if task.start_date else start_date,
                    'end_date': task.end_date if task.end_date else end_date
                }
                task_list.append(task_data)

            return Response({'taskList': task_list})
        else:
            return Response({'error': 'You do not have permission to perform this action'})
        
        
#--------------------------------------------------------- TASK MENTIONS ----------------------------------------------------------------------
class TaskMentionsCreate(generics.CreateAPIView):
    queryset = ProjectPhaseTaskMentions.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        try:
            task_id = request.data.get('task_id')
            user_ids = request.data.get('user_id', [])
            
            task = ProjectPhaseTask.objects.filter(pk=task_id).first()
            ProjectPhaseTaskMentions.objects.filter(task_id = task).delete()
            user_id = User.objects.filter(pk__in=user_ids)
            
            for user_id in user_id:
                ProjectPhaseTaskMentions.objects.create(
                    task_id = task,
                    user_id = user_id,
                    mentioned_by = request.user,
                    created_at = timezone.now()
                )
                fullname = f"{request.user.firstname} {request.user.lastname}"
                user_notifications = Notification.objects.filter(task_id=task.id, user_id=user_id.id, source='project_mentions')
                if not user_notifications.exists():
                    Notification.objects.create(
                        user_id=user_id.id,
                        user_name = user_id.get_full_name(),
                        subject='Project Management - Mention',
                        body=f'{task.title}',
                        task_id = task.id,
                        source = 'project_mentions',
                        data_id=task.project_phase_id.project_id.id,
                        data_name=task.project_phase_id.project_id.name,
                        assigned_by_id=request.user.id,
                        assigned_by_name=fullname,
                        location_name=task.project_phase_id.project_id.location_id.name,
                        created_at=timezone.now()
                    )            
            return Response({'taskMentionDetails':'task mentions created successfully'})
        except Exception as e:
            return Response({'error':str(e)})

#Dashboard tasks
class TaskListByLocationStatus(generics.ListAPIView):
    queryset = ProjectPhaseTask.objects.filter(project_phase_id__project_id__location_id__location_status__in=["operating", "projectmanagement"] ).order_by('order_number')
    serializer_class = ProjectPhaseTaskDepSerializer 
    permission_classes = (IsAuthenticated,)
    
    def get_start_date(self, task):
        if task.start_date:
            return task.start_date
        else:
            if task.project_phase_id:
                phase = task.project_phase_id
                if phase.start_date:
                    return phase.start_date
                else:
                    project = phase.project_id
                    if project.start_date:
                        return project.start_date
                    else:
                        return datetime.now().date() + timedelta(days=1)
            else:
                return None
    
    def calculate_end_date(self, start_date, target_count, target_duration):
        if not start_date:
            return None

        if target_duration == 'days':
            end_date = start_date + timedelta(days=target_count)
        elif target_duration == 'weeks':
            end_date = start_date + timedelta(weeks=target_count)
        elif target_duration == 'months':
            end_date = start_date + relativedelta(months=target_count) - timedelta(days=1)
        elif target_duration == 'years':
            end_date = start_date + relativedelta(months=target_count) - timedelta(days=1)
        else:
            end_date = None
        
        return end_date
      
    def list(self, request, *args, **kwargs):
        if request.user.is_admin:
            queryset = self.get_queryset()
            task_list = []
            for task in queryset:
                dependent_end_dates = []
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task)
                if dependencies.exists():
                    for dependency in dependencies:
                        dependent_task = dependency.dependent_task_id
                        dependent_end_date = self.calculate_end_date(
                            self.get_start_date(dependent_task),
                            dependent_task.target_count,
                            dependent_task.target_duration
                        )
                        dependent_end_dates.append(dependent_end_date)
                    
                    
                    start_date = max(dependent_end_dates)
                else:
                    start_date = self.get_start_date(task)
                
                end_date = self.calculate_end_date(start_date, task.target_count, task.target_duration)
                
                subtasks = ProjectPhaseTask.objects.filter(parent_id=task.id)
                if subtasks.exists():
                    subtasks_end_dates = [self.calculate_end_date(self.get_start_date(subtask), subtask.target_count, subtask.target_duration) for subtask in subtasks]
                    subtasks_end_dates = [date for date in subtasks_end_dates if date is not None]
                    if subtasks_end_dates:
                        end_date = max(end_date, max(subtasks_end_dates))

                assigned_users = TaskAssignedUsers.objects.filter(task_id=task)
                assigned_users_data = TaskAssignedUsersSerializer(assigned_users, many=True).data
                task_data = {
                    'id': task.id,
                    'project_id': task.project_phase_id.project_id.id if task.project_phase_id else None,
                    'project_name': task.project_phase_id.project_id.name if task.project_phase_id else None,
                    'phase_id': task.project_phase_id.id if task.project_phase_id else None,
                    'phase_name': task.project_phase_id.phase_name if task.project_phase_id else None,
                    'location_id': task.project_phase_id.project_id.location_id.id if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_name': task.project_phase_id.project_id.location_id.name if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_status': task.project_phase_id.project_id.location_id.location_status if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'title': task.title,
                    'target_count': task.target_count,
                    'target_duration': task.target_duration,
                    'prority_level': task.priority_level,
                    'status': task.status,
                    'assigned_to':task.assigned_to.id if task.assigned_to else None,
                    'assigned_to_name':task.assigned_to.name if task.assigned_to else None,
                    'assigned_to_user':task.assigned_to_user.id if task.assigned_to_user else None,
                    'assigned_to_user_name':task.assigned_to_user.get_full_name() if task.assigned_to_user else None,
                    'start_date': task.start_date if task.start_date else start_date,
                    'end_date': task.end_date if task.end_date else end_date,
                    'project_phase_task_users':assigned_users_data
                    
                }
                task_list.append(task_data)

            return Response({'taskList': task_list})
        
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
        if partner_admin_user.exists():
            task_list = []
            partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
            assigned_tasks = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids)
            for task in assigned_tasks:
                dependent_end_dates = []
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task)
                if dependencies.exists():
                    for dependency in dependencies:
                        dependent_task = dependency.dependent_task_id
                        dependent_end_date = self.calculate_end_date(
                            self.get_start_date(dependent_task),
                            dependent_task.target_count,
                            dependent_task.target_duration
                        )
                        dependent_end_dates.append(dependent_end_date)
                    
                    
                    start_date = max(dependent_end_dates) #max(end_date, max(dependent_end_dates))
                else:
                    start_date = self.get_start_date(task)
                
                end_date = self.calculate_end_date(start_date, task.target_count, task.target_duration)
                assigned_users = TaskAssignedUsers.objects.filter(task_id=task)
                assigned_users_data = TaskAssignedUsersSerializer(assigned_users, many=True).data
                
                task_data = {
                    'id': task.id,
                    'project_id': task.project_phase_id.project_id.id if task.project_phase_id else None,
                    'project_name': task.project_phase_id.project_id.name if task.project_phase_id else None,
                    'phase_id': task.project_phase_id.id if task.project_phase_id else None,
                    'phase_name': task.project_phase_id.phase_name if task.project_phase_id else None,
                    'location_id': task.project_phase_id.project_id.location_id.id if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_name': task.project_phase_id.project_id.location_id.name if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_status': task.project_phase_id.project_id.location_id.location_status if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'title': task.title,
                    'target_count': task.target_count,
                    'target_duration': task.target_duration,
                    'prority_level': task.priority_level,
                    'status': task.status,
                    'assigned_to':task.assigned_to.id if task.assigned_to else None,
                    'assigned_to_name':task.assigned_to.name if task.assigned_to else None,
                    'assigned_to_user':task.assigned_to_user.id if task.assigned_to_user else None,
                    'assigned_to_user_name':task.assigned_to_user.get_full_name() if task.assigned_to_user else None,
                    'start_date': task.start_date if task.start_date else start_date,
                    'end_date': task.end_date if task.end_date else end_date,
                    'project_phase_task_users':assigned_users_data
                }
                task_list.append(task_data)

            return Response({'taskList': task_list})
        
        elif request.user.is_customer:
            partner_ids = PartnerTypeRolesUser.objects.filter(user_id=request.user).values_list('partner_types_role_id__partner_id', flat=True)
            # assigned_tasks = ProjectPhaseTask.objects.filter(assigned_to_user__in=partner_ids)
            assigned_tasks = ProjectPhaseTask.objects.filter(taskassignedusers__user_id=request.user)
            task_list = []
            for task in assigned_tasks:
                dependent_end_dates = []
                dependencies = ProjectPhaseTaskDependency.objects.filter(task_id=task)
                if dependencies.exists():
                    for dependency in dependencies:
                        dependent_task = dependency.dependent_task_id
                        dependent_end_date = self.calculate_end_date(
                            self.get_start_date(dependent_task),
                            dependent_task.target_count,
                            dependent_task.target_duration
                        )
                        dependent_end_dates.append(dependent_end_date)
                    
                    
                    start_date = max(dependent_end_dates) #max(end_date, max(dependent_end_dates))
                else:
                    start_date = self.get_start_date(task)
                
                end_date = self.calculate_end_date(start_date, task.target_count, task.target_duration)
                assigned_users = TaskAssignedUsers.objects.filter(task_id=task)
                assigned_users_data = TaskAssignedUsersSerializer(assigned_users, many=True).data
                
                task_data = {
                    'id': task.id,
                    'project_id': task.project_phase_id.project_id.id if task.project_phase_id else None,
                    'project_name': task.project_phase_id.project_id.name if task.project_phase_id else None,
                    'phase_id': task.project_phase_id.id if task.project_phase_id else None,
                    'phase_name': task.project_phase_id.phase_name if task.project_phase_id else None,
                    'location_id': task.project_phase_id.project_id.location_id.id if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_name': task.project_phase_id.project_id.location_id.name if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'location_status': task.project_phase_id.project_id.location_id.location_status if task.project_phase_id and task.project_phase_id.project_id.location_id else None,
                    'title': task.title,
                    'target_count': task.target_count,
                    'target_duration': task.target_duration,
                    'prority_level': task.priority_level,
                    'status': task.status,
                    'assigned_to':task.assigned_to.id if task.assigned_to else None,
                    'assigned_to_name':task.assigned_to.name if task.assigned_to else None,
                    'assigned_to_user':task.assigned_to_user.id if task.assigned_to_user else None,
                    'assigned_to_user_name':task.assigned_to_user.get_full_name() if task.assigned_to_user else None,
                    'start_date': task.start_date if task.start_date else start_date,
                    'end_date': task.end_date if task.end_date else end_date,
                    'project_phase_task_users':assigned_users_data
                }
                task_list.append(task_data)

                return Response({'taskList': task_list})
        else:
            return Response({'error': 'You do not have permission to perform this action'})

class AssignUserTask(generics.CreateAPIView):
    queryset = TaskAssignedUsers.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        try:
            task_id = request.data.get('task_id')
            user_ids = request.data.get('user_id', [])
            print(user_ids)
            task = ProjectPhaseTask.objects.filter(pk=task_id).first()
            TaskAssignedUsers.objects.filter(task_id = task).delete()
            user_id = User.objects.filter(pk__in=user_ids)
            print(user_id)
            for user in user_id:
                task_assinged_users = TaskAssignedUsers.objects.create(
                    task_id = task,
                    user_id = user,
                    assigned_by = request.user,
                    created_at = timezone.now()
                )
            return Response({'taskAssigndUsers':'users updated successfully'})
        except Exception as e:
            return Response({'error':str(e)})
        
        
# class DashBoardProjectList(generics.ListAPIView):
#     queryset = Project.objects.filter(projectphase__projectphasetask__isnull = False).distinct()
#     serializer_class = ProjectSerializer
#     permission_classes = (IsAuthenticated,)
    
    
#     def post(self, request, *args, **kwargs):
#         project_status = request.data.get('project_status')
#         queryset = self.get_queryset()
#         partner_admin_user = PartnerTypeRolesUser.objects.filter(is_admin=True)
#         partner_id = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
#         if project_status:
#             if partner_admin_user:
#                 queryset = queryset.filter(projectphase__projectphasetask__assigned_to__in=partner_id, project_status=project_status)
#             elif request.user.is_customer and not partner_admin_user:
#                 queryset = queryset.filter(projectphase__projectphasetask__assigned_to__in=partner_id, project_status=project_status)
#             elif request.user.is_admin: 
#                 queryset = queryset.filter(project_status=project_status)
#         else:
#             if partner_admin_user:
#                 queryset = queryset.filter(projectphase__projectphasetask__assigned_to__in=partner_id)
#             elif request.user.is_customer and not partner_admin_user:
#                 queryset = queryset.filter(projectphase__projectphasetask__assigned_to_user__in=request.user)
            
#         serializer = self.get_serializer(queryset, many=True)
#         return Response({'projectDashboardList':serializer.data})

class DashBoardProjectList(generics.ListAPIView):
    queryset = Project.objects.filter(projectphase__projectphasetask__isnull=False).distinct()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        project_status = request.data.get('project_status')
        queryset = self.get_queryset()

        partner_admin_user = PartnerTypeRolesUser.objects.filter(is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)

        if project_status:
            if request.user.is_admin:
                queryset = queryset.filter(project_status=project_status)
            elif partner_admin_user.exists():
                queryset = queryset.filter(projectphase__projectphasetask__assigned_to__in=partner_ids, project_status=project_status)
            elif request.user.is_customer and not partner_admin_user.exists():
                queryset = queryset.filter(projectphase__projectphasetask__assigned_to=request.user, project_status=project_status)
        else:
            if request.user.is_admin:
                queryset = self.get_queryset()
            elif partner_admin_user.exists():
                queryset = queryset.filter(projectphase__projectphasetask__assigned_to__in=partner_ids)
            elif request.user.is_customer and not partner_admin_user.exists():
                queryset = queryset.filter(projectphase__projectphasetask__assigned_to=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'projectDashboardList': serializer.data})


class ProjectDetail(generics.RetrieveDestroyAPIView):
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectDetailSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        assigned_tasks = []
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)

        if user.is_admin:
            serializer = self.get_serializer(instance)
            project_details = serializer.data
            assigned_tasks = ProjectPhaseTask.objects.filter(project_phase_id__project_id=instance).order_by('order_number')
            project_phases = ProjectPhase.objects.filter(project_id=instance).distinct()

            project_phases_data = []
            for phase_data in project_phases:
                phase_tasks = [task for task in assigned_tasks if task.project_phase_id.id == phase_data.id and not task.parent_id]
                phase_data_serialized = ProjectPhaseGetSerializer(phase_data).data
                phase_data_serialized['project_phase_tasks'] = ProjectPhaseTaskSerializer(phase_tasks, many=True).data
                project_phases_data.append(phase_data_serialized)

            project_details['project_phases'] = project_phases_data
            return Response({'projectDetails': project_details})
            # serializer = self.get_serializer(instance)
            # return Response({'projectDetails': serializer.data})
        elif partner_admin_user:
            partner_admin_users = User.objects.filter(id__in=partner_admin_user.values_list('user_id', flat=True))
            assigned_tasks = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).order_by('order_number')
            project_phases_phase = ProjectPhase.objects.filter(created_by__in=partner_admin_users, project_id=instance)
            project_phase_tasks = ProjectPhase.objects.filter(project_id=instance, projectphasetask__in=assigned_tasks)
            project_phases = project_phases_phase.union(project_phase_tasks)
            response_data = {
            'id': instance.id,
            'name': instance.name,
            'location_id': instance.location_id.id,
            'location_name': instance.location_id.name if instance.location_id else None,
            'project_status': instance.project_status,
            'project_estimation': instance.project_estimation,
            'start_date': instance.start_date,
            'end_date': instance.end_date,
            'project_phases': ProjectPhaseGetSerializer(project_phases, many=True).data,
            }
            for phase_data in response_data['project_phases']:
                phase_tasks = []
                for task in assigned_tasks:
                    if task.project_phase_id.id == phase_data['id']:
                        if task.parent_id:
                            continue
                        phase_tasks.append(task)
                phase_data['project_phase_tasks'] = ProjectPhaseTaskSerializer(phase_tasks, many=True).data

            return Response({'projectDetails': response_data})
             
        elif user.is_customer and not partner_admin_user:
            assigned_tasks = ProjectPhaseTask.objects.filter(project_phase_id__project_id=instance, assigned_to_user=user).order_by('order_number')
            project_phases = ProjectPhase.objects.filter(project_id=instance,  projectphasetask__in=assigned_tasks).distinct()
        

            response_data = {
                'id': instance.id,
                'name': instance.name,
                'location_id': instance.location_id.id,
                'location_name': instance.location_id.name if instance.location_id else None,
                'project_status': instance.project_status,
                'project_estimation': instance.project_estimation,
                'start_date': instance.start_date,
                'end_date': instance.end_date,
                'project_phases': ProjectPhaseGetSerializer(project_phases, many=True).data,
            }
            for phase_data in response_data['project_phases']:
                phase_tasks = []
                for task in assigned_tasks:
                    if task.project_phase_id.id == phase_data['id']:
                        if task.parent_id:
                            continue
                        phase_tasks.append(task)
                phase_data['project_phase_tasks'] = ProjectPhaseTaskSerializer(phase_tasks, many=True).data

            return Response({'projectDetails': response_data})

        if not user.is_admin and not assigned_tasks:
            raise PermissionDenied()
        # project_phases = ProjectPhase.objects.filter(project_id=instance,  projectphasetask__in=assigned_tasks).distinct()
        

        # response_data = {
        #     'id': instance.id,
        #     'name': instance.name,
        #     'location_id': instance.location_id.id,
        #     'location_name': instance.location_id.name if instance.location_id else None,
        #     'project_status': instance.project_status,
        #     'project_estimation': instance.project_estimation,
        #     'start_date': instance.start_date,
        #     'end_date': instance.end_date,
        #     'project_phases': ProjectPhaseGetSerializer(project_phases, many=True).data,
        # }
        # for phase_data in response_data['project_phases']:
        #     phase_tasks = []
        #     for task in assigned_tasks:
        #         if task.project_phase_id.id == phase_data['id']:
        #             if task.parent_id:
        #                 continue
        #             phase_tasks.append(task)
        #     phase_data['project_phase_tasks'] = ProjectPhaseTaskSerializer(phase_tasks, many=True).data

        # return Response({'projectDetails': response_data})



    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not self.request.user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            if instance.location_id.location_status == 'operating' or instance.location_id.location_status == 'projectmanagement' :
                return Response({'status_code':658, 'error':'Operating/Inprogress location projects cannot be deleted'}, status = 500)
            
            
            self.perform_destroy(instance)
            instance.location_id.location_status = 'pipeline'
            return Response({'message': 'Project deleted successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

#--------------------------------------------------------- TASK FIELDS AND TASK TEMPLATE FIELDS -------------------------------------------------

class CreateTaskFields(generics.CreateAPIView):
    serializer_class = TaskFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        location_id = serializer.instance.project_id.location_id.id
        field_id = serializer.instance.field_id.id
        location_fields = LocationFields.objects.filter(location_id = location_id, field_id=field_id).exists()
        all_locations = Location.objects.all()
        for location in all_locations:
            if not location_fields:
                # location = Location.objects.get(pk=location_id)
                field = Field.objects.get(pk=field_id)
                LocationFields.objects.create(location_id = location, field_id = field, value = None, created_at = timezone.now())
        #Create Task Field Logs
        task_id = serializer.instance.task_id.id
        task = ProjectPhaseTask.objects.get(pk=task_id)
        TaskUpdate.objects.create(task_id = task, user_id = request.user, column_name = 'Task field created', updated_date = timezone.now())
        return Response(serializer.data)
    
class ListTaskFields(generics.ListAPIView):
    queryset = TaskFields.objects.all()
    serializer_class = TaskFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        task_id = self.kwargs.get('task_id')
        return TaskFields.objects.filter(task_id=task_id).order_by('id')
    
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, many=True)
        return Response({'TaskFieldsList':serializer.data})
    
class UpdateTaskFields(generics.UpdateAPIView):
    queryset = TaskFields.objects.all()
    serializer_class = UpdateTaskFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_required_field = instance.is_required
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        is_required = serializer.instance.is_required
        #Task Logs Create
        if is_required_field != is_required:
            TaskUpdate.objects.create(task_id=instance.task_id, user_id = request.user, column_name = 'is_required', updated_date=timezone.now())
        return Response({'taskFields':serializer.data})
    
class DeleteTaskFields(generics.DestroyAPIView):
    queryset = TaskFields.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'TaskField deleted successfully!'})
    
class CreateTaskTemplateFields(generics.CreateAPIView):
    serializer_class = TemplateTaskFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)
    
class ListTaskTemplateFields(generics.ListAPIView):
    queryset = TemplateTaskFields.objects.all()
    serializer_class = TemplateTaskFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        task_id = self.kwargs.get('task_id')
        return TemplateTaskFields.objects.filter(task_id=task_id).order_by('id')
    
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, many=True)
        return Response({'TaskTemplateFieldsList':serializer.data})
    
class DeleteTaskTemplateFields(generics.DestroyAPIView):
    queryset = TemplateTaskFields.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'TaskField deleted successfully!'})
    
class UpdateTemplateTaskFields(generics.UpdateAPIView):
    queryset = TemplateTaskFields.objects.all()
    serializer_class = UpdateTemplateTaskFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'taskFields':serializer.data})
    