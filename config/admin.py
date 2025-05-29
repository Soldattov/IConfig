from django.contrib import admin
from .models import (
    ParsedGPU, ParsedCPU, ParsedMotherboard, ParsedRAM,
    ParsedCooling, ParsedPowerSupply, ParsedStorage, ParsedCase
)

# Регистрация моделей для GPU
@admin.register(ParsedGPU)
class ParsedGPUAdmin(admin.ModelAdmin):
    list_display = ('model', 'frequency', 'memory_amount', 'price', 'relative_power')
    search_fields = ('model',)
    list_filter = ('price', 'memory_amount')

# Регистрация моделей для CPU
@admin.register(ParsedCPU)
class ParsedCPUAdmin(admin.ModelAdmin):
    list_display = ('model', 'cores_amount', 'frequency', 'socket', 'price', 'relative_power')
    search_fields = ('model',)
    list_filter = ('cores_amount', 'socket', 'price')

# Аналогично для остальных моделей
@admin.register(ParsedMotherboard)
class ParsedMotherboardAdmin(admin.ModelAdmin):
    list_display = ('model', 'form_factor', 'socket', 'ram_type', 'price')
    search_fields = ('model',)
    list_filter = ('form_factor', 'socket', 'ram_type')

@admin.register(ParsedRAM)
class ParsedRAMAdmin(admin.ModelAdmin):
    list_display = ('model', 'amount', 'typee', 'price')
    search_fields = ('model',)
    list_filter = ('typee', 'amount')

@admin.register(ParsedCooling)
class ParsedCoolingAdmin(admin.ModelAdmin):
    list_display = ('model', 'typee', 'socket', 'tdp', 'price')
    search_fields = ('model',)
    list_filter = ('typee', 'socket')

@admin.register(ParsedPowerSupply)
class ParsedPowerSupplyAdmin(admin.ModelAdmin):
    list_display = ('model', 'power', 'price')
    search_fields = ('model',)
    list_filter = ('power',)

@admin.register(ParsedStorage)
class ParsedStorageAdmin(admin.ModelAdmin):
    list_display = ('model', 'capacity', 'typee', 'price')
    search_fields = ('model',)
    list_filter = ('typee', 'capacity')

@admin.register(ParsedCase)
class ParsedCaseAdmin(admin.ModelAdmin):
    list_display = ('model', 'supported_form_factor', 'size', 'price')
    search_fields = ('model',)
    list_filter = ('supported_form_factor', 'size')

# Register your models here.
