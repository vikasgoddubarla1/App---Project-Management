from .models import *
from rest_framework import serializers
from projectmanagement.models import Project

class NotificationListSerializer(serializers.ModelSerializer):
    location_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ('id', 'user_id', 'user_name', 'subject', 'source', 'status_type', 'body', 'is_seen', 'task_id', 'data_id', 'data_name', 'assigned_by_id', 'assigned_by_name', 'location_name', 'location_status', 'created_at')
        
    def get_location_status(self, obj):
        try:
            project = Project.objects.get(id=obj.data_id)
            return project.location_id.location_status
        except Project.DoesNotExist:
            return None
class NotificationUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Notification
        fields = ('id', 'is_seen')