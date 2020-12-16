from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import FileResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse

from io import BytesIO
from docxtpl import DocxTemplate

from .forms import TemplateForm, TemplateFilter, TemplateChoiceDelete, TemplateSchemaForm, TemplateSchemaNameForm, TemplateSelection, TemplateSchemaSelection, TemplateSchemaEntryFormset, EntryFormset, EntrySetSelection
from .models import Template, TemplateSchema, TemplateSchemaEntry, EntrySet, Entry

# Create your views here.

# Home Page
class HomePageView(TemplateView):
  template_name = 'home.html'

# Upload Template - receives docx file
def upload_template(request):
    # To Do: Show helper text that explains what the description is going to be used for
    if request.method == 'POST':
        form = TemplateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            if 'upload_button' in request.POST:
                return HttpResponseRedirect(reverse('docs:manage_templates'))
            if 'create_schema_button' in request.POST:
                return HttpResponseRedirect(reverse('docs:create_schema', args=[obj.pk]))
    else:
        form = TemplateForm #displays an empty form
    return render(request, 'docs/upload.html', {'form': form})

# Manage templates 
def manage_templates(request):
    # Search for Template
    # if request.method == 'GET':
    #     f = TemplateFilter(request.GET, queryset=Template.objects.filter(user=request.user)) #TO DO: add functionality to the filter list - either go to the template or have an option to delete it
    if request.method == 'POST':
        # Upload Template
        if ('upload_button' or 'create_schema_button') in request.POST:
            upload_form = TemplateForm(request.POST, request.FILES)
            if upload_form.is_valid():
                obj = upload_form.save(commit=False)
                obj.user = request.user
                obj.save()
                if 'upload_button' in request.POST:
                    return HttpResponseRedirect(reverse('docs:manage_templates'))
                if 'create_schema_button' in request.POST:
                    return HttpResponseRedirect(reverse('docs:create_schema', args=[obj.pk]))
        else:
            upload_form = TemplateForm()
        # Delete Template
        if 'delete_template' in request.POST:
            delete_form = TemplateChoiceDelete(request.POST, user=request.user)
            if delete_form.is_valid():
                delete_form.cleaned_data['name'].delete()
                return HttpResponseRedirect(reverse('docs:manage_templates'))
        else:
            delete_form = TemplateChoiceDelete(user=request.user)
    else:
        upload_form = TemplateForm()
        delete_form = TemplateChoiceDelete(user=request.user)
    return render(request, 'docs/manage_templates.html', {'upload_form': upload_form, 'delete_form': delete_form})

# Manage Schemas (Forms)
def manage_schemas(request):
    schema_selection = TemplateSchemaSelection(user=request.user)
    entryset_selection = EntrySetSelection(user=request.user)
    creation_form = TemplateSchemaNameForm()

    if request.method== 'GET': 
        template_selection = TemplateSelection(request.GET, user=request.user)
        # Edit an existing entryset
        if 'edit_entryset' in request.GET:
            entryset_selection = EntrySetSelection(request.GET, user=request.user)
            if entryset_selection.is_valid():
                obj2 = entryset_selection.cleaned_data.get('entryset')
                schema = obj2.template_schema
                return HttpResponseRedirect(reverse('docs:edit_entryset', args=[schema.pk, obj2.pk]))

    if request.method == 'POST':
        template_selection = TemplateSelection(request.POST, user=request.user)
        # Create a new schema and edit it
        if 'create_schema' in request.POST:
            creation_form = TemplateSchemaNameForm(request.POST)
            if creation_form.is_valid() and template_selection.is_valid():
                obj3 = creation_form.save(commit=False)
                obj3.template = template_selection.cleaned_data.get('template')
                obj3.user = request.user
                obj3.save()
                return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj3.pk]))
        # Edit an existing schema
        if 'edit_schema' in request.POST:
            schema_selection = TemplateSchemaSelection(request.POST, user=request.user)
            if schema_selection.is_valid():
                obj = schema_selection.cleaned_data.get('template_schema')
                return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj.pk]))
        # Populate an existing schema
        elif 'pop_schema' in request.POST:
            schema_selection = TemplateSchemaSelection(request.POST, user=request.user)
            if schema_selection.is_valid():
                obj4 = schema_selection.cleaned_data.get('template_schema')
                return HttpResponseRedirect(reverse('docs:pop_schema', args=[obj4.pk]))
    return render(request, 'docs/manage_forms.html', {'schema_selection': schema_selection, 'template_selection': template_selection, 'entryset_selection': entryset_selection, 'creation_form': creation_form})

def load_schemas(request):
    template_id = request.GET.get('template')
    schemas = TemplateSchema.objects.filter(template=template_id).order_by('name')
    return render(request, 'docs/schema_dropdown_list_options.html', {'schemas': schemas})

# Create a Schema given a template id
def create_schema(request, template_id):
    template = Template.objects.get(pk=template_id)
    # Authentication check
    if template.user != request.user:
        return HttpResponse('You are not authorized to view this page.', status=401)
    if request.method == 'POST':
        form = TemplateSchemaNameForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.template = template
            obj.save()
            return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj.pk]))
    else:
        form = TemplateSchemaNameForm
    return render(request, 'docs/create_form.html', {'form': form} )
    
# Create Schema Entries / edit a Schema
def edit_schema(request, schema_id):
    schema = TemplateSchema.objects.get(pk=schema_id)
    template = Template.objects.get(templateschema__id=schema_id)
    # Authentication check
    if schema.user != request.user:
        return HttpResponse('You are not authorized to view this page.', status=401)
    # Upon GET request, show existing schema entries
    if request.method == 'GET':
        formset = TemplateSchemaEntryFormset(queryset=TemplateSchemaEntry.objects.filter(template_schema=schema))
    # Upon POST request, create / update entries
    elif request.method == 'POST':
        formset = TemplateSchemaEntryFormset(request.POST, queryset=TemplateSchemaEntry.objects.filter(template_schema=schema))
        if formset.is_valid():
            # Select existing entries and delete them
            old_obj = TemplateSchemaEntry.objects.filter(template_schema=schema)
            old_obj.delete()
            # Save new entries if they have a 'key' value
            counter = 1
            for form in formset:
                if form.cleaned_data.get('key'):
                    obj = form.save(commit=False)
                    obj.template_schema = TemplateSchema.objects.get(pk=schema_id)
                    obj.order = counter
                    counter += 1
                    obj.save()
            if "save_button" in request.POST:
                return HttpResponseRedirect(reverse('docs:manage_schemas'))
            if "save_pop_button" in request.POST:
                return HttpResponseRedirect(reverse('docs:pop_schema', args=[schema_id]))
    return render(request, 'docs/edit_form.html', {'formset': formset, 'schema': schema, 'template': template})

# Populate a schema and create documents
def pop_schema(request, schema_id, entryset_id=""): # entryset_id is an optional parameter
    # To do: Show the name and description of the template that is being used to populate the form
    schema = TemplateSchema.objects.get(pk=schema_id) # get schema object from ID
    # Authentication check
    if schema.user != request.user:
        return HttpResponse('You are not authorized to view this page.', status=401)
    schema_entries = TemplateSchemaEntry.objects.filter(template_schema=schema_id) #get list of schema entries from schema id
    # If modifying existing entryset, assign the object to 'entryset' variable. Otherwise, create a new entryset and assign it to 'entryset' variable. 
    if (entryset_id != ""):
        entryset = EntrySet.objects.get(pk=entryset_id)
    else: 
        entryset = EntrySet.objects.create(template_schema=schema, user=request.user)
    # Display entryset's already existing values (if any) on the formset
    if request.method == 'GET':
        formset = EntryFormset(queryset=Entry.objects.filter(entryset=entryset))
    if request.method == 'POST':
        formset = EntryFormset(request.POST, queryset=Entry.objects.filter(entryset=entryset))
        if formset.is_valid():
            # Save Entries button pressed: delete existing entries under the entryset and replace them with new values
            if 'save_entries' in request.POST:
                old_obj = Entry.objects.filter(entryset=entryset)
                old_obj.delete()
                for form, schema_entry in zip(formset, schema_entries):
                    if form.cleaned_data.get('value_short') or form.cleaned_data.get('value_long') or form.cleaned_data.get('value_bool'):
                        obj = form.save(commit=False)
                        obj.entryset_id = entryset.id
                        obj.schema_entry_id = schema_entry.id
                        obj.save()
                return HttpResponseRedirect(reverse('docs:edit_entryset', args=[schema_id, entryset.id]))
            # Create Document button pressed: 
            if 'create_doc' in request.POST:
                # create a dictionary object with keys from schema entries and values from entryset entries
                dic = {}
                for form, schema_entry in zip(formset, schema_entries):
                    value_short = form.cleaned_data.get('value_short')
                    value_long = form.cleaned_data.get('value_long')
                    value_bool = form.cleaned_data.get('value_bool')
                    if value_short:
                        value = value_short
                    elif value_long:
                        value = value_long
                    elif value_bool:
                        value = value_bool
                    else: 
                        continue
                    dic[schema_entry.key] = value
                # Render the docx file using the created dictionary
                tpl = DocxTemplate(Template.objects.get(templateschema = schema).docx_file)
                byte_io = BytesIO() #create a file-like object
                tpl.render(dic)
                tpl.save(byte_io) #save data to a file-like object
                byte_io.seek(0) #go to the beginning of a file-like object
                return FileResponse(byte_io, as_attachment=True, filename=f'generated.docx') #TO DO: Option to name the file
    return render(request, 'docs/pop_form.html', {'formset':formset, 'schema_entries': schema_entries})