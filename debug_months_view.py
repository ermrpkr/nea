#!/usr/bin/env python
import os
import sys
import sqlite3

def debug_months_view():
    print("=== DEBUGGING MONTHS VIEW LOGIC ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("Database file not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all DCs
        cursor.execute("SELECT id, name, report_start_month FROM nea_loss_distributioncenter WHERE is_active = 1")
        dcs = cursor.fetchall()
        
        print(f"Active DCs: {len(dcs)}")
        for dc in dcs:
            print(f"  - {dc[1]} (Start Month: {dc[2]})")
        
        # Get active fiscal year
        cursor.execute("SELECT id, year_bs FROM nea_loss_fiscalyear WHERE is_active = 1")
        fy_result = cursor.fetchone()
        
        if not fy_result:
            print('No active fiscal year found')
            return
        
        fy_id, fy_year = fy_result
        print(f"Active Fiscal Year: {fy_year}")
        
        # Simulate the GET method logic
        all_months = [
            (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
            (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
            (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
        ]
        
        available_months = []
        
        for month_num, month_name in all_months:
            print(f"\n--- Checking Month {month_num} ({month_name}) ---")
            can_create = True
            
            # Check if report already exists for this month (for any DC)
            cursor.execute(
                "SELECT COUNT(*) FROM nea_loss_lossreport WHERE fiscal_year_id = ? AND month = ?",
                (fy_id, month_num)
            )
            report_count = cursor.fetchone()[0]
            
            if report_count > 0:
                print(f"  - Reports exist for this month: {report_count}")
                can_create = False
            else:
                print(f"  - No reports exist for this month")
                # Check if month is before any DC's start month
                for dc_id, dc_name, dc_start_month in dcs:
                    if month_num < dc_start_month:
                        print(f"  - Month {month_num} is before {dc_name} start month ({dc_start_month})")
                        can_create = False
                        break
            
            # For months other than Shrawan, check if previous month is approved
            if month_num > 1 and can_create:
                # For each DC, check if this month is before its start month
                # If it's before any DC's start month, skip the previous month check
                skip_previous_check = False
                for dc_id, dc_name, dc_start_month in dcs:
                    if month_num < dc_start_month:
                        print(f"  - Month {month_num} is before {dc_name} start month ({dc_start_month}) - skipping previous check")
                        skip_previous_check = True
                        break
                
                if not skip_previous_check:
                    previous_month = month_num - 1
                    cursor.execute(
                        "SELECT COUNT(*) FROM nea_loss_lossreport WHERE fiscal_year_id = ? AND month = ? AND status = 'APPROVED'",
                        (fy_id, previous_month)
                    )
                    approved_count = cursor.fetchone()[0]
                    
                    if approved_count == 0:
                        print(f"  - Previous month {previous_month} not approved")
                        can_create = False
                    else:
                        print(f"  - Previous month {previous_month} is approved")
            
            if can_create:
                print(f"  - CAN CREATE: Adding to available months")
                available_months.append((month_num, month_name))
            else:
                print(f"  - CANNOT CREATE")
        
        print(f"\n=== FINAL RESULT ===")
        print(f"Available months: {available_months}")
        print(f"Count: {len(available_months)}")
        
        if len(available_months) == 0:
            print("ERROR: No available months! This is why the dropdown is empty.")
        else:
            print("SUCCESS: Months are available for selection.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    debug_months_view()
