from django.urls import path
from . import views, monthly_views

app_name = 'admin_tools'

urlpatterns = [
    # Admin DC Report Creation
    path('dc-report/', views.admin_dc_report, name='admin_dc_report'),
    
    # Admin Monthly Data Override (for admin-created reports with editable readings)
    path('monthly-data/<int:report_pk>/<int:month>/', monthly_views.AdminMonthlyDataView.get, name='admin_monthly_data'),
]
