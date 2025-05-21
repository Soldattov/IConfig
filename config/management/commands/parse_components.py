from django.core.management.base import BaseCommand
from config.parser.dns_parser import main

class Command(BaseCommand):
    help = 'Запускает парсер комплектующих'

    def handle(self, *args, **kwargs):
        self.stdout.write("Запуск парсера...")
        main()
        self.stdout.write(self.style.SUCCESS("Парсер завершил работу"))