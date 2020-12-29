import django_filters

from django import forms

from .models import Template, TemplateSchema, TemplateSchemaEntry, EntrySet, Entry
from .utility import file_size
from .constants import ENTRY_TYPES, SHORT, LONG, BOOL

# Template upload form
class TemplateForm(forms.ModelForm):
  name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Please name your template'}))
  description = forms.CharField(max_length=250, required=False, widget=forms.Textarea(attrs={'placeholder': 'Please describe the contents of your template'}))
  docx_file = forms.FileField(label="Select a file", help_text="Max. 5 megabytes", validators=[file_size])

  class Meta:
    model = Template
    fields = ['name', 'description', 'docx_file']

# Template delete form based on multiple choices
class TemplateChoiceDelete(forms.Form):
  name = forms.ModelMultipleChoiceField(queryset=Template.objects.all())

  # Limit results to templates owned by the current user
  def __init__(self, *args, **kwargs):
      user = kwargs.pop('user')
      super(TemplateChoiceDelete, self).__init__(*args, **kwargs)
      self.fields['name'].queryset = Template.objects.filter(user=user)

# TemplateSchema form
# class TemplateSchemaForm(forms.ModelForm):
#   template = forms.ModelChoiceField(queryset=Template.objects.all())
#   name = forms.CharField(max_length=50)

#   class Meta:
#     model = TemplateSchema
#     fields = ['template', 'name']

#   # Limit results to Templates owned by the current user
#   def __init__(self, *args, **kwargs):
#       user = kwargs.pop('user')
#       super(TemplateSchemaForm, self).__init__(*args, **kwargs)
#       self.fields['template'].queryset = Template.objects.filter(user=user)

# TemplateSchema name form
class TemplateSchemaNameForm(forms.ModelForm):
  name = forms.CharField(max_length=50)

  class Meta:
    model = TemplateSchema
    fields = ['name']

# Template selection form
class TemplateSelection(forms.Form):
  template = forms.ModelChoiceField(queryset=Template.objects.all())

  # Limit results to TemplateSchema owned by the current user
  def __init__(self, *args, **kwargs):
      user = kwargs.pop('user')
      super(TemplateSelection, self).__init__(*args, **kwargs)
      self.fields['template'].queryset = Template.objects.filter(user=user)

# TemplateSchema selection form
class TemplateSchemaSelection(forms.Form):
  template_schema = forms.ModelChoiceField(label="Template Form", queryset=TemplateSchema.objects.all())

  # Limit results to TemplateSchema owned by the current user
  def __init__(self, *args, **kwargs):
      user = kwargs.pop('user')
      super(TemplateSchemaSelection, self).__init__(*args, **kwargs)
      self.fields['template_schema'].queryset = TemplateSchema.objects.filter(user=user)

# TemplateSchemaEntry form
class TemplateSchemaEntryForm(forms.ModelForm):
  template_schema = forms.ModelChoiceField(queryset=TemplateSchema.objects.all())
  key = forms.CharField(max_length=50)
  description = forms.CharField(max_length=250, widget=forms.Textarea)
  entry_type = forms.ChoiceField(choices=ENTRY_TYPES, initial=SHORT)

  class Meta:
    model = TemplateSchemaEntry
    fields = ['template_schema', 'key', 'description', 'entry_type']

  # Limit results to TemplateSchema owned by the current user
  def __init__(self, *args, **kwargs):
      user = kwargs.pop('user')
      super(TemplateSchemaEntryForm, self).__init__(*args, **kwargs)
      self.fields['template_schema'].queryset = TemplateSchemaEntry.objects.filter(user=user)

# TemplateSchemaEntry formset
TemplateSchemaEntryFormset = forms.modelformset_factory(
  TemplateSchemaEntry,
  fields=('key', 'description', 'entry_type'),
  widgets={'key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Variable Name'}),
  'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your variable in the form of a prompt', 'style': 'height: 5em;'})
  },
)

# EntrySet selection form
class EntrySetSelection(forms.Form):
  entryset = forms.ModelChoiceField(queryset=EntrySet.objects.all())

  # Limit results to EntrySet owned by the current user
  def __init__(self, *args, **kwargs):
      user = kwargs.pop('user')
      super(EntrySetSelection, self).__init__(*args, **kwargs)
      self.fields['entryset'].queryset = EntrySet.objects.filter(user=user)

# Entry form
class EntryForm(forms.ModelForm):
  value_short = forms.CharField(max_length=50)
  value_long = forms.CharField(max_length=800)
  value_bool = forms.BooleanField(initial=False)

  class Meta:
    model = Entry
    fields = ['value_short', 'value_long', 'value_bool',]

# TemplateSchemaEntry formset
EntryFormset = forms.modelformset_factory(
  Entry,
  fields=('value_short', 'value_long', 'value_bool'),
  widgets={'value_short': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Value'}),
  'value_long': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Value', 'style': 'height: 5em;'}),
  'value_bool': forms.CheckboxInput(attrs={'class': 'form-control',}),
  },
  extra=200 # TO DO: find a more efficient way of having a dynamic formset size
)

# Contact Form
class ContactForm(forms.Form):
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
    reply_to = forms.EmailField(required=True)

# FILTERS

# Template filter for deletion screen.
# class TemplateFilter(django_filters.FilterSet):
#   name = django_filters.CharFilter(lookup_expr='icontains')
#   description = django_filters.CharFilter(lookup_expr='icontains')

#   class Meta:
#     model = Template
#     fields = ['name', 'description']

  # Alternative Code: Limit filter results to templates owned by the current user.
  # @property
  # def qs(self):
  #     parent = super().qs
  #     user = getattr(self.request, 'user', None)
  #     return parent.filter(user=user)