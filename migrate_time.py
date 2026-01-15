from db_manager import get_db_connection
from mysql.connector import Error

def migrate_time_schema():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check for time_minutes column
            cursor.execute("""
                SELECT count(*) 
                FROM information_schema.columns 
                WHERE table_name = 'tasks' 
                AND column_name = 'time_minutes' 
                AND table_schema = DATABASE()
            """)
            if cursor.fetchone()[0] == 0:
                print("Adding time_minutes column...")
                cursor.execute("ALTER TABLE tasks ADD COLUMN time_minutes INT DEFAULT 0")
                print("Column added successfully.")
            else:
                print("time_minutes column already exists.")
                
            conn.commit()
        except Error as e:
            print(f"Error migrating schema: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate_time_schema()
