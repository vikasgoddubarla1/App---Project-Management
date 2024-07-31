from django.shortcuts import render
from rest_framework import generics, status
from .serializers import *
from .models import *
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from partners.pagination import CustomPagination

# Create your views here.
class NotificationList(generics.ListAPIView):
    queryset = Notification.objects.all().order_by('-id')
    serializer_class = NotificationListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                "notificationList":serializer.data,
                "paginationDetails":{
                    "current_page":self.paginator.page.number,
                    "number_of_pages":self.paginator.page.paginator.num_pages,
                    "current_page_items":len(serializer.data),
                    "total_items": self.paginator.page.paginator.count,
                    "next_page": self.paginator.get_next_link(),
                    "previous_page": self.paginator.get_previous_link(),
                }
            }
            return Response(response_data)
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'notificationList': serializer.data}
        return Response(response_data)

class NotificationUpdate(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        notification_ids = request.data.get('notification_ids', [])
        is_seen = request.data.get('is_seen')
        try:
            notifications = self.get_queryset().filter(id__in=notification_ids)
            notifications.update(is_seen=is_seen)
            serializer = self.get_serializer(notifications, many=True)
            return Response({'notificationDetails': serializer.data})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

       
class NotificationListByUserId(generics.ListAPIView):
    serializer_class = NotificationListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        user_id = kwargs['user_id']
        queryset = Notification.objects.filter(user_id=user_id).order_by('-id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                "userNotificationsList":serializer.data,
                "paginationDetails":{
                    "current_page":self.paginator.page.number,
                    "number_of_pages":self.paginator.page.paginator.num_pages,
                    "current_page_items":len(serializer.data),
                    "total_items": self.paginator.page.paginator.count,
                    "next_page": self.paginator.get_next_link(),
                    "previous_page": self.paginator.get_previous_link(),
                }
            }
            return Response(response_data)
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'userNotificationsList': serializer.data}
        return Response(response_data)
    

class NotificationDelete(generics.DestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationListSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        notification_ids = request.data.get('notification_ids', [])
        try:
            notifications = Notification.objects.filter(id__in=notification_ids)
            notifications.delete()
            return Response({'message': "notifications deleted successfully"})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class TaskMentionsNotificationListByUserId(generics.ListAPIView):
    serializer_class = NotificationListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def post(self, request, *args, **kwargs):
        user_id = kwargs['user_id']
        queryset = Notification.objects.filter(user_id=user_id, source="project_mentions").order_by('-id')
        is_seen = request.data.get('is_seen')
        if is_seen:
            queryset = queryset.filter(is_seen = is_seen)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                "taskMentionsNotificationsList":serializer.data,
                "paginationDetails":{
                    "current_page":self.paginator.page.number,
                    "number_of_pages":self.paginator.page.paginator.num_pages,
                    "current_page_items":len(serializer.data),
                    "total_items": self.paginator.page.paginator.count,
                    "next_page": self.paginator.get_next_link(),
                    "previous_page": self.paginator.get_previous_link(),
                }
            }
            return Response(response_data)
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'taskMentionNotificationsList': serializer.data}
        return Response(response_data)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
