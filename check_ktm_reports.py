#!/usr/bin/env python
import os
import sqlite3

def check_ktm_reports():
    print("=== CHECKING KATHMANDU DC REPORTS ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("Database file not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get Kathmandu DC
        cursor.execute("SELECT id, name FROM nea_loss_distributioncenter WHERE name LIKE '%kathmandu%'")
        ktm_result = cursor.fetchone()
        
        if not ktm_result:
            print('DC Kathmandu not found')
            return
        
        dc_id, dc_name = ktm_result
        print(f'DC: {dc_name} (ID: {dc_id})')
        
        # Get active fiscal year
        cursor.execute("SELECT id, year_bs FROM nea_loss_fiscalyear WHERE is_active = 1")
        fy_result = cursor.fetchone()
        
        if not fy_result:
            print('No active fiscal year found')
            return
        
        fy_id, fy_year = fy_result
        print(f'Active Fiscal Year: {fy_year}')
        
        # Check existing reports for Kathmandu DC
        cursor.execute(
            "SELECT month, status FROM nea_loss_lossreport WHERE distribution_center_id = ? AND fiscal_year_id = ? ORDER BY month",
            (dc_id, fy_id)
        )
        reports = cursor.fetchall()
        
        print(f"\nExisting reports for {dc_name}:")
        for month, status in reports:
            print(f"  Month {month}: {status}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_ktm_reports()
