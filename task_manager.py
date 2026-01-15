from db_manager import get_db_connection
from mysql.connector import Error

from ai_service import AIService

class TaskManager:
    def __init__(self):
        self.ai_service = AIService()

    def add_task(self, user_id, title, parent_id=None, time_minutes=0):
        """Add a new task (or subtask) with optional time estimation."""
        conn = get_db_connection()
        if conn:
            try:
                # Call AI
                ai_suggestion = self.ai_service.get_task_suggestion(title)
                
                cursor = conn.cursor()
                if parent_id == '' or parent_id == 'None':
                    parent_id = None
                
                # Use 0 if None or empty
                if not time_minutes:
                    time_minutes = 0
                
                query = "INSERT INTO tasks (title, status, parent_id, time_minutes, ai_suggestion, user_id) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (title, 'pending', parent_id, time_minutes, ai_suggestion, user_id))
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
                query = "SELECT id, title, status, created_at, parent_id, time_minutes, ai_suggestion FROM tasks WHERE user_id = %s ORDER BY (status = 'completed') ASC, created_at ASC"
                cursor.execute(query, (user_id,))
                all_tasks = cursor.fetchall()

                # --- 1. Build Tree Structure ---
                tasks_map = {task['id']: task for task in all_tasks}
                for task in all_tasks:
                   task['children'] = []
                   task['own_time'] = task['time_minutes'] if task['time_minutes'] else 0
                   task['branch_total'] = 0 # Will be calculated
                
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
                query = f"UPDATE tasks SET status = 'completed' WHERE id IN ({format_strings})"
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

    def update_task(self, user_id, task_id, title=None, time_minutes=None):
        """Update a task's title and/or time."""
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
