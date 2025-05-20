from django import template
from ..models import (
    ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM,
    ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
)

register = template.Library()

@register.simple_tag
def get_component_list(component_type):
    """
    Возвращает список компонентов по их типу
    """
    component_models = {
        'gpu': ParsedGPU,
        'cpu': ParsedCPU,
        'motherboard': ParsedMotherboard,
        'ram': ParsedRAM,
        'cooling': ParsedCooling,
        'psu': ParsedPowerSupply,
        'storage': ParsedStorage,
        'case': ParsedCase
    }
    
    model = component_models.get(component_type)
    if model:
        return model.objects.all()
    return [] 