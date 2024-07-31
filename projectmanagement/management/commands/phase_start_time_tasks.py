from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from projectmanagement.models import ProjectPhaseTask
from dateutil.relativedelta import relativedelta

class Command(BaseCommand):
    help = 'Start dependent tasks based on phase start date'

    def handle(self, *args, **options):
        try:
            phase_start_date = timezone.now().date() 
            phase_tasks = ProjectPhaseTask.objects.filter(
                project_phase_id__start_date=phase_start_date,
                dependent_count=1,
                dependent_duration__isnull=False
            )

            for task in phase_tasks:
                duration = task.dependent_duration
                if duration == 'days':
                    start_date = phase_start_date + timedelta(days=task.dependent_count)
                elif duration == 'weeks':
                    start_date = phase_start_date + timedelta(weeks=task.dependent_count)
                elif duration == 'months':
                    start_date = phase_start_date + relativedelta(months=task.dependent_count) - timedelta(days=1)
                elif duration == 'years':
                    start_date = phase_start_date + relativedelta(years=task.dependent_count) - timedelta(days=1)

                task.start_date = start_date
                task.status = 'inprogress'
                task.save()

            self.stdout.write(self.style.SUCCESS('Dependent tasks started successfully.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
