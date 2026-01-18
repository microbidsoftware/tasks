from db_manager import get_db_connection
from mysql.connector import Error

class CTask:
    def __init__(self, user_id, task_id):
        self.user_id = user_id
        self.task_id = task_id
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
