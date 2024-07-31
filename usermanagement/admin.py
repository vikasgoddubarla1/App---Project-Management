from django.contrib import admin
from .models import *

# ----------- CUSTOMIZATION OF ADMIN FOR ALL MODELS --------------------------
class SalutationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ['id']

class TitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    ordering = ['id']


    
class UserAd(admin.ModelAdmin):
    list_display = ('id', 'firstname', 'lastname', 'email', 'salutation_id', 'title_id', 'last_login', 'is_admin')
    list_display_links = ('firstname', 'lastname', 'email')
    list_editable = ('is_admin',)
    ordering = ['id']
    
    filter_horizontal = ()
    list_filter = ()
    fieldsets = () #used for password hashing

class UserForgotPasswordAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'expired_at', 'is_expired')
    
class UserLoginLogsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'browser', 'operating_system', 'device', 'last_login', 'ip_address')
    list_display_links = ('id', 'user_id', 'browser')
    ordering = ['-last_login']
    
#---------- REGISTERING ALL THE MODELS TO ADMIN ------------------
admin.site.register(Salutation, SalutationAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(User, UserAd)
admin.site.register(RecoveryCode)
admin.site.register(UserForgotPassword, UserForgotPasswordAdmin)
admin.site.register(UserLoginLogs, UserLoginLogsAdmin)
