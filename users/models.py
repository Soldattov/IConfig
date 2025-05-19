from django.contrib.auth.models import AbstractUser
from django.db import models
import random

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)  # Флаг, подтверждён ли email
    verification_code = models.CharField(max_length=6, blank=True, null=True)  # Хранит шестизначный код

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    def __str__(self):
        return self.first_name or self.email

    def generate_verification_code(self):
        """Генерирует и сохраняет случайный шестизначный код для подтверждения."""
        code = str(random.randint(100000, 999999))
        self.verification_code = code
        self.save()