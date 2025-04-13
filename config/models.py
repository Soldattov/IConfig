from tkinter.constants import CASCADE

from django.db import models

class Project(models.Model):
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=20)
    time_creation = models.DateTimeField(auto_now_add=True)
    budget = models.IntegerField()
    description = models.CharField(max_length=500)

class GPU(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=15)
    typee = models.CharField(max_length=10)
    line = models.CharField(max_length=10)
    frequency = models.IntegerField()
    memory_amount = models.IntegerField()
    version = models.CharField(max_length=10)

    tdp = models.IntegerField()
    size = models.IntegerField()
    consumption = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

class CPU(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=6)
    line = models.CharField(max_length=10)
    family = models.CharField(max_length=3)
    generation = models.IntegerField()
    model = models.IntegerField()
    suffix = models.CharField(max_length=4)
    cores_amount = models.IntegerField()
    frequency = models.IntegerField()

    socket = models.CharField(max_length=9)
    tdp = models.IntegerField()
    consumption = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

class Motherboard(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=6)
    line = models.CharField(max_length=10)
    chipset = models.CharField(max_length=10)
    suffix = models.CharField(max_length=4)

    form_factor = models.CharField(max_length=10)
    socket = models.CharField(max_length=9)
    ram_slot = models.IntegerField()
    ram_type = models.CharField(max_length=9)
    nvme_slot = models.IntegerField()
    sata_slot = models.IntegerField()
    consumption = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

class RAM(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=6)
    line = models.CharField(max_length=10)

    moduls = models.IntegerField()
    amount = models.IntegerField()
    typee = models.CharField(max_length=9)

    price = models.IntegerField()
    relative_power = models.IntegerField()

class Cooling(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=6)
    typee = models.CharField(max_length=20)
    line = models.CharField(max_length=10)
    model = models.IntegerField()
    suffix = models.CharField(max_length=4)

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
    manufacturer = models.CharField(max_length=6)
    line = models.CharField(max_length=10)

    power = models.IntegerField()

    price = models.IntegerField()
    relative_power = models.IntegerField()

class Storage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=6)
    line = models.CharField(max_length=10)

    capacity = models.IntegerField()
    typee = models.CharField(max_length=4)

    price = models.IntegerField()

class Case(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    manufacturer = models.CharField(max_length=6)
    model = models.CharField(max_length=10)

    supported_form_factor = models.CharField(max_length=10)
    size = models.IntegerField()
    capacity = models.IntegerField()
    typee = models.CharField(max_length=4)

    price = models.IntegerField()
