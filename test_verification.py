from task_manager import TaskManager
from db_manager import initialize_database, get_db_connection

def verify_app():
    print("Initializing Database...")
    initialize_database()
    
    manager = TaskManager()
    
    print("\n--- Test: Add Task ---")
    manager.add_task("Test Task 1")
    manager.add_task("Test Task 2")
    
    print("\n--- Test: List Tasks (Expect 2 pending) ---")
    manager.list_tasks()
    
    # Get ID of first task to complete
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE title='Test Task 1' LIMIT 1")
    task_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print(f"\n--- Test: Complete Task {task_id} ---")
    manager.complete_task(task_id)
    
    print("\n--- Test: List Tasks (Expect 1 pending, 1 completed) ---")
    manager.list_tasks()

if __name__ == "__main__":
    verify_app()
