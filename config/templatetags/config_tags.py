"""
Модуль config_tags.py - пользовательские теги шаблонов Django
Предоставляет функциональность для работы с компонентами ПК в шаблонах.

Основное назначение:
1. Получение списков компонентов по их типу
2. Интеграция с моделями базы данных
3. Предоставление данных для шаблонов
"""

from django import template
from ..models import (
    ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM,
    ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
)

# Регистрация библиотеки тегов
register = template.Library()

@register.simple_tag
def get_component_list(component_type):
    """
    Пользовательский тег для получения списка компонентов по их типу.
    
    Параметры:
        component_type (str): Тип компонента ('gpu', 'cpu', 'motherboard' и т.д.)
    
    Возвращает:
        QuerySet: Список компонентов указанного типа из базы данных
        
    Пример использования в шаблоне:
        {% get_component_list 'gpu' as gpus %}
        {% for gpu in gpus %}
            {{ gpu.model }}
        {% endfor %}
    """
    # Словарь соответствия типов компонентов их моделям
    component_models = {
        'gpu': ParsedGPU,           # Видеокарты
        'cpu': ParsedCPU,           # Процессоры
        'motherboard': ParsedMotherboard,  # Материнские платы
        'ram': ParsedRAM,           # Оперативная память
        'cooling': ParsedCooling,   # Системы охлаждения
        'psu': ParsedPowerSupply,   # Блоки питания
        'storage': ParsedStorage,   # Накопители
        'case': ParsedCase          # Корпуса
    }
    
    # Получаем соответствующую модель по типу компонента
    model = component_models.get(component_type)
    if model:
        # Возвращаем все объекты выбранной модели
        return model.objects.all()
    return [] # Возвращаем пустой список, если тип компонента не найден 