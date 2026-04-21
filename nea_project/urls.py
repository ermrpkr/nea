from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from nea_loss import admin_views

urlpatterns = [
    # ── Admin ──────────────────────────────────────────────
    path('admin/', admin.site.urls),
    
    # ── Admin Actions ────────────────────────────────────
    path('admin/nea_loss/distributioncenter/<int:pk>/change/', 
        nea_loss.admin_views.change_dc_start_month, name='admin:nea_loss_distributioncenter_change'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
