from task_manager import TaskManager
from db_manager import get_db_connection
import json

def test_ai_enhancements():
    print("Testing AI Suggestion Enhancements...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users LIMIT 1")
    user_row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user_row:
        print("No user found. Please log in once.")
        return
    
    user_id = user_row[0]
    manager = TaskManager()
    
    # 1. Test add_task with run_ai=False
    print("\n1. Testing add_task with run_ai=False...")
    title = "Task without AI"
    manager.add_task(user_id, title, run_ai=False)
    
    tasks = manager.list_tasks(user_id)
    no_ai_task = next(t for t in tasks if t['title'] == title)
    print(f"Task created. ai_suggestion: {no_ai_task['ai_suggestion']}")
    assert no_ai_task['ai_suggestion'] is None
    
    # 2. Test edit_ai_suggestion_item
    print("\n2. Testing edit_ai_suggestion_item...")
    # Create a task with suggestions manually for testing
    conn = get_db_connection()
    cursor = conn.cursor()
    suggestions = [
        {"text": "Old Step", "time": 10, "done": False},
        {"text": "Stay Step", "time": 5, "done": False}
    ]
    cursor.execute("INSERT INTO tasks (title, user_id, ai_suggestion) VALUES (%s, %s, %s)", 
                   ("Task with suggestions", user_id, json.dumps(suggestions)))
    task_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    
    success = manager.edit_ai_suggestion_item(user_id, task_id, "Old Step", "New Step", 20)
    print(f"Edit success: {success}")
    assert success is True
    
    tasks = manager.list_tasks(user_id)
    edited_task = next(t for t in tasks if t['id'] == task_id)
    new_suggestions = edited_task['ai_suggestion']
    print(f"New suggestions: {new_suggestions}")
    assert any(s['text'] == "New Step" and s['time'] == 20 for s in new_suggestions)
    assert any(s['text'] == "Stay Step" and s['time'] == 5 for s in new_suggestions)
    
    print("\nAll backend tests for AI enhancements passed!")

if __name__ == "__main__":
    try:
        test_ai_enhancements()
    except Exception as e:
        print(f"Tests failed: {e}")
