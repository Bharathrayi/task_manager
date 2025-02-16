# app.py
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    deadline = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.strftime('%Y-%m-%d'),
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

def suggest_priority(deadline):
    """Calculate priority based on deadline proximity"""
    deadline_date = deadline if isinstance(deadline, datetime) else datetime.strptime(deadline, "%Y-%m-%d")
    today = datetime.now()
    
    if deadline_date <= today + timedelta(days=1):
        return "High"
    elif deadline_date <= today + timedelta(days=3):
        return "Medium"
    return "Low"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.json
    deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
    priority = suggest_priority(deadline)
    
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        deadline=deadline,
        priority=priority
    )
    
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    if 'deadline' in data:
        task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
        task.priority = suggest_priority(task.deadline)
    task.status = data.get('status', task.status)
    
    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

@app.route('/api/analytics')
def get_analytics():
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    pending_tasks = total_tasks - completed_tasks
    
    return jsonify({
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
