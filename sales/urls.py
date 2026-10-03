from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.deal_list, name='list'),
    path('add/', views.deal_create, name='create'),
    path('<int:pk>/', views.deal_detail, name='detail'),
    path('<int:pk>/edit/', views.deal_edit, name='edit'),
    path('<int:pk>/delete/', views.deal_delete, name='delete'),
    path('<int:pk>/mark-stage/', views.deal_mark_stage, name='mark_stage'),
    path('<int:pk>/invoice-pdf/', views.deal_invoice_pdf, name='invoice_pdf'),
]
