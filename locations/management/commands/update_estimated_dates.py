from django.core.management.base import BaseCommand
from locations.models import Location
from datetime import timedelta
from django.apps import apps
from projectmanagement.models import *


class Command(BaseCommand):
    help = 'Update estimated_completion_date and estimated_current_phase_end_date once a week'

    
    def calculate_estimated_completion_date(self, location):
        if location.current_phase_id:
            project = Project.objects.filter(location_id=location).first()
            if project and project.project_status == 'inprogress':
                total_duration = 0
                start_date = None

                for phase in project.projectphase_set.all():
                    if phase.start_date:
                        start_date = phase.start_date
                    for task in phase.projectphasetask_set.all():
                        actual_duration = self.calculate_actual_duration(task)
                        if actual_duration is not None:
                            total_duration += actual_duration

                if start_date:
                    estimated_end_date = start_date + timedelta(days=total_duration)
                    location.estimated_completion_date = estimated_end_date
                    location.save()


    def calculate_actual_duration(self, task):
        if task.start_date and task.end_date:
            actual_duration = (task.end_date - task.start_date).days
            if actual_duration < 0:
                actual_duration = 0
            return actual_duration
        return self.calculate_task_duration(task)

    def calculate_task_duration(self, task):
        if task.target_duration == 'days':
            return task.target_count
        if task.target_duration == 'weeks':
            return task.target_count * 7
        if task.target_duration == 'months':
            return task.target_count * 30
        if task.target_duration == 'years':
            return task.target_count * 365
        return 0


    def calculate_estimated_current_phase_end_date(self, location):
            if location.current_phase_id:
                project = Project.objects.filter(location_id=location).first()
                if project:
                    current_phase = location.current_phase_id
                    total_duration = 0

                    for task in current_phase.projectphasetask_set.all():
                        actual_duration = self.calculate_actual_duration(task)
                        if actual_duration is not None:
                            total_duration += actual_duration

                    start_date = current_phase.start_date
                    if start_date is not None:
                        estimated_end_date = start_date + timedelta(days=total_duration)
                        location.estimated_current_phase_end_date = estimated_end_date
                        location.save()

    def handle(self, *args, **kwargs):
        locations = Location.objects.filter(current_phase_id__isnull=False)

        for location in locations:
            self.calculate_estimated_completion_date(location)
            self.calculate_estimated_current_phase_end_date(location)

        self.stdout.write(self.style.SUCCESS('Updated estimated dates for locations.'))

