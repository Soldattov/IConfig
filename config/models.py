import re
from tkinter.constants import CASCADE
import config.parser.power_calculator as calculator

from django.conf import settings
from django.db import models


class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=20)
    time_creation = models.DateTimeField(auto_now_add=True)
    budget = models.CharField()
    description = models.CharField(max_length=500)

    def add_component(self, component):
        component_type = None
        """Добавляет компонент в проект"""
        if isinstance(component, ParsedGPU):
            component_type = 'gpu'
        elif isinstance(component, ParsedCPU):
            component_type = 'cpu'

        ProjectComponent.objects.get_or_create(
            project=self,
            component_type=component_type,
            component_id=component.id
        )

    def get_components(self):
        """Возвращает все компоненты проекта"""
        components = []
        for pc in self.projectcomponent_set.all():
            if pc.component_type == 'gpu':
                components.append(ParsedGPU.objects.get(id=pc.component_id))
            elif pc.component_type == 'cpu':
                components.append(ParsedCPU.objects.get(id=pc.component_id))
            # ... другие типы ...
        return components


class ProjectComponent(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    component_type = models.CharField(max_length=50)  # 'gpu', 'cpu', etc.
    component_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('project', 'component_type', 'component_id')


class BaseComponent(models.Model):
    model = models.CharField(max_length=100)
    price = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='component_images/', blank=True, null=True)
    source_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        abstract = True

class ParsedGPU(BaseComponent):
    frequency = models.CharField(max_length=50)
    memory_amount = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    consumption = models.CharField(max_length=50)
    relative_power = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        calculator.calculateGPUPower(self)
        super().save(*args, **kwargs)


class GPU(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=30)
    frequency = models.CharField()
    memory_amount = models.CharField()
    picture = models.ImageField(upload_to='gpu_images/', blank=True, null=True)

    size = models.CharField()
    consumption = models.CharField()

    price = models.CharField()
    relative_power = models.CharField()


class ParsedCPU(BaseComponent):
    cores_amount = models.CharField(max_length=10)
    frequency = models.CharField(max_length=10)
    socket = models.CharField(max_length=9)
    tdp = models.CharField(max_length=10)
    #consumption = models.CharField(max_length=10)

    relative_power = models.CharField(max_length=10)

    def save(self, *args, **kwargs):
        calculator.calculateCPUPower(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.model


class CPU(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=15)
    cores_amount = models.CharField(max_length=10)
    frequency = models.CharField(max_length=10)
    picture = models.ImageField(upload_to='cpu_images/', blank=True, null=True)
    socket = models.CharField(max_length=9)
    tdp = models.CharField(max_length=10)
    consumption = models.CharField(max_length=10)
    price = models.CharField(max_length=10)
    relative_power = models.CharField(max_length=10)

    def calculatePower(self):
        """
        Вычисляет relative_power на основе модели CPU.
        """
        base_power = 100
        model_lower = self.model.lower()
        if "i9" in model_lower:
            self.relative_power = str(int(base_power * 1.5))
        elif "i7" in model_lower:
            self.relative_power = str(int(base_power * 1.2))
        elif "i5" in model_lower:
            self.relative_power = str(int(base_power * 1.1))
        else:
            self.relative_power = str(base_power)

    def save(self, *args, **kwargs):
        self.calculatePower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.model

class Motherboard(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    chipset = models.CharField(max_length=10)
    picture = models.ImageField(upload_to='motherboard_images/', blank=True, null=True)

    form_factor = models.CharField(max_length=10)
    socket = models.CharField(max_length=9)
    ram_slots = models.CharField()
    ram_type = models.CharField(max_length=9)
    nvme_slot = models.CharField(blank=True,null=True)
    sata_slot = models.CharField(blank=True,null=True)
    consumption = models.CharField()

    price = models.CharField()
    relative_power = models.CharField()

class RAM(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='ram_images/', blank=True, null=True)

    modules = models.CharField(blank=True,null=True)
    amount = models.CharField()
    typee = models.CharField(max_length=9)

    price = models.CharField()
    relative_power = models.CharField()

class Cooling(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    typee = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='cooling_images/', blank=True, null=True)

    socket = models.CharField(max_length=9)
    tdp = models.CharField()
    consumption = models.CharField()
    size = models.CharField()
    backlight = models.CharField(max_length=5, null=True)

    price = models.CharField()
    relative_power = models.CharField()

class PowerSupply(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='powersupply_images/', blank=True, null=True)

    power = models.CharField()

    price = models.CharField()
    relative_power = models.CharField()

class Storage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='storage_images/', blank=True, null=True)

    capacity = models.CharField()
    typee = models.CharField(max_length=4)

    price = models.CharField()

class Case(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='case_images/', blank=True, null=True)

    supported_form_factor = models.CharField(max_length=10)
    size = models.CharField()
    backlight = models.CharField(max_length=5, null=True)

    price = models.CharField()

class ParsedMotherboard(BaseComponent):
    form_factor = models.CharField(max_length=50)
    socket = models.CharField(max_length=50)
    ram_slots = models.CharField(max_length=50)
    ram_type = models.CharField(max_length=50)
    nvme_slot = models.CharField(max_length=50)
    sata_slot = models.CharField(max_length=50)


class ParsedRAM(BaseComponent):
    modules = models.CharField(max_length=50)
    amount = models.CharField(max_length=50)
    typee = models.CharField(max_length=50)


class ParsedCooling(BaseComponent):
    typee = models.CharField(max_length=50)
    socket = models.CharField(max_length=50)
    tdp = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    backlight = models.CharField(max_length=50)


class ParsedPowerSupply(BaseComponent):
    power = models.CharField(max_length=50)


class ParsedStorage(BaseComponent):
    capacity = models.CharField(max_length=50)
    typee = models.CharField(max_length=50)


class ParsedCase(BaseComponent):
    supported_form_factor = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    backlight = models.CharField(max_length=50)

