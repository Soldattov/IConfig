from django.contrib import admin
from .models import GPU, CPU, Motherboard, RAM, Cooling, PowerSupply, Storage, Case

# Регистрация моделей для GPU
@admin.register(GPU)
class GPUAdmin(admin.ModelAdmin):
    list_display = ('model', 'frequency', 'memory_amount', 'price')  # Поля, которые будут отображаться в списке
    search_fields = ('model',)  # Поля для поиска
    list_filter = ('price', 'memory_amount')  # Фильтры для удобства навигации

# Регистрация моделей для CPU
@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    list_display = ('model', 'cores_amount', 'frequency', 'price')
    search_fields = ('model',)
    list_filter = ('cores_amount', 'price')

# Аналогично для остальных моделей
@admin.register(Motherboard)
class MotherboardAdmin(admin.ModelAdmin):
    list_display = ('model', 'chipset', 'form_factor', 'socket', 'price')
    search_fields = ('model',)
    list_filter = ('form_factor', 'socket')

@admin.register(RAM)
class RAMAdmin(admin.ModelAdmin):
    list_display = ('model', 'amount', 'typee', 'price')
    search_fields = ('model',)
    list_filter = ('typee',)

@admin.register(Cooling)
class CoolingAdmin(admin.ModelAdmin):
    list_display = ('model', 'typee', 'socket', 'tdp', 'price')
    search_fields = ('model',)
    list_filter = ('typee', 'socket')

@admin.register(PowerSupply)
class PowerSupplyAdmin(admin.ModelAdmin):
    list_display = ('model', 'power', 'price')
    search_fields = ('model',)
    list_filter = ('power',)

@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ('model', 'capacity', 'typee', 'price')
    search_fields = ('model',)
    list_filter = ('typee',)

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('model', 'supported_form_factor', 'size', 'price')
    search_fields = ('model',)
    list_filter = ('supported_form_factor',)
# Register your models here.
