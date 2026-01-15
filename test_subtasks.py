from task_manager import TaskManager
from db_manager import get_db_connection

def verify_subtasks():
    manager = TaskManager()
    
    print("\n--- Test: Add Subtasks ---")
    # Clean up
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    cursor.close()
    conn.close()

    manager.add_task("Root Task 1")
    
    # Get Root ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE title='Root Task 1'")
    root_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print(f"Added Root Task ID: {root_id}")
    
    manager.add_task("Subtask 1.1", parent_id=root_id)
    print("Added Subtask 1.1")
    
    # Get Subtask ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE title='Subtask 1.1'")
    sub_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    manager.add_task("Subtask 1.1.1", parent_id=sub_id)
    print("Added Subtask 1.1.1")
    
    print("\n--- Test: List Hierarchy ---")
    tasks = manager.list_tasks()
    
    # Verify Structure
    # Expect: [ {id: root, children: [ {id: sub, children: [ {id: subsub} ]} ]} ]
    
    assert len(tasks) == 1
    root = tasks[0]
    print(f"Root: {root['title']}")
    
    assert len(root['children']) == 1
    child = root['children'][0]
    print(f"  Child: {child['title']}")
    
    assert len(child['children']) == 1
    grandchild = child['children'][0]
    print(f"    Grandchild: {grandchild['title']}")
    
    print("\nVerification Passed!")

if __name__ == "__main__":
    verify_subtasks()
