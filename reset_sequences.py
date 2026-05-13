#!/usr/bin/env python
"""
Reset PostgreSQL sequences after data migration
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
django.setup()

from django.db import connection
from django.core.management.color import no_style
from django.apps import apps

def reset_sequences():
    """Reset all PostgreSQL sequences"""
    style = no_style()
    sql_list = []
    
    for app_config in apps.get_app_configs():
        app_models = app_config.get_models()
        for model in app_models:
            sql_list.extend(connection.ops.sequence_reset_sql(style, [model]))
    
    if sql_list:
        with connection.cursor() as cursor:
            for sql in sql_list:
                cursor.execute(sql)
            print(f"Reset {len(sql_list)} sequences")
    else:
        print("No sequences to reset")

if __name__ == '__main__':
    reset_sequences()
