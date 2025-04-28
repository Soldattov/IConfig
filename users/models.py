from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'      
    REQUIRED_FIELDS = ['first_name']

    def __str__(self):
        return self.first_name or self.email