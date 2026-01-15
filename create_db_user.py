import mysql.connector

def setup_permissions():
    root_password = "Test90908!"
    new_user = "task_user"
    new_password = "TaskUserPass1!"
    database = "task_db"

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=root_password
        )
        cursor = conn.cursor()

        # Create Database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        print(f"Database {database} created or exists.")

        # Create User (drop if exists to reset)
        cursor.execute(f"DROP USER IF EXISTS '{new_user}'@'localhost'")
        cursor.execute(f"CREATE USER '{new_user}'@'localhost' IDENTIFIED BY '{new_password}'")
        print(f"User {new_user} created.")

        # Grant Privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON {database}.* TO '{new_user}'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        print(f"Privileges granted to {new_user} on {database}.")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_permissions()
