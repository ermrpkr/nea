import sqlite3
import os

def test_start_month_sqlite():
    print("=== TESTING START MONTH LOGIC (SQLITE) ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("Database file not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get DC Kathmandu
        cursor.execute("SELECT id, name, report_start_month FROM nea_loss_distributioncenter WHERE name LIKE '%kathmandu%'")
        dc_result = cursor.fetchone()
        
        if not dc_result:
            print('DC Kathmandu not found')
            return
        
        dc_id, dc_name, start_month = dc_result
        print(f'DC: {dc_name}')
        print(f'Start Month: {start_month}')
        
        # Get active fiscal year
        cursor.execute("SELECT id, year_bs FROM nea_loss_fiscalyear WHERE is_active = 1")
        fy_result = cursor.fetchone()
        
        if not fy_result:
            print('No active fiscal year found')
            return
        
        fy_id, fy_year = fy_result
        print(f'Active Fiscal Year: {fy_year}')
        
        # Test different months
        test_months = [
            (8, 'Falgun'),
            (9, 'Chaitra'),
            (10, 'Baisakh'),
            (11, 'Jestha'),
        ]
        
        for month_num, month_name in test_months:
            print(f'\n--- Testing Month {month_num} ({month_name}) ---')
            
            # Check if month is before start month
            if month_num < start_month:
                print(f'  - Month {month_num} is BEFORE start month ({start_month})')
                print(f'  - SHOULD NOT BE AVAILABLE in dropdown')
                print(f'  - SHOULD NOT ALLOW creation')
            else:
                print(f'  - Month {month_num} is >= start month ({start_month})')
                
                # Check if report already exists
                cursor.execute(
                    "SELECT status FROM nea_loss_lossreport WHERE distribution_center_id = ? AND fiscal_year_id = ? AND month = ?",
                    (dc_id, fy_id, month_num)
                )
                report_result = cursor.fetchone()
                
                if report_result:
                    print(f'  - Report already exists: {report_result[0]}')
                    print(f'  - SHOULD NOT BE AVAILABLE in dropdown')
                else:
                    print(f'  - No existing report')
                    print(f'  - SHOULD BE AVAILABLE in dropdown')
                    
                    # Check previous month approval logic
                    if month_num == start_month:
                        print(f'  - This is the START MONTH')
                        print(f'  - SHOULD SKIP previous month approval check')
                        print(f'  - SHOULD ALLOW creation')
                    else:
                        print(f'  - This is NOT the start month')
                        previous_month = month_num - 1
                        cursor.execute(
                            "SELECT status FROM nea_loss_lossreport WHERE distribution_center_id = ? AND fiscal_year_id = ? AND month = ?",
                            (dc_id, fy_id, previous_month)
                        )
                        prev_result = cursor.fetchone()
                        
                        if prev_result and prev_result[0] == 'APPROVED':
                            print(f'  - Previous month {previous_month} is APPROVED')
                            print(f'  - SHOULD ALLOW creation')
                        else:
                            print(f'  - Previous month {previous_month} is NOT approved or doesn\'t exist')
                            print(f'  - SHOULD BLOCK creation')
        
        print(f'\n=== EXPECTED BEHAVIOR FOR DC KATHMANDU (Start Month: {start_month}) ===')
        print(f'Falgun (8): NOT AVAILABLE (before start month)')
        print(f'Chaitra ({start_month}): AVAILABLE (start month, no previous check)')
        print(f'Baisakh ({start_month + 1}): AVAILABLE only if Chaitra is approved')
        print(f'Jestha ({start_month + 2}): AVAILABLE only if Baisakh is approved')
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    test_start_month_sqlite()
