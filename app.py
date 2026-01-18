from flask import Flask, render_template, request, redirect, url_for, session
from task_manager import TaskManager
from db_manager import initialize_database, get_or_create_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') # Secure secret key

# Session Configuration for Localhost OAuth
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['SESSION_COOKIE_SECURE'] = False # Allow HTTP for dev
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Allow cookie on redirect


# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url=os.getenv('GOOGLE_DISCOVERY_URL'),
    client_kwargs={'scope': 'openid email profile'}
)

manager = TaskManager()

# Ensure DB is ready
initialize_database()

@app.route('/')
def index():
    user = session.get('user')
    if not user:
        return render_template('index.html', user=None, tasks=[])
    
    search_query = request.args.get('q')
    tag_filter = request.args.get('tag')
    importance_filter = request.args.get('importance')
    period_filter = request.args.get('period')
    
    tasks_tree, stats = manager.list_tasks(user['id'], search_query, tag_filter, importance_filter, period_filter)
    
    return render_template('index.html', user=user, tasks=tasks_tree, stats=stats, 
                           current_q=search_query, current_tag=tag_filter, 
                           current_importance=importance_filter, current_period=period_filter)

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    
    tasks_tree, stats = manager.list_tasks(user['id'])
    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/login')
def login():
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    return google.authorize_redirect(redirect_uri)

@app.route('/google/auth')
def auth():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        user_id = get_or_create_user(user_info)
        if user_id:
            session['user'] = {
                'id': user_id,
                'name': user_info.get('name'),
                'email': user_info.get('email'),
                'picture': user_info.get('picture')
            }
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/add_task', methods=['POST'])
def add_task_route():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    title = request.form.get('title')
    parent_id = request.form.get('parent_id')
    time_minutes = request.form.get('time_minutes')
    importance = request.form.get('importance', '')
    description = request.form.get('description')
    run_ai = request.form.get('run_ai', 'true') != 'false'
    due_at = request.form.get('due_at')
    
    if not due_at:
        due_at = None

    if title:
        manager.add_task(user['id'], title, parent_id, time_minutes, importance, description, run_ai=run_ai, due_at=due_at)
    return redirect(url_for('index'))

@app.route('/update_task', methods=['POST'])
def update_task_route():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    task_id = request.form.get('task_id')
    title = request.form.get('title')
    time_minutes = request.form.get('time_minutes')
    importance = request.form.get('importance')
    description = request.form.get('description')
    due_at = request.form.get('due_at')
    
    if task_id:
        manager.update_task(user['id'], task_id, title, time_minutes, importance, description, due_at=due_at)
        
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>', methods=['GET'])
def delete_task(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    manager.delete_task(user['id'], task_id)
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    manager.complete_task(user['id'], task_id)
    return redirect(url_for('index'))

@app.route('/uncomplete/<int:task_id>')
def uncomplete_task(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    manager.uncomplete_task(user['id'], task_id)
    return redirect(url_for('index'))

@app.route('/clear_suggestion/<int:task_id>')
def clear_suggestion(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    manager.clear_ai_suggestion(user['id'], task_id)
    return redirect(url_for('index'))

@app.route('/remove_suggestion_item/<int:task_id>')
def remove_suggestion_item(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    
    text = request.args.get('text')
    if text:
        manager.remove_ai_suggestion_item(user['id'], task_id, text)
    return redirect(url_for('index'))

@app.route('/toggle_suggestion_item/<int:task_id>')
def toggle_suggestion_item(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    
    text = request.args.get('text')
    if text:
        manager.toggle_ai_suggestion_item(user['id'], task_id, text)
    return redirect(url_for('index'))

@app.route('/edit_suggestion_item/<int:task_id>', methods=['POST'])
def edit_suggestion_item(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    
    old_text = request.form.get('old_text')
    new_text = request.form.get('new_text')
    new_time = request.form.get('new_time')
    
    if old_text and new_text:
        manager.edit_ai_suggestion_item(user['id'], task_id, old_text, new_text, new_time)
    return redirect(url_for('index'))


@app.route('/hide_task/<int:task_id>')
def hide_task(task_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
        
    duration = request.args.get('duration')
    if duration:
        manager.hide_task(user['id'], task_id, duration)
    return redirect(url_for('index'))

@app.route('/remove_tag/<int:task_id>/<int:tag_id>')
def remove_tag(task_id, tag_id):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    
    from ctask import CTask
    ctask = CTask(user['id'], task_id)
    ctask.remove_tag(tag_id)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

