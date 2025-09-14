# authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model.
    The 'role' field has been removed to use Django's built-in Group and Permission system.
    A custom permission 'view_analyst_list' has been added to control access to the analyst list view.
    """

    class Meta(AbstractUser.Meta):
        permissions = [
            ("view_analyst_list", "Can view list of analysts"),
        ]

    pass
