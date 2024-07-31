from dotenv import load_dotenv
from solar_project.settings import URL_SCHEME
import os, json, string, random, base64, qrcode, requests
from django.contrib.auth import authenticate
from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from .models import *
from .serializers import *
from usermanagement.exceptions import PermissionDenied
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from io import BytesIO
from solar_project.permission_middleware import *
from partners.pagination import CustomPagination
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .functions import *
from partners.models import *
from projectmanagement.models import *
from usermanagement.functions import get_ip_address
from django.core.cache import cache


# views.py


#-------------------------------------- GET AND POST USER VIEWS --------------------------------------------------
class UserList(generics.ListAPIView):
    queryset = User.objects.filter(is_admin=True, controller_user=False)
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs): 
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many = True)
        response_data = {'userDetails':serializer.data}
        return Response(response_data)

#--------------------------------------------- CREATE USER VIEW -------------------------------------------------    
class CreateUser(generics.CreateAPIView):
    serializer_class = UserSerializer
    # permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        # if not request.user.is_admin:
        #     return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            email = serializer.validated_data['email']
            if User.objects.filter(email=email).exists():
                return serializers.ValidationError({'status_code':600, 'error':"Email already exists please try new"})
            
            password = serializer.validated_data['password']
            confirm_password = serializer.validated_data['confirmpassword']
            if password != confirm_password:
                raise serializers.ValidationError({'status_code': 601, 'error':'passwords do not match!'})
                    
            self.perform_create(serializer)
            response_data = {"userDetails": serializer.data}
            return Response(response_data)
        except Exception:
            return Response({'status_code':600, 'error':'Email already exists please try new'}, status=500)

   
#------------------- GET, UPDATE AND DELETE USER VIEWS ------------------------
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
   queryset = User.objects.all().filter(is_admin=True)
   serializer_class = UserSerializer
   permission_classes = (IsAuthenticated,)

   def retrieve(self, request, *args, **kwargs):
       
       try:
           instance = self.get_object()

           if instance != request.user and not request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           serializer = self.get_serializer(instance)

           response_data = {"userDetails": serializer.data}
           return Response(response_data)
       except ValidationError as e:
           return Response({'error': e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

   def get_serializer_class(self):
       if self.request.method == 'PUT' or self.request.method == 'PATCH':
           return UserUpdateSerializer
       return self.serializer_class

   def update(self, request, *args, **kwargs):
       try:
           user = self.get_object()

           if user != request.user and not request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           
           max_size = 5 * 1024 * 1024
           profile_photo = request.data.get('profile_photo')
           
           if profile_photo and profile_photo.size > max_size:
                return Response({'status_code':604, 'error': 'File size should be less than 5MB.'},status=status.HTTP_400_BAD_REQUEST)

           serializer = self.get_serializer(user, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()

           if instance != request.user and not request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           self.perform_destroy(instance)
           return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    
   
   

#USERVIEW ENDS HERE      
#-----------------------------------CUSTOMER VIEWS----------------------------------------------------------------
class CustomerList(generics.ListCreateAPIView):
    queryset = User.objects.filter(is_customer=True, is_active=True, controller_user=False).order_by('id')
    serializer_class = CustomerSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    
    def list(self, request, *args, **kwargs):
        return Response({'details': 'Please use the POST method to filter customer.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user)
        partner_ids = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
        # type_ids = partner_admin_user.values_list('partner_types_role_id__type_id', flat=True)

        if user.is_admin or partner_admin_user:
            if user.is_customer and partner_admin_user:
                customer_partners = User.objects.filter(partnertyperolesuser__partner_types_role_id__partner_id__in=partner_ids)
                return customer_partners.distinct()
                # queryset = queryset.filter(partner_ids = customer_partner)#(partner_id__in=partner_id)
            search_keyword = self.request.data.get('search_keyword')
            partner_admin = self.request.data.get('partner_admin')
            partner_id = self.request.data.get('partner_id')
            
            
            filter_params = Q()
            if partner_admin:
               filter_params &= Q(partner_admin=partner_admin)
            
            if partner_id is not None:
                if partner_id == '':
                    filter_params |= Q(partner_id__isnull=True)
                else:
                    filter_params &= Q(partner_id=partner_id)
            
            queryset = queryset.filter(filter_params)

            if search_keyword:
                queryset = queryset.filter(Q(firstname__icontains=search_keyword) | Q(lastname__icontains=search_keyword) | Q(email__icontains=search_keyword))

        else:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                print(serializer)
                for data in serializer.data:
                    user = User.objects.get(id=data['id'])
                    totp_devices = devices_for_user(user, confirmed=True)
                    totp_device = next((device for device in totp_devices if isinstance(device, TOTPDevice)), None)
                    data['confirmed'] = bool(totp_device)
                response_data = {
                    "customerDetails":serializer.data,
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

            return Response({"customerDetails": []})  # If no results found

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 
#----------------------------------------CREATE CUSTOMER VIEW---------------------------------------------------------  
class CreateCustomer(generics.CreateAPIView):
   serializer_class = CustomerSerializer
   permission_classes = (IsAuthenticated,)

   def create(self, request, *args, **kwargs):
       user = request.user
       partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, is_admin=True)
       if not user.is_admin and not partner_admin_user:  
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       
    #    partner_id = request.data.get('partner_id')
       partner_types_role_id = request.data.get('partner_types_role_id')
       partner_type_role_admin = request.data.get('partner_type_admin', bool)
       partner_type_role = PartnerTypesRole.objects.get(pk=partner_types_role_id)
    #    partner_admin_types = PartnerTypeRolesUser.objects.get(is_admin = partner_is_admin)
       

       try:
           serializer = self.get_serializer(data=request.data)
           serializer.is_valid(raise_exception=True)
           email = serializer.validated_data['email']
           if User.objects.filter(email=email).exists():
               return Response({'status_code': 600, 'error': "Email already exists, please try with another email"})

           password = serializer.validated_data['password']
           confirm_password = serializer.validated_data['confirmpassword']
           if password != confirm_password:
               return Response({'status_code': 601, 'error': 'Passwords do not match, please try again'})
           
           self.perform_create(serializer)
           user_id = serializer.instance
           partner_type_roles_users = PartnerTypeRolesUser.objects.create(
               partner_types_role_id = partner_type_role,
               user_id = user_id,
               is_admin = partner_type_role_admin
           )
           response_data = {"customerDetails": serializer.data}
           return Response(response_data)
       except ValidationError as e:
           return Response({'error': e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
#------------------- GET, UPDATE AND DELETE VIEWS ------------------------
class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
   queryset = User.objects.filter(is_customer=True)
   serializer_class = CustomerSerializer
   permission_classes = (IsAuthenticated,)

   def retrieve(self, request, *args, **kwargs):
       
       try:
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user)

           # Check if the requested user is the logged-in user
           if instance != request.user and not request.user.is_admin and not partner_admin_user:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           serializer = self.get_serializer(instance)

           response_data = {"customerDetails": serializer.data}
           return Response(response_data)
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

   def get_serializer_class(self):
       if self.request.method in ['PUT', 'PATCH']:
           return UserUpdateSerializer
       return self.serializer_class

   def update(self, request, *args, **kwargs):
       try:
           user = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
           if user != request.user and not request.user.is_admin and not partner_admin_user:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           serializer = self.get_serializer(user, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           self.perform_update(serializer)
           return Response(serializer.data)
       except ValidationError as e:
           return Response({'error':e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       except Exception as e:
           return Response({'error': str(e)}, status.HTTP_422_UNPROCESSABLE_ENTITY)

   def destroy(self, request, *args, **kwargs):
       try:
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=request.user, is_admin=True)
           instance = self.get_object()
           if instance != request.user and not request.user.is_admin and not partner_admin_user:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           self.perform_destroy(instance)
           instance.is_active = False
           instance.save()
           return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
       except Exception as e:
           return Response({'error': str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)


#----------------------------------------------------- TOKEN BASED USER LOGIN VIEW -----------------------------------------------------


class UserLogin(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_class    = []
    required_scopes = []    
    
    def get_partner_type_roles(self, user):
        partner_type_roles = PartnerTypeRolesUser.objects.filter(user_id=user)
        return PartnerTypeRoleForUserSerializer(partner_type_roles, many=True).data
        
    def post(self, request):
        # try:
            username = request.data.get('email', '').lower()
            password = request.data.get('password')
            client_id = request.data.get('client_id')
            client_secret = request.data.get('client_secret')
            
            
            user = authenticate(request, email=username, password=password)
            if user is None or user.controller_user:
                return Response({'status_code':606, 'error':'Invalid Credentials'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            devices = devices_for_user(user, confirmed=True)
            totp_devices = [device for device in devices if isinstance(device, TOTPDevice)]
            if totp_devices:
                return Response({'status':'2FA enabled', 'user_id':user.id, 'confirmed':True})
            
            
            AccessToken.objects.filter(user=user.id).delete()
            RefreshToken.objects.filter(user=user.id).delete()
            
            user.last_login = timezone.now()
            user.save()
            
            # url = 'http://'+request.get_host()+ '/o/token/'
            url = f'{URL_SCHEME}://{request.get_host()}/o/token/'
            data_dict = {"grant_type":"password", "username":username, "password":password, "client_id":client_id, "client_secret":client_secret }
            # aa = requests.post(url, data=data_dict)
            # data = json.loads(aa.text)
            response = requests.post(url, data=data_dict)
            response_data = json.loads(response.text)
            access_token = response_data.get('access_token', '')
            refresh_token = response_data.get('refresh_token', '')
            
            if not request.user_agent.browser.family == "Python Requests" and not request.user_agent.browser.family == "PostmanRuntime":            
                user_login_logs = UserLoginLogs.objects.create(
                    user_id = user,
                    browser = f'{request.user_agent.browser.family} {request.user_agent.browser.version_string}',
                    operating_system = f'{request.user_agent.os.family} {request.user_agent.os.version_string}',
                    device = request.user_agent.device.family,
                    last_login = timezone.now(),
                    ip_address = get_ip_address(request)
                )
            partner_type_roles = self.get_partner_type_roles(user)
            assigned_projects = TaskAssignedUsers.objects.filter(user_id=user)
            
            response_data = {
                'tokens':{
                'refresh_token':refresh_token,
                'access_token':access_token,
                'access_token_type':'Bearer',
                },
                'userDetails': {
                    'id':user.id,
                    'salutation_id': user.salutation_id.id if user.salutation_id else None,
                    'salutation_name': user.salutation_id.name if user.salutation_id else None,
                    'title_id': user.title_id.id if user.title_id else None,
                    'title_name':user.title_id.name if user.title_id else None,
                    'email': user.email,
                    'username': user.username,
                    'firstname':user.firstname,
                    'lastname': user.lastname,
                    'is_admin': user.is_admin,
                    'is_customer': user.is_customer,
                    'partner_admin':user.partner_admin,
                    'last_login':user.last_login,
                    'partner_id':user.partner_id if user.partner_id else None,#[{'partner_id':partner.id, 'partner_name':partner.name} for partner in user.partner_id.all()] if user.partner_id.exists() else None,
                    'profile_photo': request.build_absolute_uri(user.profile_photo.url) if user.profile_photo else None,
                    'partner_type_roles':partner_type_roles,
                    'confirmed':user.confirmed,
                    'project_assigned':True if assigned_projects else False,
                                    
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        # except ValidationError as e:
        #     return Response({'error':e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
class ControllerUserLogin(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_class    = []
    required_scopes = []    
        
    def post(self, request):
        try:
            username = request.data.get('email', '').lower()
            password = request.data.get('password')
            client_id = request.data.get('client_id')
            client_secret = request.data.get('client_secret')
            
            
            user = authenticate(request, email=username, password=password)
            if user is None or not user.controller_user:
                return Response({'status_code':606, 'error':'Invalid Credentials'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            devices = devices_for_user(user, confirmed=True)
            totp_devices = [device for device in devices if isinstance(device, TOTPDevice)]
            if totp_devices:
                return Response({'status':'2FA enabled', 'user_id':user.id, 'confirmed':True})
            
            
            AccessToken.objects.filter(user=user.id).delete()
            RefreshToken.objects.filter(user=user.id).delete()
            
            user.last_login = timezone.now()
            user.save()
            
            url = f'{URL_SCHEME}://{request.get_host()}/o/token/'
            print(url)
            data_dict = {"grant_type":"password", "username":username, "password":password, "client_id":client_id, "client_secret":client_secret }
            
            response = requests.post(url, data=data_dict)
            response_data = json.loads(response.text)
            access_token = response_data.get('access_token', '')
            refresh_token = response_data.get('refresh_token', '')
            
            if not request.user_agent.browser.family == "Python Requests": #and not request.user_agent.browser.family == "PostmanRuntime":            
                user_login_logs = UserLoginLogs.objects.create(
                    user_id = user,
                    browser = f'{request.user_agent.browser.family} {request.user_agent.browser.version_string}',
                    operating_system = f'{request.user_agent.os.family} {request.user_agent.os.version_string}',
                    device = request.user_agent.device.family,
                    last_login = timezone.now(),
                    ip_address = get_ip_address(request)
                )
            
            response_data = {
                'tokens':{
                'refresh_token':refresh_token,
                'access_token':access_token,
                'access_token_type':'Bearer',
                },
                'userDetails': {
                    'id':user.id,
                    'salutation_id': user.salutation_id.id if user.salutation_id else None,
                    'salutation_name': user.salutation_id.name if user.salutation_id else None,
                    'title_id': user.title_id.id if user.title_id else None,
                    'title_name':user.title_id.name if user.title_id else None,
                    'email': user.email,
                    'username': user.username,
                    'firstname':user.firstname,
                    'lastname': user.lastname,
                    'is_customer': user.is_customer,
                    'last_login':user.last_login,
                    'controller_user':user.controller_user
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'error':e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
   
#------------------------------------- CHANGE EMAIL OF USER VIEW ------------------------------------------
class ChangeEmail(generics.UpdateAPIView):
    queryset  = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    
    
    def update(self, request, *args, **kwargs):
        email = request.data.get('email')
        user = self.get_object()
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
        if user != request.user and not user.is_admin and not partner_admin_user:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        if email:
            try:
                if User.objects.filter(email=email).exists():
                    return Response({'status_code': 600, 'error':'Email already existed please try with another email.'})
                user.email = email
                user.save() 
                AccessToken.objects.filter(user=user).delete()    
                            
                return Response ({'message': 'Your email has been updated successfully' }, status = status.HTTP_200_OK)
            except serializers.ValidationError as error:
                return Response({'error': error.detail}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response ({'error': 'Email is required'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    

#-------------------------------------------- CHANGE PASSWORD VIEW ----------------------------------------------  

  
class ChangePassword(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,) 
    
    def update(self, request, *args, **kwargs):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        
        if current_password and new_password and confirm_password:
            if new_password != confirm_password:
                return Response({'status_code': 601, 'error':'Password does not match please try agian'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            user = self.get_object()
            partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
            if user != request.user and not partner_admin_user:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
            #Checking if current and new passwords are matched 
            if new_password and confirm_password == current_password:
                return Response({'status_code': 602, 'error':'Current password and New password cannot be same'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save() 
                AccessToken.objects.filter(user=user).delete()         
                    
                
                return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'status_code': 608,'error':'Invalid password please try again!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status_code': 608, 'error': 'Current password, new password and confirm password are required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AdminPasswordChange(generics.UpdateAPIView): #Change user password without current password
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,) 
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        request_user = request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True)
        if not request_user.is_admin and not partner_admin_user:
            raise PermissionDenied()
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                return Response({'status_code': 601, 'error':'Password does not match please try agian'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if not request_user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

            user.set_password(new_password)
            user.save() 
            AccessToken.objects.filter(user=user).delete()         
            return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
            
        else:
            return Response({'error': 'new password and confirm password are required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#---------------------------------------- LOGOUT VIEW ---------------------------------------------------
class Logout(APIView):
    permission_classes = (IsAuthenticated,)
    

    def post(self, request):
        access_token =AccessToken.objects.get(user=request.user)
        access_token.delete()
        return Response({'message':'Logged out successfully!'})
    

#-------------------------------------------------------- TOKEN VIEW REFRESH AND CLIENT TOKENS---------------------------------------------------

class TokenViewClient(APIView):
    
    def get(self, request, *args, **kwargs):
        load_dotenv()
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(64))
        
        if Application.objects.filter(name="solar_project").exists():
            token_object = Application.objects.filter(name="solar_project")
            result_str = os.getenv('APP_CLIENT_SECRET')
        else:
            Application.objects.create(
                name = 'solar_project',
                client_type = 'confidential',
                authorization_grant_type = 'password',
                client_secret = result_str
            )
            token_object = Application.objects.filter(name = "solar_project")
            
            #Storing results_str in .env file
            with open('.env', 'a') as file:
                file.write(f'APP_CLIENT_SECRET={result_str}\n')
            
            
        client_id = token_object[0].client_id        
        
        response_data = {
            'client_id':client_id,
            'client_secret':result_str,
            }
        return Response({'clientDetails':response_data})
    

class ClientRefreshToken(APIView):

   def post(self, request, *args, **kwargs):
       client_id = request.data.get('client_id')
       client_secret = request.data.get('client_secret')
       refresh_token = request.data.get('refresh_token')


       url = f'{URL_SCHEME}://{request.get_host()}/o/token/'

       data_dict = {"grant_type": "refresh_token", "client_id": client_id, "client_secret": client_secret, "refresh_token": refresh_token}

       try:
           response = requests.post(url, data=data_dict)
           response_data = json.loads(response.text)

           access_token = response_data.get('access_token', '')
           refresh_token = response_data.get('refresh_token', '')

           response_data = {
               'tokens': {
                   'refresh_token': refresh_token,
                   'access_token': access_token,
                   'access_token_type': 'Bearer',
               }
           }
           return Response(response_data)

       except requests.exceptions.RequestException as e:
           error_message = f"Error making the token request: {str(e)}"
           return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       except json.JSONDecodeError as e:
           error_message = f"Error decoding JSON response: {str(e)}"
           return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

#------------------------------------------ TWO FACTOR AUTHENTICATION VIEWS ENABLE, DISABLE, VERIFY AND LOGIN AFTER VERIFY -------------------------------------------------

class Enable2FA(APIView):
   permission_classes = (IsAuthenticated,)

#    @check_userlogin
   def post(self, request):
       try:
           user = request.user

           # Check if the logged-in user is trying to enable 2FA for their own account
           if request.user != user:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           totp_devices = devices_for_user(user, confirmed=True)
           totp_device = next((device for device in totp_devices if isinstance(device, TOTPDevice)), None)

           if totp_device:
               return Response({'message': '2FA is already enabled for this user'})

           device = TOTPDevice.objects.create(user=user, name='My Authentication')
           qr_code = qrcode.QRCode()
           qr_code.add_data(device.config_url)
           qr_code.make(fit=True)
           qr_code_image = qr_code.make_image()
           qr_code_buffer = BytesIO()
           qr_code_image.save(qr_code_buffer, format='PNG')
           qr_code_buffer.seek(0)
           qr_code_data = qr_code_buffer.getvalue()
           qr_code_data_uri = 'data:image/png;base64,' + base64.b64encode(qr_code_data).decode('utf-8')
           return Response({'qrCode': qr_code_data_uri})
       except User.DoesNotExist:
           return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
       except PermissionDenied as e:
           return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#VERIFY 2FA
class Verify2FA(APIView):

    def post(self, request, id):
        otp = request.data.get('otp')
        recovery_code = request.data.get('recovery_code')
        user = User.objects.get(id=id)
        totp_devices = devices_for_user(user, confirmed=True)
        totp_device = next((device for device in totp_devices if isinstance(device, TOTPDevice)), None)

        if not otp and not recovery_code:
            return Response({'status_code': 603,'error':'OTP or Recovery code is required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not totp_device:
            return Response({'error':'2FA is not enabled for this user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        is_verified = totp_device.verify_token(otp)
        if is_verified:
            return Response({'message':'OTP Verified successfully'})

        if recovery_code:
            recovery_codes = RecoveryCode.objects.filter(user=user).first()
            if recovery_codes and recovery_code in recovery_codes.codes:
                recovery_codes.codes.remove(recovery_code)
                recovery_codes.save()
                return Response({'message':'Recovery code verified successfully'}, status = status.HTTP_200_OK)
        return Response({'status_code':607, 'error':'Invalid OTP or recovery code'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        
#LOGIN AFTER VERIFY VIEW
class LoginAfterVerify(APIView):
    def post(self, request):
        username = request.data.get('email')
        password = request.data.get('password')
        client_id = request.data.get('client_id')
        client_secret = request.data.get('client_secret')
        
        user = authenticate(request, email=username, password=password)
        
        if user is None:
            return Response({'status_code':606, 'error':'Invalid Credentials'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    
        totp_devices = devices_for_user(user, confirmed=True)
        totp_device = next((device for device in totp_devices if isinstance(device, TOTPDevice)), None)
        if not totp_device:
            return Response({'error':'2FA is not enabled for this user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        AccessToken.objects.filter(user=user.id).delete()
        RefreshToken.objects.filter(user=user.id).delete()    
        
        user.last_login = timezone.now()
        user.save()   
        url = f'{URL_SCHEME}://{request.get_host()}/o/token/'
        
        data_dict = {"grant_type":"password", "username":username, "password":password, "client_id":client_id, "client_secret":client_secret }
        aa = requests.post(url, data=data_dict)
        data = json.loads(aa.text)
        access_token = data.get('access_token', '')
        refresh_token = data.get('refresh_token', '')
        
        response_data = {
            'tokens':{
            'refresh_token':refresh_token,
            'access_token':access_token,
            'access_token_type':'Bearer',
            },
            'userDetails': {
                'id':user.id,
                'salutation_id': user.salutation_id.id if user.salutation_id else None,
                'salutation_name': user.salutation_id.name if user.salutation_id else None,
                'title_id': user.title_id.id if user.title_id else None,
                'title_name':user.title_id.name if user.title_id else None,
                'email': user.email,
                'username': user.username,
                'firstname':user.firstname,
                'lastname': user.lastname,
                'is_admin': user.is_admin,
                'is_customer': user.is_customer,
                'partner_admin':user.partner_admin,
                'profile_photo': request.build_absolute_uri(user.profile_photo.url) if user.profile_photo else None,
                'partner_id':user.partner_id if user.partner_id else None,#[{'partner_id':partner.id, 'partner_name':partner.name} for partner in user.partner_id.all()] if user.partner_id.exists() else None,
                'roles_list':[{'id':role.id, 'name':role.name} for role in user.role_id.all()] if user.role_id.exists() else None,
                'confirmed':True,
            
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

#DISABLE 2FA VIEW

class Disable2FA(APIView):
   permission_classes = (IsAuthenticated,)

   def post(self, request):

       try:
           user = request.user
           
           if request.user != user and not request.user.is_admin:
                return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except User.DoesNotExist:
           return Response({'message': 'User doesnot exists'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       totp_devices = devices_for_user(user, confirmed=True)
       for device in totp_devices:
           device.confirmed = False
           device.save()

       return Response({'message': '2FA disabled successfully!'})

    
#------------------------------------- RECOVERY CODE LOGIN VIEWS --------------------------------------------------------------------------
class GenerateRecoveryCodes(APIView):
   permission_classes = (IsAuthenticated,)

   def post(self, request, id):
       try:
           user = User.objects.get(id=id)

           if request.user != user and not request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           totp_devices = devices_for_user(user, confirmed=True)
           totp_device = next((device for device in totp_devices if isinstance(device, TOTPDevice)), None)

           if not totp_device:
               return Response({'error': '2FA is not enabled'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

           recovery_codes, created = RecoveryCode.objects.get_or_create(user=user)
           codes = recovery_codes.codes

           if not codes or len(codes) < 10:
               existing_codes = recovery_codes.codes.copy()

               # Remove expired codes
               existing_codes = [code for code in existing_codes if not code.startswith("USED")]

               num_existing_codes = len(existing_codes)
               num_new_codes = 10 - num_existing_codes

               new_codes = generate_unique_recovery_codes(user, existing_codes, count=num_new_codes)
               recovery_codes.codes.extend(new_codes)
               recovery_codes.save()

               codes = recovery_codes.codes

           return Response({'recovery_codes': codes})
       except User.DoesNotExist:
           return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#------------------------------------------- FORGET PASSWORD VIEWS ------------------------------------------------------------------
class ForgotPasswordEmailConfirmationAPIView(generics.CreateAPIView):
    serializer_class = ForgotPasswordEmailSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Email does not exist, please register.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error':str(e)})

        # Generating and saving a 14-digit code
        code = get_random_string(14, '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz')
        UserForgotPassword.objects.create(user_id=user, code=code, expired_at=timezone.now() + timezone.timedelta(minutes=10))
        load_dotenv()
        reset_url = os.getenv('RESET_URL')
        sender_email = os.getenv('EMAIL_HOST_USER')
        html_message = render_to_string('password_confirmation_mail.html', {'code': code, 'user_name':user.get_full_name(), 'url':reset_url})

        # Send email with the code and HTML template
        send_mail(
            'Password Reset Code',
            strip_tags(html_message), 
            sender_email,
            [email],
            html_message=html_message,
            fail_silently=False,
        )

        return Response({'message': 'Email sent successfully.'}, status=status.HTTP_200_OK)


class CodeConfirmationAPIView(generics.ListCreateAPIView):
    serializer_class = CodeConfirmationSerializer
    queryset = UserForgotPassword.objects.all()

    def create(self, request, *args, **kwargs):
        code = request.data.get('code')

        try:
            instance = UserForgotPassword.objects.get(code=code)
        except UserForgotPassword.DoesNotExist:
            return Response({'error': 'Code does not exist.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        if instance.is_expired or instance.expired_at < timezone.now():
            return Response({'error': 'Code has been expired or invalid.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_email = instance.user_id.email

        instance.is_expired = True
        instance.save()

        return Response({'message': 'Code confirmed successfully.', 'email':user_email}, status=status.HTTP_200_OK)
    
class ChangePasswordAPIView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        try:
            user = User.objects.get(email=email)
        except Exception as e:
            return Response({'error':str(e)}, status =500)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)

class UserLoginLogsbyUserId(generics.ListAPIView):
    serializer_class = UserLoginLogsSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return UserLoginLogs.objects.filter(user_id=user_id).order_by('-id')
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = {
                    "userLoginLogs": serializer.data,
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
            serializer = self.get_serializer(queryset, many=True)
            return Response({"userLoginLogs": serializer.data})
        except ValidationError as error:
            return Response({'error': error.detail}, status=500)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        
#--------------------------------------------------------------------- Title Views ---------------------------------------------------
class UserTitlesGetList(generics.ListAPIView):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        return Response({'titleDetails':response_data})
    
class UpdateActiveRoleUser(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserActiveRoleSerializer
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({'updatedActiveRole':serializer.data})
        except Exception as e:
            return Response({'error':str(e)})
        
        
#-------------------------------------------------------- CREATE CUSTOMER WITHOUT A PASSWORD ----------------------------------------------------
class CreateCustomerByField(generics.CreateAPIView):
    serializer_class = CustomerCreateByFieldSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        user = request.user
        partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True).exists()

        if not user.is_admin and not partner_admin_user:
            return Response({'status_code': 605, 'error': 'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
    
        try:
            password = request.data.get('password')
            if not password:
                password = generate_random_password()

            request.data['password'] = password 
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']
            
            if User.objects.filter(email=email).exists():
                raise ValidationError({'status_code': 600, 'error': 'Email already exists, please try with another email'})

            self.perform_create(serializer)
            return Response({'customerDetails':'Customer created successfully!'}, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CustomerListByPartnerID(generics.ListAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = CustomerSerializer
    
    def list(self, request, *args, **kwargs):
        partner_id = self.kwargs.get('partner_id')
        queryset = self.queryset.filter(partner_id=partner_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'customerByPartner':serializer.data})
    