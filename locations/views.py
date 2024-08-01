from django.db import IntegrityError
from solar_project.permission_middleware import check_permission_user
from rest_framework import generics, status, serializers
from .serializers import *
from .models import *
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from usermanagement.exceptions import PermissionDenied
from collections import defaultdict
from django.db.models import Q
from partners.pagination import CustomPagination
import pandas as pd
from django.db.models import Case, When, Value, CharField
from dateutil.parser import parse as parse_date
from projectmanagement.models import *
import googlemaps 
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.management import call_command
from partners.models import *
from masterdata.models import LocationFields, Field
from locations.functions import generate_location_code, generate_location_micropage_id

#--------------------------------------------------- CREATE LOCATION VIEW --------------------------------------------------
class CreateLocation(generics.CreateAPIView):
    serializer_class = CreateLocationSerializer
    permission_classes = [IsAuthenticated]
   
    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        serializer.save()
   
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            location = serializer.save()
            location_id = serializer.instance.id
            location = Location.objects.get(pk=location_id)
            tab_fileds = Field.objects.all()
            
            Project.objects.create(
                location_id = location,
                name = location.name or location.city
            )
            # tab_filed = tab_fileds.values_list('id', flat=True)
            for tab_fileds in tab_fileds:
                LocationFields.objects.create(
                    location_id = location,
                    field_id = tab_fileds
                )
            # Using the Google Maps Geocoding API to add latitude and longitude
            api_key = 'ABidzBgshBAghyOILMNzJHaSyKHGAHHjdghdhdnFXBlnDVhQGAHDFJz3JttHYF3LNEr9wto14s3kut72tIdfdfdfjdJGHsgyyeirob3hd53jdhfkagcmshdr' 
            gmaps = googlemaps.Client(key=api_key)
            address = f"{location.address_line_1}, {location.city}, {location.zipcode}"
            geocoded_result = gmaps.geocode(address)

            if geocoded_result:
                latitude = geocoded_result[0]['geometry']['location']['lat']
                longitude = geocoded_result[0]['geometry']['location']['lng']

                
                location.location_latitude = latitude
                location.location_longitude = longitude
                location.save()

                location_details = {
                    'id': location.id,
                    'name': location.name,
                    'address_line_1': location.address_line_1,
                    'address_line_2': location.address_line_2,
                    'city': location.city,
                    'zipcode': location.zipcode,
                    'state': location.state,
                    'country': location.country_id.id if location.country_id else None,
                    'country_name': location.country_id.name if location.country_id else None,
                    'snowweight_load_factor': location.snowweight_load_factor,
                    'location_latitude': location.location_latitude,  # Add latitude
                    'location_longitude': location.location_longitude,  # Add longitude
                }
                response_data = {'locationDetails': location_details}

                return Response(response_data)
            else:
                return Response({'error': 'Geocoding failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


       
#----------------------------- GET LOCATION DETAILS AND DELETE VIEWS ---------------------------------------------------------

class LocationDetail(generics.RetrieveDestroyAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = RetrieveLocationSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        location_partner = LocationPartnerType.objects.filter(partner_id__in = partner_ids)
        location_type = location_partner.values_list('type_id', flat=True)
        if user.is_admin or (partner_admin_user and ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids, project_phase_id__project_id__location_id=instance.id).exists()) or (user.is_customer and not partner_admin_user and ProjectPhaseTask.objects.filter(assigned_to_user=user, project_phase_id__project_id__location_id=instance.id).exists()) or (partner_admin_user and (location_partner and (LocationPartnerType.objects.filter(partner_id__in = partner_ids, type_id__in = location_type).values_list('location_id', flat=True)))): 
            serializer = self.get_serializer(instance)
            location_data = serializer.data
           

           
            location_contracts = LocationContract.objects.filter(location_id=instance.id)
            contract_ids = location_contracts.values_list('contract_id', flat=True)

            
            contract_files_dict = defaultdict(list)

            # Fetch contract_files for each contract_id and store them in the dictionary
            for contract_id in contract_ids:
                contract_files = ContractFile.objects.filter(contract_id=contract_id)
                contract_file_data = ContractFileSerializer(contract_files, many=True).data

                
                for file_data in contract_file_data:
                    file_data['file_url'] = request.build_absolute_uri(file_data['file_url'])

                contract_files_dict[contract_id].extend(contract_file_data)

            
            contract_file_details = []
            for contract_id, file_data_list in contract_files_dict.items():
                contract_file_details.append({
                    'contract_id': contract_id,
                    'file_urls': [file_data['file_url'] for file_data in file_data_list]
                })
            
            pv_files = PVFile.objects.filter(location_id=instance.id)
            pv_files_data = []
            for pv_file in pv_files:
                pv_file_data = {
                    'id': pv_file.id,
                    'file_url':request.build_absolute_uri(pv_file.pv_file_url.url),
                }
                pv_files_data.append(pv_file_data)

            
            sub_tenants = LocationSubTenant.objects.filter(location_id=instance.id)
            sub_tenant_serializer = SubtenantSerializer(sub_tenants, many=True)
            tenant_data = sub_tenant_serializer.data

            
            fields_to_include = [
               'id', 'name', 'location_micropage', 'micro_page_image', 'location_code', 'location_image', 'location_device_image', 'location_status', 'project_id', 'project_name', 'current_phase_id', 'current_phase','current_phase_status', 'status_id', 'status_name', 'sales_email', 'sales_phone',
               'support_email', 'support_phone', 'address_line_1', 'address_line_2', 'channel_background_color', 'channel_text_color',
               'city', 'state', 'country_id', 'country_name', 'zipcode', 'description',
               'land_owner_id', 'land_owner_name', 'property_manager_id',
               'property_manager_name', 'lead_company', 'lead_company_name','location_state', 'state_comments', 'snowweight_load_factor', 'prioritisation', 'prioritisation_comments', 'expected_kWp', 'estimated_pv_costs', 'LIS', 'state_start_date', 'state_end_date', 'created_at', 'updated_at', 'tenant_id',
               'tenant_name', 'tenant_type', 'location_device_slot_list'
           ]
            try:
                location_role = LocationRole.objects.get(locations_id=instance.id)
                location_role_details = {
                    'id': location_role.id,
                    'partnerDetails':{
                        'partner_id': location_role.partners_id.first().id,
                        'partner_name': location_role.partners_id.first().name,
                    },
                    'roleDetails':{
                        'roles_id': location_role.roles_id.first().id,
                        'role_name': location_role.roles_id.first().name,
                    },
                    'locationDetails': {
                        'location_id':instance.id,
                        'location_name':instance.name,
                    }
                }
            except LocationRole.DoesNotExist:
                location_role_details = []

           
            response_data = {field: location_data[field] for field in fields_to_include if field in location_data}

           # Include subTenantDetails and locationContractDetails
            response_data['subTenantDetails'] = tenant_data
            response_data['locationContractDetails'] = contract_file_details
            response_data['locationRoleDetails'] = location_role_details
            response_data['pvFileDetails'] = pv_files_data

            return Response({'locationDetails':response_data})
        else:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not self.request.user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            location_status = instance.location_status
            if location_status == 'operating' or location_status == 'projectmanagement':
                return Response({'error':'Operating/Inprogress locations cannot be deleted'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.perform_destroy(instance)
            return Response({'message': 'Location deleted successfully'})
        except Exception as e:
            return Response({'error': str(e)})
        

class LocationMultipleDelete(generics.CreateAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = RetrieveLocationSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            location_ids = request.data.get('location_ids', [])  # Get a list of location IDs from request data
            if not self.request.user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            locations_to_delete = Location.objects.filter(id__in=location_ids)
            if len(locations_to_delete) != len(location_ids):
                return Response({'status_code':701, 'error': 'One or more locations do not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            operating_locations = locations_to_delete.filter(location_status='operating')
            if operating_locations.exists():
                return Response({'error': 'Operating locations cannot be deleted.'}, status=status.HTTP_400_BAD_REQUEST)
            locations_to_delete.delete()
            return Response({'message': 'Locations deleted successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#--------------------------------- LOCATION LIST, GENERAL, GEO API VIEWS ----------------------------------------------------

class LocationFullList(generics.ListCreateAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = LocationFullListSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = super().get_queryset()
        user = self.request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        location_partner = LocationPartnerType.objects.filter(partner_id__in = partner_ids)
        location_type = location_partner.values_list('type_id', flat=True)
        if request.user.is_admin:
            queryset = self.filter_queryset(self.get_queryset())
        if partner_admin_user:
            if partner_admin_user and location_partner.exists():
                location_partners = LocationPartnerType.objects.filter(partner_id__in = partner_ids, type_id__in = location_type).values_list('location_id', flat=True).distinct()
                location_projects = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
                combined_ids = set(location_partners) | set(location_projects)
                queryset = queryset.filter(id__in=combined_ids)
                # queryset = queryset.filter(id__in=set(location_partners) or set(location_projects))
            else:
                location_ids = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
                queryset = queryset.filter(id__in=location_ids).order_by('id')
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'LocationFullList': serializer.data} 
        return Response(response_data)

class LocationMapList(generics.ListCreateAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = LocationMapListSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        return Response({'details': 'Please use the POST method to filter locations.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):
        queryset = super().get_queryset()
        user = self.request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        location_partner = LocationPartnerType.objects.filter(partner_id__in = partner_ids)
        location_type = location_partner.values_list('type_id', flat=True)
        if request.user.is_admin:
            queryset = self.filter_queryset(self.get_queryset())
        if partner_admin_user:
            if partner_admin_user and location_partner.exists():
                location_partners = LocationPartnerType.objects.filter(partner_id__in = partner_ids, type_id__in = location_type).values_list('location_id', flat=True).distinct()
                location_projects = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
                combined_ids = set(location_partners) | set(location_projects)
                queryset = queryset.filter(id__in=combined_ids)
                # queryset = queryset.filter(id__in=set(location_partners) or set(location_projects))
            else:
                location_ids = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
                queryset = queryset.filter(id__in=location_ids).order_by('id')
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'LocationMapList': serializer.data}
        return Response(response_data)


    
    def filter_queryset(self, queryset):
        location_status = self.request.data.get('location_status')
        search_keyword = self.request.data.get('search_keyword')
        status_ev_id = self.request.data.get('status_ev_id')
        status_pv_id = self.request.data.get('status_pv_id')
        country_id = self.request.data.get('country_id')
        city = self.request.data.get('city')
        zipcode = self.request.data.get('zipcode')
        snowweight_load_factor = self.request.data.get('snowweight_load_factor')
        prioritisation = self.request.data.get('prioritisation')
        lead_company = self.request.data.get('lead_company')
        # snowweight_load_factor_list = snowweight_load_factor.split(',')
                
        if location_status:
            queryset = queryset.filter(location_status=location_status)
        if lead_company:
            queryset = queryset.filter(lead_company=lead_company)
        if status_ev_id:
            queryset = queryset.filter(status_ev_id=status_ev_id)
        if status_pv_id:
            queryset = queryset.filter(status_pv_id=status_pv_id)
        if country_id:
            queryset = queryset.filter(country_id=country_id)
        if city:
            queryset = queryset.filter(city=city)
        if zipcode:
            queryset = queryset.filter(zipcode=zipcode)               
        if snowweight_load_factor:
            queryset = queryset.filter(snowweight_load_factor__in=snowweight_load_factor)
        if prioritisation:
            queryset = queryset.filter(prioritisation=prioritisation)
       
        if search_keyword:
            queryset = queryset.filter(
                Q(name__icontains=search_keyword) | Q(zipcode__icontains=search_keyword)
            )

        return queryset
    
class LocationList(generics.ListCreateAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = LocationListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        return Response({'details': 'Please use the POST method to filter locations.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        location_partner = LocationPartnerType.objects.filter(partner_id__in = partner_ids)
        location_type = location_partner.values_list('type_id', flat=True)
            
        country_id = self.request.data.get('country_id')
        city = self.request.data.get('city')
        zipcode = self.request.data.get('zipcode')
        snowweight_load_factor = self.request.data.get('snowweight_load_factor')
        prioritisation = self.request.data.get('prioritisation')
        location_status = self.request.data.get('location_status')
        search_keyword = self.request.data.get('search_keyword')
        status_ev_id    = self.request.data.get('status_ev_id')
        status_pv_id    = self.request.data.get('status_pv_id')
        lead_company    = self.request.data.get('lead_company')

        filter_params = Q()
        if country_id:
            filter_params &= Q(country_id=country_id)
        if city:
            filter_params &= Q(city__icontains=city)
        if zipcode:
            filter_params &= Q(zipcode=zipcode)                
        if snowweight_load_factor:
            filter_params &= Q(snowweight_load_factor__in=snowweight_load_factor)
        if prioritisation:
            filter_params &= Q(prioritisation=prioritisation)
        if location_status:
            filter_params &= Q(location_status=location_status)
        if status_ev_id:
            filter_params &= Q(status_ev_id=status_ev_id)
        if status_pv_id:
            filter_params &= Q(status_pv_id=status_pv_id)
        if lead_company:
            filter_params &= Q(lead_company=lead_company)

        queryset = queryset.filter(filter_params)

        
        if search_keyword:
            queryset = queryset.filter(Q(name__icontains=search_keyword) | Q(zipcode__icontains=search_keyword) | Q(city__icontains=search_keyword))
            
                       
        if partner_admin_user:
            if partner_admin_user and location_partner.exists():
                location_partners = LocationPartnerType.objects.filter(partner_id__in = partner_ids, type_id__in = location_type).values_list('location_id', flat=True).distinct()
                location_projects = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
                combined_ids = set(location_partners) | set(location_projects)
                queryset = queryset.filter(id__in=combined_ids)
                # queryset = queryset.filter(id__in=set(location_partners) or set(location_projects))
            else:
                location_ids = ProjectPhaseTask.objects.filter(assigned_to__in=partner_ids).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
                queryset = queryset.filter(id__in=location_ids).order_by('id')
        

        if user.is_customer and not partner_admin_user:
            location_partners = LocationPartnerType.objects.filter(partner_id__in = partner_ids, type_id__in = location_type).values_list('location_id', flat=True).distinct()
            location_projects = ProjectPhaseTask.objects.filter(assigned_to_user=user).values_list('project_phase_id__project_id__location_id', flat=True).distinct()
            combined_ids = set(location_partners) | set(location_projects)
            queryset = queryset.filter(id__in=combined_ids).order_by('id')
        
        queryset = queryset.annotate(
            ordering_priority=Case(
                When(name='name', then=Value(1)),
                When(location_status='operating', then=Value(2)),
                When(location_status='projectmanagement', then=Value(3)),
                When(location_status='pipeline', then=Value(4)),
                output_field=CharField(),
            )
        ).order_by('ordering_priority', 'name')
        
                    
        return queryset


    def create(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = {
                    "locationDetails": serializer.data,
                    "paginationDetails": {
                        "current_page": self.paginator.page.number,
                        "number_of_pages": self.paginator.page.paginator.num_pages,
                        "total_items": self.paginator.page.paginator.count,
                        "current_page_items": len(serializer.data),
                        "next_page": self.paginator.get_next_link(),
                        "previous_page": self.paginator.get_previous_link(),
                    }
                }
                return self.get_paginated_response(response_data)

            return Response({"partners": []})  # If no results found

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LocationGeneral(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationGeneralSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-general', 3]

            if not request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'detail': 'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            
            max_size = 10 * 1024 * 1024
            location_image = request.data.get('location_image')
            location_device_image = request.data.get('location_device_image')
            if location_image and location_image.size > max_size:
                return Response({'status_code':708, 'error':'Location image must be less than 5MB'}, status=400)
            if location_device_image and location_device_image.size>max_size:
                return Response({'status_code':709, 'error':'Location image must be less than 10MB'}, status=400)

            return super().update(request, *args, **kwargs)
        except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
 
class LocationStatus(generics.UpdateAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationStatusSerializer
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
           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
    
class LocationSupport(generics.UpdateAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationSupportSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-support', 3]
           user = request.user
           if not user.is_admin: # or not (user.partner_admin and user.partner_id.id == instance.id):
               has_permission = check_permission_user(self, request, obj)
               if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

    #    try:
    #        user = request.user
           instance = self.get_object()

        #    if user.is_admin or (user.partner_admin and user.partner_id.id == instance.id):
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response(serializer.data)
        #    else:
        #        return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       

#PARTNER SALES
class LocationSales(generics.UpdateAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationSalesSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = request.user
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
           partner_id = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)

           if user.is_admin or (partner_admin_user and partner_id == instance.id): #(user.partner_admin and user.partner_id.id == instance.id):
               serializer = self.get_serializer(instance, data=request.data, partial=True)
               serializer.is_valid(raise_exception=True)
               self.perform_update(serializer)
               return Response(serializer.data)
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
    

class LocationLandOwner(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationLandSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-land-owner', 3]

            if not request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)
        except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)



class LandOwnerDelete(generics.RetrieveUpdateDestroyAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationLandSerializer
   permission_classes = (IsAuthenticated,)

   def destroy(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-land-owner', 4]
           if not request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           instance = self.get_object()
           instance.land_owner_id = None
           instance.land_owner_asset_id = None
           instance.save()

           return Response({'error':'Landowner deleted successfully'}, status=status.HTTP_200_OK)
       except Exception:
           return Response({'error': 'Land owner doesnot exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LocationPropertyManager(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationPropertyManagerSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-property-manager', 3]

            if not request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)

        except PermissionDenied:
            return Response({'detail': 'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

class LocationCodeUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            location_code = request.data.get('location_code')
            
            if location_code:
                instance.location_code = location_code
                instance.save()
            elif not location_code and not instance.location_code:
                location_code = generate_location_code()
                instance.location_code = location_code
                instance.save()
            else:
                instance.location_code = None
                instance.save()
            return Response({
                "message": "location code updated successfully!",
                "id":instance.id,
                "code":instance.location_code
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        
class LocationMicroPageUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # location_micropage = request.data.get('location_micropage')
            if not instance.location_micropage:
                location_micropage = generate_location_micropage_id()
                instance.location_micropage = location_micropage
                instance.save()
            else:
                instance.location_micropage = None
                instance.save()
            return Response({
                "message": "location micropage updated successfully!",
                "id":instance.id,
                "micropage_id":instance.location_micropage
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

        
class LocationCodeVerification(generics.ListAPIView):
    queryset = Location.objects.all()
    
    def post(self, request, *args, **kwargs):
        location_micropage_id = request.data.get('location_micropage')
        location_code = request.data.get('location_code')
        location = Location.objects.filter(location_micropage=location_micropage_id, location_code=location_code).first()
        if location:
            return Response({
                'message':'Code verified successfully!',
                'id':location.id,
                'name':location.name, 
                'location_micropage': location.location_micropage,
                'location_code':location.location_code,
                'micro_page_image':request.build_absolute_uri(location.micro_page_image.url) if location.micro_page_image else None,
                'location_device_image': request.build_absolute_uri(location.location_device_image.url) if location.location_device_image else None,
                'channel_background_color':location.channel_background_color,
                'channel_text_color':location.channel_text_color
            })
        else:
            return Response({'error':'location code or micropage not found'}, status=500)
        
        
class LocationDeviceChannelColorUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationDeviceChanelColorSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'channelColors':serializer.data})
        
class PropertyManagerDelete(generics.RetrieveUpdateDestroyAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationPropertyManagerSerializer
   permission_classes = (IsAuthenticated,)

   def destroy(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-property-manager', 4]
           if not request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'detail': 'You are not authorized to perform this action.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

           instance = self.get_object()
           instance.property_manager_id = None
           instance.save()

           return Response({'error':'Property manager deleted successfully'}, status=status.HTTP_200_OK)
       except Exception:
           return Response({'error': 'Invalid property manager id please try again'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       
#Location pre-ratings
class LocationPreRatings(generics.UpdateAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationPreRateSerializers
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-pre-ratings', 3]
           user = request.user
           if not user.is_admin:
               has_permission = check_permission_user(self, request, obj)
               if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
       
class LocationLeadCompanyUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationLeadCompanySerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-lead-company', 3]
            if not request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    raise PermissionDenied()
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'leadCompanyDetails':serializer.data})
        except Exception as e:
            return Response({'error':str(e)}, status=400)
        
class LocationMicroPageImageUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationMicroPageImageSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'microPageImage':serializer.data})

#----------------------------------------------- LOCATION STATE ----------------------------------------------------------------------
class LocationStateUpdate(generics.UpdateAPIView):
   queryset = Location.objects.all().order_by('id')
   serializer_class = LocationStateSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-state', 3]
           user = self.request.user
           if not user.is_admin:
               has_permission = check_permission_user(self, request, obj)
               if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           instance = serializer.save()
           return Response({'locationStateDetails':serializer.data})
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class LocationSnowWeight(generics.UpdateAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationSnowWeightSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-snow-load-factor', 3]
           user = request.user
           if not user.is_admin:
               has_permission = check_permission_user(self, request, obj)
               if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class LocationPrioritisation(generics.UpdateAPIView):
   queryset = Location.objects.all()
   serializer_class = LocationPrioritisationSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           location_id = self.kwargs['pk']
           obj = [location_id, 'locations', 'location-prioritization', 3]
           user = request.user
           if not user.is_admin:
               has_permission = check_permission_user(self, request, obj)
               if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class LocationEVDetailsUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationEVDetailSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-ev-details', 3]
            user = request.user
            if not user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'locationEVDetails':serializer.data})
        except ValidationError as e:
            return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
    
       
class LocationPVDetailsUpdate(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationPVDetailSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-pv-details', 3]
            user = request.user
            if not user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'locationPVDetails':serializer.data})
        except ValidationError as e:
            return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
#--------------------------------------------------- LOCATION TENANTS API VIEWS ------------------------------------------------------------
class LocationTenants(generics.UpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationTenantSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            location_id = self.kwargs['pk']
            obj = [location_id, 'locations', 'location-tenants', 3]
            user = request.user
            if not user.is_admin:
                return Response({'status_code': 605, 'error': 'You do not have permission to perform this action'},
                                status=status.HTTP_421_MISDIRECTED_REQUEST)

            instance = self.get_object()
            previous_tenant_type = instance.tenant_type

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            created_subtenants = []

            # Check if the tenant_type has changed to SingleTenant
            if instance.tenant_type == 'SingleTenant' and previous_tenant_type != 'SingleTenant':
                instance.locationsubtenant_set.all().delete()
            elif instance.tenant_type == 'MultiTenant':
                instance.locationsubtenant_set.all().delete()
                subtenants_data = request.data.get('subtenants', [])

                subtenant_instances = Partner.objects.filter(id__in=subtenants_data)

                location_subtenant_instances = [
                    LocationSubTenant(location_id=instance, subtenant_id=subtenant_instance)
                    for subtenant_instance in subtenant_instances
                ]
                LocationSubTenant.objects.bulk_create(location_subtenant_instances)
                created_subtenants = SubtenantSerializer(location_subtenant_instances, many=True).data
                instance.locationsubtenant_set.exclude(id__in=[subtenant.id for subtenant in location_subtenant_instances]).delete()

            response_data = {
                'location': serializer.data,
                'created_subtenants': created_subtenants,
            }

            return Response(response_data)

        except PermissionDenied:
            return Response({'detail': 'You do not have permission to perform this action'},
                            status=status.HTTP_421_MISDIRECTED_REQUEST)

        except ValidationError as e:
            return Response({'error': e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class TenantList(generics.ListAPIView):
    serializer_class = GetTenantSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return Location.objects.exclude(tenant_id=None).order_by('id')
        else:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)


class SubtenantCreateAPIView(generics.CreateAPIView):
    serializer_class = SubtenantSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        try:
            if not request.user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            
            location_id = self.kwargs.get('location_id')
            location = Location.objects.get(id=location_id)
            
            if location.tenant_type != 'MultiTenant':
                return Response({'status_code':702, 'error': 'Subtenants can only be created for MultiTenant locations.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            existing_subtenants = LocationSubTenant.objects.filter(location_id=location_id)
            existing_subtenant_data = SubtenantSerializer(existing_subtenants, many=True).data

            subtenants_data = []
            display_order = len(existing_subtenants) + 1
            
            for key, value in request.data.items():
                if key.startswith('tenant_id'):
                    existing_subtenant = existing_subtenants.filter(tenant_id=value).exists()
                    if not existing_subtenant:
                        subtenant_data = {
                            'location_id': location.id,
                            'tenant_id': value,
                            'display_order': display_order
                        }
                        subtenants_data.append(subtenant_data)
                        display_order += 1

            serializer = self.get_serializer(data=subtenants_data, many=True, context={'location_id': location_id})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            headers = self.get_success_headers(serializer.data)

            main_tenant_data = {
                'id': location.id,
                'tenant_id': location.tenant_id.id,
                'tenant_name': location.tenant_id.name,
                'tenant_type': location.tenant_type,
                'subtenants': existing_subtenant_data + serializer.data
            }

            response_data = {
                'locationTenantDetails': [main_tenant_data]
            }

            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
        except Location.DoesNotExist:
            return Response({'error': 'Location doesnot exists'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        except IntegrityError:
            return Response({'status_code': 703, 'error': 'Duplicate subtenant found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



  
class LocationTenantDelete(generics.DestroyAPIView):
   serializer_class = LocationTenantSerializer
   permission_classes = (IsAuthenticated,)

   def get_queryset(self):
       location_id = self.kwargs['pk']
       return Location.objects.filter(id=location_id)

   def get_object(self):
       queryset = self.get_queryset()

       try:
           location = queryset.get()
           self.check_object_permissions(self.request, location)
           return location
       except Location.DoesNotExist:
           raise Response("Location does not exist.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def delete(self, request, *args, **kwargs):
       try:
           if not request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           instance = self.get_object()
           location_id = instance.id

           
           LocationSubTenant.objects.filter(location_id=location_id).delete()

           # Update the main tenant fields
           instance.tenant_id = None
           instance.tenant_type = None
           instance.save()

           return Response({'message': 'Tenant and its subtenants deleted successfully'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
       except Exception as e:
           return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubtenantDeleteAPIView(generics.DestroyAPIView):
   permission_classes = (IsAuthenticated,)
   
   def destroy(self, request, *args, **kwargs):
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       location_id = self.kwargs.get('location_id')
       subtenant_id = self.kwargs.get('subtenant_id')

       try:
           location_tenant = LocationSubTenant.objects.get(location_id=location_id, subtenant_id=subtenant_id)

           # Count the remaining subtenants for the location
           remaining_subtenants = LocationSubTenant.objects.filter(location_id=location_id).exclude(tenant_id=subtenant_id).count()

           if remaining_subtenants == 0:
               location = Location.objects.get(id=location_id)
               location.tenant_type = 'SingleTenant'
               location.save()

           location_tenant.delete()
           return Response({'message': 'Subtenant deleted successfully!'}, status = status.HTTP_200_OK)
       except ObjectDoesNotExist:
           return Response({'error': 'Location tenant does not exist.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
#----------------------------------------------------- LOCATION TENANT VIEWS ENDS -------------------------------------------------------------

#----------------------------------------- PERMISSIONS, MODULE and MODULE PANEL VIEWS ------------------------------------------------------
class Modules(generics.ListAPIView):
   queryset = Module.objects.all().order_by('id')
   serializer_class = ModuleSerializer
   permission_classes = (IsAuthenticated,)

   def list(self, request, *args, **kwargs):
       try:
           modules = self.get_queryset()
           serializer = self.get_serializer(modules, many=True)
           module_data = serializer.data

           module_ids = [module['id'] for module in module_data]
           module_panels = ModulePanel.objects.filter(module_id__in=module_ids)
           panel_serializer = ModulePanelSerializer(module_panels, many=True)
           panel_data = panel_serializer.data

           module_names = Module.objects.filter(id__in=module_ids).values('id', 'name')
           module_names_dict = {module['id']: module for module in module_names}

           for module in module_data:
               module['name'] = module_names_dict.get(module['id'], {}).get('name')
               module_panels = [
                   {
                       'id': panel['id'],
                       'name': panel['name'],
                       'slug': panel['slug'],
                   } for panel in panel_data if panel['module_id'] == module['id']
               ]

               module['modulePanels'] = module_panels

           response_data = {
               'modules': module_data,
           }
           return Response(response_data)

       except Exception as e:
           return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class Permissions(generics.ListAPIView):
   queryset = Permission.objects.all().order_by('id')
   serializer_class = PermissionSerializer
   permission_classes = (IsAuthenticated,)

   def list(self, request, *args, **kwargs):
       try:
           queryset = self.get_queryset()
           serializer = self.get_serializer(queryset, many=True)
           data = {"permissions": serializer.data}
           return Response(data)

       except Exception as e:
           return Response(str(e), status=status.HTTP_500_INTERAL_SERVER_ERROR)


#---------------------------------------------- ROLES APIS ---------------------------------------------------------------------
class Roles(generics.ListAPIView):
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        try:
            response_data = []
            for role in self.get_queryset():
                role_permissions = {
                    "id": role.id,
                    "name": role.name,
                    "is_fixed":role.is_fixed,
                    "modules": [],
                    "partners": []
                }

                
                modules = role.rolespermissions_set.values_list('modules_id', flat=True).distinct()
                for module_id in modules:
                    module = Module.objects.get(id=module_id)
                    module_data = {
                        "id": module_id,
                        "name": module.name,
                        "slug": module.slug,
                        "modulePanels": []
                    }

                    
                    module_panels = role.rolespermissions_set.filter(modules_id=module_id).values_list('modules_panels_id', flat=True).distinct()
                    for panel_id in module_panels:
                        try:
                            panel = ModulePanel.objects.get(id=panel_id)
                        except ModulePanel.DoesNotExist:
                            continue
                        panel_data = {
                            "id": panel_id,
                            "name": panel.name,
                            "slug": panel.slug,
                            "permissions": []
                        }

                        permissions = role.rolespermissions_set.filter(modules_id=module_id, modules_panels_id=panel_id).values_list('permissions_id', flat=True)
                        for permission_id in permissions:
                            permission = Permission.objects.get(id=permission_id)
                            permission_data = {
                                "id": permission_id,
                                "name": permission.name,
                            }

                            panel_data["permissions"].append(permission_data)

                        module_data["modulePanels"].append(panel_data)

                    role_permissions["modules"].append(module_data)

               
                partners = Partner.objects.filter(partnertypesrole__role_id=role.id)
                partner_info = []

                
                partners = Partner.objects.filter(partnertypesrole__role_id=role.id).distinct()

                for partner in partners:
                    partner_data = {
                        'id': partner.id,
                        'name': partner.name,
                        'partner_logo':request.build_absolute_uri(partner.partner_logo.url) if partner.partner_logo else None,
                        'address_line_1':partner.address_line_1,
                        'address_line_2':partner.address_line_2,
                        'city':partner.city,
                        'zip_code':partner.zip_code,
                        'types': [] 
                    }

                    
                    partner_types = PartnerTypesRole.objects.filter(partner_id=partner.id, role_id=role.id).values('type_id', 'type_id__name').distinct()

                    
                    unique_types = {}

                    for type_data in partner_types:
                        type_id = type_data['type_id']
                        type_name = type_data['type_id__name']

                        
                        if type_id not in unique_types:
                            unique_types[type_id] = {'type_id': type_id, 'type_name': type_name}

                    
                    type_info = list(unique_types.values())
                    partner_data['types'] = type_info

                    partner_info.append(partner_data)

                role_permissions['partners'] = partner_info

                response_data.append(role_permissions)

            return Response({'roleList': response_data})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CreateRoles(generics.CreateAPIView):
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        try:
            name = request.data.get('name')
            if name:
                existing_role = Role.objects.filter(name=name).exists()
                if existing_role:
                    return Response({'status_code':751, 'error':'Role name already exists'})
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            role = serializer.instance.id
            role_id = Role.objects.get(pk=role)
            types = Type.objects.create(
                name = serializer.instance.name,
                role_id = role_id,
                description = serializer.instance.description,
                is_fixed = serializer.instance.is_fixed
            )
            print(types)
            
            response_data = {'roleDetails':"Role and Type created successfully!"}
            return Response(response_data)
        except serializers.ValidationError as error:
           return Response({'error':error.detail}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

  
class RoleDetail(generics.RetrieveUpdateDestroyAPIView):
   queryset = Role.objects.all()
   serializer_class = RoleSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           name = request.data.get('name')
           if name:
                existing_role = Role.objects.filter(name=name).exists()
                if existing_role:
                    return Response({'status_code':751, 'error':'Role name already exists'})
           partial = kwargs.pop('partial', False)
           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=partial)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)

           if getattr(instance, '_prefetched_objects_cache', None):
               instance._prefetched_objects_cache = {}

           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           if instance.is_fixed == True:
               return Response({'error':'fixed roles cannot be deleted'}, status=500)
           role_types = Type.objects.get(role_id=instance).delete()
           self.perform_destroy(instance)
           return Response({'message': 'Role deleted successfully'})
       except Exception as e:
           return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def retrieve(self, request, *args, **kwargs):
        try:
            role = self.get_object()
            serializer = self.get_serializer(role)

            response_data = {
                "rolePermissions": {
                    "id": role.id,
                    "name": role.name,
                    "description":role.description,
                    "is_fixed":role.is_fixed,
                    "modules": []
                }
            }

            modules = role.rolespermissions_set.values_list('modules_id', flat=True).distinct()
            for module_id in modules:
                module = Module.objects.get(id=module_id)
                module_data = {
                    "id": module_id,
                    "name": module.name,
                    "slug": module.slug,
                    "modulePanels": []
                }

                module_panels = role.rolespermissions_set.filter(modules_id=module_id).values_list('modules_panels_id', flat=True).distinct()
                for panel_id in module_panels:
                    panel = ModulePanel.objects.get(id=panel_id)
                    panel_data = {
                        "id": panel_id,
                        "name": panel.name,
                        "slug": panel.slug,
                        "permissions": []
                    }

                    permissions = role.rolespermissions_set.filter(modules_id=module_id, modules_panels_id=panel_id).values_list('permissions_id', flat=True)
                    for permission_id in permissions:
                        permission = Permission.objects.get(id=permission_id)
                        permission_data = {
                            "id": permission_id,
                            "name": permission.name,
                        }

                        panel_data["permissions"].append(permission_data)

                    module_data["modulePanels"].append(panel_data)

                response_data["rolePermissions"]["modules"].append(module_data)

            return Response(response_data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#----------------------------------------------- ROLE PERMISSIONS ----------------------------------------------------------------
class RolesPermissionsAPIView(generics.CreateAPIView):
   serializer_class = RolePermissionSerializer
   permission_classes = (IsAuthenticated,)

   def create(self, request, *args, **kwargs):
       try:
           if not request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           roles_id = kwargs.get('roles_id')
           role = Role.objects.get(id=roles_id)
           modules = request.data.get('modules', [])

           RolesPermissions.objects.filter(roles_id=role).delete()

           response_data = {
               "rolePermissions": {
                   "id": roles_id,
                   "name": role.name,
                   "modules": []
               }
           }

           for module in modules:
               module_id = module['id']
               module_panels = module.get('panel', [])

               module_data = {
                   "id": module_id,
                   "name": Module.objects.get(id=module_id).name,
                   "module_panels": []
               }

               for panel in module_panels:
                   panel_id = panel['id']
                   permissions = panel.get('permission', [])

                   panel_data = {
                       "id": panel_id,
                       "name": ModulePanel.objects.get(id=panel_id).name,
                       "permissions": []
                   }

                   for permission in permissions:
                       permission_id = permission['id']

                       roles_permission = RolesPermissions.objects.create(
                           roles_id=role,
                       )
                       roles_permission.modules_id.add(module_id)
                       roles_permission.modules_panels_id.add(panel_id)
                       roles_permission.permissions_id.add(permission_id)

                       permission_data = {
                           "id": permission_id,
                           "name": Permission.objects.get(id=permission_id).name
                       }

                       panel_data['permissions'].append(permission_data)

                   module_data['module_panels'].append(panel_data)

               response_data["rolePermissions"]["modules"].append(module_data)

           return Response(response_data)

       except Role.DoesNotExist:
           return Response({"error": "Role does not exist."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       except Exception as e:
           return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------- Location Roles -------------------------------------------------------------------

class LocationRoleCreate(generics.CreateAPIView):
   queryset = LocationRole.objects.all()
   serializer_class = LocationRoleSerializer
   permission_classes = (IsAuthenticated,)

   def create(self, request, *args, **kwargs):
       partner_id = request.data['partners_id']
       role_id = request.data['roles_id']

       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

       try:
           location = Location.objects.get(id=self.kwargs['location_id'])
           location_id = location.id
       except Location.DoesNotExist:
           return Response({'message': 'Location does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       try:
           existing_location_role = LocationRole.objects.get(locations_id=location_id)
           return Response({'status_code': 704, 'message': 'Location already exists with a LocationRole'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       except LocationRole.DoesNotExist:
           pass

       mutable_data = request.data.copy()
       mutable_data['locations_id'] = location_id

       serializer = self.get_serializer(data=mutable_data)
       serializer.is_valid(raise_exception=True)
       self.perform_create(serializer)

       location_role = serializer.instance

       response_data = {
           'locationRoleDetails': {
               'id': location_role.id,
               'partnerDetails': {
                   'partners_id': partner_id,
                   'partner_names': location_role.partners_id.first().name,
               },
               'roleDetails': {
                   'roles_id': role_id,
                   'role_names': location_role.roles_id.first().name,
               },
               'locationDetails': {
                   'location_id': location_id,
                   'location_name': location.name if location else None,
               }
           }
       }

       return Response(response_data, status=status.HTTP_201_CREATED)


class LocationRoleUpdate(generics.UpdateAPIView):
   queryset = LocationRole.objects.all()
   serializer_class = LocationRoleSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       location_role_id = kwargs['id']
       partners_id = request.data.get('partners_id')
       roles_id = request.data.get('roles_id')
       
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

       try:
           location_role = LocationRole.objects.get(id=location_role_id)
       except LocationRole.DoesNotExist:
           return Response({'status_code': 705, 'message': 'LocationRole does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       if partners_id:
           try:
               partner = Partner.objects.get(id=partners_id)
               location_role.partners = partner
           except Partner.DoesNotExist:
               return Response({'status_code': 706, 'message': 'Partner does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       if roles_id:
           try:
               role = Role.objects.get(id=roles_id)
               location_role.roles = role
           except Role.DoesNotExist:
               return Response({'status_code': 707,'message': 'Role does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       location_role.save()
       response_data = {
           'locationRoleDetails': {
               'id': location_role.id,
               'partnerDetails': {
               'partners_id': partners_id or location_role.partners_id,
               'partner_names': location_role.partners.name,
               },
               'roleDetails':{
               'roles_id': roles_id or location_role.roles_id,
               'role_names': location_role.roles.name,
               },
               'locationDetails':{
               'location_id': location_role.locations_id.first().id,
               'location_name': location_role.locations_id.first().name,
               }
           }
       }

       return Response(response_data, status=status.HTTP_200_OK)
   
class LocationRoleDestroy(generics.DestroyAPIView):
   queryset = LocationRole.objects.all()
   serializer_class = LocationRoleSerializer
   permission_classes = (IsAuthenticated,)

   def destroy(self, request, *args, **kwargs):
       location_role_id = kwargs['id']
       
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

       try:
           location_role = LocationRole.objects.get(id=location_role_id)
       except LocationRole.DoesNotExist:
           return Response({'message': 'LocationRole does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       location_role.delete()

       return Response({'message': 'LocationRole deleted'}, status=status.HTTP_204_NO_CONTENT)


#-------------------------------------------------- PV FILE UPLOAD VIEWS ------------------------------------------------------------
class PVFileCreate(generics.CreateAPIView):
    queryset = PVFile.objects.all()
    serializer_class = PVFileSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        location_id = self.kwargs.get('location_id')
        location = Location.objects.get(pk=location_id)

        pv_files_data = []

        for file in request.FILES.getlist('pv_file_url'):
            pvfile = PVFile.objects.create(location_id=location, pv_file_url=file)
            pv_file_data = {
                'id': pvfile.id,
                'url': request.build_absolute_uri(pvfile.pv_file_url.url)
            }
            pv_files_data.append(pv_file_data)

        response_data = {
            'location_id': location.id,
            'location_name': location.name, 
            'pvFiles': pv_files_data,
        }

        return Response({'pvFileDetails': response_data})
    
class PVFileDelete(generics.DestroyAPIView):
    serializer_class = PVFileSerializer
    permission_classes = (IsAuthenticated, )
    
    def destroy(self, request, *args, **kwargs):
        pvfile_id = self.kwargs['id']
        location_id = self.kwargs['location_id']
        
        if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        try:
            pvfile = PVFile.objects.get(pk=pvfile_id)
            location = Location.objects.get(pk=location_id)

            # pvfile.location_id.remove(location)
            pvfile.delete()

            return Response({'error':'File removed successfully!'}, status=status.HTTP_200_OK)
        except (PVFile.DoesNotExist, Location.DoesNotExist):
            return Response({'error':'File or location doesnot exists'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    
# ------------------------------------------------ Location Contracts -------------------------------------------------------------
class LocationContractAPIView(generics.CreateAPIView):
   serializer_class = LocationContractRequestSerializer
   permission_classes = (IsAuthenticated,)

   def create(self, request, *args, **kwargs):
       if not request.user.is_admin:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

       location_id = kwargs.get('location_id')

       
       contract_ids = []
       for key, value in request.data.items():
           if key.startswith('contract_id[') and key.endswith(']'):
               contract_ids.append(int(value))

       try:
           location_contract = LocationContract.objects.get(location_id=location_id)
       except LocationContract.DoesNotExist:
           location_contract = LocationContract(location_id_id=location_id)

       location_contract.save()

       
       for contract_id in contract_ids:
           location_contract.contract_id.add(contract_id)

       contract_data = []
       for contract_id in contract_ids:
           contract_files = ContractFile.objects.filter(contract_id=contract_id)
           file_urls = [request.build_absolute_uri(file.file_url.url) for file in contract_files]
           contract_data.append({
               'contract_id': contract_id,
               'file_urls': file_urls
           })

       response_data = {
           'contractData': {
               'id': location_contract.id,
               'location_id': location_id,
               'contract_file_details': contract_data
           }
       }

       return Response(response_data, status=status.HTTP_201_CREATED)

class LocationContractDeleteAPIView(generics.DestroyAPIView):
    queryset = LocationContract.objects.all()
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'LocationContract deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
class LocationContractDelete(generics.DestroyAPIView):
   permission_classes = (IsAuthenticated,)

   def delete(self, request, location_id, contract_id, *args, **kwargs):
       try:
           location_contract = LocationContract.objects.get(location_id=location_id)
       except LocationContract.DoesNotExist:
           return Response({'detail': 'LocationContract Does not exists'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       if not request.user.is_admin:
           return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

       try:
           contract_id = int(contract_id)
           location_contract.contract_id.remove(contract_id)
       except ValueError:
           return Response({'detail': 'Invalid contract_id. It should be an integer.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       except ObjectDoesNotExist:
           return Response({'detail': 'Contract_id not found for this location.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       return Response({'detail': 'Contract_id successfully removed from the location.'}, status=status.HTTP_200_OK)
   
 
#------------------------------------------------------- LOCATION PIPELINE REPORT -------------------------------------------------
class LocationPipelineReport(generics.ListCreateAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = PipeLineReportSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        return Response({'details': 'Please use the POST method to filter locations.'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'locationPipeLineReport': serializer.data}
        return Response(response_data)

    def filter_queryset(self, queryset):
        location_status = self.request.data.get('location_status')
        search_keyword = self.request.data.get('search_keyword')

        if location_status:
            queryset = queryset.filter(location_status=location_status)
       
        if search_keyword:
            queryset = queryset.filter(
                Q(name__icontains=search_keyword) | Q(zipcode__icontains=search_keyword)
            )

        return queryset
    


#----------------------------------- LOCATION CSV/XLXS CREATE/UPDATE ---------------------------------------------------------------------------

class LocationCreateUpdateCSVView(generics.CreateAPIView):
    serializer_class = LocationCSVSerializer
    permission_classes = (IsAuthenticated,)
    
    
    def get_queryset(self):
        return Location.objects.all()
    
    
    def map_status_name_to_instance(self, status_name):
        
        try:
            instance = LocationStatusEVPV.objects.get(name=status_name)
            return instance
        except LocationStatusEVPV.DoesNotExist:
            return None
        
    
    def create_or_update_location(self, data):
        existing_location = Location.objects.filter(
            city=data['city'],
            zipcode=data['zipcode'],
            address_line_1=data['address_line_1']
        ).first()
                

        if existing_location:
            
            if existing_location.location_status == 'pipeline':
                for key, value in data.items():
                    setattr(existing_location, key, value)
                existing_location.save()
                
        else:
            
            location = Location.objects.create(**data)
            api_key = 'AIzaTyBlnDSVhQGJz3Jt3LNEr9wto19ud3kajJKjhF72tI'
            gmaps = googlemaps.Client(key=api_key)
            address = f"{location.address_line_1}, {location.city}, {location.zipcode}"
            geocoded_result = gmaps.geocode(address)

            if geocoded_result:
                latitude = geocoded_result[0]['geometry']['location']['lat']
                longitude = geocoded_result[0]['geometry']['location']['lng']

                location.location_latitude = latitude
                location.location_longitude = longitude
                location.save()

    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            if file.name.endswith('.xlsx'):
                data = pd.read_excel(file, dtype=str)
            elif file.name.endswith('.csv'):
                data = pd.read_csv(file, dtype=str)
            else:
                return Response({'error': 'Unsupported file format please use XLXS or CSV'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except pd.errors.ParserError:
            return Response({'error': 'Invalid file data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        def convert_to_decimal(value):
            if value is None:
                return None

            if isinstance(value, (int, Decimal)):
                return value

            try:
                result = Decimal(value)
                if result.is_nan():
                    return None
                return result
            except (ValueError, TypeError, InvalidOperation):
                return None
        
        def convert_to_int(value):
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
                              
        # Iterate through the rows and create or update locations
        for index, row in data.iterrows():
            milestone_date_ev_str = row.get("Milestone Date EV")
            if isinstance(milestone_date_ev_str, str):
                try:
                    milestone_date_ev = parse_date(milestone_date_ev_str)
                except ValueError:
                    milestone_date_ev = None
            else:
                milestone_date_ev = None
            
            milestone_date_pv_str = row.get("Milestone Date PV")
            if isinstance(milestone_date_pv_str, str):
                try:
                    milestone_date_pv = parse_date(milestone_date_pv_str)
                except ValueError:
                    milestone_date_pv = None
            else:
                milestone_date_pv = None
            
            exp_installation_date_str = row.get("Expected Installation Date EV")
            if isinstance(exp_installation_date_str, str):
                try:
                    exp_installation_date = parse_date(exp_installation_date_str)
                except ValueError:
                    exp_installation_date = None
            else:
                exp_installation_date = None
            
            planned_installation_date_str = row.get("Planned Installation Date EV")
            if isinstance(planned_installation_date_str, str):
                try:
                    planned_installation_date = parse_date(planned_installation_date_str)
                except ValueError:
                    planned_installation_date = None
            else:
                planned_installation_date = None
            
            exp_operation_date_str = row.get("Expected Oper. Date EV")
            if isinstance(exp_operation_date_str, str):
                try:
                    exp_operation_date = parse_date(exp_operation_date_str)
                except ValueError:
                    exp_operation_date = None
            else:
                exp_operation_date = None
            
            capex_spent_to_date_str = row.get("Capex Spent to Date EV")
            if isinstance(capex_spent_to_date_str, str):
                try:
                    capex_spent_to_date = parse_date(capex_spent_to_date_str)
                except ValueError:
                    capex_spent_to_date = None
            else:
                capex_spent_to_date = None
                
            exp_installation_date_pv_str = row.get("Expected Installation Date PV")
            if isinstance(exp_installation_date_pv_str, str):
                try:
                    exp_installation_date_pv = parse_date(exp_installation_date_pv_str)
                except ValueError:
                    exp_installation_date_pv = None
            else:
                exp_installation_date_pv = None
                
            planned_installation_date_pv_str = row.get("Planned Installation Date PV")
            if isinstance(planned_installation_date_pv_str, str):
                try:
                    planned_installation_date_pv = parse_date(planned_installation_date_pv_str)
                except ValueError:
                    planned_installation_date_pv = None
            else:
                planned_installation_date_pv = None
                
            exp_operation_date_pv_str = row.get("Expected Oper. Date PV")
            if isinstance(exp_operation_date_pv_str, str):
                try:
                    exp_operation_date_pv = parse_date(exp_operation_date_pv_str)
                except ValueError:
                    exp_operation_date_pv = None
            else:
                exp_operation_date_pv = None
            
            capex_spent_to_date_pv_str = row.get("Capex Spent to Date PV")
            if isinstance(capex_spent_to_date_pv_str, str):
                try:
                    capex_spent_to_date_pv = parse_date(capex_spent_to_date_pv_str)
                except ValueError:
                    capex_spent_to_date_pv = None
            else:
                capex_spent_to_date_pv = None
                
            def get_or_create_partner(name):
                if isinstance(name, str) and name.strip().lower() != "nan":
                    partner = Partner.objects.filter(name__iexact=name).first()
                    if not partner:
                        partner, _ = Partner.objects.get_or_create(name=name)
                    return partner
                else:
                    return None
                        
            status_ev_instance = self.map_status_name_to_instance(row['Status EV'])
            status_pv_instance = self.map_status_name_to_instance(row['Status PV'])
            # cos_pv_value = row['COS PV'].lower() if isinstance(row['COS PV'], str) else None
            
            location_data = {
                'name': row['City'],
                'city': row['City'],
                'zipcode': row['Zip Code'],
                'address_line_1': row['Street'],
                'land_owner_id': get_or_create_partner(row['Landowner']),
                'land_owner_asset_id': row['Slate Asset-ID'],
                'property_manager_id': get_or_create_partner(row['Slate PM']),
                'tenant_id': get_or_create_partner(row['Anchor Tenant']),
                'tenant_type': map_tenant_type(row['Tenant Structure']),
                'project_cluster_ev': row['Project Cluster EV'],
                'status_ev_id': status_ev_instance, 
                'approval_ev': row['Approval EV'],
                'milestone_date': milestone_date_ev,
                'disc_reason_ev': row['Disc. Reason EV'],
                'lease_partner_ev': row['Lease Partner EV'],
                'planned_ac': convert_to_decimal(row['# planned AC EV']),
                'ac_speed': convert_to_decimal(row['AC Speed EV']),
                'ac_tech_setup': row['AC Tech Setup EV'],
                'planned_dc': convert_to_decimal(row['# planned DC EV']),
                'dc_speed': convert_to_decimal(row['DC Speed EV']),
                'dc_tech_setup': row['DC Tech Setup EV'],
                'planned_battery': convert_to_decimal(row['# planned HPC EV']),
                'battery_speed': convert_to_decimal(row['HPC Speed EV']),
                'battery_tech_setup': row['HPC Tech Setup EV'],
                'construction_year': convert_to_int(row['Construction Year EV']),
                'construction_quarter': row['Construction Quarter EV'],
                'exp_installation_date': exp_installation_date,
                'planned_installation_date': planned_installation_date,
                'exp_operation_date': exp_operation_date,
                'capex_spent_to_date': capex_spent_to_date,
                'capex_total_expected': convert_to_decimal(row['Capex Total Expected EV']),
                'subsidy': row['Subsidy EV'],
                'preffered_charge_client_ev': row['Preferred Charge Client EV'],
                'lead_company': get_or_create_partner(row['Lead Comp EV']),
                'asset_management_comments': row['Asset Mgt Comment EV'],
                'approval_cs': row['Approval CS EV'],
                'pitch_ev': row['Pitch EV'],
                'negotiations_ev': row['Negot. EV'],
                'LOI': row['LoI EV'],
                'setup_ev': row['Setup EV'],
                'construction_ev': row['Construction EV'],
                'installed_ev': row['Installed EV'],
                'operating_ev': row['Operating EV'],
                'invoice_number_ev': row['Invoice No. EV'],
                'project_cluster_pv': row['Project Cluster PV'],
                'status_pv_id': status_pv_instance,
                'approval_pv': row['Approval PV'],
                'milestone_date_pv': milestone_date_pv,
                'disc_reason_pv': row['Disc. Reason PV'],
                'lease_partner_pv': row['Lease Partner PV'],
                'expected_kWp_pv': row['Expected kWp PV'],
                'expected_spec_yield_pv': row['Expec Spec Yield (kWh/kWp) PV'],
                'construction_year_pv': convert_to_int(row['Construction Year PV']),
                'construction_quarter_pv': row['Construction Quarter PV'],
                'exp_installation_date_pv': exp_installation_date_pv,
                'planned_installation_date_pv': planned_installation_date_pv,
                'exp_operation_date_pv': exp_operation_date_pv,
                'capex_spent_to_date_pv': capex_spent_to_date_pv,
                'capex_total_expected_pv': convert_to_decimal(row['Capex Total Expected PV']),
                'offtakers_pv': row['Offtakers PV'],
                'approval_pv': row['Asset Mgt Comment PV'],
                'snowweight_load_factor':row['Snow Load Factor'],
                'pitch_pv': row['Pitch PV'],
                'negotiations_pv': row['Negot. PV'],
                'LOI_pv': row['LoI PV'],
                'setup_pv': row['Setup PV'],
                'construction_pv': row['Construction PV'],
                'installed_pv': row['Installed PV'],
                'operating_pv': row['Operating PV'],
                'invoice_number_pv': row['Invoice No. PV'],
                'parking_spots':convert_to_int(row['Parking Spots']),
                'geap_ev':row['GEAP EV'],
                'gep_ev':convert_to_decimal(row['GEP EV']),
                # 'cos_pv': cos_pv_value if cos_pv_value in ['applied', 'approved'] else None,                
            }
            for field_name in ['status_ev_id', 'approval_ev', 'disc_reason_ev', 'ac_tech_setup', 'dc_tech_setup', 'battery_tech_setup', 'subsidy',
                               'asset_management_comments', 'approval_cs', 'pitch_ev', 'negotiations_ev', 'LOI', 'setup_ev', 'construction_ev',
                               'installed_ev', 'operating_ev', 'invoice_number_ev', 'project_cluster_pv', 'status_pv_id', 'pitch_pv', 'negotiations_pv',
                               'LOI_pv', 'setup_pv', 'construction_pv', 'installed_pv', 'operating_pv', 'invoice_number_pv', 'project_cluster_ev',
                               'approval_pv', 'disc_reason_pv', 'lease_partner_pv', 'expected_kWp_pv', 'expected_spec_yield_pv',
                               'construction_quarter_pv', 'offtakers_pv', 'construction_quarter', 'snowweight_load_factor', 'preffered_charge_client_ev', 'lease_partner_ev']:
                if pd.isna(location_data[field_name]) or (isinstance(location_data[field_name], str) and location_data[field_name].strip().lower() == 'nan'):
                    location_data[field_name] = None
                                        
            self.create_or_update_location(location_data)
        return Response({'message': 'Locations created/updated successfully'}, status=status.HTTP_201_CREATED)

def map_tenant_type(value):
    if value == "ST":
        return "SingleTenant"
    elif value == "MT":
        return "MultiTenant"
    else:
        return None
    
#------------------------------------------------------- Location Device Slot Views --------------------------------------------------
class LocationDeviceSlotCreate(generics.CreateAPIView):
    serializer_class = LocationDeviceSlotSerializer
    queryset = LocationDeviceSlot.objects.all() 
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        user = request.user
        location_id = request.data.get('location_id')
        obj = [location_id, 'locations', 'location-device-channels', 2]
        if not user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        points = request.data.get('points', [])
        existing_records = LocationDeviceSlot.objects.filter(location_id=location_id)
        existing_records.delete()


        created_instances = []

        for point in points:
            serializer = self.get_serializer(data={'location_id': location_id, **point})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            created_instances.append(serializer.data)

        headers = self.get_success_headers(created_instances)
        return Response(created_instances, status=status.HTTP_201_CREATED, headers=headers)

    
class LocationDeviceSlotDelete(generics.DestroyAPIView):
    queryset = LocationDeviceSlot.objects.all()
    serializer_class = LocationDeviceSlotSerializer
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        user = request.user
        if not user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({'message':'Location device slot deleted successfully!'})
        except ValidationError as error:
            return Response({'error':error.detail}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LocationDeviceSlotList(generics.ListCreateAPIView):
    queryset = LocationDeviceSlot.objects.all().order_by('id')
    serializer_class = LocationDeviceSlotSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
             
        
        response_data = {
            'locationDeviceSlotList':serializer.data,
            # 'deviceChannels': device_channels
        }
        return Response(response_data)
    

class LocationDeviceSlotRetrieve(generics.RetrieveAPIView):
    queryset = LocationDeviceSlot.objects.all()
    serializer_class = LocationDeviceSlotSerializer

    def get_queryset(self):
        location_id = self.kwargs.get('location_id')
        return LocationDeviceSlot.objects.filter(location_id=location_id)
        
    def retrieve(self, request, *args, **kwargs):
        location = self.kwargs.get('location_id')
        location_id = Location.objects.get(pk=location)
        # obj = [location_id, 'locations', 'location-device-channels', 1]
        # if not request.user.is_admin:
        #     has_permission = check_permission_user(self, request, obj)
        #     if not has_permission:
        #         return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            response_data = serializer.data
            return Response({'locationDeviceSlots':response_data})
        except ValidationError as error:
            return Response({'error':error.detail}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error':str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)



#-------------------------------------------- Location Measure Settings Update ----------------------------------------------------------------

class LocationMeasureSettingsCreateAPIView(generics.CreateAPIView):
    queryset = LocationMeasureSettings.objects.all()
    serializer_class = LocationMeasureSettingsSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        location_id = kwargs.get('location_id')
        instance = LocationMeasureSettings.objects.filter(location_id=location_id).first()
        obj = [location_id, 'locations', 'location-kpi-general-details', 2]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)


        if instance:
            serializer = self.get_serializer(instance, data=request.data, partial=True, context={'location_id':location_id})
        else:
            mutable_data = request.data.copy()
            mutable_data['location_id'] = location_id
            serializer = self.get_serializer(data=mutable_data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'LocationMeasureSettings':serializer.data}, status=status.HTTP_200_OK if instance else status.HTTP_201_CREATED)


    
class LocationMeasureSettingsRetrieveAPIView(generics.RetrieveAPIView):
    queryset = LocationMeasureSettings.objects.all()
    serializer_class = LocationMeasureSettingsSerializer
    permission_classes = (IsAuthenticated,)  

    def get_object(self):
        location_id = self.kwargs.get('location_id')
        return LocationMeasureSettings.objects.filter(location_id=location_id).first()
        
    def retrieve(self, request, *args, **kwargs):
        location = self.kwargs.get('location_id')
        location_id = Location.objects.get(pk=location)
        obj = [location_id, 'locations', 'location-kpi-general-details', 1]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            instance = self.get_object()
            if instance:
                serializer = self.get_serializer(instance)
                response_data = serializer.data
                return Response({'locationMeasureSettingsDetails':response_data})
            else:
                return Response({'locationMeasureSettingsDetails': []})
        except ValidationError as error:
            return Response({'error':error.detail}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error':str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

#-------------------------------------------------- EV AND PV RETRIEVE APIS ----------------------------------------------------------
class LocationEVDetails(generics.RetrieveAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationEVDetailSerializer
    permission_classes = (IsAuthenticated,)  

        
    def retrieve(self, request, *args, **kwargs):
        location_id = self.kwargs['pk']
        obj = [location_id, 'locations', 'location-ev-details', 1]
        user = request.user
        
        if not user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({'locationEVDetails':serializer.data})
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class LocationPVDetails(generics.RetrieveAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationPVDetailSerializer
    permission_classes = (IsAuthenticated,)  

        
    def retrieve(self, request, *args, **kwargs):
        location_id = self.kwargs['pk']
        obj = [location_id, 'locations', 'location-ev-details', 1]
        user = request.user
        if not user.is_admin:
           has_permission = check_permission_user(self, request, obj)
           if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({'locationPVDetails':serializer.data})
        except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
#---------------------------------------------------------- LOCATION MEASURES ---------------------------------------------------------
class LocationMeasuresListCreate(generics.CreateAPIView):
    serializer_class = LocationMeasuresSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        user = request.user
        location_id = self.kwargs.get('location_id')
        year = request.data.get('year')
        year = int(year)
        try:
            location = Location.objects.get(pk=location_id)
        except Location.DoesNotExist:
            return Response({'error': 'Location does not exist'})
        obj = [location_id, 'locations', 'location-kpi-values', 1]
        if not user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                raise PermissionDenied()            

        existing_measures = LocationMeasures.objects.filter(location_id=location, month_year__year=year)
        response_data = {'location_id':location_id, 'location_name': location.name, 'device_channels':[]}

        #virtual_channels = DeviceChannel.objects.filter(device__is_virtual=True).order_by('id')
        #return Response({'test': virtual_channels.values()})
        existing_device_channel_ids = LocationMeasures.objects.filter(
            location_id=location_id,
            device_channel_id__device__is_virtual=True,
            ).values_list('device_channel_id', flat=True
            ).distinct()

        for device_channel_id in existing_device_channel_ids:
            if device_channel_id is None:
                continue
            device_channel = DeviceChannel.objects.filter(pk=device_channel_id, is_active=True, is_assigned=True).first()
            if device_channel is None:
                continue
            device_channel_data = {
                'device_channel_id': device_channel_id,
                'device_channel_name': device_channel.channel_name,
                'channel_number': device_channel.channel_number,
                'is_observer': device_channel.is_observer,
                'is_active': device_channel.is_active,
                'is_assigned': device_channel.is_assigned,
                'device_topology_id': device_channel.device_topology.id,
                'device_topology_name':device_channel.device_topology.name,
                'months': []
                }

            for month in range(1, 13):
                month_date = datetime(year=year, month=month, day=1)
                measures, created = LocationMeasures.objects.get_or_create(
                    device_channel_id=device_channel,
                    location_id=location,
                    month_year=month_date.date(),
                )
                month_data = {
                    'id':measures.id,
                    'month_year': measures.month_year,
                    'generated_energy': measures.generated_energy,
                    'delivered_energy': measures.delivered_energy,
                    'advance_payment':measures.advance_payment,
                    'created_at': measures.created_at,
                    'updated_at': measures.updated_at,
                }
                device_channel_data['months'].append(month_data)

            response_data['device_channels'].append(device_channel_data)

        return Response({'locationMeasures':response_data}, status=status.HTTP_200_OK)

class LocationMeasuresUpdate(generics.UpdateAPIView):
   queryset = LocationMeasures.objects.all()
   serializer_class = LocationMeasuresSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       instance = self.get_object()
       location_id = instance.location_id.id
       obj = [location_id, 'locations', 'location-kpi-values', 3]
       try:
           user = request.user
           if not user.is_admin:
               has_permission = check_permission_user(self, request, obj)
               if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           instance = self.get_object()
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response({"locationMeasures":serializer.data})
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
#-------------------------------------------------- LOCATION MOLOS AND VALUES VIEWS -------------------------------------------------   
class LocationMalosCreateAPIView(generics.CreateAPIView):
    serializer_class = LocationMalosSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        location_id = self.kwargs.get('location_id')

        try:
            location = Location.objects.get(pk=location_id)
        except Location.DoesNotExist:
            return Response({'error': 'Location does not exist, please choose another one'}, status=500)
        obj = [location_id, 'locations', 'location-malo-numbers', 2]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)

        malo_number = request.data.get('malo_number')
        if not malo_number:
            return Response({'error':'malo_number is required'}, status=500)
        values_data = request.data.get('values', [])
        is_external = request.data.get('is_external')
        energy_type = request.data.get('energy_type')
        date_column = request.data.get('date_column')
        time_column = request.data.get('time_column')
        value_column = request.data.get('value_column')
        values_from = request.data.get('values_from')
        values_to   = request.data.get('values_to')
        notation    = request.data.get('notation')
        values_unit = request.data.get('values_unit')
        values_unit_changed = request.data.get('values_unit_changed')
        date_representation = request.data.get('date_representation')
        date_format = request.data.get('date_format')
        
        existing_malos_instance = LocationMalos.objects.filter(malo_number=malo_number).first()

        if existing_malos_instance:
            location_malos_serializer = LocationMalosSerializer(existing_malos_instance, data=request.data)
            location_malos_serializer.is_valid(raise_exception=True)
            location_malos_serializer.save(location_id=location)
        else:
            location_malos_serializer = self.get_serializer(
                data={
                    'location_id': location,
                    'malo_number': malo_number,
                    'is_external': is_external,
                    'energy_type': energy_type,
                    'date_column':date_column,
                    'time_column':time_column,
                    'value_column':value_column,
                    'values_from':values_from,
                    'values_to': values_to,
                    'notation': notation,
                    'values_unit': values_unit,
                    'values_unit_changed': values_unit_changed,
                    'date_representation': date_representation,
                    'date_format':date_format
                    }
            )
            location_malos_serializer.is_valid(raise_exception=True)
            location_malos_serializer.save(location_id=location)

        location_malo_id = location_malos_serializer.instance.id
        location_device_malo_serializer = None

        if is_external:
            for value_data in values_data:
                date = value_data.get('date')
                time = value_data.get('time')
                existing_instance = LocationMaloValues.objects.filter(
                    location_malo_id=location_malo_id,
                    date=date,
                    time=time
                ).first()

                if existing_instance:
                    existing_instance.delete()

                data = {
                    'location_malo_id': location_malo_id,
                    'value': value_data.get('value'),
                    'date': date,
                    'time': time,
                }
                location_malo_values_serializer = LocationMaloValuesSerializer(data=data)
                location_malo_values_serializer.is_valid(raise_exception=True)
                location_malo_values_serializer.save()
        else:
            malo_calc_device_channel_id = request.data.get('malo_calculation_device_channel_id')
            existing_device_channel = DeviceChannel.objects.filter(id=malo_calc_device_channel_id).first()
            if not existing_device_channel:
                return Response({'error':'device channel missing in request or not found'}, status=500)
            
            existing_location_device_malo = LocationDeviceMalos.objects.filter(location_malos_id=location_malo_id).first()
            if not existing_location_device_malo:
                location_device_malo_serializer = LocationDeviceMalosSerializer(data={'location_malos_id': location_malo_id, 'malo_calculation_device_channel_id': malo_calc_device_channel_id})
                location_device_malo_serializer.is_valid(raise_exception=True)
                location_device_malo_serializer.save()

                command = f'calculate_energyreadings_malo_quarterhour --malo_id={location_malo_id}'
                call_command(*command.split())
            else:
                return Response({'error':'location device malo already exists'}, status=500)
            
        

        if location_device_malo_serializer is not None:
            response_data = {
                'location_molos': location_malos_serializer.data,
                'location_device_malo': location_device_malo_serializer.data
            }
        else:
            response_data = {
                'location_molos': location_malos_serializer.data,
                'location_molo_values': LocationMaloValuesSerializer(LocationMaloValues.objects.filter(location_malo_id=location_malo_id), many=True).data,
            }

        return Response(response_data, status=status.HTTP_201_CREATED)
    

class LocationMalosGetList(generics.RetrieveAPIView):
    queryset = LocationMalos.objects.all()
    serializer_class = LocationMalosListSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        location_id = self.kwargs.get('location_id')
        return LocationMalos.objects.filter(location_id=location_id)
    
    def retrieve(self, request, *args, **kwargs):
        location = self.kwargs.get('location_id')
        location_id = Location.objects.get(pk=location)
        obj = [location_id, 'locations', 'location-malo-numbers', 1]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            instance = self.get_object()
            if instance:
                serializer = self.get_serializer(instance, many=True)
                response_data = serializer.data
                return Response({'locationMalos': response_data})
            else:
                return Response({'locationMalos': []})
        except ValidationError as error:
            return Response({'error':error.detail}, status = 500)
        except Exception as e:
            return Response({'error': str(e)}, status = 500)


        
class LocationMaloDelete(generics.DestroyAPIView):
    queryset = LocationMalos.objects.all()
    serializer_class = LocationMalosSerializer
    permission_classes = (IsAuthenticated,)
    
    
    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        location_id = instance.location_id.id
        obj = [location_id, 'locations', 'location-malo-numbers', 4]
        
        if not user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
        try:
            self.perform_destroy(instance)
            return Response({'message': 'Location malo deleted successfully!'})
        except ValidationError as error:
            return Response({'error': e.detail}, status = 500)
        except Exception as e:
            return Response({'error': str(e)}, status = 500)
        
class LocationStatusEVPVView(generics.ListAPIView):
    queryset = LocationStatusEVPV.objects.all()
    serializer_class = LocationStatusEVPVSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        return Response({'locationAdditionalStatusList': response_data})
    

class LocationDeviceMaloCreate(generics.CreateAPIView):
    serializer_class = LocationDeviceMalosSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        location_malos_id = request.data.get('location_malos_id')
        location_malos = LocationMalos.objects.get(pk=location_malos_id)
        location_id = location_malos.location_id.id
        obj = [location_id, 'locations', 'location-malo-virtual-channels', 2]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
        try:
            location_malo_id = request.data.get('location_malos_id')
            device_malo = LocationDeviceMalos.objects.get(location_malos_id=location_malo_id)
            

            return Response({'error': 'Location Malo already exists.'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        except LocationDeviceMalos.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
                response_data = {"device_malos": serializer.data}
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
class LocationDeviceMaloGetList(generics.CreateAPIView):
    queryset = LocationDeviceMalos.objects.all()
    serializer_class = LocationDeviceMalosSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self, request):
        location_id = request.data.get('location_id')
        if location_id is not None:
            return LocationDeviceMalos.objects.filter(location_malos_id__location_id=location_id)
        else:
            return LocationDeviceMalos.objects.all()
    
    def post(self, request, *args, **kwargs):
        location = request.data.get('location_id')
        location_id = Location.objects.get(pk=location)
        obj = [location_id, 'locations', 'location-malo-virtual-channels', 1]
        if not request.user.is_admin:
            has_permission = check_permission_user(self, request, obj)
            if not has_permission:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            instance = self.get_object(request)
            if instance:
                serializer = self.get_serializer(instance, many=True)
                response_data = serializer.data
                return Response({'location_device_malos': response_data})
            else:
                return Response({'location_device_malos': []})
        except ValidationError as error:
            return Response({'error':error.detail}, status = 500)
        except Exception as e:
            return Response({'error': str(e)}, status = 500)
        
class LocationDeviceMaloDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = LocationDeviceMalos.objects.all()
    serializer_class = LocationDeviceMalosSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        location_id = instance.location_malos_id.location_id.id
        obj = [location_id, 'locations', 'location-malo-virtual-channels', 1]
        try:
            if not self.request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            
            serializer = self.get_serializer(instance)
            response_data = {"device_malos_details": serializer.data}
            return Response(response_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LocationDeviceMalosSerializer
        return self.serializer_class

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        location_id = instance.location_malos_id.location_id.id
        obj = [location_id, 'locations', 'location-malo-virtual-channels', 3]
        try:
            if not self.request.user.is_admin:
                has_permission = check_permission_user(self, request, obj)
                if not has_permission:
                    return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            
            old_kpi_malo = None
            if instance.malo_kpi_device_channel_id is not None:
                old_kpi_malo = instance.malo_kpi_device_channel_id.id
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            response_serializer = self.serializer_class(instance)
            
            if instance.malo_kpi_device_channel_id is not None and instance.malo_kpi_device_channel_id.id is not None:
                assigned_device_channel = DeviceChannel.objects.get(pk=instance.malo_kpi_device_channel_id.id)
                assigned_device_channel.is_assigned = True
                assigned_device_channel.save()
              
                command = f'create_location_measures'
                call_command(command)

                command = f'update_kpi_malo_channels --device_channel_id={instance.malo_kpi_device_channel_id.id}'
                call_command(*command.split())

            elif old_kpi_malo is not None:
                unassigned_device_channel = DeviceChannel.objects.get(pk=old_kpi_malo)
                unassigned_device_channel.is_assigned = False
                unassigned_device_channel.save()

            return Response(response_serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def destroy(self, request, *args, **kwargs):
        device_malo_ids = request.data.get('device_malo_ids')
        instance = self.get_object()
        location_id = instance.location_malos_id.location_id.id
        obj = [location_id, 'locations', 'location-malo-virtual-channels', 4]
        if isinstance(device_malo_ids, list) and len(device_malo_ids) > 0:
            try:
                if not self.request.user.is_admin:
                    has_permission = check_permission_user(self, request, obj)
                    if not has_permission:
                        return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
                devices = LocationDeviceMalos.objects.filter(id__in=device_malo_ids)
                if devices.count() > 0:
                    devices.delete()
                    for device in devices:
                        assigned_device_channel = DeviceChannel.objects.get(pk=device.malo_kpi_device_channel_id.id)
                        assigned_device_channel.is_assigned = False
                        assigned_device_channel.save()
                    return Response({'message': 'DeviceMalo deleted.'}, status=status.HTTP_200_OK)
                return Response({'status_code':751, 'message': 'Unable to find the device malo.'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            try:
                if not self.request.user.is_admin:
                    has_permission = check_permission_user(self, request, obj)
                    if not has_permission:
                        return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

                instance = self.get_object()
                unassigned_device_channel = DeviceChannel.objects.get(pk=instance.malo_kpi_device_channel_id.id)
                self.perform_destroy(instance)
                unassigned_device_channel.is_assigned = False
                unassigned_device_channel.save()
                return Response({'message': 'DeviceMalo deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            


#------------------------------------------ LOCATION PARTNER TYPE VIEWS ----------------------------------------------------------------
  
class LocationPartnerTypeCreate(generics.CreateAPIView):
   serializer_class = LocationPartnerTypeSerializer
   permission_classes = (IsAuthenticated,)
   def create(self, request, *args, **kwargs):
       if not request.user.is_admin:
           return Response({'error':'You do not have permission to perform this action'}, status = 421)
       serializer = self.get_serializer(data=request.data)
       serializer.is_valid(raise_exception=True)
       self.perform_create(serializer)
       
       return Response({'locationPartnerTypes': serializer.data})
    
class LocationPartnerTypeDelete(generics.DestroyAPIView):
    queryset = LocationPartnerType.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
           return Response({'error':'You do not have permission to perform this action'}, status = 421)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'location partner type successfully deleted'})
    
class LocationPartnerTypeList(generics.RetrieveAPIView):
    queryest = LocationPartnerType.objects.all()
    serializer_class = LocationPartnerTypeSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        location_id = self.kwargs.get('location_id')
        return LocationPartnerType.objects.filter(location_id=location_id)
    
    def retrieve(self, request, *args, **kwargs):
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin = True)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)
        
        if not request.user.is_admin and not partner_admin_user:
            raise PermissionDenied()
        
        try:
            instance = self.get_queryset()
            serializer = self.get_serializer(instance, many=True)
            return Response({'locationPartnerTypes':serializer.data})
        except Exception as e:
                return Response({'error':str(e)})

     
class LocationPartnerTypeUpdate(generics.UpdateAPIView):
    queryset = LocationPartnerType.objects.all()
    serializer_class = LocationPartnerTypeUpdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'locationPartnerTypeDetails':serializer.data})

#----------------------------------- LOCATION LIST BY PARTNER AND TYPE ------------------------------------------------------------
class LocationListByPartnerType(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LocationListSerializer

    def list(self, request, *args, **kwargs):
        partner_id = self.kwargs.get('partner_id')
        type_id = self.kwargs.get('type_id')
        location_ids = LocationPartnerType.objects.filter(partner_id=partner_id, type_id=type_id).values_list('location_id', flat=True)
        locations = Location.objects.filter(id__in=location_ids)
        serializer = self.get_serializer(locations, many=True)
        return Response({'partnerTypeLocation': serializer.data})

class LocationListByMonth(generics.ListAPIView):
    serializer_class = LocationListSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        year = request.data.get('year')

        # locations = Location.objects.filter(operating_date__year=year)
        locations = Location.objects.filter(
            Q(operating_date__year=year, operating_date__isnull=False) | Q(exp_operation_date_pv__year=year, exp_operation_date_pv__isnull=False)
        )
        location_data = []
        for location in locations:
            location_data.append({
                'id': location.id,
                'name':location.name,
                'month_year': location.operating_date if location.operating_date else location.exp_operation_date_pv, #location.operating_date.strftime('%Y-%m-%d')
                'location_status': location.location_status, 
            })
        
        response_data = {'locationList': {'months': location_data}}
        
        return Response(response_data)



    




    
