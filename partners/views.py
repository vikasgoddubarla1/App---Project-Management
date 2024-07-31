from rest_framework import generics, status
from .serializers import *
from partners.models import Countries, Partner
from usermanagement.models import User
from usermanagement.serializers import CustomerSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from usermanagement.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.db.models import Q
from .pagination import CustomPagination
from rest_framework.exceptions import ValidationError
from locations.models import *
# Create your views here.

#------------------------------------- COUNTRIES DETAILS VIEW ---------------------------------------------------
class CountryList(generics.ListAPIView):
    queryset = Countries.objects.all().order_by('id')
    serializer_class = CountrySerializer
    
    def list(self, request, *args, **kwargs): 
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many = True)
        data = {"countries": serializer.data}
        return Response(data)

#----------------------------------------- PARTNERS GET AND CREATE VIEW -------------------------------------------------
class PartnerList(generics.ListCreateAPIView):
   queryset = Partner.objects.all().order_by('name')
   serializer_class = PartnerRetrieveSerializer
   permission_classes = (IsAuthenticated,)
   pagination_class = CustomPagination
   
   def list(self, request, *args, **kwargs):
        return Response({'details': 'Please use the POST method to filter partners.'}, status=status.HTTP_400_BAD_REQUEST)
    
   def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

   def get_queryset(self):
       queryset = super().get_queryset()
       user = self.request.user
       partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user)
       partner_id = partner_admin_user.values_list('partner_types_role_id__partner_id', flat=True)
              
       if user.is_admin or (partner_admin_user and partner_id):
           if partner_admin_user and partner_id:
                partner_id =partner_id
                queryset = queryset.filter(id__in=partner_id)
           country_id = self.request.data.get('country_id')
           city = self.request.data.get('city')
           zipcode = self.request.data.get('zip_code')
           search_keyword = self.request.data.get('search_keyword')
           type_id = self.request.data.get('type_id')


           filter_params = Q()
           if country_id:
               filter_params &= Q(country_id=country_id)
           if city:
               filter_params &= Q(city__icontains=city)
           if zipcode:
               filter_params &= Q(zip_code=zipcode)
           if type_id:
                filter_params &= Q(partnertype__type_id__in=type_id)

           queryset = queryset.filter(filter_params)

           if search_keyword:
               queryset = queryset.filter(Q(name__icontains=search_keyword) | Q(email__icontains=search_keyword) | Q(address_line_1__icontains=search_keyword) | Q(address_line_2__icontains=search_keyword))

           
       elif user.is_customer and not user.partner_id:
           raise PermissionDenied({'status_code':626, 'detail':'You are not associated with any partner.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       else:
           return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

       return queryset

   def create(self, request, *args, **kwargs):
        try:
            
            queryset = self.get_queryset()
            # if not queryset.exists():
            #     return Response({'detail':'No matching details found for this query, please try again'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response_data = {
                    "partnerDetails":serializer.data,
                    "paginationDetails": {
                        "current_page": self.paginator.page.number,
                        "number_of_pages": self.paginator.page.paginator.num_pages,
                        "current_page_items": len(serializer.data),
                        "total_items"    : self.paginator.page.paginator.count,
                        "next_page"      : self.paginator.get_next_link(),
                        "previous_page"  : self.paginator.get_previous_link(),
                    }
                }
                return self.get_paginated_response(response_data)
            
            return Response({'"partners": []'}) 

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreatePartner(generics.CreateAPIView):  
    
    serializer_class = PartnerRetrieveSerializer 
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        email = request.data.get('email')
        if name:
            existing_name = Partner.objects.filter(name=name).exists()
            if existing_name:
                return Response({"status_code":629, "error":"name already exists"}, status=500)
        if email:
            existing_email = Partner.objects.filter(email=email).exists()
            if existing_email:
                return Response({"status_code":630, "error":"email already exists"}, status=500)
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        
            self.perform_create(serializer)
            response_data = {'partnerDetails':serializer.data}
            return Response(response_data)
        except serializers.ValidationError as error:
           return Response({'error':error.detail}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#--------------------------------------------- PARTNERS RETRIEVE AND DESTROY VIEWS -------------------------------
class PartnerDetail(generics.RetrieveDestroyAPIView):
   queryset = Partner.objects.all()
   serializer_class = PartnerRetrieveSerializer
   permission_classes = (IsAuthenticated,)

   def retrieve(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = request.user, partner_types_role_id__partner_id = instance.id)
           if not request.user.is_admin and not (partner_admin_user): #(request.user.is_customer and request.user.partner_id.id == instance.id):
                raise PermissionDenied()
           serializer = self.get_serializer(instance)
           partner_data = serializer.data
           partner_type_roles = instance.partnertypesrole_set.all().order_by('id')
           partner_data['partner_type_roles'] = PartnerTypeRoleSerializer(partner_type_roles, many=True).data
           return Response({'partnerDetails': partner_data})
           
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           if not self.request.user.is_admin:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
           customers = User.objects.filter(partner_id=instance.id, is_customer = True)
           customers.delete()
           self.perform_destroy(instance)
           return Response({'message': 'Partner deleted successfully'})
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#--------------------------------------- PARTNER GENERAL, SUPPORT, SALES AND REMARKS VIEWS----------------------------------------------    
class PartnerGeneral(generics.UpdateAPIView):
   queryset = Partner.objects.all()
   serializer_class = PartnerGeneralSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin=True, partner_types_role_id__partner_id=instance.id)
           name = request.data.get('name')
           email = request.data.get('email')
           if name:
                existing_name = Partner.objects.filter(name=name).exists()
                if existing_name:
                    return Response({"status_code":629, "error":"name already exists"}, status=500)
           if email:
                existing_email = Partner.objects.filter(email=email).exists()
                if existing_email:
                    return Response({"status_code":630, "error":"email already exists"}, status=500)
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           if user.is_admin or partner_admin_user: #or (user.partner_admin and user.partner_id.id == instance.id):
               instance = serializer.save()
               return Response(serializer.data)
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
       
class PartnerWebsiteUpdate(generics.UpdateAPIView):
   queryset = Partner.objects.all()
   serializer_class = PartnerWebsiteLinkUpdateSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin=True, partner_types_role_id__partner_id=instance.id)
           
           serializer = self.get_serializer(instance, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           if user.is_admin or partner_admin_user: #or (user.partner_admin and user.partner_id.id == instance.id):
               instance = serializer.save()
               return Response(serializer.data)
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
    
#PARTNER SUPPORT    
class PartnerSupport(generics.UpdateAPIView):
   queryset = Partner.objects.all()
   serializer_class = PartnerSupportSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id =user, is_admin=True, partner_types_role_id__partner_id=instance.id)
           if user.is_admin or partner_admin_user: #(user.partner_admin and user.partner_id.id == instance.id):
               serializer = self.get_serializer(instance, data=request.data, partial=True)
               serializer.is_valid(raise_exception=True)
               instance = serializer.save()
               return Response(serializer.data)
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

# PARTNER SALES
class PartnerSales(generics.UpdateAPIView):
   queryset = Partner.objects.all()
   serializer_class = PartnerSalesSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id = user, is_admin =True, partner_types_role_id__partner_id = instance.id)
           if user.is_admin or partner_admin_user: #(user.partner_admin and user.partner_id.id == instance.id):
               serializer = self.get_serializer(instance, data=request.data, partial=True)
               serializer.is_valid(raise_exception=True)
               instance = serializer.save()
               return Response(serializer.data)
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

# PARTNER REMARKS
class PartnerRemarks(generics.UpdateAPIView):
   queryset = Partner.objects.all()
   serializer_class = PartnerRemarksSerializer
   permission_classes = (IsAuthenticated,)

   def update(self, request, *args, **kwargs):
       try:
           user = self.request.user
           instance = self.get_object()
           partner_admin_user = PartnerTypeRolesUser.objects.filter(user_id=user, is_admin=True, partner_types_role_id__partner_id = instance.id)
           if user.is_admin or partner_admin_user: #(user.partner_admin and user.partner_id.id == instance.id):
               serializer = self.get_serializer(instance, data=request.data, partial=True)
               serializer.is_valid(raise_exception=True)
               instance = serializer.save()
               return Response(serializer.data)
           else:
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
       except ValidationError as e:
           return Response({'error':e.detail}, status.HTTP_500_INTERNAL_SERVER_ERROR) 
       except Exception as e:
           return Response({'error': str(e)}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
    
#--------------------------------- PATNER CUSTOMER ADD VIEW -------------------------------
class PartnerCustomerAdd(APIView):
   permission_classes = (IsAuthenticated,)

   def post(self, request, partner_id, *args, **kwargs):
       try:
           customer_ids = request.data.get('customer_ids', [])

           try:
               partner = Partner.objects.get(id=partner_id)
           except Partner.DoesNotExist:
               return Response({'error': 'Partner Does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

           if not request.user.is_admin and not (request.user.partner_admin == partner_id and not request.user.partner_id == partner_id):
               return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)

           existing_customers = User.objects.filter(id__in=customer_ids, is_customer=True, partner_id__isnull=False)
           conflicting_customers = existing_customers.exclude(partner_id=partner_id)

           if conflicting_customers.exists():
               conflicting_partner = conflicting_customers.first().partner_id
               return Response({'status_code':627, 'error': 'Customer already exists with another partner, please contact support'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

           customers = User.objects.filter(id__in=customer_ids, is_customer=True).order_by('id')
           if len(customers) != len(customer_ids):
               return Response({'error': 'Customer Not Found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

           for customer in customers:
               customer.partner_id = partner
               customer.save()

           partner_serializer = PartnerCustomerSerializer(partner)
           customer_serializer = CustomerSerializer(User.objects.filter(partner_id=partner_id, is_customer=True).order_by('id'), many=True)

           partner_data = partner_serializer.data
           partner_data['customerDetails'] = customer_serializer.data

           response_data = {
               'partnerDetails': [partner_data]
           }

           return Response(response_data)

       except Exception as e:
           return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
#----------------------------------------- PATNER CUSTOMER DELETE VIEW ---------------------------------------
class PartnerCustomerDelete(APIView):
    permission_classes = (IsAuthenticated,)
    
    def delete(self, request, partner_id, customer_id, *args, **kwargs):
        if not request.user.is_admin and not request.user.partner_admin == partner_id:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
        try:
            partner = Partner.objects.get(id=partner_id)
        except Partner.DoesNotExist:
            return Response({'error':'Partner doesnot exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            customer = User.objects.get(id=customer_id, is_customer=True, partner_id=partner)
        except User.DoesNotExist:
            return Response({'status_code':628, 'error':'Customer doesnot exist or is not associated with the given partner'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        customer.partner_id = None
        customer.partner_admin= False
        customer.save()
        
        return Response({'message':'Customer removed from the partner'})
    

# --------------------------------------- PARTNER ADMIN REMOVE --------------------------------------------------------

class PartnerAdminDelete(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, partner_id, customer_id, *args, **kwargs):
        if not request.user.is_admin and not request.user.partner_admin == partner_id:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        
        try:
            partner = Partner.objects.get(id=partner_id)
        except Partner.DoesNotExist:
            return Response({'error':'Partner doesnot exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            customer = User.objects.get(id=customer_id, is_customer=True, partner_id=partner)
        except User.DoesNotExist:
            return Response({'status_code':628, 'error':'Customer doesnot exist or is not associated with the given partner'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # customer.partner_id = None
        customer.partner_admin= False
        customer.save()
        
        return Response({'message':'Partner admin removed Successfully'})
       
#----------------------------------------- PATNER ADMIN ADD VIEW ------------------------------------------     
class PartnerAdminAdd(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, partner_id, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605,'error':'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            partner = Partner.objects.get(id=partner_id)
        except Partner.DoesNotExist:
            return Response({'error':'Partner doesnot exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        data = request.data
        customer_id = data.get('customer_id')
       
        
        try:
            partner_admin_add = User.objects.get(id=customer_id, is_customer=True, partner_id=partner_id)
            
        except User.DoesNotExist:
            return Response({'error': 'customer doesnot exists'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        partner_admin_add.partner_admin = True
        partner_admin_add.save()
        
        return Response({'message':'Partner admin added successfully'})
    
class PartnerRoleUpdateAPIView(generics.UpdateAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerRoleUpdateSerializer
    permission_classes = (IsAuthenticated,)
      
    def update(self, request, *args, **kwargs):
        role_ids = request.data.get('role_ids', [])
        try:
            instance = self.get_object()
            instance.role_id.set(role_ids)

            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            response_data = {
            'role_ids': [
                {'id': role.id, 'name': role.name}
                for role in instance.role_id.all()
            ]
            }
            return Response({'partnerRoleDetail':response_data})
        except ValidationError as e:
            return Response({'error':e.detail}, status=500)
        except Exception as error:
            return Response({'error':str(error)}, status=500)  
        
class RolePartnerCreateAPIView(generics.CreateAPIView):
    queryset = Role.objects.all()

    def create(self, request, *args, **kwargs):
        role_id = self.kwargs.get('role_id')
        partner_ids = request.data.get('partner_ids', [])

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({'error': 'Role Does not exist'})

        partners = Partner.objects.filter(id__in=partner_ids)
        if not partners.exists():
            return Response({'error': 'No partner found with this id'})
               
        for partner in Partner.objects.filter(role_id=role):
            partner.role_id.remove(role)
            partner.remove_roles_to_users([role])
        
        for partner in partners:
            partner.role_id.add(role)
            partner.assign_roles_to_users([role])

        return Response({'success': 'Roles added to partners successfully'})

       
class PartnerFullList(generics.ListAPIView):
    queryset = Partner.objects.all().order_by('name')
    serializer_class = PartnerFullListSerializer
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            response_data = serializer.data
            return Response({'partnerDetails': response_data})
        except Exception as e:
            return Response({'error':str(e)}, status = 500)
   
        
       
#----------------------------------------------------- TYPE VIEWS --------------------------------------------------------------
class TypeCreate(generics.CreateAPIView):
    serializer_class = TypeSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            response_data = serializer.data
            return Response(response_data)
        except Exception as e:
            return Response({'errror':str(e)}, status=500)

class TypeDelete(generics.DestroyAPIView):
    queryset = Type.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        instance = self.get_object()
        if instance.is_fixed == True:
            return Response({'error':'fixed types cannot be deleted'}, status = 500)
        self.perform_destroy(instance)
        return Response({'message':"Type deleted successfully"})
    
class MultiTypeDelete(generics.CreateAPIView):
    queryset = Type.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        type_ids = request.data.get('type_ids', [])
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        
        instances = self.get_queryset().filter(id__in=type_ids)
        if not instances:
            return Response({'error': 'Ids not found'}, status = 500)
        for instance in instances:
            if instance.is_fixed==True:
                return Response({'error':'All other types deleted successfully except fixed types'}, status=200)
            else:
                instance.delete()
        return Response({'message':f'{len(instances)} Types deleted successfully!'})
    
class TypeList(generics.ListAPIView):
    queryset = Type.objects.all().order_by('id')
    serializer_class = TypeSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        return Response({'typeList':response_data})
    
class TypeUpdate(generics.UpdateAPIView):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception =True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
#------------------------------------------------------ PARTNER TYPES VIEWS --------------------------------------------------------

class PartnerTypeCreate(generics.CreateAPIView):
    serializer_class = PartnerTypeSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code': 605, 'error': 'You do not have permission to perform this action'}, status=status.HTTP_421_MISDIRECTED_REQUEST)
        partner_id = request.data.get('partner_id')
        type_id = request.data.get('type_id')
        partner_type_exists = PartnerType.objects.filter(partner_id=partner_id, type_id=type_id).exists()
        if partner_type_exists:
            return Response({'error': 'Partner and type already exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            partner_id = serializer.validated_data['partner_id']
            type_id = serializer.validated_data['type_id']
            role_id = type_id.role_id.id if type_id.role_id else None
            
            role = Role.objects.filter(pk=role_id).first()
            
            partner_type_role = PartnerTypesRole.objects.create(
                partner_id=partner_id,
                type_id=type_id,
                role_id=role if role else None
            )
            
        return Response(serializer.data)



class PartnerTypeDelete(generics.DestroyAPIView):
    queryset = PartnerType.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        instance = self.get_object()
        type_id = instance.type_id
        partner_id = instance.partner_id
        partner_role = PartnerTypesRole.objects.filter(partner_id=partner_id, type_id=type_id)
        partner_role.delete()
        self.perform_destroy(instance)
        return Response({'message':'Partner Type deleted successfully'})
    
class PartnerTypeList(generics.ListAPIView):
    queryset = PartnerType.objects.all().order_by('id')
    serializer_class = PartnerTypeSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        partner_id = self.kwargs.get('partner_id')
        return PartnerType.objects.filter(partner_id=partner_id).order_by('id')
    
    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, many=True)
        return Response({'partnerTypeList':serializer.data})


class MultiplePartnerTypeCreate(generics.CreateAPIView):
    queryset = PartnerType.objects.all()
    serializer_class = PartnerTypeSerializer

    def create(self, request, *args, **kwargs):
        partner_ids = request.data.get('partner_id', [])
        type_ids = request.data.get('type_id', [])
        instances = []
        existing_partner_types = PartnerType.objects.filter(partner_id__in=partner_ids, type_id__in=type_ids)

        for partner_id in partner_ids:
            for type_id in type_ids:
                if not existing_partner_types.filter(partner_id=partner_id, type_id=type_id).exists():
                    data = {'partner_id': partner_id, 'type_id': type_id}
                    serializer = self.get_serializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    instances.append(serializer.save())
                    
                    partner_type_role_data = {
                        'partner_id':partner_id,
                        'type_id':type_id,
                        'role_id':None
                    }
                    partner_type_role_serializer = PartnerTypeRoleSerializer(data=partner_type_role_data)
                    partner_type_role_serializer.is_valid(raise_exception=True)
                    partner_type_role_serializer.save()

        if instances:
            return Response({'partnerTypes':self.get_serializer(instances, many=True).data}, status=status.HTTP_201_CREATED)
        else:
            return Response("Partner types already exists.", status=status.HTTP_400_BAD_REQUEST)



#-------------------------------------------------- PARTNER TYPE ROLES VIEWS ----------------------------------------------------------   
class PartnerTypeRoleCreate(generics.CreateAPIView):
    serializer_class = PartnerTypeRoleSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        
        partner_id = request.data.get('partner_id', [])
        partner = Partner.objects.filter(pk__in = partner_id)
        type_id = request.data.get('type_id')
        partner_type = Type.objects.get(pk=type_id)
        role_id = request.data.get('role_id')
        role = None
        if role_id:
            try:
                role = Role.objects.get(pk=role_id)
            except Exception as e:
                return Response({'error':str(e)})
        for partner in partner:
            PartnerTypesRole.objects.create(
                partner_id = partner,
                type_id = partner_type,
                role_id = role
                
            )
        return Response({'partnerTypeRole':'successfully created'})
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception = True)
        
        # self.perform_create(serializer)
        # return Response(serializer.data)
    
class PartnerTypeRoleUpdate(generics.UpdateAPIView):
    queryset = PartnerTypesRole.objects.all()
    serializer_class = PartnerTypeRoleupdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'partnerTypeRoleDetails':serializer.data})
       
    
class PartnerTypeRoleDelete(generics.DestroyAPIView):
    queryset = PartnerTypesRole.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'status_code':605, 'error':'You do not have permission to perform this action'}, status = status.HTTP_421_MISDIRECTED_REQUEST)
        instance = self.get_object()
        partner_id = instance.partner_id
        type_id = instance.type_id
        partner_type = PartnerType.objects.filter(partner_id=partner_id, type_id=type_id)
        partner_type.delete()
        self.perform_destroy(instance)
        return Response({'message':'Partner Type Role deleted successfully'})

class PartnerTypeRoleList(generics.ListAPIView):
    queryset = PartnerTypesRole.objects.all().order_by('id')
    serializer_class = PartnerTypeRoleSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'partnerTypeRoleList':serializer.data})
    
#------------------------------------------------------- PARTNER TYPE ROLE USER VIEWS -------------------------------------------------------
class PartnerTypeRoleUserCreate(generics.CreateAPIView):
    serializer_class = PartnerTypeRoleUserSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        self.perform_create(serializer)
        return Response(serializer.data)
    
class PartnerTypeRoleUserDelete(generics.DestroyAPIView):
    queryset = PartnerTypeRolesUser.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message':'Partner Type Role User deleted Successfully'})
    
class PartnerTypeRoleUserList(generics.ListAPIView):
    queryset = PartnerTypeRolesUser.objects.all().order_by('id')
    serializer_class = PartnerTypeRoleUserSerializer
    permission_classes = (IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'partneTypeRoleUser':serializer.data})
    
class PartnerTypeUserUpdate(generics.UpdateAPIView):
    queryset = PartnerTypeRolesUser.objects.all()
    serializer_class = PartnerTypeRoleUserUpdateSerializer
    permission_classes = (IsAuthenticated,)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'partnerTypeUserDetail':serializer.data})

#-------------------------------------------------- USER DETAIL BY PARTNER ID ---------------------------------------------------------
class UserDetailByPartnerId(generics.RetrieveAPIView):
    serializer_class = PartnerCustomerListbyPartnerSerializer
    
    def get_queryset(self):
       partner_id = self.kwargs.get('partner_id')
       queryset= User.objects.filter(partnertyperolesuser__partner_types_role_id__partner_id=partner_id)
       return queryset.distinct()
   
    def retrieve(self, request, *args, **kwargs):
       queryset = self.get_queryset()
       serializer = self.get_serializer(queryset, many=True)
       response_data = {'partnerCustomerDetails':serializer.data}
       return Response(response_data)
   
