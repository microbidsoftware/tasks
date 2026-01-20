from flask import Flask, render_template_string

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    .children { border: 1px solid red; padding: 10px; }
    .task-container { border: 1px solid blue; margin: 5px; }
</style>
</head>
<body>
    {% macro render_task(task, level=0) %}
    <div id="task-container-{{ task.id }}" class="task-container">
        <div class="task-row">
            {{ task.title }}
        </div>
        
        {% if task.children %}
        <div id="children-{{ task.id }}" class="children">
            {% for child in task.children %}
            {{ render_task(child, level + 1) }}
            {% endfor %}
        </div>
        {% endif %}
    </div>
    {% endmacro %}

    {% for task in tasks %}
    {{ render_task(task) }}
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def index():
    tasks = [
        {
            'id': 1, 'title': 'Root Task', 'children': [
                {'id': 2, 'title': 'Subtask 1', 'children': []},
                {'id': 3, 'title': 'Subtask 2', 'children': []},
                {'id': 4, 'title': 'Subtask 3', 'children': []}
            ]
        }
    ]
    return render_template_string(TEMPLATE, tasks=tasks)

if __name__ == '__main__':
    app.run(port=5001)
