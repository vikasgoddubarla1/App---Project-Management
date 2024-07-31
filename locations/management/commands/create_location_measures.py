from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
 
from locations.models import LocationMeasures

class Command(BaseCommand):
    help = 'Create LocationMeasures for existing device channels'

    def handle(self, *args, **options):
        current_year = timezone.now().year

        existing_device_channels = DeviceChannel.objects.all()

        for channel in existing_device_channels:
            try:
                location_device = LocationDevice.objects.get(device=channel.device)
                location_id = location_device.location  
            except LocationDevice.DoesNotExist:
                self.stdout.write(self.style.SUCCESS(f'LocationDevice/Location not found for DeviceChannel {channel.id}'))
                continue

            existing_measures = LocationMeasures.objects.filter(device_channel_id=channel)
            if not existing_measures.exists():
                for month in range(1, 13):
                    month_date = datetime(year=current_year, month=month, day=1)
                    LocationMeasures.objects.create(
                        location_id=location_id,
                        device_channel_id=channel,
                        month_year=month_date.date(),
                    )
                for month in range(1, 13):
                    month_date = datetime(year=current_year - 1, month=month, day=1)
                    LocationMeasures.objects.create(
                        location_id=location_id,
                        device_channel_id=channel,
                        month_year=month_date.date(),
                    )    

                self.stdout.write(self.style.SUCCESS(f'Created LocationMeasures for DeviceChannel {channel.id}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'LocationMeasures already exist for DeviceChannel {channel.id}'))
