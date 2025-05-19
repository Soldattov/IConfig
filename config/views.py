from django.shortcuts import render
from django.http import JsonResponse, Http404
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

def component_detail(request, component_type, component_id):
    """
    API-представление для возврата данных компонента по его типу и id.
    """
    try:
        if component_type == 'gpu':
            component = ParsedGPU.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',                'relative_power': component.relative_power,
                # Добавьте другие необходимые поля, например: memory_amount, frequency и т.д.
            }
        elif component_type == 'cpu':
            component = ParsedCPU.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',                'cores_amount': component.cores_amount,
                'frequency': component.frequency,
                'socket': component.socket,
            }
        elif component_type == 'motherboard':
            component = ParsedMotherboard.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',                'socket': component.socket,
                'form_factor': component.form_factor,
            }
        elif component_type == 'ram':
            component = ParsedRAM.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',                'amount': component.amount,
                'typee': component.typee,
            }
        elif component_type == 'cooling':
            component = ParsedCooling.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',                'typee': component.typee,
                'socket': component.socket,
            }
        elif component_type == 'psu':
            component = ParsedPowerSupply.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'power': component.power,
            }
        elif component_type == 'storage':
            component = ParsedStorage.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'capacity': component.capacity,
                'typee': component.typee,
            }
        elif component_type == 'case':
            component = ParsedCase.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'supported_form_factor': component.supported_form_factor,
                'size': component.size,
            }
        else:
            raise Http404("Неизвестный тип компонента")
    except (ParsedGPU.DoesNotExist, ParsedCPU.DoesNotExist, ParsedMotherboard.DoesNotExist,
            ParsedRAM.DoesNotExist, ParsedCooling.DoesNotExist, ParsedPowerSupply.DoesNotExist,
            ParsedStorage.DoesNotExist, ParsedCase.DoesNotExist):
        raise Http404("Компонент не найден")

    return JsonResponse(data)