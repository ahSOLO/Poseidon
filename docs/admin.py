from django.contrib import admin
from .models import Template, TemplateSchema, TemplateSchemaEntry, EntrySet, Entry

# Register your models here.
class TemplateSchemaEntryAdmin(admin.StackedInline):
  model = TemplateSchemaEntry
  list_display = ['key', 'description']

class TemplateAdmin(admin.ModelAdmin):
  model = Template
  
class TemplateSchemaAdmin(admin.ModelAdmin):
  model = TemplateSchema
  inlines = [TemplateSchemaEntryAdmin]

class EntryAdmin(admin.StackedInline):
  model = Entry
  list_display = ['value_short', 'value_long', 'value_bool']

class EntrySetAdmin(admin.ModelAdmin):
  model = EntrySet
  inlines = [EntryAdmin]

admin.site.register(Template, TemplateAdmin)
admin.site.register(TemplateSchema, TemplateSchemaAdmin)
admin.site.register(EntrySet, EntrySetAdmin)