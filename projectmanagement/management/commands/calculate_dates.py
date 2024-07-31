from django.core.management.base import BaseCommand
from django.utils import timezone
from projectmanagement.models import Project

class Command(BaseCommand):
    help = 'Update start date for projects'

    def handle(self, *args, **kwargs):
        projects = Project.objects.filter(project_status='todo') | Project.objects.filter(start_date__isnull=True)
        for project in projects:
            project.start_date = timezone.now() + timezone.timedelta(days=1)
            project.save()
            self.stdout.write(self.style.SUCCESS(f"Start date updated for project '{project.name}'"))
