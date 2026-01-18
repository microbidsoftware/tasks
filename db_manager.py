import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    """Connect to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            database=os.getenv('MYSQL_DATABASE'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def initialize_database():
    """Create the tasks table if it doesn't exist."""
    try:
        # Connect without database to create it if needed
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD')
        )
        cursor = conn.cursor()
        
        db_name = os.getenv('MYSQL_DATABASE')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.database = db_name
        
        create_users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            google_id VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_users_table_query)

        create_table_query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            parent_id INT,
            time_minutes INT DEFAULT 0,
            ai_suggestion TEXT,
            importance VARCHAR(50),
            description TEXT,
            hide_until TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            due_at TIMESTAMP NULL,
            user_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_table_query)

        create_tags_table_query = """
        CREATE TABLE IF NOT EXISTS tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_tag_user (name, user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_tags_table_query)

        create_task_tags_table_query = """
        CREATE TABLE IF NOT EXISTS task_tags (
            task_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (task_id, tag_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_task_tags_table_query)
        
        # Check if user_id column exists (migration 1)
        cursor.execute("SHOW COLUMNS FROM tasks LIKE 'user_id'")
        if not cursor.fetchone():
            print("Adding user_id column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN user_id INT")
            cursor.execute("ALTER TABLE tasks ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE")

        # Check if description column exists (migration 3)
        cursor.execute("SHOW COLUMNS FROM tasks LIKE 'description'")
        if not cursor.fetchone():
            print("Adding description column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN description TEXT")

        # Check if importance column exists (migration 2)
        cursor.execute("SHOW COLUMNS FROM tasks LIKE 'importance'")
        if not cursor.fetchone():
            print("Adding importance column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN importance VARCHAR(50)")

        # Check if hide_until column exists (migration 4)
        cursor.execute("SHOW COLUMNS FROM tasks LIKE 'hide_until'")
        if not cursor.fetchone():
            print("Adding hide_until column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN hide_until TIMESTAMP NULL")

        # Check if completed_at column exists (migration 5)
        cursor.execute("SHOW COLUMNS FROM tasks LIKE 'completed_at'")
        if not cursor.fetchone():
            print("Adding completed_at column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP NULL")

        # Check if due_at column exists (migration 6)
        cursor.execute("SHOW COLUMNS FROM tasks LIKE 'due_at'")
        if not cursor.fetchone():
            print("Adding due_at column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN due_at TIMESTAMP NULL")

        conn.commit()
        print("Database and tables initialized successfully.")
        
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
            cursor.close()
            conn.close()

def get_or_create_user(user_info):
    """Get existing user or create a new one based on Google info."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE google_id = %s", (user_info['sub'],))
            user = cursor.fetchone()
            
            if user:
                return user['id']
            else:
                # Create new user
                query = "INSERT INTO users (google_id, email, name) VALUES (%s, %s, %s)"
                cursor.execute(query, (user_info['sub'], user_info['email'], user_info.get('name', '')))
                conn.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"Error managing user: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    return None

if __name__ == '__main__':
    initialize_database()
