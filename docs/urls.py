from django.urls import path

from . import views

app_name = 'docs'
urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('upload/', views.upload_template, name='upload'),
    path('manage_templates/', views.manage_templates, name='manage_templates'),
    path('manage_forms/', views.manage_schemas, name='manage_schemas'),
    path('create_form/<template_id>', views.create_schema, name='create_schema'),
    path('edit_form/<schema_id>', views.edit_schema, name='edit_schema'),
    path('pop_form/<schema_id>/<entryset_id>', views.pop_schema, name='edit_entryset'),
    path('pop_form/<schema_id>/', views.pop_schema, name='pop_schema'),
    path('ajax/load-schemas/', views.load_schemas, name='ajax-load-schemas'),
]
