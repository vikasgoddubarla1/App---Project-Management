from django.urls import path
from .views import *

urlpatterns = [    
    #--------------------------------------- NOFICIATIONS MANAGEMENT URLS --------------------------------------
    path('v1/notifications/list', NotificationList.as_view(), name = 'notifications-list'),
    path('v1/notifications/update', NotificationUpdate.as_view(), name = 'notifications-update'),
    path('v1/notifications/list/<int:user_id>', NotificationListByUserId.as_view(), name = 'notifications-list'),
    path('v1/notifications/taskMentions/list/<int:user_id>', TaskMentionsNotificationListByUserId.as_view(), name = 'notifications-list'),
    path('v1/notifications/delete', NotificationDelete.as_view(), name = 'notifications-delete'),
    
]