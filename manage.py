#!/usr/bin/env python
import glob
import os
import sys


def _use_project_venv_site_packages():
    root = os.path.dirname(os.path.abspath(__file__))
    if sys.platform == 'win32':
        site_packages = os.path.join(root, '.venv', 'Lib', 'site-packages')
    else:
        matches = glob.glob(os.path.join(root, '.venv', 'lib', 'python*', 'site-packages'))
        site_packages = matches[0] if matches else ''
    if site_packages and os.path.isdir(site_packages):
        sys.path.insert(0, site_packages)


_use_project_venv_site_packages()


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
