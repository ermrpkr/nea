#!/usr/bin/env python
"""
Clean PostgreSQL database by dropping all tables
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
django.setup()

from django.db import connection

def clean_database():
    """Drop all tables in the PostgreSQL database"""
    with connection.cursor() as cursor:
        # Disable foreign key constraints
        cursor.execute("SET session_replication_role = replica;")
        
        # Get all table names
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Drop all tables
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                print(f"Dropped table: {table}")
            except Exception as e:
                print(f"Error dropping table {table}: {e}")
        
        # Reset sequences
        cursor.execute("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        sequences = [row[0] for row in cursor.fetchall()]
        
        for sequence in sequences:
            try:
                cursor.execute(f'DROP SEQUENCE IF EXISTS "{sequence}" CASCADE;')
                print(f"Dropped sequence: {sequence}")
            except Exception as e:
                print(f"Error dropping sequence {sequence}: {e}")
        
        # Re-enable foreign key constraints
        cursor.execute("SET session_replication_role = DEFAULT;")
        
        connection.commit()
        print("Database cleaned successfully!")

if __name__ == '__main__':
    clean_database()
