from task_manager import TaskManager
from db_manager import get_db_connection

def verify_completion_logic():
    manager = TaskManager()
    print("\n--- Test: Recursive Completion & Sorting ---")
    
    # 1. Clear DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    cursor.close()
    conn.close()
    
    # 2. Setup:
    # Task Pending1 (Created first)
    # Task RootToComplete
    #   -> Sub1
    #       -> SubSub1
    # Task Pending2 (Created last)
    
    manager.add_task("Pending1")
    manager.add_task("RootToComplete")
    
    tasks = manager.list_tasks()
    root_tc = next(t for t in tasks if t['title'] == 'RootToComplete')
    
    manager.add_task("Sub1", parent_id=root_tc['id'])
    
    tasks = manager.list_tasks()
    sub1 = next(t for t in tasks if t['children'] and t['title'] == 'RootToComplete')['children'][0]
    
    manager.add_task("SubSub1", parent_id=sub1['id'])
    manager.add_task("Pending2")
    
    # Check Initial Order (creation order)
    # Expected: Pending1, RootToComplete, Pending2
    tasks_init = manager.list_tasks()
    titles_init = [t['title'] for t in tasks_init]
    print(f"Initial Order: {titles_init}")
    assert titles_init == ['Pending1', 'RootToComplete', 'Pending2']
    
    # 3. Complete RootToComplete
    print("Completing RootToComplete...")
    manager.complete_task(root_tc['id'])
    
    # 4. Verify Recursion
    # Fetch directly from DB to check status
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT title, status FROM tasks")
    all_statuses = {row['title']: row['status'] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    
    print(f"Statuses: {all_statuses}")
    assert all_statuses['RootToComplete'] == 'completed'
    assert all_statuses['Sub1'] == 'completed'
    assert all_statuses['SubSub1'] == 'completed'
    assert all_statuses['Pending1'] == 'pending'
    
    # 5. Verify Sorting
    # Expected: Pending1, Pending2, RootToComplete (at bottom)
    tasks_final = manager.list_tasks()
    titles_final = [t['title'] for t in tasks_final]
    print(f"Final Order: {titles_final}")
    
    # Pending tasks first?
    assert titles_final[0] == 'Pending1'
    assert titles_final[1] == 'Pending2'
    assert titles_final[2] == 'RootToComplete'
    
    print("Verification Passed!")

if __name__ == "__main__":
    verify_completion_logic()
