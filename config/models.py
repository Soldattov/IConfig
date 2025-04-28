from tkinter.constants import CASCADE

from django.conf import settings
from django.db import models


class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=20)
    time_creation = models.DateTimeField(auto_now_add=True)
    budget = models.IntegerField()
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
    price = models.IntegerField()
    picture = models.ImageField(upload_to='components/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ParsedGPU(BaseComponent):
    frequency = models.IntegerField()
    memory_amount = models.IntegerField()
    tdp = models.IntegerField()
    size = models.IntegerField()
    consumption = models.IntegerField()
    relative_power = models.IntegerField()

    def calculatePower(self):
        base_power = 100
        match self.model:
            # отсчет идет от RTX 4060 согласно бенчмарку
            case model if "SUPER" in model:
                self.relative_power = int(base_power * 1.07)
            case model if "Ti" in model:
                self.relative_power = int(base_power * 1.05)
            case model if "XT" in model:
                self.relative_power = int(base_power * 1.07)
            case model if "XTX" in model:
                self.relative_power = int(base_power * 1.09)
            case model if "RX 6700" in model:
                self.relative_power = int(base_power * 0.97)
            case model if "RTX 2080" in model:
                self.relative_power = int(base_power * 0.95)
            case model if "RTX 3060" in model:
                self.relative_power = int(base_power * 0.865)
            case model if "RX 7600" in model:
                self.relative_power = int(base_power * 0.84)
            case model if "RTX 2070" in model:
                self.relative_power = int(base_power * 0.817)
            case model if "Arc B580" in model:
                self.relative_power = int(base_power * 0.793)
            case model if "GTX 1080" in model:
                self.relative_power = int(base_power * 0.79)
            case model if "RX 6600" in model:
                self.relative_power = int(base_power * 0.765)
            case model if "RTX 4050" in model:
                self.relative_power = int(base_power * 0.73)
            case model if "RX 5700" in model:
                self.relative_power = int(base_power * 0.727)
            case model if "RX 2060" in model:
                self.relative_power = int(base_power * 0.716)
            case model if "Arc B570" in model:
                self.relative_power = int(base_power * 0.697)
            case model if "GTX 1070" in model:
                self.relative_power = int(base_power * 0.684)
            case model if "Arc A770" in model:
                self.relative_power = int(base_power * 0.667)
            case model if "GTX 1660" in model:
                self.relative_power = int(base_power * 0.59)
            case _:
                self.relative_power = base_power

    def save(self, *args, **kwargs):
        self.calculatePower()
        super().save(*args, **kwargs)

class GPU(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=30)
    frequency = models.IntegerField()
    memory_amount = models.IntegerField()
    picture = models.ImageField(upload_to='gpu_images/', blank=True, null=True)

    tdp = models.IntegerField()
    size = models.IntegerField()
    consumption = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()


class ParsedCPU(models.Model):
    model = models.CharField(max_length=15)
    cores_amount = models.IntegerField()
    frequency = models.IntegerField()
    picture = models.ImageField(upload_to='parsed_cpu_images/', blank=True, null=True)
    socket = models.CharField(max_length=9)
    tdp = models.IntegerField()
    consumption = models.IntegerField()
    price = models.IntegerField()
    relative_power = models.IntegerField()

    def __str__(self):
        return self.model

class CPU(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=15)
    cores_amount = models.IntegerField()
    frequency = models.IntegerField()
    picture = models.ImageField(upload_to='cpu_images/', blank=True, null=True)

    socket = models.CharField(max_length=9)
    tdp = models.IntegerField()
    consumption = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

    def calculatePower(self):
        """
        Вычисляет relative_power на основе характеристик CPU.
        """
        base_power = 100

        if "i9" in self.model:
            self.relative_power = int(base_power * 1.5)
        elif "i7" in self.model:
            self.relative_power = int(base_power * 1.2)
        elif "i5" in self.model:
            self.relative_power = int(base_power * 1.1)
        else:
            self.relative_power = base_power

    def save(self, *args, **kwargs):
        self.calculatePower()
        super().save(*args, **kwargs)

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
    ram_slots = models.IntegerField()
    ram_type = models.CharField(max_length=9)
    nvme_slot = models.IntegerField(blank=True,null=True)
    sata_slot = models.IntegerField(blank=True,null=True)
    consumption = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

class RAM(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='ram_images/', blank=True, null=True)

    modules = models.IntegerField(blank=True,null=True)
    amount = models.IntegerField()
    typee = models.CharField(max_length=9)

    price = models.IntegerField()
    relative_power = models.IntegerField()

class Cooling(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    typee = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='cooling_images/', blank=True, null=True)

    socket = models.CharField(max_length=9)
    tdp = models.IntegerField()
    consumption = models.IntegerField()
    size = models.IntegerField()
    backlight = models.CharField(max_length=5, null=True)

    price = models.IntegerField()
    relative_power = models.IntegerField()

class PowerSupply(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='powersupply_images/', blank=True, null=True)

    power = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

class Storage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='storage_images/', blank=True, null=True)

    capacity = models.IntegerField()
    typee = models.CharField(max_length=4)

    price = models.IntegerField()

class Case(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='case_images/', blank=True, null=True)

    supported_form_factor = models.CharField(max_length=10)
    size = models.IntegerField()
    backlight = models.CharField(max_length=5, null=True)

    price = models.IntegerField()
