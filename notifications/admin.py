from django.contrib import admin
from .models import *

# Register your models here.

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id','subject', 'body',  'user_id', 'is_seen', 'data_id', 'data_name', 'assigned_by_id', 'assigned_by_name', 'location_name']
    list_display_links = ['id', 'subject', 'body']

admin.site.register(Notification, NotificationAdmin)
