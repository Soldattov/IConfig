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
    budget = models.CharField(max_length=20)
    description = models.CharField(max_length=500)

    def add_component(self, component):
        component_type = None
        """Добавляет компонент в проект"""
        if isinstance(component, ParsedGPU):
            component_type = 'gpu'
        elif isinstance(component, ParsedCPU):
            component_type = 'cpu'
        elif isinstance(component, ParsedMotherboard):
            component_type = 'motherboard'
        elif isinstance(component, ParsedRAM):
            component_type = 'ram'
        elif isinstance(component, ParsedCooling):
            component_type = 'cooling'
        elif isinstance(component, ParsedPowerSupply):
            component_type = 'psu'
        elif isinstance(component, ParsedStorage):
            component_type = 'storage'
        elif isinstance(component, ParsedCase):
            component_type = 'case'

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
            elif pc.component_type == 'motherboard':
                components.append(ParsedMotherboard.objects.get(id=pc.component_id))
            elif pc.component_type == 'ram':
                components.append(ParsedRAM.objects.get(id=pc.component_id))
            elif pc.component_type == 'cooling':
                components.append(ParsedCooling.objects.get(id=pc.component_id))
            elif pc.component_type == 'psu':
                components.append(ParsedPowerSupply.objects.get(id=pc.component_id))
            elif pc.component_type == 'storage':
                components.append(ParsedStorage.objects.get(id=pc.component_id))
            elif pc.component_type == 'case':
                components.append(ParsedCase.objects.get(id=pc.component_id))
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


class ParsedCPU(BaseComponent):
    cores_amount = models.CharField(max_length=10)
    frequency = models.CharField(max_length=10)
    socket = models.CharField(max_length=9)
    tdp = models.CharField(max_length=10)
    relative_power = models.CharField(max_length=10)

    def save(self, *args, **kwargs):
        calculator.calculateCPUPower(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.model


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

