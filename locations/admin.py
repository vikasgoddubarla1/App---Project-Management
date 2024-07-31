from django.contrib import admin
from .models import *
# Register your models here.

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    prepopulated_fields = {"slug": ["name"]}
    ordering = ['id']

class ModulePanelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'module_id')
    list_display_links = ('id', 'name')
    prepopulated_fields = {"slug": ["name"]}
    ordering = ['id']
    
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ['id']

class RolesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ['id']
    
class RolesPermissionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'roles_id')
    filter_horizontal = ('modules_id', 'modules_panels_id', 'permissions_id')
    ordering = ['id']
    
class LocationTenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'location_id', 'subtenant_id', 'display_order')
    ordering = ['id']
    
class LocationRoleAdmin(admin.ModelAdmin):
    list_display = ('id',)
    ordering = ['id']

class LocationContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'location_id')

class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',  'location_longitude', 'location_latitude')
    list_display_links = ('id', 'name')
    ordering = ('id',)
    
class LocationDeviceSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'x_point', 'y_point', 'formula', 'formula_condition', 'formula_condition_value')
    list_display_links = ('id', 'x_point', 'y_point',)
    ordering = ('id',)
    
class LocationMeasureAdmin(admin.ModelAdmin):
    list_display = ('id', 'month_year', 'advance_payment', 'generated_energy', 'delivered_energy')
    list_display_links = ('id', 'month_year', 'advance_payment')
    ordering = ('id',)
    
class LocationMalosAdmin(admin.ModelAdmin):
    list_display = ('id', 'malo_number', 'location_id')
    list_display_links = ('id', 'malo_number')
    ordering = ('id',)
    
class LocationMaloValuesAdmin(admin.ModelAdmin):
    list_display = ('id', 'location_malo_id', 'value', 'date', 'time')
    list_display_links = ('id', 'value')
    ordering = ('id',)
    
class LocationStatusEVPVAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ('id',)
    
class LocationPartnerTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'location_id', 'partner_id', 'type_id')
    ordering = ('id',)
    list_display_links = ('id', 'location_id', 'partner_id', 'type_id')
    list_filter = ('type_id',)
    
admin.site.register(Status)
admin.site.register(Location, LocationAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(ModulePanel, ModulePanelAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(RolesPermissions, RolesPermissionsAdmin)
admin.site.register(Role, RolesAdmin)
admin.site.register(LocationSubTenant, LocationTenantAdmin)
admin.site.register(LocationRole, LocationRoleAdmin)
admin.site.register(PVFile)
admin.site.register(LocationContract, LocationContractAdmin)
admin.site.register(LocationDeviceSlot, LocationDeviceSlotAdmin)
admin.site.register(LocationMeasureSettings)
admin.site.register(LocationMeasures, LocationMeasureAdmin)
admin.site.register(LocationMalos, LocationMalosAdmin)
admin.site.register(LocationMaloValues, LocationMaloValuesAdmin)
admin.site.register(LocationStatusEVPV, LocationStatusEVPVAdmin)
admin.site.register(LocationDeviceMalos)
admin.site.register(LocationPartnerType, LocationPartnerTypeAdmin)
