from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home_redirect, name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # DC Loss Reports
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/edit/', views.ReportEditView.as_view(), name='report_edit'),
    path('reports/<int:pk>/submit/', views.report_submit, name='report_submit'),
    path('reports/<int:pk>/delete/', views.report_delete, name='report_delete'),
    path('reports/<int:pk>/approve/', views.report_approve, name='report_approve'),
    path('reports/<int:pk>/reject/', views.report_reject, name='report_reject'),
    path('reports/<int:pk>/print/', views.ReportPrintView.as_view(), name='report_print'),
    path('reports/<int:pk>/export-excel/', views.report_export_excel, name='report_export_excel'),

    # Monthly Data Entry
    path('reports/<int:report_pk>/months/<int:month>/', views.MonthlyDataView.as_view(), name='monthly_data'),
    path('reports/<int:report_pk>/months/<int:month>/delete/', views.monthly_data_delete, name='monthly_data_delete'),

    # Provincial Reports
    path('reports/provincial/', views.ProvincialReportListView.as_view(), name='provincial_report_list'),
    path('reports/provincial/dc-reports/', views.ProvincialDCReportsView.as_view(), name='provincial_dc_reports'),
    path('reports/provincial/create/', views.ProvincialReportCreateView.as_view(), name='provincial_report_create'),
    path('reports/provincial/print/', views.ProvincialReportPrintView.as_view(), name='provincial_report_print'),
    path('reports/provincial/<int:pk>/', views.ProvincialReportDetailView.as_view(), name='provincial_report_detail'),
    path('reports/provincial/<int:pk>/excel/', views.ProvincialReportDetailView.as_view(), name='provincial_report_excel'),

    # Organization Management
    path('organizations/', views.OrgOverviewView.as_view(), name='org_overview'),
    path('organizations/dc/<int:pk>/', views.DCDetailView.as_view(), name='dc_detail'),

    # DC Yearly Targets
    path('targets/dc-yearly/', views.DCYearlyTargetView.as_view(), name='dc_yearly_targets'),

    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('analytics/comparison/', views.ComparisonView.as_view(), name='comparison'),

    # User Management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),

    # Messaging
    path('messages/', views.MessageInboxView.as_view(), name='message_inbox'),
    path('messages/compose/', views.MessageComposeView.as_view(), name='message_compose'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),
    path('messages/<int:pk>/reply/', views.message_reply, name='message_reply'),
    path('api/messages/unread/', views.api_unread_messages, name='api_unread_messages'),

    # API endpoints
    path('api/dashboard-chart-data/', views.api_dashboard_chart, name='api_dashboard_chart'),
    path('api/loss-summary/', views.api_loss_summary, name='api_loss_summary'),
    path('api/notifications/mark-read/', views.api_mark_notifications_read, name='api_mark_read'),
    path('api/monthly-data/create/', views.api_create_monthly_data, name='api_create_monthly_data'),
    path('api/meter-readings/save/', views.api_save_meter_readings, name='api_save_readings'),
    path('api/meter-points/manage/', views.api_manage_meter_point, name='api_manage_meter_point'),
    path('api/consumer-categories/manage/', views.api_manage_consumer_category, name='api_manage_consumer_category'),
    path('api/meter-readings/delete-month/', views.api_delete_meter_reading_for_month, name='api_delete_meter_reading_for_month'),
    path('api/meter-points/disable-month/', views.api_disable_meter_point_for_month, name='api_disable_meter_point_for_month'),
    path('api/consumer-data/save/', views.api_save_consumer_data, name='api_save_consumer'),
    path('api/recalculate/<int:report_pk>/', views.api_recalculate, name='api_recalculate'),
]