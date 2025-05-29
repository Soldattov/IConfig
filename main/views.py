from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from config.models import ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM, ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
from .models import SavedConfiguration, ConfigurationComponent
import json

def index(request):
    return render(request, 'main/index.html')

def config(request):
    # Получаем все компоненты из базы данных
    gpus = ParsedGPU.objects.all()
    cpus = ParsedCPU.objects.all()
    motherboards = ParsedMotherboard.objects.all()
    rams = ParsedRAM.objects.all()
    coolings = ParsedCooling.objects.all()
    power_supplies = ParsedPowerSupply.objects.all()
    storages = ParsedStorage.objects.all()
    cases = ParsedCase.objects.all()

    # Словарь типов компонентов для отображения
    component_types = {
        'gpu': 'Видеокарта',
        'cpu': 'Процессор',
        'motherboard': 'Материнская плата',
        'ram': 'Оперативная память',
        'cooling': 'Охлаждение',
        'psu': 'Блок питания',
        'storage': 'Накопитель',
        'case': 'Корпус'
    }

    context = {
        'component_types': component_types,
        'default_image': '/static/images/no-image.png',
        'assembly_price': 4990,  # Цена сборки
    }

    return render(request, 'main/config.html', context)

@login_required
def save_configuration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('Полученные данные:', data)
            
            # Создаем конфигурацию
            config = SavedConfiguration.objects.create(
                user=request.user,
                name=data.get('name', 'My Configuration'),
                total_price=data.get('total_price', 0),
                is_public=data.get('is_public', False)
            )
            print('Создана конфигурация:', config)
            
            # Добавляем компоненты
            components = data.get('components', {})
            print('Компоненты для добавления:', components)
            
            for component_type, component_data in components.items():
                try:
                    component = ConfigurationComponent.objects.create(
                        configuration=config,
                        component_type=component_type,
                        component_id=component_data['id'],
                        name=component_data['name'],
                        price=component_data['price']
                    )
                    print(f'Добавлен компонент: {component_type} - {component.name}')
                except Exception as e:
                    print(f'Ошибка при добавлении компонента {component_type}:', str(e))
                    raise
            
            # Проверяем, что компоненты действительно добавлены
            print(f'Всего добавлено компонентов: {config.components.count()}')
            for comp in config.components.all():
                print(f'Компонент в БД: {comp.component_type} - {comp.name}')
            
            return JsonResponse({
                'status': 'success',
                'config_id': config.id,
                'message': 'Configuration saved successfully'
            })
        except Exception as e:
            print('Ошибка при сохранении:', str(e))
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def my_configurations(request):
    print('Получение конфигураций для пользователя:', request.user.username)
    configs = SavedConfiguration.objects.filter(user=request.user).prefetch_related('components')
    print('Найдено конфигураций:', configs.count())
    for config in configs:
        print(f'Конфигурация: {config.name}, ID: {config.id}, Компонентов: {config.components.count()}')
        for component in config.components.all():
            print(f'  - {component.component_type}: {component.name} ({component.price} ₽)')
    
    context = {
        'configurations': configs,
        'page_title': 'Мои конфигурации'
    }
    return render(request, 'main/my_configurations.html', context)

@login_required
def view_configuration(request, config_id):
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    return render(request, 'main/view_configuration.html', {
        'configuration': config
    })

@login_required
@require_POST
def delete_configuration(request, config_id):
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    config.delete()
    return JsonResponse({'status': 'success', 'message': 'Configuration deleted successfully'})

@login_required
@require_POST
def toggle_public(request, config_id):
    config = get_object_or_404(SavedConfiguration, id=config_id, user=request.user)
    config.is_public = not config.is_public
    config.save()
    return JsonResponse({
        'status': 'success',
        'is_public': config.is_public,
        'message': 'Configuration visibility updated'
    })
