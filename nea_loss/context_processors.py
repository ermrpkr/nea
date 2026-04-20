"""Template context shared across all pages."""


def nea_permissions(request):
    u = request.user
    if not u.is_authenticated:
        return {
            'can_create_loss_report': False,
            'can_create_provincial_report': False,
            'is_system_admin': False,
            'is_top_management': False,
            'is_provincial': False,
            'is_dc_level': False,
        }

    is_sys_admin = getattr(u, 'is_system_admin', False)
    is_top = getattr(u, 'is_top_management', False)
    is_prov = getattr(u, 'is_provincial', False)
    is_dc = getattr(u, 'is_dc_level', False)

    # Only DC users can create DC reports; provincial creates provincial reports; sys_admin can do all
    can_create_dc = False
    if is_sys_admin:
        can_create_dc = True
    elif is_dc:
        can_create_dc = bool(getattr(u, 'distribution_center_id', None))

    # Provincial office can create monthly consolidated reports
    can_create_prov = False
    if is_sys_admin:
        can_create_prov = True
    elif is_prov:
        can_create_prov = bool(getattr(u, 'provincial_office_id', None))

    return {
        'can_create_loss_report': can_create_dc,
        'can_create_provincial_report': can_create_prov,
        'is_system_admin': is_sys_admin,
        'is_top_management': is_top,
        'is_provincial': is_prov,
        'is_dc_level': is_dc,
    }
