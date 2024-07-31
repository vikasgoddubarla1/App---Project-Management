from django.shortcuts import render
from rest_framework import generics, status
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from usermanagement.exceptions import PermissionDenied
import pandas as pd
from django.db.models import Max
from django.db import transaction
import googlemaps
from django.db import transaction
from projectmanagement.models import Project, TaskUpdate
from django.db import connection
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta

import json
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
class CreateCheckList(generics.CreateAPIView):
    serializer_class = CheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied()
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            max_display_order = CheckList.objects.aggregate(models.Max('display_order'))['display_order__max']
            new_display_order = 1 if max_display_order is None else max_display_order + 1
            serializer.save(display_order=new_display_order)
            return Response({'checkList':serializer.data})
        except Exception as e:
            return Response({'error':str(e)}, status=500)
    
class GetCheckList(generics.ListAPIView):
    queryset = CheckList.objects.all().order_by('display_order')
    serializer_class = CheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied()
        try:
            is_master = request.data.get('is_master')
            queryset = self.get_queryset()
            if is_master:
                queryset = queryset.filter(is_master=is_master)
            serializer = self.get_serializer(queryset, many=True)
            return Response({'checkList':serializer.data})
        except Exception as e:
            return Response({'error':str(e)}, status = 500)
        
class CheckListUpdate(generics.UpdateAPIView):
    queryset = CheckList.objects.all()
    serializer_class = CheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'checkList':serializer.data})
        except Exception as e:
            return Response({'error':str(e)}, status = 500)
    
class CheckListDetail(generics.RetrieveAPIView):
    queryset = CheckList.objects.all()
    serializer_class = CheckListDetailSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({'checkListDetails':serializer.data})
        except Exception as e:
            return Response({'error':str(e)}, status = 500)
    
class CheckListDelete(generics.DestroyAPIView):
    queryset = CheckList.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({'checkListDelete':'Checklist deleted successfully!'})
        except Exception as e:
            return Response({'error':str(e)}, status = 500)


class CheckListSorting(generics.CreateAPIView):
    queryset = CheckList.objects.all()
    serializer_class = CheckListSortSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        checklist_order_update = request.data.get('checklist_order_update', [])
        for checklist_order in checklist_order_update:
            checklist_id = checklist_order.get('id')
            new_order_number = checklist_order.get('display_order')
            try:
                checklist = CheckList.objects.get(pk=checklist_id)
            except CheckList.DoesNotExist:
                return Response({'error': f'Checklist with id {checklist_id} does not exist'}, status=404)
            checklist.display_order = new_order_number
            checklist.save()
            
        return Response({'message': 'Checklist order has been updated successfully!'})

#------------------------------------------------------------- CHECK LIST ITEMS VIEWS -------------------------------------------------------------

class CreateCheckListItems(generics.CreateAPIView):
    serializer_class = CheckListItemSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'checkListItems':serializer.data})
    
class CheckListItemUpdate(generics.UpdateAPIView):
    queryset = CheckListItems.objects.all()
    serializer_class = CheckListItemSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid()
        self.perform_update(serializer)
        return Response({'checkListItem':'serializer.data'})
    
class CheckListItemDelete(generics.DestroyAPIView):
    queryset = CheckListItems.objects.all()
    serializer = CheckListItemSerializer
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'CheckListItem deleted successfully!'})
    
#-------------------------------------------------- TASK CHECKLIST ----------------------------------------------------------------------------
class CreateTaskCheckList(generics.CreateAPIView):
    serializer_class = TaskCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        task_id = request.data.get('task_id')
        task = ProjectPhaseTask.objects.get(pk=task_id)
        checklist = request.data.get('checklist_id', [])
        if checklist:
            checklist_id = CheckList.objects.filter(pk__in=checklist)
            for checklists in checklist_id:
                taskchecklists = TaskCheckList.objects.create(
                    task_id = task,
                    checklist_id = checklists
                )
                check_list_id = CheckList.objects.filter(pk=taskchecklists.checklist_id.id)
                checklistitems = CheckListItems.objects.filter(checklist_id__in=check_list_id)
                for checklistitem in checklistitems:
                    task_checklist_id = TaskCheckList.objects.get(pk=taskchecklists.id)
                    TaskCheckListItems.objects.create(
                        taskchecklist_id = task_checklist_id,
                        checklistitems_id = checklistitem
                        
                    )
            return Response({'taskCheckList':'Task check list created successfully'})
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'taskCheckList':serializer.data})
        
class GetTaskCheckList(generics.ListAPIView):
    queryset = TaskCheckList.objects.all().order_by('id')
    serializer_class = TaskCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckList':serializer.data})
    
class TaskCheckListDetail(generics.RetrieveAPIView):
    queryset = TaskCheckList.objects.all().order_by('id')
    serializer_class = TaskCheckListDetailSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'taskCheckListDetail':serializer.data})
    
class TaskCheckListDetailByTaskId(generics.ListAPIView):
    queryset = TaskCheckList.objects.all().order_by('id')
    serializer_class = TaskCheckListDetailSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_id')
        queryset = self.queryset.filter(task_id=task_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckListDetail':serializer.data})

class TaskCheckListDelete(generics.DestroyAPIView):
    queryset = TaskCheckList.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'taskCheckList':'Task checklist and task checklist items deleted successfully!'})

class UpdateTaskCheckList(generics.UpdateAPIView):
    queryset = TaskCheckList.objects.all().order_by('id')
    serializer_class = TaskCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        task_id = request.data.get('task_id')
        task = ProjectPhaseTask.objects.get(pk=task_id)
        checklist_id = request.data.get('checklist_id', [])
        if checklist_id:            
            checklist = CheckList.objects.filter(pk__in = checklist_id)
            if not checklist:
                for checklist in checklist:
                    taskchecklists = TaskCheckList.objects.create(
                        task_id = task_id,
                        checklist_id = checklist
                    )
                    check_list_id = CheckList.objects.filter(pk=taskchecklists.checklist_id.id)
                    checklistitems = CheckListItems.objects.filter(checklist_id__in=check_list_id)
                    for checklistitem in checklistitems:
                        task_checklist_id = TaskCheckList.objects.get(pk=taskchecklists.id)
                        TaskCheckListItems.objects.create(
                            taskchecklist_id = task_checklist_id,
                            checklistitems_id = checklistitem
                            
                        )
            return Response({'taskCheckList':'Task check list created successfully'})
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'taskCheckList':serializer.data})
        
#------------------------------------------------------------- TASK CHECKLIST ITEMS ----------------------------------------------------------

class CreateTaskCheckListItems(generics.CreateAPIView):
    serializer_class = TaskCheckListItemSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'taskCheckListItems':serializer.data})
    
class UpdateTaskCheckListItems(generics.UpdateAPIView):
    queryset = TaskCheckListItems.objects.all().order_by('id')
    serializer_class = TaskCheckListItemUpdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.checked_by = request.user
        instance.save()
        self.perform_update(serializer)
        return Response({'taskCheckListItems':serializer.data})
    
class GetTaskCheckListItems(generics.ListAPIView):
    queryset = TaskCheckListItems.objects.all().order_by('id')
    serializer_class = TaskCheckListItemSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckListitems':serializer.data})
    
class GetTaskCheckListItemByTaskID(generics.RetrieveAPIView):
    queryset = TaskCheckListItems.objects.all().order_by('id')
    serializer_class = TaskCheckListItemListSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_id')
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckListItems':serializer.data})
    
class DeleteTaskCheckListItems(generics.DestroyAPIView):
    queryset = TaskCheckListItems.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'taskCheckListItem':'Task check list item deleted successfully!'})
    
#--------------------------------------------------------- TASK TEMPLATE CHECKLIST ---------------------------------------------------------

class CreateTaskTemplateCheckList(generics.CreateAPIView):
    serializer_class = TaskTemplateCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        task_id = request.data.get('task_id')
        task = ProjectPhaseTaskTemplate.objects.get(pk=task_id)
        checklist = request.data.get('checklist_id', [])
        if checklist:
            checklist_id = CheckList.objects.filter(pk__in=checklist)
            for checklists in checklist_id:
                taskchecklists = TaskTemplateCheckList.objects.create(
                    task_id = task,
                    checklist_id = checklists
                )
                check_list_id = CheckList.objects.filter(pk=taskchecklists.checklist_id.id)
                checklistitems = CheckListItems.objects.filter(checklist_id__in=check_list_id)
                for checklistitem in checklistitems:
                    task_checklist_id = TaskTemplateCheckList.objects.get(pk=taskchecklists.id)
                    TaskTemplateCheckListItems.objects.create(
                        tasktemplatechecklist_id = task_checklist_id,
                        checklistitems_id = checklistitem
                        
                    )
            return Response({'taskCheckList':'Task check list created successfully'})
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({'taskCheckList':serializer.data})
        
class GetTaskTemplateCheckList(generics.ListAPIView):
    queryset = TaskTemplateCheckList.objects.all().order_by('id')
    serializer_class = TaskTemplateCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckList':serializer.data})
    
class TaskTemplateCheckListDetail(generics.RetrieveAPIView):
    queryset = TaskTemplateCheckList.objects.all().order_by('id')
    serializer_class = TaskTemplateCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'taskCheckListDetail':serializer.data})
    
class TaskTemplateCheckListDetailByTaskId(generics.ListAPIView):
    queryset = TaskTemplateCheckList.objects.all().order_by('id')
    serializer_class = TaskTemplateCheckListDetailSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_id')
        queryset = self.queryset.filter(task_id=task_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckListDetail':serializer.data})

class TaskTemplateCheckListDelete(generics.DestroyAPIView):
    queryset = TaskTemplateCheckList.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'taskCheckList':'Task checklist and task checklist items deleted successfully!'})

class UpdateTaskTemplateCheckList(generics.UpdateAPIView):
    queryset = TaskTemplateCheckList.objects.all()
    serializer_class = TaskTemplateCheckListSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        task_id = request.data.get('task_id')
        task = ProjectPhaseTaskTemplate.objects.get(pk=task_id)
        checklist_id = request.data.get('checklist_id', [])
        if checklist_id:            
            checklist = CheckList.objects.filter(pk__in = checklist_id)
            if not checklist:
                for checklist in checklist:
                    taskchecklists = TaskTemplateCheckList.objects.create(
                        task_id = task_id,
                        checklist_id = checklist
                    )
                    check_list_id = CheckList.objects.filter(pk=taskchecklists.checklist_id.id)
                    checklistitems = CheckListItems.objects.filter(checklist_id__in=check_list_id)
                    for checklistitem in checklistitems:
                        task_checklist_id = TaskTemplateCheckList.objects.get(pk=taskchecklists.id)
                        TaskTemplateCheckListItems.objects.create(
                            taskchecklist_id = task_checklist_id,
                            checklistitems_id = checklistitem
                            
                        )
            return Response({'taskCheckList':'Task check list created successfully'})
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'taskCheckList':serializer.data})
    
#-------------------------------------------------------- TASK TEMPLATE CHECKLIST ITEMS------------------------------------------------------------
class CreateTaskTemplateCheckListItems(generics.CreateAPIView):
    serializer_class = TaskTemplateCheckListItemListSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'taskCheckListItems':serializer.data})
    
class UpdateTaskTemplateCheckListItems(generics.UpdateAPIView):
    queryset = TaskTemplateCheckListItems.objects.all()
    serializer_class = TaskTemplateCheckListItemUpdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.checked_by = request.user
        instance.save()
        self.perform_update(serializer)
        return Response({'taskCheckListItems':serializer.data})
    
class GetTaskTemplateCheckListItems(generics.ListAPIView):
    queryset = TaskCheckListItems.objects.all().order_by('id')
    serializer_class = TaskTemplateCheckListItemListSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckListitems':serializer.data})
    
class GetTaskTemplateCheckListItemByTaskID(generics.RetrieveAPIView):
    queryset = TaskTemplateCheckListItems.objects.all().order_by('id')
    serializer_class = TaskTemplateCheckListItemListSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_id')
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'taskCheckListItems':serializer.data})
    
class DeleteTaskTemplateCheckListItems(generics.DestroyAPIView):
    queryset = TaskTemplateCheckListItems.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'taskCheckListItem':'Task check list item deleted successfully!'})


# ------------------------------------------------------------------- TABFIELDS AND LOCATIONFIELDS -------------------------------------------------
class CreateTab(generics.CreateAPIView):
    serializer_class = TabSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'tabDetails':serializer.data})

class ListTab(generics.ListAPIView):
    queryset = Tab.objects.all()
    serializer_class = TabSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'tabDetails':serializer.data})
    
class UpdateTab(generics.UpdateAPIView):
    queryset = Tab.objects.all()
    serializer_class = TabSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'tabDetails':serializer.data})
    
class DeleteTab(generics.DestroyAPIView):
    queryset = Tab.objects.all()
    serializer_class = TabSerializer
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'tabDetails':'Tab deleted successfully!'})
    
class RetrieveTab(generics.RetrieveAPIView):
    queryset = Tab.objects.all()
    serializer_class = TabListSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'tabDetails':serializer.data})
    
    
class CreateField(generics.CreateAPIView):
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def perform_create(self, serializer):
        max_order = Field.objects.aggregate(Max('display_order'))['display_order__max']
        if max_order is None:
            max_order = 0
        serializer.save(display_order=max_order + 1)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        locations = Location.objects.all()
        location_ids = locations.values_list('id', flat=True)
        field_id = serializer.instance
        location_list_exists = LocationFields.objects.filter(location_id__in=location_ids, field_id=field_id).exists()
        
        if not location_list_exists:
            for location in locations:
                LocationFields.objects.create(
                    location_id=location,
                    tab_id = None,
                    field_id=field_id,
                    value = None
                )
        return Response({'fieldDetail':serializer.data})
    
class CreateFieldFromCSV(generics.CreateAPIView):
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error':'No file uploaded'})
        
        try:
            if file.name.endswith('.xlsx'):
                data = pd.read_excel(file, dtype=str)
            elif file.name.endswith('.csv'):
                data = pd.read_csv(file, dtype=str)
            else:
                return Response({'error': 'Unsupported file format please use XLXS or CSV'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            max_display_order = Field.objects.aggregate(max_display_order=models.Max('display_order'))['max_display_order']
            if max_display_order is None:
                max_display_order = 0
            fields_to_create =[]
            for index, row in data.iterrows():
                name = row['Field Name']
                
                if Field.objects.filter(name=name).exists():
                    continue
                field_data = {
                    "name":name,
                    "field_type":row['Field Type'].lower(),
                    "options":eval(row['Options']) if pd.notna(row['Options']) else None,
                    'display_order':max_display_order + 1, 
                }
                serializer = self.get_serializer(data=field_data)
                serializer.is_valid(raise_exception=True)
                fields_to_create.append(serializer)
                max_display_order += 1
            for serializer in fields_to_create:
                serializer.save()
                
            return Response({'status':'Fields created successfully!'})
        except Exception as e:
            return Response({'error':str(e)})
                
                
class ListField(generics.ListAPIView):
    queryset = Field.objects.all().order_by('id')
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class UpdateField(generics.UpdateAPIView):
    queryset = Field.objects.all()
    serializer_class = UpdateFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'fieldDetail':serializer.data})
    
class DeleteField(generics.DestroyAPIView):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'fieldDetail':'field deleted successfully!'})
    
class FieldListSorting(generics.CreateAPIView):
    queryset = Field.objects.all()
    serializer_class = FieldListSortSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        field_order_update = request.data.get('field_order_update', [])
        for field_order in field_order_update:
            field_id = field_order.get('id')
            new_order_number = field_order.get('display_order')
            try:
                checklist = Field.objects.get(pk=field_id)
            except CheckList.DoesNotExist:
                return Response({'error': f'Checklist with id {field_id} does not exist'}, status=404)
            checklist.display_order = new_order_number
            checklist.save()
            
        return Response({'message': 'Checklist order has been updated successfully!'})
    

class CreateTabFields(generics.CreateAPIView):
    serializer_class = TabFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'tabFieldDetails': serializer.data}, status=status.HTTP_201_CREATED)

    
class ListTabFields(generics.ListAPIView):
    queryset = TabFields.objects.all()
    serializer_class = TabFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'tabFieldDetails':serializer.data})
    
class UpdateTabFields(generics.UpdateAPIView):
    queryset = TabFields.objects.all()
    serializer_class = TabFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'tabFieldDetails':serializer.data})
    
class DeleteTabFields(generics.DestroyAPIView):
    queryset = TabFields.objects.all()
    serializer_class = TabFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'tabFieldDetails':'TabFields deleted successfully!'})

#----------------------------------------------------------------- LOCATION FIELDS -------------------------------------------------------------    
class CreateLocationFields(generics.CreateAPIView):
    serializer_class = LocationFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'locationFields':serializer.data})


class UpdateLocationFields(generics.UpdateAPIView):
    queryset = LocationFields.objects.all()
    serializer_class = UpdateLocationFieldSerializer
    permission_classes = (IsAuthenticated,)
        
    def update(self, request, *args, **kwargs):
        module_id = request.data.get('module_id')
        module = None
        if module_id is not None:
            module = GroupModule.objects.get(pk=module_id)
        task_id = request.data.get('task_id')
        task = None
        if task_id is not None:#Used to create task logs
            task = ProjectPhaseTask.objects.get(pk=task_id)
        instance = self.get_object()
        value = instance.value
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        location_field_id = serializer.instance
        if module_id and value != serializer.instance.value:
            ViewLocationFieldsLogs.objects.create(group_module_id = module, location_field_id = location_field_id, updated_at = timezone.now(), updated_by = request.user.id)
        if task_id and value != serializer.instance.value:
            TaskUpdate.objects.create(task_id = task, user_id=request.user, column_name =serializer.instance.field_id.name, updated_date=datetime.now())
                
        return Response({'locationFields':serializer.data})

class DeleteLocationFields(generics.DestroyAPIView):
    queryset = LocationFields.objects.all()
    permission_classes = (IsAuthenticated,)
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'LocationField deleted succesfully!'})
    
class LocationFieldsListbyLocationID(generics.ListAPIView):
    queryset = LocationFields.objects.all()
    serializer_class = LocationFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        location_id = self.kwargs.get('location_id')
        return LocationFields.objects.filter(location_id=location_id).order_by('id')
    
    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, many=True)
        return Response({'TaskTemplateFieldsList':serializer.data})
    
class PipelineListLocationFields(generics.ListAPIView):
    queryset = LocationFields.objects.all().order_by('location_id')
    serializer_class = LocationFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'locationFields':serializer.data})

# class ListLocationFields(generics.ListAPIView):
#     queryset = LocationFields.objects.all().order_by('location_id')
#     serializer_class = LocationFieldSerializer
#     pagination_class = LocationFieldsPagination 

#     def post(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         filters = request.data.get('filters', [])
#         condition_type = request.data.get('condition_type', 'AND').upper()
#         sorting = request.data.get('sorting', [])

#         if filters:
#             location_ids_sets = []

#             for filter_data in filters:
#                 field_id = filter_data.get('field_id')
#                 condition = filter_data.get('condition')
#                 value = filter_data.get('value')
#                 if field_id:
#                     q = Q()
#                     if condition == "equalsto":
#                         q = Q(field_id=field_id, value__iexact=value)
#                     elif condition == "notequalsto":
#                         q = Q(field_id=field_id) & ~Q(value__iexact=value)
#                     elif condition == "greaterthan":
#                         q = Q(field_id=field_id, value__gt=value)
#                     elif condition == "lessthan":
#                         q = Q(field_id=field_id, value__lt=value)
#                     elif condition == "greaterthanorequalsto":
#                         q = Q(field_id=field_id, value__gte=value)
#                     elif condition == "lessthanorequalsto":
#                         q = Q(field_id=field_id, value__lte=value)
#                     elif condition == "contains":
#                         q = Q(field_id=field_id) & Q(value__icontains=value)
#                     elif condition == "doesnotcontain":
#                         q = Q(field_id=field_id) & ~Q(value__icontains=value)
#                     elif condition == "isempty":
#                         q = Q(field_id=field_id, value__isnull=True)
#                     elif condition == "isnotempty":
#                         q = Q(field_id=field_id, value__isnull=False)
#                     # elif condition == "doesnotcontainanyof":
#                     #     values_list = value if isinstance(value, list) else [value]
#                     #     q = Q()
#                     #     for val in values_list:
#                     #         q |= Q(field_id=field_id, value__icontains=val)
#                     #     q = ~q

#                     filtered_location_ids = queryset.filter(q).values_list('location_id', flat=True).distinct()
#                     location_ids_sets.append(set(filtered_location_ids))

#             if condition_type == "AND":
#                 common_location_ids = set.intersection(*location_ids_sets) if location_ids_sets else set()
#             elif condition_type == "OR":
#                 common_location_ids = set.union(*location_ids_sets) if location_ids_sets else set()
#             else:
#                 common_location_ids = set()

#             queryset = queryset.filter(location_id__in=common_location_ids).distinct()

#         # if sorting:
#         for sort_data in sorting:
#             sort_field_id = sort_data.get('field_id')
#             sort_type = sort_data.get('sort_type')
#             if sort_field_id:
#                 if sort_type in ["0to9", "9to0"]:
#                     if sort_type == "0to9":
#                         queryset = queryset.filter(field_id=sort_field_id).annotate(
#                             int_value=Cast('value', IntegerField())
#                         ).order_by(Coalesce('int_value', Value(float('inf'))))
#                     elif sort_type == "9to0":
#                         queryset = queryset.filter(field_id=sort_field_id).annotate(
#                             int_value=Cast('value', IntegerField())
#                         ).order_by(Coalesce('int_value', Value(float('-inf'))).desc())
#                 else:
#                     if sort_type == "atoz":
#                         queryset = queryset.filter(field_id=sort_field_id).order_by(
#                             Coalesce('value', Value('')).asc())
#                     elif sort_type == "ztoa":
#                         queryset = queryset.filter(field_id=sort_field_id).order_by(
#                             Coalesce('value', Value('')).desc())

#         location_ids = queryset.values_list('location_id', flat=True).distinct()
#         locations = self.paginate_queryset(location_ids)

#         if locations is not None:
#             location_fields_data = []
#             for location_id in locations:
#                 location_fields = LocationFields.objects.filter(location_id=location_id)
#                 serializer = self.get_serializer(location_fields, many=True)
#                 location_fields_data.append(serializer.data)
#             return self.get_paginated_response(location_fields_data)

#         all_location_fields = []
#         for location_id in location_ids:
#             location_fields = LocationFields.objects.filter(location_id=location_id)
#             serializer = self.get_serializer(location_fields, many=True)
#             all_location_fields.append(serializer.data)

#         return Response({'locationFields': all_location_fields})


# @method_decorator(csrf_exempt, name='dispatch')
# class ListLocationFields(View):
#    def post(self, request, *args, **kwargs):
#        with connection.cursor() as cursor:
#            cursor.execute("SELECT DISTINCT location_id_id FROM masterdata_locationfields ORDER BY location_id_id")
#            location_ids = cursor.fetchall()
#            location_fields_data = []
#            for location_id in location_ids:
#                location_id = location_id[0]
#                cursor.execute("""SELECT lf.id, lf.location_id_id AS location_id, lf.field_id_id AS field_id, f.name AS field_name, f.field_type AS field_type,
#                        f.options AS field_options, f.display_order AS order_number, lf.value FROM masterdata_locationfields lf
#                    LEFT JOIN masterdata_field f ON lf.field_id_id =f.id WHERE lf.location_id_id = %s ORDER BY lf.location_id_id""", [location_id])
#                rows = cursor.fetchall()
#                fields = []
#                for row in rows:
#                    fields.append({
#                        'id': row[0], 'location_id': row[1], 'field_id': row[2], 'field_name': row[3], 'field_type': row[4], 'field_options': row[5],
#                        'order_number': row[6], 'value': row[7],})
#                locato=location_fields_data.append(fields)
#        return JsonResponse({'locationFields': location_fields_data}, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class ListLocationFields(View):
    def post(self, request, *args, **kwargs):
        body = json.loads(request.body) if request.body else {}
        filters = body.get('filters', [])
        condition_type = body.get('condition_type', 'AND').upper()
        sorting = body.get('sorting', [])

        common_location_ids = set()
        filter_queries = []

        # Fetch all locations if no filters are provided
        with connection.cursor() as cursor:
            if not filters:
                cursor.execute("SELECT DISTINCT location_id_id FROM masterdata_locationfields")
                location_ids = cursor.fetchall()
                common_location_ids = set(location_id[0] for location_id in location_ids)
            else:
                for filter_data in filters:
                    field_id = filter_data.get('field_id')
                    condition = filter_data.get('condition')
                    value = filter_data.get('value')
                    print("Filter Data:", filter_data)
                    if field_id:
                        if condition == "equalsto":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value = '{value}')")
                        elif condition == "notequalsto":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value != '{value}')")
                        elif condition == "greaterthan":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value > '{value}')")
                        elif condition == "lessthan":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value < '{value}')")
                        elif condition == "greaterthanorequalsto":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value >= '{value}')")
                        elif condition == "lessthanorequalsto":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value <= '{value}')")
                        elif condition == "contains":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value LIKE '%{value}%')")
                        elif condition == "doesnotcontain":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value NOT LIKE '%{value}%')")
                        elif condition == "isempty":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value IS NULL)")
                        elif condition == "isnotempty":
                            filter_queries.append(f"(lf.field_id_id = {field_id} AND lf.value IS NOT NULL)")

                location_ids_sets = []
                for query in filter_queries:
                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT DISTINCT location_id_id FROM masterdata_locationfields lf WHERE {query}")
                        filtered_location_ids = cursor.fetchall()
                        location_ids_sets.append(set(location_id[0] for location_id in filtered_location_ids))

                if filters:
                    if condition_type == "AND":
                        common_location_ids = set.intersection(*location_ids_sets) if location_ids_sets else set()
                    elif condition_type == "OR":
                        common_location_ids = set.union(*location_ids_sets) if location_ids_sets else set()

        location_fields_data = []

        if not sorting:
            # Fetch location fields for filtered locations without sorting
            for location_id in common_location_ids:
                with connection.cursor() as cursor:
                    base_query = """
                        SELECT lf.id, lf.location_id_id AS location_id, lf.field_id_id AS field_id, f.name AS field_name,
                               f.field_type AS field_type, f.options AS field_options, f.display_order AS order_number,
                               lf.value
                        FROM masterdata_locationfields lf
                        LEFT JOIN masterdata_field f ON lf.field_id_id = f.id
                        WHERE lf.location_id_id = %s
                    """
                    cursor.execute(base_query, [location_id])
                    rows = cursor.fetchall()

                    fields = []
                    for row in rows:
                        fields.append({
                            'id': row[0],
                            'location_id': row[1],
                            'field_id': row[2],
                            'field_name': row[3],
                            'field_type': row[4],
                            'field_options': row[5],
                            'order_number': row[6],
                            'value': row[7],
                        })

                    location_fields_data.append(fields)
        else:
            sorted_locations = []
            for sort in sorting:
                sort_field_id = sort.get('field_id')
                sort_type = sort.get('sort_type')
                if sort_field_id:
                    sort_order = 'ASC' if sort_type in ['atoz', '0to9'] else 'DESC'
                    sorted_locations_query = f"""
                        SELECT lf.location_id_id, lf.value
                        FROM masterdata_locationfields lf
                        WHERE lf.field_id_id = %s
                        ORDER BY lf.value {sort_order} NULLS LAST
                    """
                    with connection.cursor() as cursor:
                        cursor.execute(sorted_locations_query, [sort_field_id])
                        sorted_locations = cursor.fetchall()
                    break  # Only the first sorting criteria is considered

            for location_id, _ in sorted_locations:
                if location_id in common_location_ids:
                    with connection.cursor() as cursor:
                        base_query = """
                            SELECT lf.id, lf.location_id_id AS location_id, lf.field_id_id AS field_id, f.name AS field_name,
                                   f.field_type AS field_type, f.options AS field_options, f.display_order AS order_number,
                                   lf.value
                            FROM masterdata_locationfields lf
                            LEFT JOIN masterdata_field f ON lf.field_id_id = f.id
                            WHERE lf.location_id_id = %s
                        """
                        cursor.execute(base_query, [location_id])
                        rows = cursor.fetchall()

                        fields = []
                        for row in rows:
                            fields.append({
                                'id': row[0],
                                'location_id': row[1],
                                'field_id': row[2],
                                'field_name': row[3],
                                'field_type': row[4],
                                'field_options': row[5],
                                'order_number': row[6],
                                'value': row[7],
                            })

                        location_fields_data.append(fields)

        return JsonResponse({'locationFields': location_fields_data}, safe=False)


class RetrieveLocationFields(generics.RetrieveAPIView):
    queryset = LocationFields.objects.all().order_by('field_id__display_order')
    serializer_class = LocationFieldSerializer
    permission_classes = (IsAuthenticated,)
        
    def retrieve(self, request, *args, **kwargs):
        location_id = self.kwargs.get('location_id')
        tab_id = request.data.get('tab_id')
        if tab_id:
            queryset = self.queryset.filter(location_id=location_id, tabfields_id__tab_id=tab_id)
        else:
            queryset = self.queryset.filter(location_id=location_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'locationFields':serializer.data})
    
# ------------------------------------------------------ MODULE ---------------------------------------------------------
class CreateGroupModule(generics.CreateAPIView):
    serializer_class = ModuleSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        is_default = request.data.get('is_default')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if is_default== True:
            group_module = GroupModule.objects.filter(is_global= True, is_default=True).first()
            if group_module:
                group_module.is_default=False
                group_module.save()
        self.perform_create(serializer)
        return Response({'moduleDetail':serializer.data})


class CreateUserGroupModule(generics.CreateAPIView):
    queryset = GroupModule.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = (IsAuthenticated,)
    
    
    def create(self, request, *args, **kwargs):
        
        user = request.user
        with transaction.atomic():
            name = request.data.get('name')
            group_module_id = request.data.get('group_module_id')
            is_default = request.data.get('is_default')
            if not group_module_id:
                return Response({'error':'Group module id required'}, status=500)
            
            
            try:
                group_module = GroupModule.objects.get(pk=group_module_id)
            except GroupModule.DoesNotExist:
                return Response({'error':'Group module doesnot exist'})
            
            
            if is_default == True:
                group_module_exist = GroupModule.objects.filter(user_id=user, is_default=True).first()
                print(group_module)
                if group_module_exist:
                    group_module_exist.is_default = False
                    group_module_exist.save()
                    
            new_module = GroupModule.objects.create(
                name = name,
                is_global = False,
                is_default = is_default,
                user_id = request.user,
                created_at = timezone.now()
                
            )
            group_views = GroupView.objects.filter(group_module_id = group_module)
            for group_view in group_views:
                GroupView.objects.create(
                    group_id = group_view.group_id,
                    group_module_id = new_module,
                    order_number = group_view.order_number
                )
            serializer = self.get_serializer(new_module)
            return Response({'userGroup':serializer.data})
        
class UpdateUserGroupModule(generics.UpdateAPIView):
    queryset = GroupModule.objects.filter(is_global=False)
    serializer_class = ModuleUserUpdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        user = request.user
        is_default = request.data.get('is_default')
        instance = self.get_object()
        serializer = self.get_serializer(instance, data = request.data)
        serializer.is_valid(raise_exception=True)
        if is_default== True:
            group_module = GroupModule.objects.filter(user_id=user, is_default=True).first()
            if group_module:
                group_module.is_default=False
                group_module.save()
        serializer.save(is_global=False)
        return Response({'moduleDetail':serializer.data})

class ListGroupModuleByUserID(generics.RetrieveAPIView):
    queryset = GroupModule.objects.filter(is_global=False).order_by('id')
    serializer_class = ListModuleSerializer
    
    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        queryset = self.queryset.filter(user_id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'groupModule':serializer.data})
class UpdateGroupModule(generics.UpdateAPIView):
    queryset = GroupModule.objects.filter(is_global=True)
    serializer_class = ModuleSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        is_default = request.data.get('is_default')
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        if is_default == True:
            group_module = GroupModule.objects.filter(is_global=True, is_default=True).first()
            if group_module:
                group_module.is_default=False
                group_module.save()
        self.perform_update(serializer)
        return Response({'moduleDetail': serializer.data})
    
class RetrieveGroupModule(generics.RetrieveAPIView):
    queryset = GroupModule.objects.filter()
    serializer_class = ListModuleSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"groupModule":serializer.data})
    
    
class GetGroupModule(generics.ListAPIView):
    queryset = GroupModule.objects.filter(is_global=True).order_by('id')
    serializer_class = ListModuleSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'moduleDetail': serializer.data})
    
class DeleteGroupModule(generics.DestroyAPIView):
    queryset = GroupModule.objects.all()
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'moduleDetail': 'Module Deleted Successfully'})
    
# ------------------------------------------------------ GROUPS AND USER GROUPS -----------------------------------------------------------------
class CreateGroup(generics.CreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'groupDetail':serializer.data})
    

class UpdateGroup(generics.UpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'groupDetail':serializer.data})
    


class GetGroup(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupListSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'groupDetail':serializer.data,
        }
        return Response(response_data)

class RetrieveGroup(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupRetrieveSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'groupDetails':serializer.data})
    
class DeleteGroup(generics.DestroyAPIView):
    queryset = Group.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'groupDetail':'Group deleted successfully!'})
    
#---------------------------------------------------------------- GROUP VIEWS ------------------------------------------------------------------
class CreateGroupView(generics.CreateAPIView):
    serializer_class = GroupViewSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        order_number = request.data.get('order_number')
        group_module_id = request.data.get('group_module_id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        #----------- ORDER NUMBER ADDING AUTOMATICALLY ------------------------
        if not order_number:
            existing_views = GroupView.objects.filter(group_module_id = group_module_id)
            max_order_number = existing_views.aggregate(models.Max('order_number'))['order_number__max']
            order_number = (max_order_number or 0) + 1
        serializer.save(order_number = order_number)
        return Response({'groupView':serializer.data})        

class GroupViewSorting(generics.CreateAPIView):
    queryset = GroupView.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        order_number_update = request.data.get('groupview_order_update', [])
        for order_number in order_number_update:
            group_view_id = order_number.get('id')
            new_order_number = order_number.get('order_number')
            try:
                group_view = GroupView.objects.get(pk=group_view_id)
            except GroupField.DoesNotExist:
                return Response({'error': f'Usergroup with id {group_view_id} does not exist'}, status=404)
            group_view.order_number = new_order_number
            group_view.save()
            
        return Response({'message': 'UserGroup order has been updated successfully!'})
    
   
class GroupViewRetrieve(generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        group_module_id = self.kwargs.get('group_module_id')
        group_views = GroupView.objects.filter(pk=group_module_id).order_by('order_number').distinct()
        response_data = {
            'group_module_id': group_module_id,
            'group_module_name': group_views.first().group_module_id.name if group_views.exists() else '',
            'groupList': []
        }
        seen_groups = set()
        for gv in group_views:
            if gv.group_id.id not in seen_groups:
                seen_groups.add(gv.group_id.id)
                response_data['groupList'].append({
                    'id': gv.id,
                    'group_id': gv.group_id.id,
                    'group_name': gv.group_id.name,
                    'order_number': gv.order_number
                })
        return Response({'groupView': response_data})
    
class GroupViewDelete(generics.DestroyAPIView):
    queryset = GroupView.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'Group view deleted successfully!'})

#----------------------------------------------------------------- GROUP FIELD ------------------------------------------------------------------
class CreateGroupField(generics.CreateAPIView):
    serializer_class = GroupFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        group_id = request.data.get('group_id')
        field_id = request.data.get('field_id')
        group_module = request.data.get('group_module_id')
        order_number = request.data.get('order_number')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not order_number:
            max_order_number = GroupField.objects.filter(group_id=group_id, group_module_id=group_module).aggregate(Max('order_number'))['order_number__max'] or 0
            order_number = max_order_number +1
        group_fields = GroupField.objects.filter(group_id=group_id, field_id=field_id, group_module_id=group_module).exists()
        if group_fields:
            return Response({'message':'Field already exists with group'}, status=500)
        serializer.save(order_number=order_number)

        # existing_user_ids = UserGroup.objects.values_list('user_id', flat=True).distinct()
        # users = User.objects.filter(id__in=existing_user_ids)
        
        # field_id = serializer.instance.field_id
        # group_id = serializer.instance.group_id
        # user_group_fields_exist = UserGroup.objects.filter(user_id__in=users, field_id=field_id, group_id=group_id).exists()
        # max_order = UserGroup.objects.aggregate(Max('field_order'))['field_order__max']
        
        # if not user_group_fields_exist:
        #     for user in users:
        #         UserGroup.objects.create(
        #             user_id=user,
        #             group_id=group_id,
        #             field_id=field_id,
        #             field_order=1 if not max_order else max_order + 1,
        #             is_checked=True,
        #             created_at=timezone.now()
        #         )
        
        return Response({'groupFieldDetails': serializer.data})


class UpdateGroupField(generics.UpdateAPIView):
    queryset = GroupField.objects.all()
    serializer_class = GroupFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'groupField':serializer.data})


class UpdateGroupFieldIsHidden(generics.UpdateAPIView):
    queryset = GroupField.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        group_field_ids = request.data.get('group_field_id', [])
        is_hidden = request.data.get('is_hidden')
        group_fields = GroupField.objects.filter(pk__in = group_field_ids)
        group_fields.update(is_hidden=is_hidden)
        return Response({'groupField':"GroupFields updated"})
class GroupFieldList(generics.ListAPIView):
    queryset = GroupField.objects.all().order_by('id')
    serializer_class = GroupFieldSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'groupFields':serializer.data})
    
class DeleteGroupField(generics.DestroyAPIView):
    queryset = GroupField.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        group_id = instance.group_id
        field_id = instance.field_id
        user_groups = UserGroup.objects.filter(group_id = group_id, field_id=field_id).delete()
        self.perform_destroy(instance)
        return Response({'userField':'User Field and associated usergroup is deleted successfully'})
    
class GroupFieldSorting(generics.CreateAPIView):
    queryset = GroupField.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        field_order_update = request.data.get('groupfield_order_update', [])
        for field_order in field_order_update:
            groupfield_id = field_order.get('id')
            group_id = field_order.get('group_id')
            field_id = field_order.get('field_id')
            group_module_id = field_order.get('group_module_id')
            new_order_number = field_order.get('order_number')
            try:
                usergroup = GroupField.objects.get(pk=groupfield_id)
            except GroupField.DoesNotExist:
                return Response({'error': f'Usergroup with id {groupfield_id} does not exist'}, status=404)
            usergroup.order_number = new_order_number
            usergroup.save()
            
        return Response({'message': 'UserGroup order has been updated successfully!'})
    
# -------------------------------------------------------------- USER GROUPS -------------------------------------------------------------------

class CreateUserGroup(generics.CreateAPIView):
    serializer_class = UserGroupSerializer
    permission_classes = (IsAuthenticated,)
        
    def create(self, request, *args, **kwargs):
       created_objects = []
       with transaction.atomic():
           for request in request.data:
               user_id = request.get('user_id')
               group_id = request.get('group_id')
               group_module_id = request.get('group_module_id')
               field_ids = request.get('field_id', [])
               if not all([user_id, group_id]):
                   return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)
               existing_user_groups = UserGroup.objects.filter(user_id=user_id, group_id=group_id, group_module_id=group_module_id).delete()
               field_order = 1
               for field_id in field_ids:
                   user_group = UserGroup(
                       user_id_id=user_id,
                       group_id_id=group_id,
                       group_module_id_id = group_module_id,
                       field_id_id=field_id,
                       field_order = field_order
                   )                   
                   user_group.save() 
                   created_objects.append(user_group)
                   field_order += 1
       serializer = self.get_serializer(created_objects, many=True)
       return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class UpdateUserGroup(generics.UpdateAPIView):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'userGroup':serializer.data})
    
class UpdateUserGroupIsPinned(generics.UpdateAPIView):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupIsPinnedUpdate
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'userGroup', serializer.data})
    
class RetrieveUserGroupByUserID(generics.RetrieveAPIView):
    queryset = UserGroup.objects.all().order_by('id')
    serializer_class = UserGroupSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        queryset = self.queryset.filter(user_id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'userGroup':serializer.data})
    
class DestroyUserGroup(generics.DestroyAPIView):
    queryset = UserGroup.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'userGroup':'user group deleted successfully!'})
    

class UserGroupFieldSorting(generics.CreateAPIView):
    queryset = UserGroup.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        field_order_update = request.data.get('usergroup_order_update', [])
        for field_order in field_order_update:
            usergroup_id = field_order.get('id')
            user_id = field_order.get('user_id')
            group_id = field_order.get('group_id')
            field_id = field_order.get('field_id')
            module_id = field_order.get('group_view_id')
            new_order_number = field_order.get('field_order')
            try:
                usergroup = UserGroup.objects.get(pk=usergroup_id)
            except UserGroup.DoesNotExist:
                return Response({'error': f'Usergroup with id {usergroup_id} does not exist'}, status=404)
            usergroup.field_order = new_order_number
            usergroup.save()
            
        return Response({'message': 'UserGroup order has been updated successfully!'})
    

# -----------------------------PROJECT PHASE TASK FIELDS-----------------------

class CreateProjectPhaseTaskFields(generics.CreateAPIView):
    serializer_class = ProjectPhaseTaskFieldsCreateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'projectPhaseTaskFields':serializer.data})
    
class UpdateProjectPhaseTaskFields(generics.UpdateAPIView):
    queryset = ProjectPhaseTaskFields.objects.all()
    serializer_class = ProjectPhaseTaskFieldsUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args,**kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'projectPhaseTaskFields':serializer.data})
    
class GetProjectPhaseTaskFields(generics.ListAPIView):
    queryset = ProjectPhaseTaskFields.objects.all().order_by('id')
    serializer_class = ProjectPhaseTaskFieldsCreateSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'projectPhaseTaskFields': serializer.data})

class RetrieveProjectPhaseTaskFields(generics.RetrieveAPIView):
    queryset = ProjectPhaseTaskFields.objects.all()
    serializer_class = ProjectPhaseTaskFieldsCreateSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
class DeleteProjectPhaseTaskFields(generics.DestroyAPIView):
    queryset = ProjectPhaseTaskFields.objects.all()
    permission_classes = (IsAuthenticated,)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object
        self.perform_destroy(instance)
        return Response({'projectPhaseTaskFields': 'Task Field Deleted Successfully'})
    
class RetrieveProjectPhaseTaskFieldsByTaskId(generics.RetrieveAPIView):
    queryset = ProjectPhaseTaskFields.objects.all().order_by('id')
    serializer_class = ProjectPhaseTaskFieldsCreateSerializer
    permission_classes = (IsAuthenticated,)
    
    def retrieve(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_id')
        queryset = self.queryset.filter(task_id=task_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'userGroup':serializer.data})


class FieldCreateWithCSV(generics.CreateAPIView):
    serializer_class = FieldSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied()
        file = request.FILES['file']
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, header=None)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, header=None)
        else:
            return Response({'error': 'Unsupported file format'}, status=status.HTTP_400_BAD_REQUEST)
        
        if df.shape[0] < 3:
            return Response({'error': 'File must contain at least three rows: field names, field types, and values'}, status=status.HTTP_400_BAD_REQUEST)

        field_names = df.iloc[0].tolist()
        field_types = df.iloc[1].tolist()
        mandatory_columns = ['Project-ID', 'City', 'Zip-Code']
        if not all(column in field_names for column in mandatory_columns):
            missing_columns = [col for col in mandatory_columns if col not in field_names]
            return Response({'error': f'Missing mandatory columns: {", ".join(missing_columns)}'}, status=status.HTTP_400_BAD_REQUEST)

        max_display_order = Field.objects.aggregate(max_order=models.Max('display_order'))['max_order'] or 0

        fields_to_create = []
        display_order = max_display_order + 1 
        for name, field_type in zip(field_names, field_types):
            if Field.objects.filter(name=name).exists():
                field = Field.objects.get(name=name)
                
                if field.field_type != field_type:
                    if field.field_type == 'dependency':
                        continue
                    field.field_type = field_type
                    field.save()
                if field.field_type == 'dropdown':
                    options_column_index = field_names.index(name)
                    new_options = df.iloc[2:, options_column_index].dropna().unique().tolist()
                    existing_options = field.options or []
                    
                    existing_option_values = {option['name'] for option in existing_options}
                    
                    for option in new_options:
                        if option not in existing_option_values:
                            existing_options.append({'label': option, 'name': option})
                    
                    existing_options_with_ids = [{'id': idx + 1, 'name': option['name']} for idx, option in enumerate(existing_options)]
                    field.options = existing_options_with_ids
                    field.save()
                continue 

            if field_type == 'dropdown':
                options_column_index = field_names.index(name)
                options = df.iloc[2:, options_column_index].dropna().unique().tolist()
                options_with_ids = [{'id': idx + 1, 'name': option} for idx, option in enumerate(options)]
            else:
                options_with_ids = None

            field_data = {
                'name': name,
                'field_type': field_type,
                'options': options_with_ids,
                'display_order': display_order
            }
            try:
                field_serializer = FieldSerializer(data=field_data)
                if field_serializer.is_valid():
                    fields_to_create.append(Field(**field_serializer.validated_data))
                    display_order += 1
                else:
                    continue
            except Exception as e:
                continue

        Field.objects.bulk_create(fields_to_create)
        projects_to_create = []
        for i in range(2, df.shape[0]):
            row = df.iloc[i]
            project_name = row[field_names.index('Project-ID')]
            city = row[field_names.index('City')]
            zipcode = row[field_names.index('Zip-Code')]
            street = row[field_names.index('Street')]
            location, created = Location.objects.get_or_create(
                name=city,
                city=city,
                zipcode=zipcode,
                project_number=project_name,
                address_line_1=street
            )
            
            api_key = 'AIzaSyBlnDVhQGJz3Jt3LNEr9wto14s3kut72tI'
            gmaps = googlemaps.Client(key=api_key)
            address = f"{location.name}, {location.city}, {location.zipcode}"
            geocoded_result = gmaps.geocode(address)
            
            if geocoded_result:
                latitude = geocoded_result[0]['geometry']['location']['lat']
                longitude = geocoded_result[0]['geometry']['location']['lng']

                location.location_latitude = latitude
                location.location_longitude = longitude
                location.save()

            project, created = Project.objects.update_or_create(
                location_id=location,
                project_id=project_name,
                defaults={
                    'name': location.city,
                    'start_date': None,  
                    'end_date': None,  
                    'project_estimation': None,
                    'total_target_kWp': 0,
                }
            )
            
            for name, value in zip(field_names, row):
                field = Field.objects.filter(name=name).first()
                if not field:
                    continue
                
                if pd.isna(value) or value == "-" or value == "n.a.":
                    value = None
                    
                if field.field_type == 'date' and value:
                    try:
                        value = pd.to_datetime(value, errors='coerce')
                        if pd.isnull(value):
                            value = None
                        else:
                            value = value.strftime('%d.%m.%Y')
                    except Exception as e:
                        value = None
                
                location_field, created = LocationFields.objects.update_or_create(
                    location_id=location,
                    field_id=field,
                    defaults={'value': value, 'value_json': None}
                )
                if not created:
                    location_field.value = value
                    location_field.save()
                
        return Response({'success': 'Fields, Locations, and LocationFields created/updated successfully'}, status=status.HTTP_201_CREATED)



#--------------------------------------------------- VIEW LOCATION FIELDS LOGS -------------------------------------------------------------------

class ViewLocationFieldLogsbyModule(generics.ListAPIView):
    queryset = ViewLocationFieldsLogs.objects.all()
    serializer_class = ViewLocationFieldLogSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        group_module_id = self.kwargs.get('group_module_id')
        from_date = self.request.data.get('from')
        to_date = self.request.data.get('to')
        
        queryset = ViewLocationFieldsLogs.objects.filter(group_module_id=group_module_id)
        
        if from_date:
            from_date = parse_datetime(from_date)
            queryset = queryset.filter(updated_at__gte=from_date)
        
        if to_date:
            to_date = parse_datetime(to_date)
            to_date = to_date + timedelta(days=1)
            queryset = queryset.filter(updated_at__lte=to_date)
            
        latest_updates = queryset.order_by('location_field_id', '-updated_at').distinct('location_field_id')
        
        return latest_updates
    
    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, many=True)
        return Response({'viewLocationFieldLogs': serializer.data})
