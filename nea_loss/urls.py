from django.urls import path, re_path, include
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
    path('reports/<int:pk>/review/', views.ReportReviewView.as_view(), name='report_review'),
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
    path('reports/provincial/<int:pk>/review/', views.ProvincialReportReviewView.as_view(), name='provincial_report_review'),
    path('reports/provincial/<int:pk>/excel/', views.provincial_report_excel_export, name='provincial_report_excel'),
    path('reports/provincial/approved/', views.ProvincialApprovedReportsView.as_view(), name='provincial_approved_reports'),
    
    # Province Reports (Approved)
    path('reports/province-approved/', views.ProvinceReportsApprovedView.as_view(), name='province_reports_approved'),
    path('reports/province-approved/review/', views.ProvinceReportsReviewView.as_view(), name='province_reports_review'),
    
    # DMD Approval System
    path('approvals/dmd/', views.DMDApprovalDashboardView.as_view(), name='dmd_approval_dashboard'),
    path('approvals/dmd/<int:pk>/approve/', views.dmd_approve_provincial_report, name='dmd_approve_provincial_report'),
    path('approvals/dmd/<int:pk>/reject/', views.dmd_reject_provincial_report, name='dmd_reject_provincial_report'),
    path('reports/dmd/create/', views.DMDCreateReportView.as_view(), name='dmd_create_report'),
    path('reports/dmd/create/print/', views.DMDCreateReportPrintView.as_view(), name='dmd_create_report_print'),

    # DCS Monthly Reports
    path('reports/dcs-monthly/create/', views.DCSMonthlyReportCreateView.as_view(), name='dcs_monthly_report_create'),

    # Organization Management
    path('organizations/', views.OrgOverviewView.as_view(), name='org_overview'),
    path('organizations/dc/<int:pk>/', views.DCDetailView.as_view(), name='dc_detail'),

    # DC Yearly Targets
    path('targets/dc-yearly/', views.DCYearlyTargetView.as_view(), name='dc_yearly_targets'),

    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('analytics/comparison/', views.ComparisonView.as_view(), name='comparison'),
    path('analytics/managerial/', views.ManagerialAnalyticsView.as_view(), name='managerial_analytics'),

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
    path('api/dc-feeders/', views.api_dc_feeders, name='api_dc_feeders'),

    # DC Report Override Management
    path('overrides/request/', views.OverrideRequestView.as_view(), name='override_request'),
    path('overrides/manage/', views.OverrideManagementView.as_view(), name='override_manage'),

    # Feeder Management
    path('feeders/', views.FeederListView.as_view(), name='feeder_list'),
    path('feeders/request/', views.FeederRequestView.as_view(), name='feeder_request'),
    path('feeders/management/', views.FeederManagementView.as_view(), name='feeder_management'),
    path('feeders/requests/', views.FeederRequestsView.as_view(), name='feeder_requests'),
    path('feeders/requests/<int:pk>/approve/', views.feeder_request_approve, name='feeder_request_approve'),
    path('feeders/requests/<int:pk>/reject/', views.feeder_request_reject, name='feeder_request_reject'),

    # DCS Detail
    path('dcs-detail/<int:dc_id>/', views.DCSDetailView.as_view(), name='dcs_detail'),
    path('dcs-detail/<int:dc_id>/edit/', views.DCSDetailEditView.as_view(), name='dcs_detail_edit'),
    path('dcs-detail/approval/', views.DCSDetailApprovalView.as_view(), name='dcs_detail_approval'),
    path('dcs-detail/approval/<int:pk>/approve/', views.dcs_detail_approve, name='dcs_detail_approve'),
    path('dcs-detail/approval/<int:pk>/reject/', views.dcs_detail_reject, name='dcs_detail_reject'),
    path('province/password/', views.ProvincePasswordView.as_view(), name='province_password'),
    
    # DCs List for Province/DMD/MD
    path('dcs/', views.DCsListView.as_view(), name='dcs_list'),

    # History
    path('history/', views.DCHistoryView.as_view(), name='dc_history'),
    path('api/history-data/', views.api_history_data, name='api_history_data'),

    # Admin Tools (separate module - can be easily removed)
    path('admin-tools/', include('nea_loss.admin_tools.urls')),
]
