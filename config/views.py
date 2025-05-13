from django.shortcuts import render
from .models import (
    ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM,
    ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
)

def configurator(request):
    # Получаем все компоненты из базы данных
    gpus = ParsedGPU.objects.all()
    cpus = ParsedCPU.objects.all()
    motherboards = ParsedMotherboard.objects.all()
    rams = ParsedRAM.objects.all()
    coolings = ParsedCooling.objects.all()
    power_supplies = ParsedPowerSupply.objects.all()
    storages = ParsedStorage.objects.all()
    cases = ParsedCase.objects.all()

    context = {
        'gpus': gpus,
        'cpus': cpus,
        'motherboards': motherboards,
        'rams': rams,
        'coolings': coolings,
        'power_supplies': power_supplies,
        'storages': storages,
        'cases': cases
    }

    return render(request, 'config_page.html', context)
