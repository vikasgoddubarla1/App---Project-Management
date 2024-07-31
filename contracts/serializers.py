from rest_framework import serializers, status
from .models import *

#list and create contracts
class CreateContractSerializer(serializers.ModelSerializer):
   created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
   class Meta:
       model = Contract
       fields = ('id', 'contract_number', 'name', 'category_id', 'sub_category_id', 'location_id', 'made_by', 'made_by_type', 'made_to', 'made_to_type', 'begin_date', 'duration', 'duration_cycle', 'auto_extended', 'extend_duration', 'extend_cycle', 'termination_duration', 'termination_cycle', 'end_date', 'termination_date', 'created_by', 'created_by_name')

class ContractFileGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractFile
        fields = ('id', 'file_url', 'created_at')
class ContractListSerializer(serializers.ModelSerializer):
    files = ContractFileGetSerializer(source='contractfile_set', many=True, read_only=True)
    category_name = serializers.ReadOnlyField(source = 'category_id.name')
    sub_category_name = serializers.ReadOnlyField(source = 'sub_category_id.name')
    location_city = serializers.ReadOnlyField(source='location_id.name')
    made_by_name = serializers.ReadOnlyField(source='made_by.name')
    made_to_name = serializers.ReadOnlyField(source='made_to.name')
    made_by_type_name = serializers.ReadOnlyField(source='made_by_type.name')
    made_to_type_name = serializers.ReadOnlyField(source='made_to_type.name')
    address_line_1 = serializers.ReadOnlyField(source='location_id.address_line_1')
    zipcode         = serializers.ReadOnlyField(source='location_id.zipcode')
    class Meta:
        model = Contract
        fields = ('id', 'contract_number', 'name',  'status', 'created_by', 'category_id', 'category_name', 'sub_category_id', 'sub_category_name',
                  'begin_date', 'duration', 'duration_cycle', 'auto_extended', 'end_date','is_terminated', 'termination_duration',
                  'termination_cycle', 'termination_date', 'is_active', 'terminated_on', 'location_id', 'location_city','address_line_1', 'zipcode', 'made_by', 'made_by_name', 'made_by_type', 'made_by_type_name', 'made_to', 'made_to_name', 'made_to_type', 'extend_duration', 'extend_cycle', 'made_to_type_name', 'approval_status', 'previous_status', 'previous_status_comments', 'files')

class ContractGeneralSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source = 'category_id.name')
    sub_category_name = serializers.ReadOnlyField(source = 'sub_category_id.name')
    
    class Meta:
        model = Contract
        fields = ('id', 'name', 'category_id', 'contract_number', 'category_name', 'sub_category_id', 'sub_category_name', 'made_by', 'made_by_type', 'made_to', 'made_to_type', 'location_id')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'contractGeneralDetails':data}

class ContractRestoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ('id', 'is_active')
    

# serializers.py
#-----------------------------------------------------------------------------------------------------------------------------
class ContractUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['name', 'created_by']


class ContractPartnerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPartner
        fields = ['partner_id']

#------------------------------------------------------------------------------------------------------------------------------   

class ContractDurationUpdateSerializer(serializers.ModelSerializer):
    end_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = ['id', 'begin_date', 'duration', 'duration_cycle', 'auto_extended', 'extend_duration', 'extend_cycle', 'is_terminated', 'termination_duration', 'termination_cycle', 'termination_date', 'terminated_on', 'status', 'end_date']

    def get_end_date(self, obj):
        return obj.end_date if obj.end_date else None
    
    def get_status(self, obj):
        return obj.status if obj.status else None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'contractDurationDetails':data}



class ContractFrameworkSerializer(serializers.ModelSerializer):
    # contract_name = serializers.ReadOnlyField(source='contract_id.name')
    class Meta:
        model = ContractFramework
        fields = ('id', 'contract_id', 'individual_contract_id')
        
    
        
        
class ContractFileSerializer(serializers.ModelSerializer):
    img_url = serializers.SerializerMethodField()
    class Meta:
        model = ContractFile
        fields = ('id', 'file_url', 'img_url', 'created_at')
        extra_kwargs = {
            'partner_id':{'write_only':True}
        }
        
    def get_image_url(self, obj):
        return obj.file_url.url if obj.file_url else None

        
class RetrieveContractList(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source ='category_id.name')
    sub_category_name = serializers.ReadOnlyField(source ='sub_category_id.name')
    
    class Meta:
        model = Contract
        fields = ('id', 'contract_number', 'name',  'status', 'created_by', 'category_id', 'category_name', 'sub_category_id', 'sub_category_name',
                  'begin_date', 'duration', 'duration_cycle', 'auto_extended', 'end_date','is_terminated', 'termination_duration',
                  'termination_cycle', 'termination_date')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data
    
class ContractSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractSubCategory
        fields = '__all__'
        
class ContractCategorySerializer(serializers.ModelSerializer):
    contractSubCategories = ContractSubCategorySerializer(source='contractsubcategory_set', many=True, read_only=True)
    class Meta:
        model = ContractCategory
        fields = ('id', 'name', 'contractSubCategories')
        
class ContractLogSerializer(serializers.ModelSerializer):
    contract_name = serializers.ReadOnlyField(source='contract_id.name')
    user_name = serializers.ReadOnlyField(source='user_id.get_full_name')
    profile_photo = serializers.SerializerMethodField()
    def get_profile_photo(self, obj):
       profile_photo = obj.user_id.profile_photo
       if profile_photo:
           request = self.context.get('request')
           if request:
               return request.build_absolute_uri(profile_photo.url)
       return None
    class Meta:
        model = ContractLogs
        fields = ('id', 'contract_id', 'contract_name', 'user_id', 'user_name', 'profile_photo', 'column_name', 'updated_at')
        

#------------------------------------------------------------- CONTRACT APPROVALS SERIALIZER -------------------------------------------------
class ContractApprovalSerializer(serializers.ModelSerializer):
    contract_name = serializers.ReadOnlyField(source='contract_id.name')
    partner_name = serializers.ReadOnlyField(source='partner_id.name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')
    type_name = serializers.ReadOnlyField(source='type_id.name')
    class Meta:
        model = ContractApprovals
        fields = ('id', 'contract_id', 'contract_name', 'partner_id', 'type_id', 'type_name', 'partner_name', 'is_approved', 'comments', 'approved_by', 'approved_by_name', 'created_at')
        
        
class ContractApprovalUpdateSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')
    class Meta:
        model = ContractApprovals
        fields = ('id', 'is_approved', 'comments', 'approved_by', 'approved_by_name', 'created_at')