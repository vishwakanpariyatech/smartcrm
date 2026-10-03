from django.urls import path
from . import views

app_name = 'followups'

urlpatterns = [
    path('', views.followup_list, name='list'),
    path('calendar/', views.followup_calendar, name='calendar'),
    path('add/', views.followup_create, name='create'),
    path('<int:pk>/edit/', views.followup_edit, name='edit'),
    path('<int:pk>/complete/', views.followup_complete, name='complete'),
    path('<int:pk>/delete/', views.followup_delete, name='delete'),
]
