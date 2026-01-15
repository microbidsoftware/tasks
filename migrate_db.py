from db_manager import get_db_connection
from mysql.connector import Error

def migrate_schema():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Add parent_id column if it doesn't exist
            # Note: Checking for column existence slightly verbose in MySQL, 
            # simplest way for this script is attempting to add and catching error 
            # or checking information_schema.
            
            # Simple approach: Check information_schema
            cursor.execute("""
                SELECT count(*) 
                FROM information_schema.columns 
                WHERE table_name = 'tasks' 
                AND column_name = 'parent_id' 
                AND table_schema = DATABASE()
            """)
            if cursor.fetchone()[0] == 0:
                print("Adding parent_id column...")
                cursor.execute("ALTER TABLE tasks ADD COLUMN parent_id INT DEFAULT NULL")
                cursor.execute("ALTER TABLE tasks ADD CONSTRAINT fk_parent FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE")
                print("Column added successfully.")
            else:
                print("parent_id column already exists.")
                
            conn.commit()
        except Error as e:
            print(f"Error migrating schema: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate_schema()
