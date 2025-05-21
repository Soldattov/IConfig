"""
Модуль views.py - представления Django для конфигуратора ПК
Предоставляет функциональность для:
1. Отображения страницы конфигуратора
2. API для получения детальной информации о компонентах
3. Обработки запросов к базе данных
"""

from django.shortcuts import render
from django.http import JsonResponse, Http404
from .models import (
    ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM,
    ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
)

def configurator(request):
    """
    Основное представление конфигуратора ПК.
    
    Функциональность:
    1. Получает все компоненты из базы данных
    2. Формирует контекст с данными для шаблона
    3. Отображает страницу конфигуратора
    
    Параметры:
        request: HTTP-запрос от клиента
        
    Возвращает:
        HttpResponse: Отрисованная страница конфигуратора
    """
    # Получаем все компоненты из базы данных
    gpus = ParsedGPU.objects.all()
    cpus = ParsedCPU.objects.all()
    motherboards = ParsedMotherboard.objects.all()
    rams = ParsedRAM.objects.all()
    coolings = ParsedCooling.objects.all()
    power_supplies = ParsedPowerSupply.objects.all()
    storages = ParsedStorage.objects.all()
    cases = ParsedCase.objects.all()

    # Формируем контекст с данными для шаблона
    context = {
        # Списки компонентов
        'gpus': gpus,
        'cpus': cpus,
        'motherboards': motherboards,
        'rams': rams,
        'coolings': coolings,
        'power_supplies': power_supplies,
        'storages': storages,
        'cases': cases,
        
        # Дополнительные данные
        'assembly_price': 4990,  # Цена сборки
        'default_image': '/static/images/no-image.png',  # Путь к изображению по умолчанию
        
        # Словарь типов компонентов для отображения
        'component_types': {
            'gpu': 'Видеокарта',
            'cpu': 'Процессор',
            'motherboard': 'Материнская плата',
            'ram': 'Оперативная память',
            'cooling': 'Охлаждение',
            'psu': 'Блок питания',
            'storage': 'Накопитель',
            'case': 'Корпус'
        }
    }

    return render(request, 'config_page.html', context)

def component_detail(request, component_type, component_id):
    """
    API-представление для получения детальной информации о компоненте.
    
    Функциональность:
    1. Получает компонент по типу и ID
    2. Формирует JSON-ответ с данными компонента
    3. Обрабатывает ошибки и несуществующие компоненты
    
    Параметры:
        request: HTTP-запрос от клиента
        component_type (str): Тип компонента ('gpu', 'cpu' и т.д.)
        component_id (int): ID компонента в базе данных
        
    Возвращает:
        JsonResponse: JSON с данными компонента или ошибкой 404
    """
    try:
        # Обработка разных типов компонентов
        if component_type == 'gpu':
            component = ParsedGPU.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'memory_amount': component.memory_amount,
                'frequency': component.frequency,
            }
        elif component_type == 'cpu':
            component = ParsedCPU.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'cores_amount': component.cores_amount,
                'frequency': component.frequency,
                'socket': component.socket,
            }
        elif component_type == 'motherboard':
            component = ParsedMotherboard.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',  
                'socket': component.socket,
                'form_factor': component.form_factor,
            }
        elif component_type == 'ram':
            component = ParsedRAM.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'amount': component.amount,
                'modules': component.modules,
                'typee': component.typee,
            }
        elif component_type == 'cooling':
            component = ParsedCooling.objects.get(pk=component_id)
            data = {
                'model': component.model,
                'picture': str(component.picture) if component.picture else '/static/images/no-image.png',
                'typee': component.typee,
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