#!/usr/bin/env python
import os
import sys
import sqlite3

def debug_specific_dc():
    print("=== DEBUGGING SPECIFIC DC SELECTION ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("Database file not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get Kathmandu DC specifically
        cursor.execute("SELECT id, name, report_start_month FROM nea_loss_distributioncenter WHERE name LIKE '%kathmandu%'")
        ktm_result = cursor.fetchone()
        
        if not ktm_result:
            print('DC Kathmandu not found')
            return
        
        dc_id, dc_name, start_month = ktm_result
        print(f'Testing for DC: {dc_name} (ID: {dc_id}, Start Month: {start_month})')
        
        # Get active fiscal year
        cursor.execute("SELECT id, year_bs FROM nea_loss_fiscalyear WHERE is_active = 1")
        fy_result = cursor.fetchone()
        
        if not fy_result:
            print('No active fiscal year found')
            return
        
        fy_id, fy_year = fy_result
        print(f"Active Fiscal Year: {fy_year}")
        
        # Test months for this specific DC only
        all_months = [
            (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
            (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
            (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
        ]
        
        available_months = []
        
        for month_num, month_name in all_months:
            print(f"\n--- Checking Month {month_num} ({month_name}) ---")
            can_create = True
            
            # Check if report already exists for this specific DC
            cursor.execute(
                "SELECT status FROM nea_loss_lossreport WHERE distribution_center_id = ? AND fiscal_year_id = ? AND month = ?",
                (dc_id, fy_id, month_num)
            )
            existing_report = cursor.fetchone()
            
            if existing_report:
                print(f"  - Report already exists: {existing_report[0]}")
                can_create = False
            else:
                print(f"  - No existing report")
                # Check if month is before this DC's start month
                if month_num < start_month:
                    print(f"  - Month {month_num} is before DC start month ({start_month})")
                    can_create = False
                else:
                    print(f"  - Month {month_num} >= DC start month ({start_month})")
            
            # For months other than Shrawan, check if previous month is approved
            if month_num > 1 and can_create:
                # If this month is the DC's start month, skip previous month check
                if month_num == start_month:
                    print(f"  - This is the DC start month - skipping previous month check")
                else:
                    previous_month = month_num - 1
                    cursor.execute(
                        "SELECT status FROM nea_loss_lossreport WHERE distribution_center_id = ? AND fiscal_year_id = ? AND month = ?",
                        (dc_id, fy_id, previous_month)
                    )
                    previous_report = cursor.fetchone()
                    
                    if previous_report and previous_report[0] == 'APPROVED':
                        print(f"  - Previous month {previous_month} is approved")
                    else:
                        print(f"  - Previous month {previous_month} not approved or doesn't exist")
                        can_create = False
            
            if can_create:
                print(f"  - CAN CREATE: Adding to available months")
                available_months.append((month_num, month_name))
            else:
                print(f"  - CANNOT CREATE")
        
        print(f"\n=== FINAL RESULT FOR {dc_name} ===")
        print(f"Available months: {available_months}")
        print(f"Count: {len(available_months)}")
        
        if len(available_months) == 0:
            print("ERROR: No available months for this DC!")
        else:
            print("SUCCESS: Months are available for selection.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    debug_specific_dc()
