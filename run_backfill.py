from task_manager import TaskManager

def run_backfill():
    manager = TaskManager()
    print("Starting backfill...")
    success = manager.backfill_tree_fields()
    if success:
        print("Backfill completed successfully.")
    else:
        print("Backfill failed.")

if __name__ == "__main__":
    run_backfill()
