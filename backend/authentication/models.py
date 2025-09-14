# authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model to include roles for business logic.
    """
    ROLE_CHOICES = (
        ('manager', 'Manager'),
        ('supervisor', 'Supervisor'),
        ('analyst', 'Analyst'),
    )
    # Add the role field with choices. It can be blank if a user doesn't have a specific role.
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)