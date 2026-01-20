from db_manager import get_db_connection
import json
from mysql.connector import Error

from ai_service import AIService
from tag_utils import extract_tags_from_text, strip_tags_from_text
from ctask import CTask
from info_panel_manager import InfoPanelManager
from search_manager import SearchManager

class TaskManager:
    def __init__(self):
        self.ai_service = AIService()

    def add_task(self, user_id, title, parent_id=None, time_minutes=0, importance=None, description=None, run_ai=True, due_at=None, from_suggestion_text=None):
        """Add a new task (or subtask) with optional time estimation, importance, description, and due time."""
        conn = get_db_connection()
        if conn:
            try:
                # Call AI
                ai_suggestion_json = None
                if run_ai:
                    branch_context = None
                    current_leaf_title = None
                    
                    if parent_id:
                        try:
                            # Use CTask to get branch context
                            parent_ctask = CTask(user_id, int(parent_id))
                            branch_structure = parent_ctask.get_full_task_structure_json()
                            if branch_structure:
                                branch_context = json.dumps(branch_structure)
                            current_leaf_title = title
                        except Exception as e:
                            print(f"Error fetching branch context: {e}")

                    ai_suggestions = self.ai_service.get_task_suggestion(title, branch_context, current_leaf_title)
                    ai_suggestion_json = json.dumps(ai_suggestions) if ai_suggestions else None
                
                cursor = conn.cursor()
                if parent_id == '' or parent_id == 'None':
                    parent_id = None
                
                # Use 0 if None or empty
                if not time_minutes:
                    time_minutes = 0
                
                # Handle Tags
                tags_to_add = extract_tags_from_text(title)
                
                # Clean title before saving
                # Clean title before saving
                title = strip_tags_from_text(title)

                # Determine Level and Branch ID
                level = 0
                branch_id = None
                
                if parent_id:
                    # Fetch parent's level and branch_id
                    cursor.execute("SELECT level, branch_id FROM tasks WHERE id = %s", (parent_id,))
                    parent = cursor.fetchone()
                    if parent:
                        level = parent[0] + 1
                        branch_id = parent[1]

                query = "INSERT INTO tasks (title, status, parent_id, time_minutes, ai_suggestion, user_id, importance, description, due_at, level, branch_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (title, 'pending', parent_id, time_minutes, ai_suggestion_json, user_id, importance, description, due_at, level, branch_id))
                conn.commit()
                task_id = cursor.lastrowid

                # If root task, branch_id is its own ID
                if not parent_id:
                    branch_id = str(task_id)
                    cursor.execute("UPDATE tasks SET branch_id = %s WHERE id = %s", (branch_id, task_id))
                    conn.commit()
                
                # Handle Tags
                if tags_to_add:
                    ctask = CTask(user_id, task_id)
                    for tag in tags_to_add:
                        ctask.add_tag(tag)

                # Remove suggestion from parent if this was converted from one
                if parent_id and from_suggestion_text:
                    try:
                        parent_ctask = CTask(user_id, int(parent_id))
                        parent_ctask.remove_ai_suggestion(from_suggestion_text)
                    except Exception as e:
                        print(f"Error removing suggestion from parent: {e}")

                print(f"Task '{title}' added successfully.")
                return True
            except Error as e:
                print(f"Error adding task: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        return False

    def list_tasks(self, user_id, search_query=None, tag_filter=None, importance_filter=None, period_filter=None):
        """List tasks in a hierarchy, optionally filtered by search query, tag, importance, or period."""
        conn = get_db_connection()
        tasks_tree = []
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                # Sort: Pending (0) first, Completed (1) last. Then by created_at.
                query = """
                    SELECT id, title, status, created_at, parent_id, time_minutes, ai_suggestion, importance, description, hide_until, due_at, is_folded, level, branch_id, completed_at
                    FROM tasks 
                    WHERE user_id = %s 
                    AND (hide_until IS NULL OR hide_until <= NOW())
                    ORDER BY 
                        (status = 'completed') ASC,
                        CASE 
                            WHEN status = 'completed' THEN completed_at 
                            ELSE created_at 
                        END DESC
                """
                cursor.execute(query, (user_id,))
                all_tasks = cursor.fetchall()

                # --- 1. Build Tree Structure ---
                # Fetch all tags for all user tasks to avoid N+1 problem
                cursor.execute("""
                    SELECT tt.task_id, t.id, t.name 
                    FROM tags t
                    JOIN task_tags tt ON t.id = tt.tag_id
                    WHERE t.user_id = %s
                """, (user_id,))
                all_tags_raw = cursor.fetchall()
                task_tags_map = {}
                for row in all_tags_raw:
                    tid = row['task_id']
                    if tid not in task_tags_map:
                        task_tags_map[tid] = []
                    task_tags_map[tid].append({'id': row['id'], 'name': row['name']})

                tasks_map = {task['id']: task for task in all_tasks}
                for task in all_tasks:
                   task['children'] = []
                   task['own_time'] = task['time_minutes'] if task['time_minutes'] else 0
                   task['branch_total'] = 0 # Will be calculated
                   task['tags'] = task_tags_map.get(task['id'], [])

                   if task['ai_suggestion']:
                       try:
                           task['ai_suggestion'] = json.loads(task['ai_suggestion'])
                       except (json.JSONDecodeError, TypeError):
                           pass
                
                # --- 1.5 Apply Filters if provided ---
                if search_query or tag_filter or importance_filter or period_filter:
                    all_tasks = SearchManager.filter_tasks(all_tasks, search_query, tag_filter, importance_filter, period_filter)
                    # Rebuild maps with filtered tasks
                    tasks_map = {task['id']: task for task in all_tasks}
                
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
                
                stats = InfoPanelManager.calculate_stats(all_tasks)
                return tasks_tree, stats
                        
            except Error as e:
                print(f"Error listing tasks: {e}")
            finally:
                cursor.close()
                conn.close()
        
        # Default stats object to avoid template errors
        default_stats = {
            'total_time': 0,
            'importance_summary': {'Important': 0, 'Medium': 0, 'Normal': 0},
            'tag_summary': {}
        }
    def backfill_tree_fields(self):
        """Calculate and update level and branch_id for all tasks."""
        conn = get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, parent_id FROM tasks")
            all_tasks = cursor.fetchall()
            
            tasks_map = {t['id']: t for t in all_tasks}
            updates = []

            for task in all_tasks:
                level = 0
                current = task
                path = []
                
                # Traverse up to find root
                while current['parent_id']:
                    path.append(current['id'])
                    parent = tasks_map.get(current['parent_id'])
                    if not parent:
                        break # Orphaned task
                    current = parent
                    level += 1
                
                # current is now root
                branch_id = str(current['id'])
                updates.append((level, branch_id, task['id']))
            
            # Batch update
            cursor.close() # Switch to normal cursor for updates
            cursor = conn.cursor()
            update_query = "UPDATE tasks SET level = %s, branch_id = %s WHERE id = %s"
            cursor.executemany(update_query, updates)
            conn.commit()
            print(f"Backfilled {len(updates)} tasks with tree fields.")
            return True
            
        except Error as e:
            print(f"Error backfilling tree fields: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

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

    def update_task(self, user_id, task_id, title=None, time_minutes=None, importance=None, description=None, due_at=None):
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
                
                tags_to_add = []
                if title is not None:
                    # Extract tags before cleaning title
                    tags_to_add = extract_tags_from_text(title)
                    # Clean title
                    title = strip_tags_from_text(title)
                    
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

                if due_at is not None:
                    # Expecting due_at to be a string in ISO format or None to clear
                    if due_at == '':
                        updates.append("due_at = NULL")
                    else:
                        updates.append("due_at = %s")
                        params.append(due_at)

                if not updates:
                    return True
                
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
                
                cursor.execute(query, tuple(params))
                conn.commit()

                # Handle Tags
                if tags_to_add:
                    ctask = CTask(user_id, task_id)
                    for tag in tags_to_add:
                        ctask.add_tag(tag)

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
        ctask = CTask(user_id, task_id)
        if ctask.fields:
            return ctask.remove_ai_suggestion(item_text)
        return False

    def toggle_ai_suggestion_item(self, user_id, task_id, item_text):
        """Toggle the completion status of a specific suggestion item."""
        ctask = CTask(user_id, task_id)
        if ctask.fields:
            return ctask.toggle_ai_suggestion(item_text)
        return False

    def edit_ai_suggestion_item(self, user_id, task_id, old_text, new_text, new_time=None):
        """Update the text and optionally time of a specific suggestion item."""
        ctask = CTask(user_id, task_id)
        if ctask.fields:
            return ctask.edit_ai_suggestion(old_text, new_text, new_time)
        return False

    def hide_task(self, user_id, task_id, duration_str):
        """Hide task for a certain duration."""
        import datetime
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                now = datetime.datetime.now()
                hide_until = now
                if duration_str == '1h':
                    hide_until = now + datetime.timedelta(hours=1)
                elif duration_str == 'tomorrow':
                    hide_until = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=8)
                elif duration_str == 'next_week':
                    hide_until = now + datetime.timedelta(days=7)
                
                query = "UPDATE tasks SET hide_until = %s WHERE id = %s AND user_id = %s"
                cursor.execute(query, (hide_until, task_id, user_id))
                conn.commit()
                return True
            except Error as e:
                print(f"Error hiding task: {e}")
            finally:
                cursor.close()
                conn.close()
        return False

    def toggle_task_folding(self, user_id, task_id):
        """Toggle the is_folded state of a task."""
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = "UPDATE tasks SET is_folded = 1 - is_folded WHERE id = %s AND user_id = %s"
                cursor.execute(query, (task_id, user_id))
                conn.commit()
                return True
            except Error as e:
                print(f"Error toggling task folding: {e}")
            finally:
                cursor.close()
                conn.close()
        return False
