from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import FileResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.mixins import LoginRequiredMixin

import uuid
from io import BytesIO
from docxtpl import DocxTemplate

from .forms import ContactForm, TemplateForm, TemplateChoiceDelete, TemplateSchemaNameForm, TemplateSelection, TemplateSchemaSelection, TemplateSchemaEntryFormset, EntryFormset, EntrySetSelection
from .models import Template, TemplateSchema, TemplateSchemaEntry, EntrySet, Entry

# Create your views here.

# Home Page
class HomePageView(TemplateView):
    template_name = 'home.html'

# Getting Started Page
class GetStartedView(LoginRequiredMixin, TemplateView):
    template_name = 'get_started.html'
    login_url='login'

# Help Page
def help_view(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            reply_to = form.cleaned_data['reply_to']
            try:
                send_mail(subject, message + " \nREPLY EMAIL: " + reply_to, ['poseidondocshelp@gmail.com'], ['poseidondocuments@gmail.com'])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return HttpResponseRedirect(reverse('docs:home'))
    return render(request, "help.html", {'form': form})


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
        if 'upload_button' or 'create_schema_button' in request.POST:
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
    template_selection = None

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
        elif 'get_schema_link' in request.POST:
            schema_selection = TemplateSchemaSelection(request.POST, user=request.user)
            if schema_selection.is_valid():
                obj4 = schema_selection.cleaned_data.get('template_schema')
                return HttpResponseRedirect(reverse('docs:schema_link', args=[obj4.pk]))
    return render(request, 'docs/manage_forms.html', {'schema_selection': schema_selection, 'template_selection': template_selection, 'entryset_selection': entryset_selection, 'creation_form': creation_form})

def load_schemas(request):
    template_id = request.GET.get('template')
    options = TemplateSchema.objects.filter(template=template_id).order_by('name')
    return render(request, 'docs/dropdown_list_options.html', {'options': options})

def load_entryset(request):
    template_schema_id = request.GET.get('template_schema')
    options = EntrySet.objects.filter(template_schema=template_schema_id)
    return render(request, 'docs/dropdown_list_options.html', {'options': options})

# Create a Schema given a template id
def create_schema(request, template_id):
    template = Template.objects.get(pk=template_id)
    # Authorization check
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
    formset = None
    # Authorization check
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
    formset = None
    # Authorization check
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
                return FileResponse(byte_io, as_attachment=True, filename=f'Poseidon_{schema.name}.docx') #TO DO: Option to name the file
    return render(request, 'docs/pop_form.html', {'formset':formset, 'schema_entries': schema_entries, 'schema':schema })


# Anonymously populate a schema and create documents using a schema uuid link
def anon_pop_schema(request, schema_uuid):
    # To do: Show the name and description of the template that is being used to populate the form
    schema = TemplateSchema.objects.get(uuid=schema_uuid) # get schema object from ID
    formset = None
    schema_entries = TemplateSchemaEntry.objects.filter(template_schema__uuid=schema_uuid) #get list of schema entries from schema id
    # entryset = EntrySet.objects.create(template_schema=schema, user=request.user)
    # Display entryset's already existing values (if any) on the formset
    if request.method == 'GET':
        formset = EntryFormset(queryset=Entry.objects.none())
    if request.method == 'POST':
        formset = EntryFormset(request.POST)
        if formset.is_valid():
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
                return FileResponse(byte_io, as_attachment=True, filename=f'Poseidon_{schema.name}.docx') #TO DO: Option to name the file
    return render(request, 'docs/anon_pop_form.html', {'formset':formset, 'schema_entries': schema_entries, 'schema':schema })

def schema_link(request, schema_id):
    schema = TemplateSchema.objects.get(pk=schema_id) # get schema object from ID
    # Authorization check
    if schema.user != request.user:
        return HttpResponse('You are not authorized to view this page.', status=401)
    # Generate a new uuid and refresh the page
    if request.method == 'POST':
        schema.uuid = uuid.uuid4()
        schema.save()
        return HttpResponseRedirect(reverse('docs:schema_link', args=[schema_id])) 
    return render(request, 'docs/form_link.html', {'schema':schema})