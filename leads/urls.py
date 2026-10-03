from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.lead_list, name='list'),
    path('pipeline/', views.lead_pipeline, name='pipeline'),
    path('add/', views.lead_create, name='create'),
    path('<int:pk>/', views.lead_detail, name='detail'),
    path('<int:pk>/edit/', views.lead_edit, name='edit'),
    path('<int:pk>/delete/', views.lead_delete, name='delete'),
    path('<int:pk>/convert/', views.lead_convert, name='convert'),
    path('<int:pk>/update-stage/', views.lead_update_stage, name='update_stage'),
]
