from .models import *
from rest_framework import serializers
from usermanagement.models import User

#------------------------------------------- COUNTRY SERIALIZER --------------------------------
class CountrySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Countries
        fields = ('id', 'name', 'emoji')
        
#------------------------------------------- PARTNER SERIALIZERS -----------------------------------
class PartnerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Partner
        fields = ('id', 'name', 'email', 'city', 'country_id')

class PartnerRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ('id', 'role_id')
        
class PartnerTypeRoleUserSerializer(serializers.ModelSerializer):
   salutation_id = serializers.ReadOnlyField(source='user_id.salutation_id.id')
   salutation_name = serializers.ReadOnlyField(source='user_id.salutation_id.name')
   firstname = serializers.ReadOnlyField(source='user_id.firstname')
   lastname = serializers.ReadOnlyField(source='user_id.lastname')
   profile_photo = serializers.SerializerMethodField()
   confirmed = serializers.ReadOnlyField(source='user_id.confirmed')
   is_customer = serializers.ReadOnlyField(source='user_id.is_customer')
   is_admin = serializers.ReadOnlyField(source='user_id.is_admin')
   partner_type_admin = serializers.ReadOnlyField(source='is_admin')
   created_at = serializers.ReadOnlyField(source='user_id.created_at')
   last_login = serializers.ReadOnlyField(source='user_id.last_login')
   email = serializers.ReadOnlyField(source='user_id.email')
   
   def get_profile_photo(self, obj):
       profile_photo = obj.user_id.profile_photo
       if profile_photo:
           request = self.context.get('request')
           if request:
               return request.build_absolute_uri(profile_photo.url)
       return None
   
   class Meta:
       model = PartnerTypeRolesUser
       fields = ('id', 'user_id', 'salutation_id', 'salutation_name', 'firstname', 'lastname', 'email', 'profile_photo', 'confirmed', 'is_customer', 'is_admin', 'created_at', 'last_login', 'partner_type_admin')
       
class PartnerTypeRoleSerializer(serializers.ModelSerializer):
    partner_name = serializers.ReadOnlyField(source='partner_id.name')
    type_name = serializers.ReadOnlyField(source='type_id.name')
    role_name = serializers.ReadOnlyField(source='role_id.name')
    customers = PartnerTypeRoleUserSerializer(source='partnertyperolesuser_set', read_only=True, many=True)
        
    class Meta:
        model = PartnerTypesRole
        fields = ('id', 'partner_id', 'partner_name', 'type_id', 'type_name', 'role_id', 'role_name', 'customers')
        
class PartnerRetrieveSerializer(serializers.ModelSerializer):
    partner_type_roles = PartnerTypeRoleSerializer(source='partnertypesrole_set', read_only=True, many=True)
    country_name = serializers.ReadOnlyField(source = 'country_id.name')
    # partner_image = serializers.ReadOnlyField(source='partner_logo.url')

    class Meta:
        model = Partner
        fields = ('id', 'name', 'email', 'phone', 'support_phone', 'partner_logo', 'support_email', 'sales_phone', 'sales_email', 
                  'address_line_1', 'address_line_2', 'city', 'zip_code', 'website', 'country_id','country_name', 'remarks', 'partner_type_roles')
        
        extra_kwargs = {
            'email':{'required': False}
        }
        
class PartnerGeneralSerializer(serializers.ModelSerializer):
    country_name = serializers.ReadOnlyField(source = 'country_id.name')
    class Meta:
        model = Partner
        fields = ('id', 'name', 'email', 'phone', 'partner_logo', 'address_line_1', 'address_line_2', 'city', 'zip_code', 'country_id', 'country_name')
   
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'partnerGeneralDetails':data}
    
class PartnerWebsiteLinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ('id', 'website')
        
class PartnerSupportSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Partner
        fields = ('support_phone', 'support_email')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'partnerSupportDetails':data}
        
class PartnerSalesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Partner
        fields = ('sales_phone', 'sales_email')
         
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'partnerSalesDetails':data}
        
class PartnerRemarksSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Partner
        fields = ('remarks',)
     
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'partnerRemarks':data}
        
class PartnerCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'

class PartnerTypeRoleSerializerForPartnerFullList(serializers.ModelSerializer):
    type_name = serializers.ReadOnlyField(source='type_id.name')
    role_name = serializers.ReadOnlyField(source='role_id.name')
    class Meta:
        model = PartnerTypesRole
        fields = ('id', 'type_id', 'type_name', 'role_id', 'role_name')
        
class PartnerFullListSerializer(serializers.ModelSerializer):
    partner_type_roles = PartnerTypeRoleSerializerForPartnerFullList(source='partnertypesrole_set', read_only=True, many=True)
    
    class Meta:
        model = Partner
        fields = ('id', 'name', 'partner_type_roles')
        

        
#-------------------------------------------------- PARTNER TYPES AND ROLES NEW ----------------------------------------------------------
class TypeSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role_id.name')
    class Meta:
        model = Type
        fields = ('id', 'name', 'role_id', 'role_name', 'description', 'is_fixed')
        
class PartnerTypeSerializer(serializers.ModelSerializer):
    partner_name = serializers.ReadOnlyField(source = 'partner_id.name')
    type_name = serializers.ReadOnlyField(source='type_id.name')
    class Meta:
        model = PartnerType
        fields = ('id', 'partner_id', 'partner_name', 'type_id', 'type_name')


class PartnerTypeRoleupdateSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role_id.name')
    
    class Meta:
        model = PartnerTypesRole
        fields = ('id', 'role_id', 'role_name')
        
class PartnerTypeRoleUserSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user_id.get_full_name')  
    address_line_1 = serializers.ReadOnlyField(source='user_id.address_line_1')
    address_line_2 = serializers.ReadOnlyField(source='user_id.address_line_2')
    
    class Meta:
        model = PartnerTypeRolesUser
        fields = ('id', 'partner_types_role_id', 'user_id', 'user_name', 'is_admin', 'address_line_1', 'address_line_2')
    
class PartnerTypeRoleForUserSerializer(serializers.ModelSerializer):#used in user serializers
    partner_id = serializers.ReadOnlyField(source = 'partner_types_role_id.partner_id.id')
    partner_name = serializers.ReadOnlyField(source = 'partner_types_role_id.partner_id.name')
    partner_logo  = serializers.SerializerMethodField() #serializers.ImageField(source='partner_types_role_id.partner_id.partner_logo', allow_null=True)
    type_id = serializers.ReadOnlyField(source = 'partner_types_role_id.type_id.id')
    type_name = serializers.ReadOnlyField(source = 'partner_types_role_id.type_id.name')
    role_id = serializers.ReadOnlyField(source = 'partner_types_role_id.role_id.id')
    role_name = serializers.ReadOnlyField(source = 'partner_types_role_id.role_id.name')
    
    
    class Meta:
        model = PartnerTypeRolesUser
        fields = ('id', 'partner_types_role_id', 'partner_id', 'partner_name', 'partner_logo', 'type_id', 'type_name', 'role_id', 'role_name', 'is_admin')
    
   
    def get_partner_logo(self, obj):
        request = self.context.get('request', None)
        if obj.partner_types_role_id.partner_id.partner_logo:
            if request:
                return request.build_absolute_uri(obj.partner_types_role_id.partner_id.partner_logo.url)
        return None
    
class PartnerTypeRoleUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerTypeRolesUser
        fields = ('id', 'is_admin')
        
class PartnerTypeRoleUserSerializerForPartners(serializers.ModelSerializer):
   partner_type_admin = serializers.ReadOnlyField(source='is_admin')
   type_id = serializers.ReadOnlyField(source='partner_types_role_id.type_id.id')
   type_name = serializers.ReadOnlyField(source='partner_types_role_id.type_id.name')
   role_id = serializers.ReadOnlyField(source='partner_types_role_id.role_id.id')
   role_name = serializers.ReadOnlyField(source='partner_types_role_id.role_id.name')
   
   def get_profile_photo(self, obj):
       profile_photo = obj.user_id.profile_photo
       if profile_photo:
           request = self.context.get('request')
           if request:
               return request.build_absolute_uri(profile_photo.url)
       return None
   
   class Meta:
       model = PartnerTypeRolesUser
       fields = ('id', 'partner_types_role_id', 'partner_type_admin', 'type_id', 'type_name', 'role_id', 'role_name')
        
        
class PartnerCustomerListbyPartnerSerializer(serializers.ModelSerializer):
    salutation_name = serializers.ReadOnlyField(source='salutation_id.name')
    partner_type_roles = PartnerTypeRoleUserSerializerForPartners(source='partnertyperolesuser_set', read_only=True, many=True)
    country_name =  serializers.ReadOnlyField(source='country_id.name')
    class Meta:
        model = User
        fields = ('id', 'salutation_id', 'salutation_name', 'firstname', 'lastname', 'profile_photo', 'confirmed', 'is_customer', 'is_admin', 'address_line_1', 'address_line_2', 'city', 'country_id', 'country_name', 'zip_code', 'created_at', 'last_login', 'email', 'partner_type_roles')