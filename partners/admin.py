from django.contrib import admin
from .models import *
# Register your models here.

class TimezoneAdmin(admin.ModelAdmin):
    list_display = ['id','zoneName', 'gmtOffset', 'gmtOffsetName', 'abbreviation', 'tzName']
    ordering = ['id']
    
class CountriesAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'iso3', 'iso2', 'numeric_code', 'phone_code', 'capital', 'emoji']
    ordering = ['id']
    
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'email', 'phone', 'city', 'country_id', 'zip_code']
    ordering = ['id']
    
class TypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ('id',)

class PartnerTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'partner_id', 'type_id')
    list_display_links = ('id', 'partner_id', 'type_id')
    ordering = ('id',)
    
class PartnerTypeRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'partner_id', 'type_id', 'role_id')
    list_display_links = ('id', 'partner_id', 'type_id', 'role_id')
    ordering = ('id',)
    
class PartnerTypeRoleUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'partner_types_role_id', 'user_id', 'is_admin')
    list_display_links = ('id', 'partner_types_role_id')
    ordering = ('id',)
    
    
admin.site.register(Timezone, TimezoneAdmin)
admin.site.register(Countries, CountriesAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(PartnerType, PartnerTypeAdmin)
admin.site.register(PartnerTypesRole, PartnerTypeRoleAdmin)
admin.site.register(PartnerTypeRolesUser, PartnerTypeRoleUserAdmin)
