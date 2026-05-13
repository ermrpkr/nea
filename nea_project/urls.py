from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main application
    path('', include('nea_loss.urls')),
    
    # Admin actions handled by admin.site.urls
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
