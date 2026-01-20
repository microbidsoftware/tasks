from db_manager import get_db_connection
import json
from mysql.connector import Error

class CTask:
    def __init__(self, user_id, task_id):
        self.user_id = user_id
        try:
            self.task_id = int(task_id)
        except (ValueError, TypeError):
            self.task_id = task_id # Fallback if not convertible, though usually should be
        self.fields = {}
        self.tags = []
        self._load_task()
        self._load_tags()

    def _load_task(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM tasks WHERE id = %s AND user_id = %s"
                cursor.execute(query, (self.task_id, self.user_id))
                row = cursor.fetchone()
                if row:
                    self.fields = row
            except Error as e:
                print(f"Error loading task in CTask: {e}")
            finally:
                cursor.close()
                conn.close()

    def _load_tags(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                    SELECT t.id, t.name 
                    FROM tags t
                    JOIN task_tags tt ON t.id = tt.tag_id
                    WHERE tt.task_id = %s
                """
                cursor.execute(query, (self.task_id,))
                self.tags = cursor.fetchall()
            except Error as e:
                print(f"Error loading tags in CTask: {e}")
            finally:
                cursor.close()
                conn.close()

    def add_tag(self, tag_name):
        """Ensure tag exists for user and then link it to this task."""
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            # 1. Get or create tag
            tag_name = tag_name.lower().strip()
            if tag_name.startswith('#'):
                tag_name = tag_name[1:]
            
            if not tag_name:
                return False

            cursor.execute("SELECT id FROM tags WHERE name = %s AND user_id = %s", (tag_name, self.user_id))
            row = cursor.fetchone()
            if row:
                tag_id = row[0]
            else:
                cursor.execute("INSERT INTO tags (name, user_id) VALUES (%s, %s)", (tag_name, self.user_id))
                conn.commit()
                tag_id = cursor.lastrowid

            # 2. Link to task
            cursor.execute("INSERT IGNORE INTO task_tags (task_id, tag_id) VALUES (%s, %s)", (self.task_id, tag_id))
            conn.commit()
            self._load_tags() # Refresh in-memory tags
            return True
        except Error as e:
            print(f"Error adding tag in CTask: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def remove_tag(self, tag_id):
        """Unlink tag from this task."""
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = "DELETE FROM task_tags WHERE task_id = %s AND tag_id = %s"
            cursor.execute(query, (self.task_id, tag_id))
            conn.commit()
            self._load_tags() # Refresh in-memory tags
            return True
        except Error as e:
            print(f"Error removing tag in CTask: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_tags(self):
        return self.tags

    def get_full_task_structure_json(self):
        """Returns the full task structure in JSON for the branch this task belongs to."""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            # 1. Fetch all tasks for this user
            query = "SELECT id, title, parent_id FROM tasks WHERE user_id = %s"
            cursor.execute(query, (self.user_id,))
            all_user_tasks = cursor.fetchall()
            
            if not all_user_tasks:
                return None
            
            # Map of task_id to task data
            task_map = {t['id']: t for t in all_user_tasks}
            
            # 2. Find the root of the branch containing self.task_id
            curr_id = self.task_id
            if curr_id not in task_map:
                # If current task is not in map (e.g. just deleted or wrong ID), load it individually
                self._load_task()
                if not self.fields:
                    return None
                curr_id = self.task_id
                # This case shouldn't really happen if all_user_tasks is fetched correctly
            
            # Trace back to the absolute root parent
            visited = set()
            while task_map[curr_id]['parent_id'] is not None:
                if curr_id in visited: # Cycle protection
                    break
                visited.add(curr_id)
                pid = task_map[curr_id]['parent_id']
                if pid not in task_map:
                    break
                curr_id = pid
            
            root_id = curr_id
            
            # 3. Build children map for efficient lookup
            children_map = {}
            for t_id, t_data in task_map.items():
                pid = t_data['parent_id']
                if pid not in children_map:
                    children_map[pid] = []
                children_map[pid].append(t_data)
            
            # 4. Recursive builder
            def build_node(tid):
                t = task_map[tid]
                node = {
                    "id": str(t['id']),
                    "title": t['title'],
                    "subtasks": []
                }
                for child in children_map.get(tid, []):
                    node["subtasks"].append(build_node(child['id']))
                return node
            
            return build_node(root_id)

        except Error as e:
            print(f"Error in get_full_task_structure_json: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    def _save_ai_suggestions(self, suggestions):
        """Helper to save the ai_suggestion JSON to the database."""
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = "UPDATE tasks SET ai_suggestion = %s WHERE id = %s AND user_id = %s"
            cursor.execute(query, (json.dumps(suggestions), self.task_id, self.user_id))
            conn.commit()
            self._load_task() # Refresh fields
            return True
        except Error as e:
            print(f"Error saving AI suggestions in CTask: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def remove_ai_suggestion(self, item_text):
        """Remove a specific item from the AI suggestion list."""
        if not self.fields.get('ai_suggestion'):
            return False
        try:
            suggestions = json.loads(self.fields['ai_suggestion'])
            if not isinstance(suggestions, list):
                return False
            
            new_suggestions = []
            for s in suggestions:
                text = s['text'] if isinstance(s, dict) else s
                if text != item_text:
                    new_suggestions.append(s)
            
            return self._save_ai_suggestions(new_suggestions)
        except json.JSONDecodeError:
            return False

    def toggle_ai_suggestion(self, item_text):
        """Toggle the completion status of a specific suggestion item."""
        if not self.fields.get('ai_suggestion'):
            return False
        try:
            suggestions = json.loads(self.fields['ai_suggestion'])
            if not isinstance(suggestions, list):
                return False
            
            updated = False
            for s in suggestions:
                if isinstance(s, dict) and s['text'] == item_text:
                    s['done'] = not s.get('done', False)
                    updated = True
                elif isinstance(s, str) and s == item_text:
                    # Convert legacy string to object on toggle
                    index = suggestions.index(s)
                    suggestions[index] = {"text": s, "done": True}
                    updated = True
            
            if updated:
                return self._save_ai_suggestions(suggestions)
            return False
        except json.JSONDecodeError:
            return False

    def edit_ai_suggestion(self, old_text, new_text, new_time=None):
        """Update the text and optionally time of a specific suggestion item."""
        if not self.fields.get('ai_suggestion'):
            return False
        try:
            suggestions = json.loads(self.fields['ai_suggestion'])
            if not isinstance(suggestions, list):
                return False
            
            updated = False
            for s in suggestions:
                text = s['text'] if isinstance(s, dict) else s
                if text == old_text:
                    if isinstance(s, dict):
                        s['text'] = new_text
                        if new_time is not None:
                            try:
                                s['time'] = int(new_time)
                            except (ValueError, TypeError):
                                pass
                    else:
                        # Convert legacy string to object
                        index = suggestions.index(s)
                        suggestions[index] = {"text": new_text, "done": False, "time": new_time if new_time is not None else 0}
                    updated = True
                    break
            
            if updated:
                return self._save_ai_suggestions(suggestions)
            return False
        except json.JSONDecodeError:
            return False
