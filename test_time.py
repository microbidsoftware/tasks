from task_manager import TaskManager
from db_manager import get_db_connection

def verify_time():
    manager = TaskManager()
    
    print("\n--- Test: Add Tasks with Time ---")
    
    # 1. Add Root A (10m)
    manager.add_task("Root A", time_minutes=10)
    
    # 2. Add Root B (20m) - Sibling to A
    manager.add_task("Root B", time_minutes=20)
    
    # Check aggregation for Roots
    tasks = manager.list_tasks()
    
    # Filter to just added ones for clarity (ignoring previous runs data if any, though verify_subtasks cleared DB?)
    # Let's focus on logic.
    
    root_a = next((t for t in tasks if t['title'] == 'Root A'), None)
    root_b = next((t for t in tasks if t['title'] == 'Root B'), None)
    
    if root_a and root_b:
        print(f"Root A Time: {root_a['time_minutes']} | Group Total: {root_a['sibling_total_time']}")
        print(f"Root B Time: {root_b['time_minutes']} | Group Total: {root_b['sibling_total_time']}")
        
        # Verify
        assert root_a['sibling_total_time'] >= 30 # At least 10+20. Could be more if DB not cleared.
        assert root_b['sibling_total_time'] == root_a['sibling_total_time']
        print("Root Sibling Aggregation: OK")
        
        # 3. Add Subtasks to A
        manager.add_task("Sub A.1", parent_id=root_a['id'], time_minutes=5)
        manager.add_task("Sub A.2", parent_id=root_a['id'], time_minutes=5)
        
        tasks_again = manager.list_tasks()
        root_a_updated = next(t for t in tasks_again if t['id'] == root_a['id'])
        
        child1 = root_a_updated['children'][0]
        child2 = root_a_updated['children'][1]
        
        print(f"Child 1 Time: {child1['time_minutes']} | Group Total: {child1['sibling_total_time']}")
        
        assert child1['sibling_total_time'] == 10
        assert child2['sibling_total_time'] == 10
        print("Child Sibling Aggregation: OK")

if __name__ == "__main__":
    verify_time()
