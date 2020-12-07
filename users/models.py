from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
  # Fields
  first_name = models.CharField(max_length=50)
  last_name = models.CharField(max_length=50)
  organization = models.CharField(max_length=50, default="", blank=True)
  # created = models.DateTimeField(auto_now_add=True, editable=False)
  # last_updated = models.DateTimeField(auto_now=True, editable=False)

  def __str__(self):
    return str(self.username)
  