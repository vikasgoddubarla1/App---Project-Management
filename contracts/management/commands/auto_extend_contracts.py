
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from contracts.models import *

class Command(BaseCommand):
    help = 'Automatically extends contracts if necessary'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        contracts_to_extend = Contract.objects.filter(auto_extended=True, end_date__lte=today)
        
        for contract in contracts_to_extend:
            self.auto_extend_contract(contract)
            self.calculate_termination_date(contract)
            contract.save()

    def auto_extend_contract(self, contract):
        today = timezone.now().date()
        while today >= contract.end_date:
            if contract.extend_cycle == 'days':
                contract.end_date += timedelta(days=contract.extend_duration)
            elif contract.extend_cycle == 'weeks':
                contract.end_date += timedelta(weeks=contract.extend_duration)
            elif contract.extend_cycle == 'months':
                contract.end_date += relativedelta(months=contract.extend_duration)
            elif contract.extend_cycle == 'years':
                contract.end_date += relativedelta(years=contract.extend_duration)

    def calculate_termination_date(self, contract):
        if contract.termination_cycle == 'days':
            contract.termination_date = contract.end_date - timedelta(days=contract.termination_duration)
        elif contract.termination_cycle == 'weeks':
            contract.termination_date = contract.end_date - timedelta(weeks=contract.termination_duration)
        elif contract.termination_cycle == 'months':
            contract.termination_date = contract.end_date - relativedelta(months=contract.termination_duration)
        elif contract.termination_cycle == 'years':
            contract.termination_date = contract.end_date - relativedelta(years=contract.termination_duration)
