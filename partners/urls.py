from django.urls import path
from .views import *

urlpatterns = [    
    #--------------------------------------- Partner URLS --------------------------------------
    path('v1/countries', CountryList.as_view(), name = 'countries-list'),
    path('v1/partner', PartnerList.as_view(), name = 'partner-list'), 
    path('v1/partner/create', CreatePartner.as_view(), name='create-partner'),
    path('v1/partner/<int:pk>', PartnerDetail.as_view(), name = 'partner-details'),
    path('v1/fullList/partner', PartnerFullList.as_view(), name = 'partner-full-list'),
    
    #-----------------------------Update Partner Details Views -----------------------------------
    path('v1/partner/general/<int:pk>', PartnerGeneral.as_view(), name='partner-general'),
    path('v1/partner/website/<int:pk>', PartnerWebsiteUpdate.as_view(), name='partner-website'),
    path('v1/partner/support/<int:pk>', PartnerSupport.as_view(), name='partner-support'),
    path('v1/partner/sales/<int:pk>', PartnerSales.as_view(), name='partner-sales'),
    path('v1/partner/remarks/<int:pk>', PartnerRemarks.as_view(), name='partner-remarks'),
    #-------------------------- Partner and Customer URLS-------------------------------------------
    path('v1/partner/customers/add/<int:partner_id>', PartnerCustomerAdd.as_view(), name='partner-customer-add'),
    path('v1/partner/customers/<int:partner_id>/<int:customer_id>', PartnerCustomerDelete.as_view(), name="partner-delete"),
    path('v1/partner/admin/add/<int:partner_id>', PartnerAdminAdd.as_view(), name='partner-admin-add'),
    path('v1/partner/admin/remove/<int:partner_id>/<int:customer_id>', PartnerAdminDelete.as_view(), name="partner-admin-delete"),
    path('v1/partner/role/update/<int:pk>', PartnerRoleUpdateAPIView.as_view(), name='partner-role-update'),
    path('v1/partner/role/add/<int:role_id>', RolePartnerCreateAPIView.as_view(), name='role-partner-add'),
    
    #-------------------------------------------------------------TYPES ---------------------------------------------------------------------
    path('v1/type/create', TypeCreate.as_view(), name='type-create'),
    path('v1/types/list', TypeList.as_view(), name='type_list'),
    path('v1/type/delete/<int:pk>', TypeDelete.as_view(), name='type-delete'),
    path('v1/type/update/<int:pk>', TypeUpdate.as_view(), name='type-update'),
    
    #------------------------------------------------------- PARTNER TYPES -------------------------------------------------------------------------
    path('v1/partner/type/create', PartnerTypeCreate.as_view(), name='partner-type-create'),
    path('v1/partner/type/list/<int:partner_id>', PartnerTypeList.as_view(), name='partner-type-list'),
    path('v1/partner/type/delete/<int:pk>', PartnerTypeDelete.as_view(), name='partner-type-delete'),
    
    #----------------------------------------------------- PARTNER TYPE ROLE CREATE ---------------------------------------------------
    path('v1/partner/type/role/create', PartnerTypeRoleCreate.as_view(), name='partner-role-create'),
    path('v1/partner/type/role/delete/<int:pk>', PartnerTypeRoleDelete.as_view(), name='partner-type-role-delete'),
    path('v1/partner/type/role/list', PartnerTypeRoleList.as_view(), name='partner-type-role-list'),
    path('v1/partner/type/role/update/<int:pk>', PartnerTypeRoleUpdate.as_view(), name='partner-type-role-update'),
    
    #---------------------------------------------------- PARTNER TYPE ROLE USER ---------------------------------------------------
    path('v1/partner/type/role/user/create', PartnerTypeRoleUserCreate.as_view(), name='partner-type-role-user-create'),
    path('v1/partner/type/role/user/list', PartnerTypeRoleUserList.as_view(), name='partner-type-role-user-create'),
    path('v1/partner/type/role/user/delete/<int:pk>', PartnerTypeRoleUserDelete.as_view(), name='partner-type-role-user-create'),
    path('v1/partner/type/role/user/update/<int:pk>', PartnerTypeUserUpdate.as_view(), name='partner-type-user-update'),
    path('v1/partner/user/<int:partner_id>', UserDetailByPartnerId.as_view(), name='partner-type-user-update'),
    
    path('v1/partner/type/multi/create', MultiplePartnerTypeCreate.as_view(), name='multiple-partner-type-create'),
    path('v1/type/multi/delete', MultiTypeDelete.as_view(), name='multi-type-delete'),
 
    
]