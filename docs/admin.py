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
  list_display = ['name', 'uuid']
  inlines = [TemplateSchemaEntryAdmin]

class EntryAdmin(admin.StackedInline):
  model = Entry
  list_display = ['value_short', 'value_long', 'value_bool']
  # Only display schema entries that correspond to the correct template schema
  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    field = super(EntryAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    if db_field.name == 'schema_entry':
      if request._obj_ is not None:
        field.queryset = field.queryset.filter(template_schema = request._obj_.template_schema)  
      else:
        field.queryset = field.queryset.none()
    return field

class EntrySetAdmin(admin.ModelAdmin):
  model = EntrySet
  inlines = [EntryAdmin]
  # Save obj reference for processing in Inline
  def get_form(self, request, obj=None, **kwargs):
    request._obj_ = obj
    return super(EntrySetAdmin, self).get_form(request, obj, **kwargs)

admin.site.register(Template, TemplateAdmin)
admin.site.register(TemplateSchema, TemplateSchemaAdmin)
admin.site.register(EntrySet, EntrySetAdmin)