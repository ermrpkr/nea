def admin_tools_context(request):
    """Add admin tools context variables"""
    return {
        'admin_tools_enabled': True,  # Flag to enable admin tools
        'show_admin_dc_report': getattr(request.user, 'is_system_admin', False),
    }
