from rest_framework import serializers
from .models import *
from django_otp.plugins.otp_totp.models import TOTPDevice
from partners.serializers import *
from projectmanagement.models import ProjectPhaseTask
# from PIL import Image

#-------------- UPDATE USER SERIALIZER  FOR UPDATE SPECIFIC FIELDS USER VIEW----------------------------- 
#IF 2FA CONFIRMED
class ConfirmedStatusField(serializers.Field):
   def get_attribute(self, instance):
       return instance  

   def to_representation(self, value):
       try:
           user = value  
           totp_devices = TOTPDevice.objects.filter(user=user)
           return any(totp_device.confirmed for totp_device in totp_devices)
       except TOTPDevice.DoesNotExist:
           return False   
class UserUpdateSerializer(serializers.ModelSerializer):
    salutation_name = serializers.ReadOnlyField(source = 'salutation_id.name')
    title_name = serializers.ReadOnlyField(source = 'title_id.name')
    class Meta:
        model = User
        fields = ['id','salutation_id', 'salutation_name', 'title_id', 'title_name', 'address_line_1', 'address_line_2', 'telephone', 'mobile', 'city', 'country_id', 'zip_code', 'firstname', 'lastname', 'username', 'profile_photo' ]

#------------------------- USER SERIALIZER FOR USER VIEWS ---------------------------------- 

           
class UserSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True)
    confirmpassword = serializers.CharField(write_only=True)
    salutation_name = serializers.ReadOnlyField(source = 'salutation_id.name')
    title_name = serializers.ReadOnlyField(source = 'title_id.name')
    profile_photo = serializers.ImageField(required=False)
    confirmed = ConfirmedStatusField(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'salutation_id','salutation_name', 'title_id','title_name', 'firstname', 'lastname', 'address_line_1', 'address_line_2', 'username', 'email', 'password', 'confirmpassword', 'address_line_1', 'address_line_2', 'telephone', 'mobile', 'is_admin', 'is_customer', 'profile_photo', 'created_at', 'last_login', 'confirmed']
        extra_kwargs = {
            'password':{'required': True}
        }
       
    def validate(self, data):
        if data['password'] != data['confirmpassword']:
            raise serializers.ValidationError({'error':"The passwords do not match."}, code='password_mismatch')
        return data
    
    def create(self, validated_data):
        validated_data ['is_customer'] = False
        validated_data['is_staff'] = True
        validated_data ['is_admin'] = True
        validated_data.pop('confirmpassword', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    

#--------------------------------Customer serializer for customersView ------------------------------------------------
class CustomerSerializer(serializers.ModelSerializer):
    partner_type_roles = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)
    confirmpassword = serializers.CharField(write_only=True)
    salutation_name = serializers.ReadOnlyField(source='salutation_id.name')
    title_name = serializers.ReadOnlyField(source='title_id.name')
    profile_photo = serializers.ImageField(required=False)
    roles_list = serializers.SerializerMethodField()
    # partner_ids = serializers.SerializerMethodField()
    partner_name = serializers.ReadOnlyField(source='partner_id.name')
    partner_types = serializers.SerializerMethodField()
    confirmed = ConfirmedStatusField(required=False)
    country_name = serializers.ReadOnlyField(source='country_id.name')
    project_assigned = serializers.SerializerMethodField()

    def get_project_assigned(self, user):
        assigned_tasks_exist = ProjectPhaseTask.objects.filter(assigned_to_user=user).exists()
        return assigned_tasks_exist
    
    def get_partner_type_roles(self, instance):
       partner_type_roles = instance.partnertyperolesuser_set.all()
       request = self.context.get('request')
       return PartnerTypeRoleForUserSerializer(partner_type_roles, many=True, context={'request': request}).data
   
    
    # def get_partner_ids(self, user):
    #     partners = user.partner_id.all()
    #     return [
    #         {
    #             'id': partner.id,
    #             'name': partner.name
    #         }
    #         for partner in partners
    #     ]
    
    def get_partner_types(self, user):
        partner_types = user.partner_type.all()
        return [
            {'id':partner_type.id, 'name':partner_type.name} for partner_type in partner_types
        ]

    def get_roles_list(self, partner):
        roles = partner.role_id.all()
        return [
            {
                'id': role.id,
                'name': role.name
            }
            for role in roles
        ]

    class Meta:
        model = User
        fields = ['id', 'salutation_id', 'salutation_name', 'title_id', 'title_name', 'firstname', 'lastname', 'partner_id', 'partner_name', 'address_line_1', 'address_line_2', 'city', 'country_id', 'country_name', 'zip_code', 'partner_types', 'username', 'email', 'password', 'confirmpassword', 'profile_photo', 'address_line_1', 'address_line_2', 'telephone', 'mobile', 'partner_admin', 'confirmed', 'is_customer', 'is_admin', 'created_at', 'last_login', 'roles_list', 'partner_type_roles', 'project_assigned']
        extra_kwargs = {
            'firstname': {'required': True},
            'lastname': {'required': True},
            'password':{'required':True},
        }

    def validate(self, data):
        if data['password'] != data['confirmpassword']:
            raise serializers.ValidationError("The passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data['is_customer'] = True
        validated_data['is_admin'] = False
        validated_data.pop('confirmpassword', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserActiveRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'active_role')

#-------------------------------------- Forgot Password Serializers ---------------------------------------------------------------
class ForgotPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
class CodeConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserForgotPassword
        fields = ['email', 'code', 'expired_at']
        
class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
class UserLoginLogsSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user_id.get_full_name')
    class Meta:
        model = UserLoginLogs
        fields = ('id', 'user_id', 'user_name', 'browser', 'operating_system', 'device', 'ip_address', 'last_login')
        
#--------------------------------------------------- Title List --------------------------------------------------------------------
class TitleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Title
        fields = ('id', 'name')
        
class CustomerCreateByFieldSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id', 'firstname', 'lastname', 'email', 'password', 'partner_id', 'is_customer')
        
