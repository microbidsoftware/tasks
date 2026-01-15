import unittest
from app import app
from db_manager import get_db_connection

class BasicTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.secret_key = 'test_secret'
        self.app = app.test_client()

    def test_main_page_redirect_or_login(self):
        # Without login, should show login button
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login with Google', response.data)

    def test_add_task_logged_in(self):
        # Create a dummy user in DB
        conn = get_db_connection()
        user_id = None
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (google_id, email, name) VALUES ('test_sub', 'test@example.com', 'Test User')")
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()

        # Mock session with real user_id
        with self.app.session_transaction() as sess:
            sess['user'] = {
                'id': user_id,
                'name': 'Test User',
                'email': 'test@example.com'
            }
            
        # Add a task
        response = self.app.post('/add_task', data=dict(title="Web Test Task"), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should be redirected to index and see the task
        self.assertIn(b'Web Test Task', response.data)
        
        # Cleanup
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE title='Web Test Task'")
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()

if __name__ == "__main__":
    unittest.main()

