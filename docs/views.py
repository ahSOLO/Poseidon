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
    if request.method == 'GET':
        f = TemplateFilter(request.GET, queryset=Template.objects.filter(user=request.user)) #TO DO: add functionality to the filter list - either go to the template or have an option to delete it
    # Delete Template
    if request.method == 'POST':
        choice_form = TemplateChoiceDelete(request.POST, user=request.user)
        if choice_form.is_valid():
            choice_form.cleaned_data['name'].delete()
            return HttpResponseRedirect(reverse('docs:manage_templates'))
    else:
        choice_form = TemplateChoiceDelete(user=request.user)
    return render(request, 'docs/manage_templates.html', {'filter': f, 'choice_form': choice_form}) #TO DO: investigate error after deleting multiple files

# Manage Schemas (Forms)
def manage_schemas(request):
    if request.method== 'GET': # TO DO: Allow user to filter by template
        # selection_form = TemplateSelection(request.GET, user=request.user)
        selection_form2 = TemplateSchemaSelection(request.GET, user=request.user)
        selection_form3 = EntrySetSelection(request.GET, user=request.user)
        # Edit an existing schema
        if 'edit_schema' in request.GET:
            if selection_form2.is_valid():
                obj = selection_form2.cleaned_data.get('template_schema')
                return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj.pk]))
        # Edit an existing entryset
        if 'edit_entryset' in request.GET:
            if selection_form3.is_valid():
                obj2 = selection_form3.cleaned_data.get('entryset')
                schema = obj2.template_schema
                return HttpResponseRedirect(reverse('docs:edit_entryset', args=[schema.pk, obj2.pk]))
    if request.method == 'POST':
        # Create a new schema and edit it
        if 'create_schema' in request.POST:
            creation_form = TemplateSchemaForm(request.POST, user=request.user)
            if creation_form.is_valid():
                obj3 = creation_form.save(commit=False)
                obj3.user = request.user
                obj3.save()
                return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj3.pk]))
        # Populate an existing schema
        if 'pop_schema' in request.POST:
            populate_form = TemplateSchemaSelection(request.POST, user=request.user)
            if populate_form.is_valid():
                obj4 = populate_form.cleaned_data.get('template_schema')
                return HttpResponseRedirect(reverse('docs:pop_schema', args=[obj4.pk]))
    else:
        creation_form = TemplateSchemaForm(user=request.user)
        populate_form = TemplateSchemaSelection(user=request.user)
    return render(request, 'docs/manage_forms.html', {'selection_form2': selection_form2, 'selection_form3': selection_form3, 'creation_form': creation_form, 'populate_form': populate_form}) # removed selection_form

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
    return render(request, 'docs/edit_form.html', {'formset': formset})

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