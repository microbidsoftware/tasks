from task_manager import TaskManager
import json

def debug_list_tasks():
    manager = TaskManager()
    tasks, stats = manager.list_tasks(1)
    print(f"Total tasks: {len(tasks)}")
    print(json.dumps(tasks, indent=2, default=str))

if __name__ == "__main__":
    debug_list_tasks()
