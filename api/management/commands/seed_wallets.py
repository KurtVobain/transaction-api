# api/management/commands/seed_wallets.py
import random
from faker import Faker
from django.core.management.base import BaseCommand
from api.models import Wallet

class Command(BaseCommand):
    help = 'Seed random wallets into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'wallets_amount',
            type=int,
            nargs='?',
            default=50,
            help='Number of wallets to create (default: 50)'
        )

    def handle(self, *args, **options):
        count = options['wallets_amount']
        fake = Faker()
        for _ in range(count):
            # integer part 0–99, two decimal places
            balance = round(random.uniform(0, 99.99), 2)
            Wallet.objects.create(
                label=fake.word(),
                balance=balance
            )
        self.stdout.write(self.style.SUCCESS(f'✔ Created {count} wallets'))
