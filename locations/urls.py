from django.urls import path
from .views import *

urlpatterns = [    
    #--------------------------------------- Partner URLS --------------------------------------
    path('v1/location/create', CreateLocation.as_view(), name = 'Create-Location'),
    path('v1/location/<int:pk>', LocationDetail.as_view(), name = 'Get-Location-by-id'),
    path('v1/location', LocationList.as_view(), name = 'Get-Location-list'),
    path('v1/location/microPageImage/<int:pk>', LocationMicroPageImageUpdate.as_view(), name = 'update-Location-micropage-image'),
    path('v1/location/general/<int:pk>', LocationGeneral.as_view(), name = 'Location-General-details'),
    path('v1/location/status/<int:pk>', LocationStatus.as_view(), name = 'Location-status-details'),
    path('v1/location/landOwner/<int:pk>', LocationLandOwner.as_view(), name = 'Location-landowner-update'),
    path('v1/location/leadCompany/<int:pk>', LocationLeadCompanyUpdate.as_view(), name = 'Location-leadcompany-update'),
    path('v1/location/landOwner/delete/<int:pk>', LandOwnerDelete.as_view(), name = 'Location-landowner-delete'),
    path('v1/location/propertyManager/<int:pk>', LocationPropertyManager.as_view(), name = 'Location-property-manager-details'),
    path('v1/location/propertyManager/delete/<int:pk>', PropertyManagerDelete.as_view(), name = 'Location-property-manager-delete'),
    path('v1/location/tenant/<int:pk>', LocationTenants.as_view(), name = 'Location-Tenant-details'),
    path('v1/location/tenant/delete/<int:pk>', LocationTenantDelete.as_view(), name = 'Location-Tenant-delete'),
    path('v1/location/subtenant/create/<int:location_id>', SubtenantCreateAPIView.as_view(), name = 'Location-Tenant-create'),
    path('v1/location/subtenant/delete/<int:location_id>/<int:tenant_id>', SubtenantDeleteAPIView.as_view(), name = 'Location-Tenant-create'),
    path('v1/location/tenant', TenantList.as_view(), name = 'Location-Tenant-delete'),
    path('v1/location/state/<int:pk>', LocationStateUpdate.as_view(), name='Location-state-update'),
    path('v1/location/snowLoadFactor/<int:pk>', LocationSnowWeight.as_view(), name='Location-snowweight-update'),
    path('v1/location/prioritisation/<int:pk>', LocationPrioritisation.as_view(), name='Location-prioritisation-update'),
    path('v1/location/preRatings/<int:pk>', LocationPreRatings.as_view(), name='Location-pre-ratings-update'),
    path('v1/location/fullList', LocationFullList.as_view(), name = 'Get-Location-full-list'),
    path('v1/location/mapList', LocationMapList.as_view(), name = 'Get-Location-map-list'),
    path('v1/location/pipeline', LocationPipelineReport.as_view(), name = 'Get-Location-pipeline-list'),
    path('v1/location/multiple/delete', LocationMultipleDelete.as_view(), name='location-multiple-delete'),
    path('v1/location/evDetails/<int:pk>', LocationEVDetailsUpdate.as_view(), name='location_ev_details_update'),
    path('v1/location/pvDetails/<int:pk>', LocationPVDetailsUpdate.as_view(), name='location_pv_details_update'),
    path('v1/location/code/<int:pk>', LocationCodeUpdate.as_view(), name='location_code_update'),
    path('v1/location/microPage/create/<int:pk>', LocationMicroPageUpdate.as_view(), name='location_micropage_update'),
    path('v1/location/code/verification', LocationCodeVerification.as_view(), name='location_code_verify'),
    path('v1/location/channelColor/update/<int:pk>', LocationDeviceChannelColorUpdate.as_view(), name='location-channel-color-update'),
    
    #---------------------------------------Permissions, Module& Panels URLS -------------------------
    path('v1/modules', Modules.as_view(), name = 'Modules-and-panels'),
    path('v1/permissions', Permissions.as_view(), name = 'Permissions'),
    
    #---------------------------------------- Roles ---------------------------------------------------
    path('v1/roles', Roles.as_view(), name = 'Roles-list'),
    path('v1/roles/create', CreateRoles.as_view(), name = 'create-roles'),
    path('v1/roles/<int:pk>', RoleDetail.as_view(), name = 'delete-update-roles'),
    path('v1/permission/<int:roles_id>', RolesPermissionsAPIView.as_view(), name= 'create-role-permissions'),
    
    #----------------------------------------- Sales and Support -------------------------------------------------------
    path('v1/location/support/<int:pk>', LocationSupport.as_view(), name='location-support'),
    path('v1/location/sales/<int:pk>', LocationSales.as_view(), name='location-sales'),
    
    #---------------------------------Location Role ---------------------------------------------------------------
    path('v1/locationRole/<int:location_id>', LocationRoleCreate.as_view(), name='location-role-create'),
    path('v1/locationRole/update/<int:id>', LocationRoleUpdate.as_view(), name='location-role-create'),
    path('v1/locationRole/delete/<int:id>', LocationRoleDestroy.as_view(), name='location-role-create'),
    
    #------------------------------------------------ PVFile URL -------------------------------------------------------
    
    path('v1/files/pvfiles/<int:location_id>', PVFileCreate.as_view(), name='Pv-file-create'),
    path('v1/files/pvfiles/delete/<int:location_id>/<int:id>', PVFileDelete.as_view(), name='Pv-file-delete'),
    
    # ---------------------------------------------- Location Contract Files -------------------------------------------
    path('v1/locationContract/create/<int:location_id>', LocationContractAPIView.as_view(), name='location-contract-create'),
    path('v1/locationContract/delete/<int:pk>', LocationContractDeleteAPIView.as_view(), name='location-contract-delete'),
    path('v1/locationContract/delete/<int:location_id>/<int:contract_id>', LocationContractDelete.as_view(), name='location-contract-delete'),
    
    #---------------------------------------------- CREATE LOCATION USING CSV ----------------------------------------------------
    
    path('v1/location/create/csv', LocationCreateUpdateCSVView.as_view(), name = 'Create-Location-csv'),
    
    #--------------------------------------------- Location Device Slots --------------------------------------------------------------
    path('v1/location/device/slot/create', LocationDeviceSlotCreate.as_view(), name= 'location-device-slot-create'),
    path('v1/location/device/slot/delete/<int:pk>', LocationDeviceSlotDelete.as_view(), name= 'location-device-slot-delete'),
    path('v1/location/device/slot', LocationDeviceSlotList.as_view(), name= 'location-device-slot-list'),
    path('v1/location/device/slot/detail/<int:location_id>', LocationDeviceSlotRetrieve.as_view(), name= 'location-device-slot-detail'),
    
    #------------------------------------------------- Location Measures -------------------------------------------------------------
    path('v1/location/measureSettings/<int:location_id>', LocationMeasureSettingsCreateAPIView.as_view(), name= 'location-measure-settings-create'),
    path('v1/location/measureSettings/get/<int:location_id>', LocationMeasureSettingsRetrieveAPIView.as_view(), name= 'location-measure-settings-retreive'),
    
    #------------------------------------------------ LOCATION EV AND PV DETAILS ----------------------------------------------------
    path('v1/location/ev/<int:pk>', LocationEVDetails.as_view(), name='location-ev-details'),
    path('v1/location/pv/<int:pk>', LocationPVDetails.as_view(), name='location-pv-details'),
    
    #--------------------------------------------------- LOCATION MEASURES ----------------------------------------------------------
    path('v1/location/measures/<int:location_id>', LocationMeasuresListCreate.as_view(), name='location-measures-list-create'),
    path('v1/location/measures/update/<int:pk>', LocationMeasuresUpdate.as_view(), name='location-measures-Update-create'),
    
    #---------------------------------------------------- LOCATION MALOS AND VALUES ------------------------------------------------
    path('v1/location/malos/create/<int:location_id>', LocationMalosCreateAPIView.as_view(), name='location-malos-view'),
    path('v1/location/malos/<int:location_id>', LocationMalosGetList.as_view(), name='location-malos-list'),
    path('v1/location/malo/delete/<int:pk>', LocationMaloDelete.as_view(), name='location-malo-delete'),
    path('v1/location/devicemalo/create', LocationDeviceMaloCreate.as_view(), name='location-device-malo-create'),
    path('v1/location/devicemalo', LocationDeviceMaloGetList.as_view(), name='location-device-malo-get-list'),
    path('v1/location/devicemalo/<int:pk>', LocationDeviceMaloDetail.as_view(), name='location-device-malo-details'),
    
    # --------------------------------------------------- LOCATION ADDITIONAL STATUS -----------------------------------------------
    path('v1/location/additional/status', LocationStatusEVPVView.as_view(), name = 'location-ev-pv-status'),
    
    #----------------------------------------------------- LOCATION PARTNER TYPES ----------------------------------------------------
    path('v1/location/partner/create', LocationPartnerTypeCreate.as_view(), name='location-partner-type-create'),
    path('v1/location/parnter/delete/<int:pk>', LocationPartnerTypeDelete.as_view(), name='location-partner-type-delete'),
    path('v1/location/partner/<int:location_id>', LocationPartnerTypeList.as_view(), name='location-partner-retrieve'),
    path('v1/location/partner/type/update/<int:pk>', LocationPartnerTypeUpdate.as_view(), name='location-partner-update'),
    path('v1/location/partner/type/<int:partner_id>/<int:type_id>', LocationListByPartnerType.as_view(), name='location-list-by-partner-type'),

    #--------------------------------------------------------- LOCATION OPERATING BASED ON QUARTERS -----------------------------------
    path('v1/location/month', LocationListByMonth.as_view(), name='location-list-by-month')
]