import sys
from task_manager import TaskManager
from db_manager import initialize_database

def print_menu():
    print("\nTask Manager Menu Obsolete")
    print("1. Add Task")
    print("2. List Tasks")
    print("3. Complete Task")
    print("4. Exit")

def main():
    # Ensure DB is ready
    initialize_database()
    
    manager = TaskManager()
    
    while True:
        print_menu()
        choice = input("Enter your choice: ")
        
        if choice == '1':
            title = input("Enter task title: ")
            if title.strip():
                manager.add_task(title)
            else:
                print("Task title cannot be empty.")
        elif choice == '2':
            manager.list_tasks()
        elif choice == '3':
            try:
                task_id = int(input("Enter task ID to complete: "))
                manager.complete_task(task_id)
            except ValueError:
                print("Invalid input. Please enter a numeric Task ID.")
        elif choice == '4':
            print("Exiting...")
            sys.exit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
