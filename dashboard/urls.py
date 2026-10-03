from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('search/', views.global_search, name='global_search'),
    path('quick-add/', views.quick_add, name='quick_add'),
]
