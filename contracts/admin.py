from django.contrib import admin
from .models import *

class ContractCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ('id',)
    
class ContractSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ('id',)
    
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract_number', 'name')
    list_display_links = ('id', 'contract_number', 'name')
    ordering = ('id',)
    
class ContractFrameworkAdmin(admin.ModelAdmin):
    list_display = ('id',)
    ordering = ('id',)
    filter_horizontal=('individual_contract_id',)
    
class ContractFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract_id', 'file_url')
    ordering = ('id',)
    list_display_links = ('id', 'contract_id')

class ContractApprovalsAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract_id', 'type_id', 'is_approved', 'approved_by', 'created_at')
    list_display_links = ('id', 'contract_id')
    
class ContractLogsAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract_id', 'user_id', 'updated_at')
    list_display_links = ('id', 'contract_id')
    
admin.site.register(ContractCategory, ContractCategoryAdmin)
admin.site.register(ContractSubCategory, ContractSubCategoryAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(ContractFramework, ContractFrameworkAdmin)
admin.site.register(ContractPartner)
admin.site.register(ContractFile, ContractFileAdmin)
admin.site.register(ContractLogs, ContractLogsAdmin)
admin.site.register(ContractApprovals, ContractApprovalsAdmin)
