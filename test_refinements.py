from task_manager import TaskManager
from db_manager import get_db_connection

def verify_refinements():
    manager = TaskManager()
    
    print("\n--- Test: Refinements (Time, Delete) ---")
    
    # 1. Setup Data
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    cursor.close()
    conn.close()
    
    manager.add_task("Root A", time_minutes=10) # ID 1 (approx)
    
    tasks = manager.list_tasks()
    root_a = tasks[0]
    
    manager.add_task("Sub A1", parent_id=root_a['id'], time_minutes=5)
    
    # Verify Initial Time
    tasks_1 = manager.list_tasks()
    root_1 = tasks_1[0]
    print(f"Initial: Branch Total = {root_1['branch_total']} (Exp: 15)")
    assert root_1['branch_total'] == 15
    
    # 2. Test Time Exclusion on Complete
    print("Completing Root A...")
    manager.complete_task(root_1['id'])
    
    tasks_2 = manager.list_tasks()
    root_2 = tasks_2[0]
    # Root A is complete, so its 10m should NOT count.
    # Sub A1 is pending (5m), so it should count?
    # Wait, recursive logic: 
    # calculate_branch_total(task): total = own_time (if !complete) + child totals.
    # So if Root A is complete, its own 10m is ignored. But it still sums children.
    # So Branch Total = 0 + 5 = 5.
    
    print(f"After Complete: Branch Total = {root_2['branch_total']} (Exp: 5)")
    assert root_2['branch_total'] == 5
    
    # 3. Test Delete
    print("Deleting Root A...")
    manager.delete_task(root_2['id'])
    
    tasks_3 = manager.list_tasks()
    print(f"Count after delete: {len(tasks_3)}")
    assert len(tasks_3) == 0
    
    print("Verification Passed!")

if __name__ == "__main__":
    verify_refinements()
