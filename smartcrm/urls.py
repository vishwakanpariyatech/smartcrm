from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.root_redirect, name='root'),

    # Modular CRM App Routes
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('customers/', include('customers.urls')),
    path('leads/', include('leads.urls')),
    path('sales/', include('sales.urls')),
    path('tasks/', include('tasks.urls')),
    path('followups/', include('followups.urls')),
    path('employees/', include('employees.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
    path('activity-logs/', include('activity_logs.urls')),
]

# Static & Media file handling in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom Error Handlers
handler403 = 'smartcrm.views.error_403'
handler404 = 'smartcrm.views.error_404'
handler500 = 'smartcrm.views.error_500'
