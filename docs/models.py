from django.db import models
from django.core.validators import FileExtensionValidator

from .utility import user_directory_path
from .constants import ENTRY_TYPES, SHORT, LONG, BOOL 

# Create your models here.
class Template(models.Model):
  # Relationships
  user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)

  # Fields
  name = models.CharField(max_length=50)
  description = models.TextField(max_length=250)
  docx_file = models.FileField(("DOCX File"), 
    upload_to=user_directory_path, 
    validators=[FileExtensionValidator(allowed_extensions=['docx'])])
  created = models.DateTimeField(auto_now_add=True, editable=False)
  last_updated = models.DateTimeField(auto_now=True, editable=False)

  def __str__(self):
    return self.name

class TemplateSchema(models.Model):
  # Relationships
  template = models.ForeignKey("docs.Template", null=True, on_delete=models.SET_NULL)
  user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)

  # Fields
  name = models.CharField(max_length=50)
  created = models.DateTimeField(auto_now_add=True, editable=False)
  last_updated = models.DateTimeField(auto_now=True, editable=False)

  def __str__(self):
    return self.name

class TemplateSchemaEntry(models.Model):
  # Relationships
  template_schema = models.ForeignKey("docs.TemplateSchema", on_delete=models.CASCADE)

  # Fields
  order = models.PositiveSmallIntegerField()
  key = models.CharField(max_length=50, unique=True)
  description = models.TextField(max_length=250)
  entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES, default=SHORT,)
  created = models.DateTimeField(auto_now_add=True, editable=False)
  last_updated = models.DateTimeField(auto_now=True, editable=False)

class EntrySet(models.Model):
  # Relationships
  template_schema = models.ForeignKey("docs.TemplateSchema", on_delete=models.CASCADE)
  user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)

  # Fields
  created = models.DateTimeField(auto_now_add=True, editable=False)
  last_updated = models.DateTimeField(auto_now=True, editable=False)

  def __str__(self):
    return "created: " + self.created + ", last updated: " + self.last_updated

class Entry(models.Model):
  # Relationships
  entryset = models.ForeignKey("docs.EntrySet", on_delete=models.CASCADE)
  schema_entry = models.ForeignKey("docs.TemplateSchemaEntry", on_delete=models.CASCADE)

  # Fields
  value_short = models.CharField(max_length=50, default="", blank=True)
  value_long = models.TextField(max_length=800, default="", blank=True)
  value_bool = models.BooleanField(default=False, blank=True)
  created = models.DateTimeField(auto_now_add=True, editable=False)
  last_updated = models.DateTimeField(auto_now=True, editable=False)

  def __str__(self):
    return value_short + value_long + str(value_bool)