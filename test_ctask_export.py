from ctask import CTask
from db_manager import get_db_connection
import json

def test_export():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return
    
    cursor = conn.cursor(dictionary=True)
    # Get the latest task to test with
    cursor.execute("SELECT user_id, id FROM tasks ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        print("No tasks found in DB")
        return
    
    user_id = row['user_id']
    task_id = row['id']
    
    print(f"Testing with User ID: {user_id}, Task ID: {task_id}")
    
    ctask = CTask(user_id, task_id)
    structure = ctask.get_full_task_structure_json()
    
    if structure:
        print("\nFull Task Structure JSON:")
        print(json.dumps(structure, indent=2))
    else:
        print("Failed to retrieve structure or structure is empty")

if __name__ == "__main__":
    test_export()
