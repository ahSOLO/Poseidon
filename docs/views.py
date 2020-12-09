from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import FileResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse

from io import BytesIO
from docxtpl import DocxTemplate

from .forms import TemplateForm, TemplateFilter, TemplateChoiceDelete, TemplateSchemaForm, TemplateSelection, TemplateSchemaSelection, TemplateSchemaEntryFormset, EntryFormset
from .models import Template, TemplateSchema, TemplateSchemaEntry, EntrySet, Entry

# Create your views here.
class HomePageView(TemplateView):
  template_name = 'home.html'

def upload_template(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return HttpResponseRedirect('success/')
    else:
        form = TemplateForm #displays an empty form
    return render(request, 'docs/upload.html', {'form': form})

def manage_templates(request):
    if request.method == 'GET':
        f = TemplateFilter(request.GET, queryset=Template.objects.filter(user=request.user)) #TO DO: add functionality to the filter list - either go to the template or have an option to delete it
    if request.method == 'POST':
        choice_form = TemplateChoiceDelete(request.POST, user=request.user)
        if choice_form.is_valid():
            choice_form.cleaned_data['name'].delete()
    else:
        choice_form = TemplateChoiceDelete(user=request.user)
    return render(request, 'docs/manage_templates.html', {'filter': f, 'choice_form': choice_form})

def manage_schemas(request):
    if request.method== 'GET': # TO DO: Allow user to filter by template
        # selection_form = TemplateSelection(request.GET, user=request.user)
        selection_form2 = TemplateSchemaSelection(request.GET, user=request.user)
        if selection_form2.is_valid():
            obj2 = selection_form2.cleaned_data.get('template_schema')
            return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj2.pk]))
    if request.method == 'POST':
        if 'create_form' in request.POST:
            creation_form = TemplateSchemaForm(request.POST, user=request.user)
            if creation_form.is_valid():
                obj = creation_form.save(commit=False)
                obj.user = request.user
                obj.save()
                return HttpResponseRedirect(reverse('docs:edit_schema', args=[obj.pk]))
        if 'pop_form' in request.POST:
            populate_form = TemplateSchemaSelection(request.POST, user=request.user)
            if populate_form.is_valid():
                obj3 = populate_form.cleaned_data.get('template_schema')
                return HttpResponseRedirect(reverse('docs:pop_schema', args=[obj3.pk]))
    else:
        creation_form = TemplateSchemaForm(user=request.user)
        populate_form = TemplateSchemaSelection(user=request.user)
    return render(request, 'docs/manage_forms.html', {'selection_form2': selection_form2, 'creation_form': creation_form, 'populate_form': populate_form}) # removed selection_form

def edit_schema(request, schema_id):
    schema = TemplateSchema.objects.get(pk=schema_id)
    if schema.user != request.user:
        return HttpResponse('You are not authorized to view this page.', status=401)
    if request.method == 'GET':
        formset = TemplateSchemaEntryFormset(queryset=TemplateSchemaEntry.objects.filter(template_schema=schema))
    elif request.method == 'POST':
        formset = TemplateSchemaEntryFormset(request.POST, queryset=TemplateSchemaEntry.objects.filter(template_schema=schema))
        if formset.is_valid():
            old_obj = TemplateSchemaEntry.objects.filter(template_schema=schema)
            old_obj.delete()
            counter = 1
            for form in formset:
                if form.cleaned_data.get('key'):
                    obj = form.save(commit=False)
                    obj.template_schema = TemplateSchema.objects.get(pk=schema_id)
                    obj.order = counter
                    counter += 1
                    obj.save()
            return HttpResponseRedirect('success/')
    return render(request, 'docs/edit_form.html', {'formset': formset})

def pop_schema(request, schema_id, entryset_id=""):
    schema = TemplateSchema.objects.get(pk=schema_id)
    schema_entries = TemplateSchemaEntry.objects.filter(template_schema=schema_id)
    if (entryset_id != ""):
        entryset = EntrySet.objects.get(pk=entryset_id)
    else: 
        entryset = EntrySet.objects.create(template_schema=schema, user=request.user)
    if schema.user != request.user:
        return HttpResponse('You are not authorized to view this page.', status=401)
    if request.method == 'GET':
        formset = EntryFormset(queryset=Entry.objects.filter(entryset=entryset))
    if request.method == 'POST':
        formset = EntryFormset(request.POST, queryset=Entry.objects.filter(entryset=entryset))
        if formset.is_valid():
            if 'save_entries' in request.POST:
                old_obj = Entry.objects.filter(entryset=entryset)
                old_obj.delete()
                for form, schema_entry in zip(formset, schema_entries):
                    if form.cleaned_data.get('value_short') or form.cleaned_data.get('value_long') or form.cleaned_data.get('value_bool'):
                        obj = form.save(commit=False)
                        obj.entryset_id = entryset.id
                        obj.schema_entry_id = schema_entry.id
                        obj.save()
                    return HttpResponseRedirect('')
            if 'create_doc' in request.POST:
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
                tpl = DocxTemplate(Template.objects.get(templateschema = schema).docx_file)
                byte_io = BytesIO() #create a file-like object
                tpl.render(dic)
                tpl.save(byte_io) #save data to a file-like object
                byte_io.seek(0) #go to the beginning of a file-like object
                return FileResponse(byte_io, as_attachment=True, filename=f'generated.docx')
    return render(request, 'docs/pop_form.html', {'formset':formset, 'schema_entries': schema_entries})