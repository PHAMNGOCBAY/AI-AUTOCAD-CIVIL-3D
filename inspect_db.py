import sqlite3

def inspect():
    conn = sqlite3.connect('bim_data.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=== TABLES ===")
    for t in tables:
        table_name = t[0]
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        for col in schema:
            print(f"  - {col[1]} ({col[2]})")
            
        # Get count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  Total rows: {count}")
        
        # Sample data if it contains 'parcel' or 'element'
        if 'parcel' in table_name.lower() or 'element' in table_name.lower():
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            print("  Sample data:")
            for r in rows:
                print(f"    {r}")
                
if __name__ == "__main__":
    inspect()
