from tag_utils import extract_tags_from_text
from ctask import CTask
from task_manager import TaskManager
from db_manager import get_db_connection
import os

def test_tag_extraction():
    print("Testing tag extraction...")
    text = "Work on #project-alpha and #health goals"
    tags = extract_tags_from_text(text)
    print(f"Extracted: {tags}")
    assert "project-alpha" in tags
    assert "health" in tags
    assert len(tags) == 2
    print("Tag extraction passed!")

def test_ctask_tags():
    print("\nTesting CTask tag management...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users LIMIT 1")
    user_row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user_row:
        print("No user found in DB, skipping CTask tests. Please log in once.")
        return
    
    user_id = user_row[0]
    print(f"Using user_id: {user_id}")
    manager = TaskManager()
    
    # 1. Add Task with tags in title
    input_title = "Test task with #tag1 #tag2"
    manager.add_task(user_id, input_title)
    
    tasks = manager.list_tasks(user_id)
    # The title should be cleaned: hashtags removed
    expected_title = "Test task with"
    test_task = next(t for t in tasks if t['title'] == expected_title)
    task_id = test_task['id']
    
    print(f"Task created with ID {task_id}. Saved title: '{test_task['title']}'")
    assert test_task['title'] == expected_title
    
    print(f"Initial tags in list_tasks: {[t['name'] for t in test_task['tags']]}")
    assert len(test_task['tags']) == 2
    assert any(t['name'] == 'tag1' for t in test_task['tags'])
    assert any(t['name'] == 'tag2' for t in test_task['tags'])
    
    # 2. Test CTask manually
    ctask = CTask(user_id, task_id)
    print("Adding manual tag #manual")
    ctask.add_tag("manual")
    
    tags = ctask.get_tags()
    print(f"Tags after manual add: {[t['name'] for t in tags]}")
    assert any(t['name'] == 'manual' for t in tags)
    
    # 3. Test remove tag
    tag_to_remove = next(t for t in tags if t['name'] == 'tag1')
    print(f"Removing tag {tag_to_remove['name']} (ID: {tag_to_remove['id']})")
    ctask.remove_tag(tag_to_remove['id'])
    
    tags_after_remove = ctask.get_tags()
    print(f"Tags after remove: {[t['name'] for t in tags_after_remove]}")
    assert not any(t['name'] == 'tag1' for t in tags_after_remove)
    
    print("CTask tag management passed!")

if __name__ == "__main__":
    try:
        test_tag_extraction()
        test_ctask_tags()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()
