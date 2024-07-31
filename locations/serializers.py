from rest_framework import serializers
from .models import *
from projectmanagement.models import Project
from contracts.models import ContractFile
from django.db.models import Min, Max
from django.db.models import ExpressionWrapper, F, Func, DateTimeField
# from .serializers import LocationDeviceSlotSerializer


#-------------------------------------------------- Location Serializers ------------------------------------------------------------
class CreateLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'snowweight_load_factor', 'city', 'zipcode', 'address_line_1', 'location_latitude', 'location_longitude')

class LocationListSerializer(serializers.ModelSerializer):
    country_name = serializers.ReadOnlyField(source = 'country_id.name')
    location_status = serializers.ReadOnlyField()
    tenant_name = serializers.ReadOnlyField(source = 'tenant_id.name')
    property_manager_name = serializers.ReadOnlyField(source = 'property_manager_id.name')
    land_owner_name = serializers.ReadOnlyField(source='land_owner_id.name')
    project_id = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    current_phase = serializers.ReadOnlyField(source='current_phase_id.phase_name')
    lead_company_name = serializers.ReadOnlyField(source='lead_company.name')
    
    class Meta:
        model = Location
        fields = ('id', 'location_micropage', 'micro_page_image', 'location_code', 'location_status', 'channel_background_color', 'channel_text_color', 'operating_date', 'project_id', 'project_name', 'current_phase_id', 'current_phase', 'estimated_current_phase_end_date', 'name', 'sales_email', 'sales_phone', 'support_email', 'support_phone', 'address_line_1', 'address_line_2',
                  'city', 'state', 'location_state' ,'state_start_date', 'state_comments', 'state_end_date', 'location_image', 'location_device_image', 'country_id', 'country_name', 'zipcode', 'description', 'snowweight_load_factor', 'prioritisation', 'prioritisation_comments', 'expected_kWp', 'estimated_pv_costs', 'LIS', 'tenant_id', 'tenant_name', 'tenant_type', 'property_manager_id', 'property_manager_name', 'land_owner_id', 'land_owner_name', 'expected_kWp_pv', 'estimated_completion_date', 'lead_company', 'lead_company_name')
        
    def get_project_id(self, obj):
        project = Project.objects.filter(location_id=obj).first()
        if project:
            return project.id
        return None
    
    def get_project_name(self, obj):
        project = Project.objects.filter(location_id=obj).first()
        if project:
            return project.name
        return None

class LocationDeviceSlotSerializer(serializers.ModelSerializer):
    device_id = serializers.ReadOnlyField(source ='location_device_id.device.id')
    device_name = serializers.ReadOnlyField(source ='location_device_id.device.name')
    channel_number = serializers.ReadOnlyField(source ='device_channel_id.channel_number')
    channel_name = serializers.ReadOnlyField(source ='device_channel_id.channel_name')
    is_observer = serializers.ReadOnlyField(source ='is_observer.is_observer')
    is_active = serializers.ReadOnlyField(source ='is_observer.is_active')

    
    class Meta:
        model = LocationDeviceSlot
        fields = ('id', 'location_id', 'location_device_id', 'device_id', 'device_name', 'x_point', 'y_point', 'channel_number', 'channel_name', 'is_observer', 'is_active')
        
        
   
    
class RetrieveLocationSerializer(serializers.ModelSerializer):
    country_name = serializers.ReadOnlyField(source = 'country_id.name')
    status_name = serializers.ReadOnlyField(source = 'status_id.name')
    tenant_name = serializers.ReadOnlyField(source = 'tenant_id.name')
    land_owner_name = serializers.ReadOnlyField(source = 'land_owner_id.name')
    property_manager_name = serializers.ReadOnlyField(source = 'property_manager_id.name')
    contract_id = serializers.SerializerMethodField()
    location_status = serializers.ReadOnlyField()
    project_id = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    current_phase = serializers.ReadOnlyField(source='current_phase_id.phase_name')
    current_phase_status = serializers.ReadOnlyField(source='current_phase_id.phase_status')
    lead_company_name = serializers.ReadOnlyField(source= 'lead_company.name')
    
    def get_contract_id(self, obj):
        try:
            location_contracts = LocationContract.objects.filter(location_id=obj.id)
            return [contract.contract_id for contract in location_contracts]
        except LocationContract.DoesNotExist:
            return []
    class Meta:
        model = Location
        fields = ('id', 'name', 'location_micropage', 'micro_page_image', 'location_code', 'location_image', 'location_status', 'project_id', 'project_name', 'current_phase_id', 'current_phase','current_phase_status', 'status_id','status_name', 'sales_phone',  'sales_email','support_email', 'support_phone', 'address_line_1', 'address_line_2',
                  'city', 'state', 'country_id', 'country_name', 'zipcode', 'description', 'land_owner_id', 'land_owner_name', 'channel_background_color', 'channel_text_color',
                  'property_manager_id', 'property_manager_name', 'lead_company', 'lead_company_name', 'location_state', 'state_comments', 'location_device_image', 'snowweight_load_factor', 'prioritisation', 'prioritisation_comments', 'expected_kWp', 'estimated_pv_costs', 'LIS', 'state_start_date', 'state_end_date', 'created_at','updated_at', 'tenant_id', 'tenant_name', 'tenant_type',  'contract_id')
        
    def get_project_id(self, obj):
        project = Project.objects.filter(location_id=obj).first()
        if project:
            return project.id
        return None
    
    def get_project_name(self, obj):
        project = Project.objects.filter(location_id=obj).first()
        if project:
            return project.name
        return None
        

class LocationGeneralSerializer(serializers.ModelSerializer):
    
    country_name = serializers.ReadOnlyField(source = 'country_id.name')
    
    class Meta:
        model = Location
        fields = ('id', 'name', 'description', 'address_line_1', 'address_line_2', 'city', 'state', 'country_id', 'country_name','zipcode', 'location_image', 'location_device_image', 'lead_company')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'locationGeneralDetails':data}
    
    
class LocationStatusSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    status_name = serializers.ReadOnlyField(source = 'status_id.name')
    
    class Meta:
        model = Location
        fields = ('id', 'name','status_id', 'status_name')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'statusDetails':data}
    
class LocationLandSerializer(serializers.ModelSerializer):
    land_owner_name = serializers.ReadOnlyField(source = 'land_owner_id.name')
    class Meta:
        model = Location
        fields = ('id', 'land_owner_id', 'land_owner_name', 'land_owner_asset_id')
        extra_kwargs = {
            'land_owner_id':{'required':True},
        }
        
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'locationLandOwnerDetails':data}
    
class LocationPropertyManagerSerializer(serializers.ModelSerializer):
    property_manager_name = serializers.ReadOnlyField(source = 'property_manager_id.name')
    class Meta:
        model = Location
        fields = ('id', 'property_manager_id', 'property_manager_name')
        extra_kwargs = {
            'property_manager_id':{'required':True},
        }
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'locationPropertyManagerDetails':data}
    
    
#------------------------------------------------------------------- LOCATION STATE ----------------------------------------------------

class LocationStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'location_state', 'state_start_date', 'state_end_date', 'state_comments')
        
class LocationSnowWeightSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    
    class Meta:
        model = Location
        fields = ('id', 'name','snowweight_load_factor')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'statusDetails':data}

class LocationPrioritisationSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    
    class Meta:
        model = Location
        fields = ('id', 'name','prioritisation', 'prioritisation_comments')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'statusDetails':data}


class LocationTenantSerializer(serializers.ModelSerializer):
    tenant_name = serializers.ReadOnlyField(source='tenant_id.name')

    class Meta:
        model = Location
        fields = ('id', 'tenant_id', 'tenant_name', 'tenant_type')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'locationTenantDetails': data}


class SubtenantSerializer(serializers.ModelSerializer):
   subtenant_name = serializers.ReadOnlyField(source='subtenant_id.name')

   class Meta:
       model = LocationSubTenant
       fields = ('subtenant_id', 'subtenant_name')




class GetTenantSerializer(serializers.ModelSerializer):
   subtenants = serializers.SerializerMethodField()
   tenant_name = serializers.ReadOnlyField(source='tenant_id.name')

   class Meta:
       model = Location
       fields = ('id', 'tenant_id', 'tenant_name', 'tenant_type', 'subtenants')

   def get_subtenants(self, instance):
       if instance.tenant_type == 'SingleTenant':
           return []
       subtenants = LocationSubTenant.objects.filter(location_id=instance)
       serializer = SubtenantSerializer(subtenants, many=True)
       return serializer.data

   def to_representation(self, instance):
       representation = super().to_representation(instance)
       if self.instance == Location.objects.first():
           tenant_data = {
               'id': representation['id'],
               'tenant_id': representation['tenant_id'],
               'tenant_name': representation['tenant_name'],
               'tenant_type': representation['tenant_type'],
               'subtenants': representation['subtenants']
           }
           return {'locationTenantDetails': [tenant_data]}
       else:
           return representation

#-------------Location Sales

class LocationSalesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Location
        fields = ('sales_phone', 'sales_email')
    #Response data 
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'locationSalestDetails':data}

class LocationSupportSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Partner
        fields = ('support_phone', 'support_email')
    #Response data   
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'locationSupportDetails':data}
    
class LocationLeadCompanySerializer(serializers.ModelSerializer):
    lead_company_name  = serializers.ReadOnlyField(source='lead_company.name')
    class Meta:
        model = Location
        fields = ('id', 'lead_company', 'lead_company_name')
    
#----------------------------------------- LOCATION PRE-RATINGS---------------------------------------------------------------------
class LocationPreRateSerializers(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'expected_kWp', 'estimated_pv_costs', 'LIS')
        
    def update(self, instance, validated_data):
        expected_kWp = validated_data.get('expected_kWp')
        if expected_kWp is not None:
            instance.expected_kWp = int(expected_kWp)

        estimated_pv_costs = validated_data.get('estimated_pv_costs')
        if estimated_pv_costs is not None:
            instance.estimated_pv_costs = int(estimated_pv_costs)

        return super().update(instance, validated_data)
    
class PipeLineReportSerializer(serializers. ModelSerializer):
    land_owner_name = serializers.ReadOnlyField(source='land_owner_id.name')
    property_manager_name = serializers.ReadOnlyField(source = 'property_manager_id.name')
    tenant_name         = serializers.ReadOnlyField(source = 'tenant_id.name')
    lead_company_name  = serializers.ReadOnlyField(source='lead_company.name')
    lead_manager_ev_name  = serializers.ReadOnlyField(source='lead_manager_ev.get_full_name')
    lead_manager_pv_name = serializers.ReadOnlyField(source= 'lead_manager_pv.get_full_name')
    class Meta:
        model = Location
        fields = '__all__'


#----------------------------------------------------- Location Serializers End ------------------------------------------------------

#------------------------------------------ Permissions, Module & Module Panel Serializers ------------------------------------------
class PermissionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Permission
        fields = ('id', 'name')
        
class ModulePanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePanel
        fields = ('id', 'name', 'slug', 'module_id')

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('id', 'name', 'slug')
        
           


    
#------------------------------------------ ROLES SERIALIZERS -------------------------------------------------------------------------

class RoleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'is_fixed')
        

class RolePermissionSerializer(serializers.ModelSerializer):
    modules_name = serializers.ReadOnlyField(source = 'modules_id.name')
    module_panel_name = serializers.ReadOnlyField(source = 'modules_panels_id.name')
    permissions_name = serializers.ReadOnlyField(source = 'permissions_id.name')
    
    
    class Meta:
        model = RolesPermissions
        fields = ('id', 'modules_id', 'modules_name', 'modules_panels_id', 'module_panel_name', 'permissions_id', 'permissions_name')
        
class CustomRolePermissionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RolesPermissions
        fields = ('id', 'modules_id', 'modules_panels_id', 'permissions_id')
        
        
        
class LocationRoleSerializer(serializers.ModelSerializer):
   partners_id = serializers.PrimaryKeyRelatedField(queryset=Partner.objects.all(), many=True)
   roles_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True)
   partner_names = serializers.SerializerMethodField()
   role_names = serializers.SerializerMethodField()

   class Meta:
       model = LocationRole
       fields = ['id','locations_id', 'partners_id', 'partner_names', 'roles_id', 'role_names']

   def get_partner_names(self, obj):
       partner_ids = obj.partners_id.values_list('id', flat=True)
       partners = Partner.objects.filter(id__in=partner_ids)
       return [partner.name for partner in partners]

   def get_role_names(self, obj):
       role_ids = obj.roles_id.values_list('id', flat=True)
       roles = Role.objects.filter(id__in=role_ids)
       return [role.name for role in roles]

   def get_location_name(self, obj):
       location = Location.objects.get(id=obj.location_id)
       return location.name
        
#------------------------------------------------- PV Files Uplaods --------------------------------------------------------------

class PVFileSerializer(serializers.ModelSerializer):
    img_url = serializers.SerializerMethodField()
    class Meta:
        model = PVFile
        fields = ('id', 'pv_file_url', 'img_url')
        extra_kwargs = {
            'partner_id':{'write_only':True}
        }
        
    def get_image_url(self, obj):
        return obj.pv_file_url.url if obj.pv_file_url else None


#------------------------------------------------------ Location Contracts ------------------------------------------------------


class ContractFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractFile
        fields = '__all__'

class LocationContractRequestSerializer(serializers.Serializer):
    contract_id = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all())





#--------------------------------------- CREATE LOCATION USING CSV --------------------------------------------------------
       

class LocationCSVSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Location
        fields = ('name', 'address_line_1', 'city', 'state', 'zipcode', 'land_owner_id', 'land_owner_asset_id', 'property_manager_id', 'tenant_id', 'tenant_type', 'location_state', 'snowweight_load_factor',
                  'location_status', 'prioritisation', 'expected_kWp', 'estimated_pv_costs', 'LIS', 'project_number', 'status_ev', 'approval_ev',
                  'milestone_date', 'disc_reason_ev', 'planned_ac', 'ac_speed', 'ac_tech_setup', 'planned_dc', 'dc_speed', 'dc_tech_setup',
                  'planned_battery', 'battery_speed', 'battery_tech_setup', 'construction_year', 'construction_quarter', 'exp_installation_date',
                  'planned_installation_date', 'exp_operation_date', 'capex_spent_to_date', 'capex_total_expected', 'subsidy', 'asset_management_comments',
                  'approval_cs', 'pitch_ev', 'negotiations_ev', 'LOI', 'setup_ev', 'construction_ev', 'installed_ev', 'operating_ev', 
                  'invoice_number_ev', 'project_cluster_pv', 'status_pv', 'asset_management_comments_pv', 'pitch_pv', 'negotiations_pv', 'LOI_pv', 'setup_pv', 'construction_pv',
                  'installed_pv', 'operating_pv', 'invoice_number_pv', 'parking_spots', 'project_cluster_ev', 'lead_company', 'lead_manager_ev', 'geap_ev', 'gep_ev', 'cos_pv')
        
        
#----------------------------------------------------------- LOCATION EV DETAIL UPDATE ------------------------------------------------
class LocationEVDetailSerializer(serializers.ModelSerializer):
    
    lead_company_name = serializers.ReadOnlyField(source = 'lead_company.name')
    lead_manager_name = serializers.ReadOnlyField(source = 'lead_manager_ev.get_full_name')
    status_ev_name  = serializers.ReadOnlyField(source = 'status_ev_id.name')
    
    class Meta:
        model = Location
        fields = ('id', 'status_ev_id', 'status_ev_name', 'approval_ev', 'milestone_date', 'disc_reason_ev', 'planned_ac', 'ac_speed', 'ac_tech_setup',
                  'planned_dc', 'dc_speed', 'dc_tech_setup', 'planned_battery', 'battery_speed', 'battery_tech_setup',
                  'construction_year', 'construction_quarter', 'exp_installation_date', 'planned_installation_date', 'exp_operation_date',
                  'capex_spent_to_date', 'capex_total_expected', 'subsidy', 'asset_management_comments', 'approval_cs', 'pitch_ev', 
                  'negotiations_ev', 'LOI', 'setup_ev', 'construction_ev', 'installed_ev', 'operating_ev', 'invoice_number_ev', 
                  'project_cluster_ev', 'lead_company', 'lead_company_name', 'parking_spots', 'lead_manager_ev', 'lead_manager_name', 'lease_partner_ev', 'preffered_charge_client_ev',
                  'geap_ev', 'gep_ev')
        
class LocationPVDetailSerializer(serializers.ModelSerializer):
    lead_manager_pv_name = serializers.ReadOnlyField(source = 'lead_manager_pv.get_full_name')
    status_pv_name  = serializers.ReadOnlyField(source = 'status_pv_id.name')
    
    class Meta:
        model = Location
        fields = ('id', 'project_cluster_pv', 'status_pv_id', 'status_pv_name', 'asset_management_comments_pv', 'pitch_pv', 'negotiations_pv', 'LOI_pv', 'setup_pv',
                  'construction_pv', 'installed_pv', 'operating_pv', 'invoice_number_pv', 'approval_pv', 'milestone_date_pv', 
                  'disc_reason_pv', 'lease_partner_pv', 'expected_kWp_pv', 'expected_spec_yield_pv', 'construction_year_pv', 
                  'construction_quarter_pv', 'exp_installation_date_pv', 'planned_installation_date_pv', 'exp_operation_date_pv',
                  'capex_spent_to_date_pv', 'cos_pv', 'capex_total_expected_pv', 'offtakers_pv', 'lead_manager_pv','lead_manager_pv_name')
        
        

        
#------------------------------------------------- Location Device Slot ---------------------------------------------------------------

class LocationDeviceSlotSerializer(serializers.ModelSerializer):
    device_id = serializers.ReadOnlyField(source ='location_device_id.device.id')
    device_name = serializers.ReadOnlyField(source ='location_device_id.device.name')
    channel_number = serializers.ReadOnlyField(source ='device_channel_id.channel_number')
    channel_name = serializers.ReadOnlyField(source ='device_channel_id.channel_name')
    is_observer = serializers.ReadOnlyField(source ='is_observer.is_observer')
    is_active = serializers.ReadOnlyField(source ='is_observer.is_active')
    
    
    class Meta:
        model = LocationDeviceSlot
        fields = ('id', 'location_id', 'location_device_id', 'device_id', 'device_name', 'x_point', 'y_point', 'channel_number', 'channel_name', 'is_observer', 'is_active', 'device_channel_id')
        
        
class LocationMapListSerializer(serializers.ModelSerializer):
    country_name = serializers.ReadOnlyField(source='country_id.name')
    status_ev_name = serializers.ReadOnlyField(source = 'status_ev_id.name')
    status_pv_name = serializers.ReadOnlyField(source= 'status_pv_id.name')
    
    class Meta:
        model = Location
        fields = ('id', 'city', 'status_ev_id', 'status_ev_name', 'status_pv_id', 'status_pv_name', 'snowweight_load_factor', 'address_line_1', 'address_line_2', 'zipcode', 'country_id', 'country_name', 'location_status', 'lead_company', 'location_latitude', 'location_longitude')
        

#----------------------------------------------------------- LOCATION MEASURES and Measure Settings ---------------------------------------------------------
class LocationMeasuresSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LocationMeasures
        fields = ('id', 'location_id', 'device_channel_id', 'month_year', 'advance_payment', 'generated_energy', 'delivered_energy', 'created_at', 'updated_at')

class LocationMeasureSettingsSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source='location_id.name')
    class Meta:
        model = LocationMeasureSettings
        fields = ('id', 'location_id', 'location_name', 'grid_op', 'capex', 'insurance', 'billing', 'energy_meter', 'direct_marketing', 'roof_rent')
        
    
#------------------------------------------------------- LOCATION MOLOS AND VALUES SERIALIZERS --------------------------------------
class LocationMalosSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'location_id.name')
    class Meta:
        model = LocationMalos
        fields = ('id', 'location_id', 'location_name', 'malo_number', 'is_external', 'energy_type', 'date_column', 'time_column', 'value_column',
                  'values_from', 'values_to', 'notation', 'values_unit', 'values_unit_changed', 'date_representation', 'date_format')
        read_only_fields = ('location_id',)

class LocationMalosListSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'location_id.name')
    begin_date = serializers.DateField(read_only=True)
    begin_time = serializers.TimeField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    malo_calculation_device_channel = serializers.SerializerMethodField(read_only=True)
    malo_kpi_device_channel = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = LocationMalos
        fields = ('id', 'location_id', 'location_name', 'malo_number', 'is_external', 'energy_type', 'date_column', 'time_column', 'value_column',
                  'values_from', 'values_to', 'notation', 'values_unit', 'values_unit_changed', 'date_representation', 'date_format',
                  'begin_date','begin_time', 'end_date', 'end_time', 'malo_calculation_device_channel', 'malo_kpi_device_channel')
        read_only_fields = ('location_id',)
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Computing the begin_date, begin_time, end_date, and end_time for each malo number
        values = LocationMaloValues.objects.filter(location_malo_id=instance.id)
        if values.exists():
            begin_datetime = values.aggregate(
                begin_datetime=Min(ExpressionWrapper(F('date') + F('time'), output_field=DateTimeField()))
            )['begin_datetime']
            end_datetime = values.aggregate(
                end_datetime=Max(ExpressionWrapper(F('date') + F('time'), output_field=DateTimeField()))
            )['end_datetime']

            representation['begin_date'] = begin_datetime.date()
            representation['begin_time'] = begin_datetime.time()
            representation['end_date'] = end_datetime.date()
            representation['end_time'] = end_datetime.time()

        return representation
    
    # def get_malo_calculation_device_channel(self, instance):
    #     location_device_malos = LocationDeviceMalos.objects.filter(location_malos_id=instance.id).first()
        

    # def get_malo_kpi_device_channel(self, instance):
    #     location_device_malos = LocationDeviceMalos.objects.filter(location_malos_id=instance.id).first()
        
        
    


class LocationDeviceMalosSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source = 'location_malos_id.location_id.name')
    malo_number = serializers.ReadOnlyField(source = 'location_malos_id.malo_number')
    class Meta:
        model = LocationDeviceMalos
        fields = ('id', 'location_malos_id', 'malo_number', 'location_name', 'malo_calculation_device_channel_id', 'malo_kpi_object')
        

class LocationMaloValuesSerializer(serializers.ModelSerializer):
    location_malo_number = serializers.ReadOnlyField(source = 'location_malo_id.malo_number')
    
    class Meta:
        model = LocationMaloValues
        fields = ('id', 'location_malo_id', 'location_malo_number', 'value', 'date', 'time')
        
class LocationStatusEVPVSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationStatusEVPV
        fields = ('id', 'name')
        


#----------------------------------------------------- LOCATION PARTNER TYPE SERIALIZERS ---------------------------------------------
class LocationPartnerTypeSerializer(serializers.ModelSerializer):
    location_name = serializers.ReadOnlyField(source ='location_id.name')
    partner_name = serializers.ReadOnlyField(source='partner_id.name')
    type_name = serializers.ReadOnlyField(source = 'type_id.name')
    
    class Meta:
        model = LocationPartnerType
        fields = ('id', 'location_id', 'location_name', 'partner_id', 'partner_name', 'type_id', 'type_name')
        
class LocationPartnerTypeUpdateSerializer(serializers.ModelSerializer):
    partner_name = serializers.ReadOnlyField(source='partner_id.name')
    class Meta:
        model = LocationPartnerType
        fields = ('id', 'partner_id', 'partner_name')
        
class LocationFullListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'location_status')
        
class LocationMicroPageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'micro_page_image')
    
class LocationDeviceChanelColorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Location
        fields = ('id', 'channel_background_color', 'channel_text_color')