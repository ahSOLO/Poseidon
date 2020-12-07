from django.contrib import admin
from .models import Template, TemplateSchema, TemplateSchemaEntry

# Register your models here.
class TemplateSchemaEntryAdmin(admin.StackedInline):
  model = TemplateSchemaEntry
  list_display = ['key', 'description']

class TemplateAdmin(admin.ModelAdmin):
  model = Template
  
class TemplateSchemaAdmin(admin.ModelAdmin):
  model = TemplateSchema
  inlines = [TemplateSchemaEntryAdmin]


admin.site.register(Template, TemplateAdmin)
admin.site.register(TemplateSchema, TemplateSchemaAdmin)