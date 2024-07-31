from django.shortcuts import render
from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from usermanagement.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, APIException
from django.utils import timezone
from django.db.models import Q
from partners.pagination import CustomPagination
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from locations.models import Location
from partners.models import *
from .functions import *
import os
from solar_project.permission_middleware import check_permission_user
from notifications.models import Notification

from django.conf import settings
class CreateContract(generics.CreateAPIView):
    serializer_class = CreateContractSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        partner_id = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        if not request.user.is_admin and not (partner_admin_user and partner_id):
            return Response({'status_code': 605, 'error': 'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            begin_date = serializer.validated_data.get('begin_date')
            duration = serializer.validated_data.get('duration')
            duration_cycle = serializer.validated_data.get('duration_cycle')            
            category_id = serializer.validated_data.get('category_id')
            sub_category_id = serializer.validated_data.get('sub_category_id')
            end_date = serializer.validated_data.get('end_date')
            made_by = serializer.validated_data.get('made_by')
            made_by_type = serializer.validated_data.get('made_by_type')
            made_to = serializer.validated_data.get('made_to')
            made_to_type = serializer.validated_data.get('made_to_type')
            auto_extended = serializer.validated_data.get('auto_extended')
            extend_duration = serializer.validated_data.get('extend_duration')
            extend_cycle = serializer.validated_data.get('extend_cycle')
            termination_duration = serializer.validated_data.get('termination_duration')
            termination_cycle = serializer.validated_data.get('termination_cycle')
            termination_date = serializer.validated_data.get('termination_date')

            if category_id and category_id.id != 1 and sub_category_id:
                return Response({'status_code': 676, "error": "Sub-categories are only allowed for category_id 1."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if not end_date:
                if duration_cycle == 'days':
                    end_date = begin_date + timedelta(days=duration)
                elif duration_cycle == 'weeks':
                    end_date = begin_date + timedelta(weeks=duration)
                elif duration_cycle == 'months':
                    end_date = begin_date + relativedelta(months=duration) - timedelta(days=1)
                elif duration_cycle == 'years':
                    end_date = begin_date + relativedelta(years=duration) - timedelta(days=1)
                else:
                    raise ValidationError('Duration and duration cycle are required.')
            serializer.save(end_date=end_date)  
            contract = serializer.instance
            contract.created_by=request.user
            if auto_extended:
                auto_extend_end_date(self, contract, extend_duration, extend_cycle)
                calculate_termination_date(self, contract, termination_duration, termination_cycle)       
            contract.save()                          
            contract_id = Contract.objects.get(pk=contract.id)
            create_contract_approvals(self, contract, made_by.id, made_by_type.id, made_to.id, made_to_type.id)
            create_contract_logs(self, contract_id, request.user, 'Contract Created')
            response_data = {'contractDetails': serializer.data}
            return Response(response_data)
        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ContractList(generics.ListCreateAPIView):
    queryset = Contract.objects.all().order_by('id')
    serializer_class = ContractListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    
    def list(self, request, *args, **kwargs):
        return Response({'details': 'Please use the POST method to filter partners.'}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        user = self.request.user
        queryset = Contract.objects.all().order_by('id')
        obj = [queryset, 'contracts', 'contract-general', 1]
        status = self.request.data.get('status')
        category_id = self.request.data.get('category_id')
        made_by     = self.request.data.get('made_by')
        made_to = self.request.data.get('made_to')
        location_id = self.request.data.get('location_id')
        search_keyword = self.request.data.get('search_keyword')
        is_active       = self.request.data.get('is_active')
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin=True)
        if partner_admin_user:
            partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
            type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
            approved_contracts = ContractApprovals.objects.filter(
                partner_id__in=partner_ids,
                type_id__in=type_ids
            ).values_list('contract_id', flat=True)
            
            queryset = queryset.filter(
                Q(Q(made_by__in=partner_ids) & Q(made_by_type__in=type_ids)) |
                Q(Q(made_to__in=partner_ids) & Q(made_to_type__in=type_ids)) | Q(id__in=approved_contracts)
            ).filter(
                Q(approval_status='review') |
                Q(approval_status='published') |
                Q(created_by=user)
            )
        elif user.is_admin:
            pass
        else:
            has_permission = check_permission_user(self, self.request, obj)
            if not has_permission:
                queryset = Contract.objects.none()
        
        filter_params = Q()
        if category_id:
            filter_params &= Q(category_id=category_id)
        if location_id:
            filter_params &= Q(location_id=location_id)
        if made_by:
            filter_params &= Q(made_by=made_by)
        if made_to:
            filter_params &= Q(made_to = made_to)
        if status:
            filter_params &= Q(status__icontains=status)
        if is_active:
            filter_params &= Q(is_active = is_active)

        queryset = queryset.filter(filter_params)

        if search_keyword:
            queryset = queryset.filter(Q(name__icontains=search_keyword) | Q(contract_number__icontains=search_keyword))
        
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            user = request.user
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = {
                    "contractDetails":serializer.data,
                    "paginationDetails": {
                        "current_page": self.paginator.page.number,
                        "number_of_pages": self.paginator.page.paginator.num_pages,
                        "total_items"    : self.paginator.page.paginator.count,
                        "current_page_items": len(serializer.data),
                        "next_page"      : self.paginator.get_next_link(),
                        "previous_page"  : self.paginator.get_previous_link(),
                    }
                }
                return self.get_paginated_response(response_data)

            return Response({"partners": []})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContractGeneralUpdate(generics.UpdateAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractGeneralSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user = request.user
            obj = [instance.id, 'contracts', 'contract-general', 3]
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
            partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
            type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
            if not request.user.is_admin: #and not (partner_admin_user and (instance.made_by_id in partner_ids or instance.made_to_id in partner_ids) and not (instance.made_by_type in type_ids or instance.made_to_type in type_ids)): 
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    raise PermissionDenied()
            if instance.approval_status == 'published':
                return Response({'error':'You cannot update published contracts, please contact support'}, status=400)
            
            updated_fields = []
            field_names_mapping = {'location_id':'location', 'category_id':'category', 'sub_category_id':'sub category', 'made_by':'made by', 'made_by_type':'made by type', 'made_to': 'made to', 'made_to_type': 'made to type', 'contract_number':'contract number'}
              
            if 'location_id' in request.data and instance.location_id is not None and instance.location_id.id != request.data['location_id']:
                updated_fields.append(field_names_mapping['location_id'])
            if 'name' in request.data and instance.name != request.data['name']:
                updated_fields.append('name')
            if 'category_id' in request.data and instance.category_id is not None and instance.category_id.id != request.data['category_id']:
                updated_fields.append(field_names_mapping['category_id'])
            if 'sub_category_id' in request.data and instance.sub_category_id is not None and instance.sub_category_id.id != request.data['sub_category_id']:
                updated_fields.append(field_names_mapping['sub_category_id'])
            if 'made_by' in request.data and instance.made_by is not None and instance.made_by.id != request.data['made_by']:
                updated_fields.append(field_names_mapping['made_by'])
            if 'made_by_type' in request.data and instance.made_by_type is not None and instance.made_by_type.id != request.data['made_by_type']:
                updated_fields.append(field_names_mapping['made_by_type'])
            if 'made_to' in request.data and instance.made_to is not None and instance.made_to.id != request.data['made_to']:
                updated_fields.append(field_names_mapping ['made_to'])
            if 'made_to_type' in request.data and instance.made_to_type is not None and instance.made_to_type.id != request.data['made_to_type']:
                updated_fields.append(field_names_mapping['made_to_type'])
            if 'contract_number' in request.data and instance.contract_number is not None and instance.contract_number != request.data['contract_number']:
                updated_fields.append(field_names_mapping['contract_number'])
            
            if updated_fields:
                user = request.user
                for field_name in updated_fields:
                    column_name = field_name
                    create_contract_logs(self, instance, request.user, column_name)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            existing_location_id = instance.location_id.id if instance.location_id else None
            new_location_id = request.data.get('location_id')
            location_changed = existing_location_id != new_location_id

            made_by_changed = instance.made_by_id != request.data.get('made_by')
            made_to_changed = instance.made_to_id != request.data.get('made_to')
            contract_id = instance.id
            contract = Contract.objects.get(pk=contract_id)
            contract_data = ContractApprovals.objects.filter(contract_id=instance)
            if location_changed or made_by_changed or made_to_changed:
                contract_data.delete()
            self.perform_update(serializer)
            if not contract_data:
                create_contract_approvals(self, contract, instance.made_by.id, instance.made_by_type.id, instance.made_to.id, instance.made_to_type.id)
            partner_admin_made_to = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = instance.made_to, partner_types_role_id__type_id=instance.made_to_type)
            partner_admin_made_by = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = instance.made_by, partner_types_role_id__type_id=instance.made_by_type)
            partner_admin_user = partner_admin_made_by |partner_admin_made_to
            for user in partner_admin_user:
                user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
                fullname = f"{request.user.firstname} {request.user.lastname}"
                create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Contract General Details Updated", contract.id, contract.name,
                                            request.user.id, fullname, contract.location_id.name if contract.location_id else None, 'contract', None)
            
            return Response({'contractDetails':serializer.data})
        except ValidationError as error:
            return Response({'error':error.detail}, status = 500)
        except Exception as e:
            return Response({'error':str(e)}, status = 500)
class ContractPermanentDelete(generics.DestroyAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractListSerializer
    permission_classes = (IsAuthenticated,)
       
    def destroy(self, request, *args, **kwargs):
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       try:
           instance = self.get_object()
           self.perform_destroy(instance)
           return Response({'message':'Contract permanently deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ContractTrashDelete(generics.DestroyAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractListSerializer
    permission_classes = (IsAuthenticated,)
       
    def destroy(self, request, *args, **kwargs):
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       try:
           instance = self.get_object()
           if instance.approval_status == "review" or instance.approval_status == "published":
               return Response({'status_code':686, 'error':'You cannot delete review or published contracts'}, status = 500)
           instance.is_active = False
           instance.save()
           return Response({'message':'Contract deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
class ContractRestoreUpdate(generics.UpdateAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractRestoreSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'message':'Contract restored successfully'}, status=200)


class ContractDurationUpdateView(generics.UpdateAPIView):
    serializer_class = ContractDurationUpdateSerializer
    queryset = Contract.objects.all()
    permission_classes = (IsAuthenticated,)
    

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        obj = [instance.id, 'contracts', 'contract-duration', 3]
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        if not request.user.is_admin: # and not (partner_admin_user and (instance.made_by_id in partner_ids or instance.made_to_id in partner_ids) and not (instance.made_by_type in type_ids or instance.made_to_type in type_ids)): 
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                raise PermissionDenied()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception = True)
        begin_date = serializer.validated_data['begin_date']
        duration = serializer.validated_data['duration']
        duration_cycle = serializer.validated_data['duration_cycle']
        auto_extended = serializer.validated_data['auto_extended']
        extend_duration = serializer.validated_data['extend_duration']
        extend_cycle    = serializer.validated_data['extend_cycle']
        is_terminated = serializer.validated_data['is_terminated']
        termination_duration = serializer.validated_data['termination_duration']
        termination_cycle = serializer.validated_data['termination_cycle']
        
        updated_fields = []
        field_names_mapping = {'begin_date':'begin date', 'duration_cycle':'duration cycle', 'auto_extended':'auto extended', 'extend_duration':'extend_duration', 'extend_cycle':'extend_cycle', 'is_terminated':'is terminated', 'termination_duration':'termination duration', 'termination_cycle':'termination cycle'}
    
        if 'begin_date' in request.data and str(instance.begin_date) != request.data['begin_date']:
            updated_fields.append(field_names_mapping['begin_date'])
        if 'duration' in request.data and instance.duration != request.data['duration']:
            updated_fields.append('duration')
        if 'duration_cycle' in request.data and instance.duration_cycle != request.data['duration_cycle']:
            updated_fields.append(field_names_mapping['duration_cycle'])
        if 'auto_extended' in request.data and instance.auto_extended != request.data['auto_extended']:
            updated_fields.append(field_names_mapping['auto_extended'])
        if 'extend_duration' in request.data and instance.extend_duration != request.data['extend_duration']:
            updated_fields.append(field_names_mapping['extend_duration'])
        if 'extend_cycle' in request.data and instance.extend_cycle != request.data['extend_cycle']:
            updated_fields.append(field_names_mapping['extend_cycle'])
        if 'is_terminated' in request.data and instance.is_terminated != request.data['is_terminated']:
            updated_fields.append(field_names_mapping['is_terminated'])
        if 'termination_duration' in request.data and instance.termination_duration != request.data['termination_duration']:
            updated_fields.append(field_names_mapping['termination_duration'])
        if 'termination_cycle' in request.data and instance.termination_cycle != request.data['termination_cycle']:
            updated_fields.append(field_names_mapping['termination_cycle'])
    
        if updated_fields:
            for field_name in updated_fields:
                column_name = field_name
                create_contract_logs(self, instance, request.user, column_name)
        
        calculate_end_date(self, instance, begin_date, duration, duration_cycle)
        
        if auto_extended:
            auto_extend_end_date(self, instance, extend_duration, extend_cycle)
            calculate_termination_date(self, instance, termination_duration, termination_cycle)
        today = timezone.now().date()
        if is_terminated and today < instance.termination_date:
            return Response({'status_code':682, 'message': f"is_terminated cannot be enabled now. It can be enabled from {instance.termination_date}."}, status=status.HTTP_400_BAD_REQUEST)
        if is_terminated:
            instance.terminated_on = timezone.now().date()
        
        instance.save()
        self.perform_update(serializer)
        partner_admin_made_to = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = instance.made_to, partner_types_role_id__type_id=instance.made_to_type)
        partner_admin_made_by = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = instance.made_by, partner_types_role_id__type_id=instance.made_by_type)
        partner_admin_users = partner_admin_made_by |partner_admin_made_to
        if not instance.approval_status == "draft":
            for user in partner_admin_users:
                user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
                fullname = f"{request.user.firstname} {request.user.lastname}"
                create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Contract Duration Details Updated", instance.id, instance.name,
                                            request.user.id, fullname, instance.location_id.name if instance.location_id else None, 'contract', None)
        return Response(serializer.data)
class ContractFrameworkCreateView(generics.CreateAPIView):
    queryset = ContractFramework.objects.all()
    serializer_class = ContractFrameworkSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        contract_id = kwargs.get('contract_id')
        individual_contract_ids = []

        for key in request.data.keys():
            if key.startswith('individual_contract_id[') and key.endswith(']'):
                individual_contract_ids.append(int(request.data[key]))

        if not contract_id or not individual_contract_ids:
            return Response({'status_code':583, "error": "contract_id and individual_contract_id are required."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            return Response({"error": "Contract not found."}, status=404)

        if contract.category_id_id != 2:
            return Response({'status_code':683, "error": "This contract does not belong to the group contract."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        individual_contracts = Contract.objects.filter(pk__in=individual_contract_ids)
        for individual_contract in individual_contracts:
            if individual_contract.category_id_id != 1: 
                return Response({'status_code':684, "error": f"The individual contract with ID {individual_contract.id} does not belong to the individual category."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        contract_framework_data = {
            "contract_id": contract_id,
            "individual_contract_id": individual_contract_ids,
        }

        serializer = self.get_serializer(data=contract_framework_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_data = {
            "id": serializer.data['id'],
            "contract_id": contract_id,
            "contract_name": contract.name,
            "individualContractDetails": [
                {
                    "individual_contract_id": item['id'],
                    "individual_contract_name": item['name']
                }
                for item in individual_contracts.values('id', 'name')
            ]
        }

        return Response({'contractFrameworkDetails':response_data}, status=201)

class ContractFileCreate(generics.CreateAPIView):
    queryset = ContractFile.objects.all()
    serializer_class = ContractFileSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        contract_id = self.kwargs.get('contract_id')
        contract = Contract.objects.get(pk=contract_id)
        obj = [contract, 'contracts', 'contract-files', 2]
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        if not request.user.is_admin and not (partner_admin_user and (contract.made_by_id in partner_ids or contract.made_to_id in partner_ids) and not (contract.made_by_type in type_ids or contract.made_to_type in type_ids)): 
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                raise PermissionDenied()
        
        if contract.category_id.id == 2:
            return Response({'status_code':685, 'error': 'Grouped contracts are not allowed to post files.'}, status=status.HTTP_400_BAD_REQUEST)
        
        files_data = []

        for file in request.FILES.getlist('file_url'):
            
            upload_dir = os.path.join('files/contractfiles/', str(contract_id))

           
            full_upload_dir = os.path.join(settings.MEDIA_ROOT, upload_dir)
            os.makedirs(full_upload_dir, exist_ok=True)

            
            original_file_name, file_extension = os.path.splitext(file.name)
            new_file_name = original_file_name + file_extension

           
            counter = 1
            while os.path.exists(os.path.join(settings.MEDIA_ROOT, upload_dir, new_file_name)):
                new_file_name = f"{original_file_name}_copy({counter}){file_extension}"
                counter += 1

            file_path = os.path.join(upload_dir, new_file_name)

            
            with open(os.path.join(settings.MEDIA_ROOT, file_path), 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            contract_file = ContractFile.objects.create(contract_id=contract, file_url=file_path)
            file_data = {
                'id': contract_file.id,
                'url': request.build_absolute_uri(contract_file.file_url.url)
            }
            files_data.append(file_data)

        response_data = {
            'contractFileDetails': {
                'contract_id': contract.id,
                'contract_name': contract.name,
                'files': files_data,
            }
        }
        create_contract_logs(self, contract, request.user, 'File Upload')
        partner_admin_made_to = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = contract.made_to, partner_types_role_id__type_id=contract.made_to_type)
        partner_admin_made_by = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = contract.made_by, partner_types_role_id__type_id=contract.made_by_type)
        partner_admin_user = partner_admin_made_by |partner_admin_made_to
        for user in partner_admin_user:
            user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
            fullname = f"{request.user.firstname} {request.user.lastname}"
            create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Contract File Created", contract.id, contract.name,
                                        request.user.id, fullname, contract.location_id.name if contract.location_id else None, 'contract', None)
        return Response(response_data)

    
class ContractFileDelete(generics.DestroyAPIView):
    serializer_class = ContractFileSerializer
    permission_classes = (IsAuthenticated, )
    
    def destroy(self, request, *args, **kwargs):
        contractfile_id = self.kwargs['id']
        contract_id = self.kwargs['contract_id']
        
        obj = [contract_id, 'contracts', 'contract-files', 4]
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        if not request.user.is_admin and not (partner_admin_user and (contract.made_by_id in partner_ids or contract.made_to_id in partner_ids) and not (contract.made_by_type in type_ids or contract.made_to_type in type_ids)): 
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                raise PermissionDenied()
        
        # if not request.user.is_admin:
        #    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        try:
            contractfile = ContractFile.objects.get(pk=contractfile_id)
            contract = Contract.objects.get(pk=contract_id)

            contractfile.delete()
            create_contract_logs(self, contract, request.user, 'Deleted File')

            return Response({'error':'File removed successfully!'}, status=status.HTTP_200_OK)
        except (ContractFile.DoesNotExist, Contract.DoesNotExist):
            return Response({'error':'File or location doesnot exists'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)



class ContractDetail(generics.RetrieveDestroyAPIView):
    queryset = Contract.objects.filter(is_active=True).order_by('id')
    serializer_class = ContractListSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        try:
            serializer = self.get_serializer(instance)
            contract_data = serializer.data
            return Response({'contractDetails': contract_data})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def destroy(self, request, *args, **kwargs):
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       try:
           instance = self.get_object()
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           self.perform_destroy(instance)
           return Response({'message': 'Contract deleted successfully'}, status=status.HTTP_200_OK)
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
       

class ContractCategoryList(generics.ListAPIView):
    queryset = ContractCategory.objects.all().order_by('id')
    serializer_class = ContractCategorySerializer
    
    def list(self, request, *args, **kwargs): 
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many = True)
        data = {"contractCategories": serializer.data}
        return Response(data)
class ContractApprovalStatusUpdate(generics.UpdateAPIView):
    queryset = Contract.objects.all()
    serializer_class = ContractListSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        approval_status_reset = request.data.get('approval_status_reset', False)
        user = request.user
        instance = self.get_object()
        made_to = instance.made_to.id if instance.made_to else None
        made_by = instance.made_by.id if instance.made_by else None
        made_by_type = instance.made_by_type.id if instance.made_by_type else None
        made_to_type = instance.made_to_type.id if instance.made_to_type else None
        
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        try:
            if not request.user.is_admin: #and not (partner_admin_user and (made_to in partner_ids or made_by in partner_ids) and not (made_to_type in type_ids or made_by_type in type_ids)):
                raise PermissionDenied()
            approval_status_reset = request.data.get('approval_status_reset', False)  # Set default value to False

            if 'approval_status' in request.data and instance.approval_status != request.data['approval_status']:
                if request.data['approval_status'] == 'review' and approval_status_reset == True:
                    contract_approvals = ContractApprovals.objects.filter(contract_id = instance.id)
                    if contract_approvals.exists():
                        for contract_approval in contract_approvals:
                            contract_approval.is_approved = None
                            contract_approval.comments = None
                            contract_approval.approved_by = None
                            contract_approval.save()
                elif request.data['approval_status'] == 'review' and approval_status_reset == False:
                    contract_approvals = ContractApprovals.objects.filter(contract_id = instance.id, is_approved='reject')
                    if contract_approvals.exists():
                        for contract_approval in contract_approvals:
                            contract_approval.is_approved = None
                            contract_approval.comments = None
                            contract_approval.approved_by = None
                            contract_approval.save()
                # create_contract_logs(self, instance, request.user, instance.approval_status)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            create_contract_logs(self, instance, request.user, f'contract status updated to {instance.approval_status}')
            # contract_approved_all = ContractApprovals.objects.filter(contract_id=instance.id)
            # if contract_approved_all.exists() and contract_approved_all.count() == contract_approved_all.filter(is_approved='approve').count():
            #     instance.approval_status = "published"
            #     instance.save()
            if instance.approval_status == "review" or instance.approval_status == "published": #and approval_status_reset ==True:
                contract_notifications = Notification.objects.filter(data_id = instance.id, source='contract')
                contract_notifications.delete()
                contract_approval_partners = ContractApprovals.objects.values_list('partner_id').distinct()
                contract_approval_types = ContractApprovals.objects.values_list('type_id').distinct()
                partner_admin_user = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id__in = contract_approval_partners, partner_types_role_id__type_id__in=contract_approval_types)
                
                for user in partner_admin_user:
                    user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
                    fullname = f"{request.user.firstname} {request.user.lastname}"
                    if approval_status_reset == True:
                        create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Partner Contract Is Created", instance.id, instance.name,
                                                request.user.id, fullname, instance.location_id.name if instance.location_id else None, 'contract', None)
                        create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Contract Approvals Created", instance.id, instance.name,
                                        request.user.id, fullname, instance.location_id.name if instance.location_id else None, 'contract', None)
                    else:
                        create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", f"Contract Status Updated To {instance.approval_status}", instance.id, instance.name,
                                        request.user.id, fullname, instance.location_id.name if instance.location_id else None, 'contract', None)
        
            return Response(serializer.data)
        except ValidationError as e:
            return Response({'error': e.detail}, status = 500)
        except Exception as error:
            return Response({'error':str(error)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
# class ContractListByLocation(generics.RetrieveAPIView):
#     queryset = Contract.objects.filter(is_active=True).order_by('id')
#     serializer_class = ContractListSerializer
#     permission_classes = (IsAuthenticated,)
    
#     def get_object(self):
#         location_id = self.kwargs.get('location_id')
#         return Contract.objects.filter(location_id=location_id)
    
#     def retrieve(self, request, *args, **kwargs):
#         partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)

#         if request.user.is_admin:
#             try:
#                 instance = self.get_object()
#                 serializer = self.get_serializer(instance, many=True)
#                 response_data = serializer.data
#                 return Response({'locationContractList': response_data})
#             except ValidationError as error:
#                 return Response({'error': error.detail}, status=500)
#             except Exception as e:
#                 return Response({'error': str(e)}, status=500)
            
#         elif partner_admin_user:
#             queryset = Contract.objects.all()
#             partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
#             type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
#             queryset = queryset.filter(
#                 Q(Q(made_by__in=partner_ids) & Q(made_by_type__in=type_ids)) |
#                 Q(Q(made_to__in=partner_ids) & Q(made_to_type__in=type_ids)), Q(location_id=location_id)
#             ).filter(
#                 Q(approval_status='review') |
#                 Q(approval_status='published') |
#                 Q(created_by=request.user)
#             )
#             serializer = self.get_serializer(queryset, many=True)
#             return Response({'locationContractList':serializer.data})
#         else:
#             raise PermissionDenied()

class ContractListByLocation(generics.RetrieveAPIView):
    queryset = Contract.objects.filter(is_active=True).order_by('id')
    serializer_class = ContractListSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        location_id = self.kwargs.get('location_id')
        queryset = Contract.objects.filter(location_id=location_id, is_active=True)
        if not queryset.exists():
            raise ValidationError("No contracts found for this location.")
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        location_id = kwargs.get('location_id')  # Extract location_id from kwargs
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)

        if request.user.is_admin:
            try:
                instance = self.get_object()
                serializer = self.get_serializer(instance, many=True)
                response_data = serializer.data
                return Response({'locationContractList': response_data})
            except ValidationError as error:
                return Response({'error': error.detail}, status=404)
            except Exception as e:
                return Response({'error': str(e)}, status=500)
            
        elif partner_admin_user:
            queryset = Contract.objects.filter(is_active=True).order_by('id')
            partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
            type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
            approved_contracts = ContractApprovals.objects.filter(
                partner_id__in=partner_ids,
                type_id__in=type_ids
            ).values_list('contract_id', flat=True)
            queryset = queryset.filter(
                Q(Q(made_by__in=partner_ids) & Q(made_by_type__in=type_ids)) |
                Q(Q(made_to__in=partner_ids) & Q(made_to_type__in=type_ids)) | Q(id__in=approved_contracts),
                location_id=location_id
            ).filter(
                Q(approval_status='review') |
                Q(approval_status='published') |
                Q(created_by=request.user)
            )
            serializer = self.get_serializer(queryset, many=True)
            return Response({'locationContractList': serializer.data})
        else:
            raise PermissionDenied()




class ContractLogListByContractID(generics.RetrieveAPIView):
    serializer_class = ContractLogSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    
    def get_object(self):
        contract_id = self.kwargs.get('contract_id')
        search_keyword = self.request.data.get('search_keyword')
        
        queryset = ContractLogs.objects.filter(contract_id=contract_id).order_by('-id')
        
        if search_keyword:
            queryset = queryset.filter(column_name__icontains=search_keyword) 
        
        return queryset
    
    def post(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance:
                page = self.paginate_queryset(instance)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    pagination_details = {
                        "current_page": self.paginator.page.number,
                        "number_of_pages": self.paginator.page.paginator.num_pages,
                        "total_items": self.paginator.page.paginator.count,
                        "current_page_items": len(serializer.data),
                        "next_page": self.paginator.get_next_link(),
                        "previous_page": self.paginator.get_previous_link(),
                    }
                    return self.get_paginated_response({
                        "contractLogs": serializer.data,
                        "paginationDetails": pagination_details
                    })
                else:
                    serializer = self.get_serializer(instance, many=True)
                    return Response({"contractLogs": serializer.data, "paginationDetails": {}})
            else:
                return Response({"contractLogs": [], "paginationDetails": {}})
        except ValidationError as error:
            return Response({'error': error.detail}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
#----------------------------------------------------------- CONTRACT APPROVALS------------------------------------------------------------------
class ContractApprovalCreate(generics.CreateAPIView):
    serializer_class = ContractApprovalSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        contract = request.data.get('contract_id')
        contract_id = Contract.objects.get(pk=contract)
        partner_id = request.data.get('partner_id')
        type_id = request.data.get('type_id')
        obj = [contract, 'contracts', 'contract-approvals', 2]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                raise PermissionDenied()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        partner_admin_user = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = partner_id, partner_types_role_id__type_id=type_id)
        for user in partner_admin_user:
            user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
            fullname = f"{request.user.firstname} {request.user.lastname}"
            create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Contract Approvals Created", contract_id.id, contract_id.name,
                                    request.user.id, fullname, contract_id.location_id.name if contract_id.location_id else None, 'contract', None)
        
        response_data = serializer.data
        contract_id = serializer.validated_data.get('contract_id')
        create_contract_logs(self, contract_id, request.user, 'Created Contract Approval')
        return Response({'contractApprovalDetails':response_data})

class ContractApprovalsIsApprovedUpdate(generics.UpdateAPIView):
    queryset = ContractApprovals.objects.all()
    serializer_class = ContractApprovalUpdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        contract = instance.contract_id.id
        obj = [contract, 'contracts', 'contract-approvals', 3]
        is_approved = request.data.get('is_approved')
        made_by = instance.contract_id.made_by.id
        made_to = instance.contract_id.made_to.id
        made_by_type = instance.contract_id.made_by_type
        made_to_type = instance.contract_id.made_to_type
        comments = request.data.get('comments')
        previous_status = request.data.get('previous_status')
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)#partner_types_role_id__partner_id=instance.partner_id.id, 
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        if not request.user.is_admin: #or (partner_admin_user and made_by in partner_ids or made_to in partner_ids) or (made_by_type in type_ids or made_to_type in type_ids):#partner_admin_user.exists():
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                raise PermissionDenied()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.approved_by = request.user
        instance.approved_by.save()
        self.perform_update(serializer)
        response_data = serializer.data
        if instance.contract_id and instance.is_approved == "approve":
            all_approved = all([approval.is_approved == "approve" for approval in instance.contract_id.contractapprovals_set.all()])
            if all_approved:
                instance.contract_id.approval_status = "published"
                instance.contract_id.save()
                partner_admin_user = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = instance.partner_id, partner_types_role_id__type_id=instance.type_id)
                for user in partner_admin_user:
                    user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
                    fullname = f"{request.user.firstname} {request.user.lastname}"
                    create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", f"Contract {instance.contract_id.name} is published", instance.contract_id.id, instance.contract_id.name,
                                        request.user.id, fullname, instance.contract_id.location_id.name if instance.contract_id.location_id else None, 'contract', is_approved)
                
        elif instance.contract_id and instance.is_approved =="reject":
            any_rejected = any([approval.is_approved == "reject" for approval in instance.contract_id.contractapprovals_set.all()])
            if any_rejected:
                instance.contract_id.approval_status = "draft"
                instance.contract_id.previous_status = previous_status
                instance.contract_id.previous_status_comments = comments
                instance.contract_id.save()
        partner_admin_user = PartnerTypeRolesUser.objects.filter(is_admin=True, partner_types_role_id__partner_id = instance.partner_id, partner_types_role_id__type_id=instance.type_id)
        for user in partner_admin_user:
            user_name = f"{user.user_id.firstname} {user.user_id.lastname}"
            fullname = f"{request.user.firstname} {request.user.lastname}"
            create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", f"Contract Approvals Updated To {is_approved}", instance.contract_id.id, instance.contract_id.name,
                                    request.user.id, fullname, instance.contract_id.location_id.name if instance.contract_id.location_id else None, 'contract', is_approved)
        
            # create_contract_notifications(self, user.user_id.id, user_name, "Partner - Contract Management", "Contract Approvals Updated", instance.contract_id.id, instance.contract_id.name,
            #                         request.user.id, fullname, instance.contract_id.location_id.name if instance.contract_id.location_id else None, 'contract', is_approved)
        
        return Response({'contractApprovalDetails': response_data})
        
class ContractApprovalDelete(generics.DestroyAPIView):
    queryset = ContractApprovals.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        contract_id = instance.contract_id.id
        obj = [contract_id, 'contracts', 'contract-approvals', 4]
        try:
            if request.user.is_admin:
                if instance.is_approved == 'approve':
                    return Response({'error':'approved items cannot be deleted'})
                self.perform_destroy(instance)
                return Response({'message':'Contract approval deleted successfully'})
            else:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    raise PermissionDenied()
        except ValidationError as error:
            return Response({'error':error.detail}, status=500)
        except Exception as e:
            return Response({'error':str(e)}, status=500)

class ContractApprovalsList(generics.RetrieveAPIView):
    queryset = ContractApprovals.objects.all().order_by('id')
    serializer_class = ContractApprovalSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        contract_id = self.kwargs.get('contract_id')
        return ContractApprovals.objects.filter(contract_id=contract_id).order_by('id')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        contract_id = self.kwargs['contract_id']
        obj = [contract_id, 'contracts', 'contract-approvals', 1]
        contract = Contract.objects.get(pk=contract_id)
        made_to = contract.made_to.id if contract.made_to else None
        made_by = contract.made_by.id if contract.made_by else None
        made_to_type = contract.made_to_type.id if contract.made_to_type else None
        made_by_type = contract.made_by_type.id if contract.made_by_type else None
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        if not request.user.is_admin and not (partner_admin_user and (made_to in partner_ids or made_by in partner_ids) or (made_by_type in type_ids and made_to_type in type_ids)):
            raise PermissionDenied()
            
        try:
            instance = self.get_object()
            if instance:
                serializer = self.get_serializer(instance, many=True)
                response_data = serializer.data
                return Response({'contractApprovalList':response_data})
            else:
                return Response({'contractApprovalList': []})
        except ValidationError as error:
            return Response({'error':error.detail}, status=500)
        except Exception as e:
            return Response({'error':str(e)}, status = 500)

