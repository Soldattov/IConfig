from django.shortcuts import render
from .models import GPU, CPU, Motherboard, RAM, Cooling, PowerSupply, Storage, Case

def component_list(request):
    gpus = GPU.objects.all()
    cpus = CPU.objects.all()
    motherboards = Motherboard.objects.all()
    rams = RAM.objects.all()
    coolings = Cooling.objects.all()
    power_supplies = PowerSupply.objects.all()
    storages = Storage.objects.all()
    cases = Case.objects.all()

    return render(request, 'component_list.html', {
        'gpus': gpus,
        'cpus': cpus,
        'motherboards': motherboards,
        'rams': rams,
        'coolings': coolings,
        'power_supplies': power_supplies,
        'storages': storages,
        'cases': cases
    })
