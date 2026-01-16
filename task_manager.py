from db_manager import get_db_connection
import json
from mysql.connector import Error

from ai_service import AIService

class TaskManager:
    def __init__(self):
        self.ai_service = AIService()

    def add_task(self, user_id, title, parent_id=None, time_minutes=0, importance=None, description=None):
        """Add a new task (or subtask) with optional time estimation, importance and description."""
        conn = get_db_connection()
        if conn:
            try:
                # Call AI
                ai_suggestions = self.ai_service.get_task_suggestion(title)
                ai_suggestion_json = json.dumps(ai_suggestions) if ai_suggestions else None
                
                cursor = conn.cursor()
                if parent_id == '' or parent_id == 'None':
                    parent_id = None
                
                # Use 0 if None or empty
                if not time_minutes:
                    time_minutes = 0
                
                query = "INSERT INTO tasks (title, status, parent_id, time_minutes, ai_suggestion, user_id, importance, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (title, 'pending', parent_id, time_minutes, ai_suggestion_json, user_id, importance, description))
                conn.commit()
                print(f"Task '{title}' added successfully.")
                return True
            except Error as e:
                print(f"Error adding task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def list_tasks(self, user_id):
        """List all tasks in a hierarchy with calculated sibling branch totals."""
        conn = get_db_connection()
        tasks_tree = []
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                # Sort: Pending (0) first, Completed (1) last. Then by created_at.
                query = """
                    SELECT id, title, status, created_at, parent_id, time_minutes, ai_suggestion, importance, description, hide_until 
                    FROM tasks 
                    WHERE user_id = %s 
                    AND (hide_until IS NULL OR hide_until <= NOW())
                    ORDER BY (status = 'completed') ASC, created_at DESC
                """
                cursor.execute(query, (user_id,))
                all_tasks = cursor.fetchall()

                # --- 1. Build Tree Structure ---
                tasks_map = {task['id']: task for task in all_tasks}
                for task in all_tasks:
                   task['children'] = []
                   task['own_time'] = task['time_minutes'] if task['time_minutes'] else 0
                   task['branch_total'] = 0 # Will be calculated

                   if task['ai_suggestion']:
                       try:
                           task['ai_suggestion'] = json.loads(task['ai_suggestion'])
                       except (json.JSONDecodeError, TypeError):
                           pass
                
                # Link children to parents
                root_tasks = []
                for task in all_tasks:
                    if task['parent_id']:
                        parent = tasks_map.get(task['parent_id'])
                        if parent:
                            parent['children'].append(task)
                    else:
                        root_tasks.append(task)
                
                # --- 2. Calculate Branch Totals (Recursive) ---
                def calculate_branch_total(task):
                    # Only count own time if NOT completed
                    total = task['own_time'] if task['status'] != 'completed' else 0
                    
                    for child in task['children']:
                        total += calculate_branch_total(child)
                    
                    task['branch_total'] = total
                    return total

                # Run on all roots (this will traverse the whole forest)
                for task in root_tasks:
                    calculate_branch_total(task)

                tasks_tree = root_tasks
                        
            except Error as e:
                print(f"Error listing tasks: {e}")
            finally:
                cursor.close()
                conn.close()
        return tasks_tree

    def complete_task(self, user_id, task_id):
        """Mark a task AND all its descendants as completed."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # 1. Find all descendants recursively
                # Since we don't have a simple recursive query handy universally,
                # let's fetch all (id, parent_id) and build a quick graph.
                cursor.execute("SELECT id, parent_id FROM tasks WHERE user_id = %s", (user_id,))
                all_nodes = cursor.fetchall()
                
                # Build tree in memory
                children_map = {}
                for tid, pid in all_nodes:
                    if pid:
                        if pid not in children_map: children_map[pid] = []
                        children_map[pid].append(tid)

                ids_to_complete = [task_id]
                queue = [task_id]
                
                while queue:
                    current = queue.pop(0)
                    children = children_map.get(current, [])
                    ids_to_complete.extend(children)
                    queue.extend(children)
                
                # 2. Update all of them
                format_strings = ','.join(['%s'] * len(ids_to_complete))
                query = f"UPDATE tasks SET status = 'completed', completed_at = NOW() WHERE id IN ({format_strings})"
                cursor.execute(query, tuple(ids_to_complete))
                conn.commit()
                return True
            except Error as e:
                print(f"Error completing task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def uncomplete_task(self, user_id, task_id):
        """Mark a task as pending (Undo completion)."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Status 'pending' is the active state
                query = "UPDATE tasks SET status = 'pending', completed_at = NULL WHERE id = %s AND user_id = %s"
                cursor.execute(query, (task_id, user_id))
                conn.commit()
                return True
            except Error as e:
                print(f"Error uncompleting task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def update_task(self, user_id, task_id, title=None, time_minutes=None, importance=None, description=None):
        """Update a task's details."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check exist
                check_query = "SELECT id, title, time_minutes FROM tasks WHERE id = %s AND user_id = %s"
                cursor.execute(check_query, (task_id, user_id))
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Prepare update
                updates = []
                params = []
                
                if title is not None:
                    updates.append("title = %s")
                    params.append(title)
                
                if importance is not None:
                    updates.append("importance = %s")
                    params.append(importance)

                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                
                if time_minutes is not None:
                    try:
                        time_val = int(time_minutes)
                        updates.append("time_minutes = %s")
                        params.append(time_val)
                    except (ValueError, TypeError):
                        pass

                if not updates:
                    return True
                
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
                
                cursor.execute(query, tuple(params))
                conn.commit()
                print(f"Task {task_id} updated.")
                return True
            except Error as e:
                print(f"Error updating task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def delete_task(self, user_id, task_id):
        """Delete a task and its descendants."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # ON DELETE CASCADE is set in DB, so deleting parent deletes children
                query = "DELETE FROM tasks WHERE id = %s AND user_id = %s"
                cursor.execute(query, (task_id, user_id))
                conn.commit()
                return True
            except Error as e:
                print(f"Error deleting task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

        return False

    def clear_ai_suggestion(self, user_id, task_id):
        """Remove the entire AI suggestion for a specific task."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = "UPDATE tasks SET ai_suggestion = NULL WHERE id = %s AND user_id = %s"
                cursor.execute(query, (task_id, user_id))
                conn.commit()
                return True
            except Error as e:
                print(f"Error clearing AI suggestion: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def remove_ai_suggestion_item(self, user_id, task_id, item_text):
        """Remove a specific item from the AI suggestion list."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT ai_suggestion FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
                row = cursor.fetchone()
                if row and row['ai_suggestion']:
                    suggestions = json.loads(row['ai_suggestion'])
                    if isinstance(suggestions, list):
                        # Handle legacy strings and new objects
                        new_suggestions = []
                        for s in suggestions:
                            text = s['text'] if isinstance(s, dict) else s
                            if text != item_text:
                                new_suggestions.append(s)
                        
                        query = "UPDATE tasks SET ai_suggestion = %s WHERE id = %s AND user_id = %s"
                        cursor.execute(query, (json.dumps(new_suggestions), task_id, user_id))
                        conn.commit()
                        return True
            except (Error, json.JSONDecodeError) as e:
                print(f"Error removing AI item: {e}")
            finally:
                cursor.close()
                conn.close()
        return False

    def toggle_ai_suggestion_item(self, user_id, task_id, item_text):
        """Toggle the completion status of a specific suggestion item."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT ai_suggestion FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
                row = cursor.fetchone()
                if row and row['ai_suggestion']:
                    suggestions = json.loads(row['ai_suggestion'])
                    if isinstance(suggestions, list):
                        for s in suggestions:
                            if isinstance(s, dict) and s['text'] == item_text:
                                s['done'] = not s.get('done', False)
                            elif isinstance(s, str) and s == item_text:
                                # Convert legacy string to object on toggle
                                index = suggestions.index(s)
                                suggestions[index] = {"text": s, "done": True}
                        
                        query = "UPDATE tasks SET ai_suggestion = %s WHERE id = %s AND user_id = %s"
                        cursor.execute(query, (json.dumps(suggestions), task_id, user_id))
                        conn.commit()
                        return True
            except (Error, json.JSONDecodeError) as e:
                print(f"Error toggling AI item: {e}")
            finally:
                cursor.close()
                conn.close()
        return False


    def hide_task(self, user_id, task_id, duration_str):
        """Make a task invisible until a certain time based on duration_str."""
        import datetime
        
        now = datetime.datetime.now()
        hide_until = None
        
        if duration_str == '1 day':
            hide_until = now + datetime.timedelta(days=1)
        elif duration_str == '2 days':
            hide_until = now + datetime.timedelta(days=2)
        elif duration_str == '3 days':
            hide_until = now + datetime.timedelta(days=3)
        elif duration_str == '1 week':
            hide_until = now + datetime.timedelta(weeks=1)
        elif duration_str == '2 weeks':
            hide_until = now + datetime.timedelta(weeks=2)
        elif duration_str == '1 month':
            # Simplified month Calculation (30 days)
            hide_until = now + datetime.timedelta(days=30)
        
        if not hide_until:
            return False
            
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = "UPDATE tasks SET hide_until = %s WHERE id = %s AND user_id = %s"
                cursor.execute(query, (hide_until, task_id, user_id))
                conn.commit()
                return True
            except Error as e:
                print(f"Error hiding task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False
