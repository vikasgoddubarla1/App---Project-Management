from django.db import models

# Create your models here.
class Notification(models.Model):
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=955, null=True, blank=True)
    subject = models.CharField(max_length=955)
    source = models.CharField(max_length=100, null=True, blank=True)
    task_id = models.IntegerField(null=True)
    body    = models.CharField(max_length=955)
    is_seen = models.BooleanField(default=False)
    data_id = models.IntegerField()
    data_name = models.CharField(max_length=955)
    assigned_by_id = models.IntegerField()
    assigned_by_name = models.CharField(max_length=955)
    location_name = models.CharField(max_length=955, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    status_type = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.subject} - {self.body}"
    