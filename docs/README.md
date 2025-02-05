# Crumple Application Documentation

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Container Setup](#container-setup)
3. [Database Schema](#database-schema)
4. [Frontend Structure](#frontend-structure)
5. [Backend Development](#backend-development)
6. [API Documentation](#api-documentation)
7. [Adding New Features](#adding-new-features)
8. [Templates and Pages](#templates-and-pages)

## System Architecture

The application is built using Flask (Python) and follows a modular architecture with the following main components:

- **Models**: Database models using SQLAlchemy (`app/models/`)
- **Routes**: HTTP endpoints (`app/routes/`)
- **Templates**: Jinja2 templates for rendering pages (`app/templates/`)
- **Services**: Business logic and external service integrations (`app/services/`)
- **Tasks**: Background tasks (`app/tasks/`)
- **API**: RESTful API endpoints (`app/routes/api/v1/`)

## Container Setup

The application uses Docker for containerization with three main services defined in `docker-compose.yml`:

1. **Web Application**: Main Flask application
   - Dockerfile: `docker/app.Dockerfile`
   - Handles web requests and API endpoints

2. **Worker**: Background task processor
   - Dockerfile: `docker/worker.Dockerfile`
   - Processes asynchronous tasks like sync operations

3. **Database**: PostgreSQL database
   - Initialized with `init.sql`
   - Stores application data

## Database Schema

The application uses SQLAlchemy ORM with the following main models:

- **User** (`app/models/user.py`): User authentication and management
- **Cluster** (`app/models/cluster.py`): Cluster management
- **Device** (`app/models/device.py`): Device information
- **Connection** (`app/models/connection.py`): Network connections
- **Settings** (`app/models/settings.py`): Application settings
- **DeviceRole** (`app/models/device_role.py`): Device role definitions

## Frontend Structure

The frontend is template-based using Jinja2 with a base template structure:

### Base Template
Location: `app/templates/base.html`
This template provides:
- Common HTML structure
- Navigation menu
- CSS/JS includes

### Adding New Pages

1. Create a new template in `app/templates/`:
   ```html
   {% extends "base.html" %}
   {% block content %}
   Your page content here
   {% endblock %}
   ```

2. Add a route in `app/routes/`:
   ```python
   from flask import render_template
   
   @app.route('/your-page')
   def your_page():
       return render_template('your-page.html')
   ```

3. Add menu item to `base.html`:
   ```html
   <nav>
     <!-- Add your new menu item -->
     <a href="{{ url_for('your_page') }}">Your Page</a>
   </nav>
   ```

## Backend Development

### Adding New Routes

1. Create a new route file in `app/routes/`:
   ```python
   from flask import Blueprint, render_template
   
   bp = Blueprint('your_feature', __name__)
   
   @bp.route('/your-feature')
   def index():
       return render_template('your-feature.html')
   ```

2. Register blueprint in `app/__init__.py`:
   ```python
   from app.routes.your_feature import bp as your_feature_bp
   app.register_blueprint(your_feature_bp)
   ```

### Adding New Models

1. Create a new model in `app/models/`:
   ```python
   from app import db
   
   class YourModel(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(64), unique=True)
   ```

2. Create a migration:
   ```bash
   flask db migrate -m "add your model"
   flask db upgrade
   ```

## API Documentation

The API is versioned and located in `app/routes/api/v1/`. To add new API endpoints:

1. Create a new file in `app/routes/api/v1/`:
   ```python
   from flask import Blueprint, jsonify
   
   bp = Blueprint('your_api', __name__)
   
   @bp.route('/api/v1/your-endpoint', methods=['GET'])
   def get_data():
       return jsonify({'status': 'success'})
   ```

2. Register in `app/routes/api/v1/__init__.py`:
   ```python
   from app.routes.api.v1.your_api import bp as your_api_bp
   app.register_blueprint(your_api_bp)
   ```

## Adding New Features

To add a new feature:

1. **Plan Your Feature**
   - Determine required models
   - Design API endpoints
   - Plan UI components

2. **Implement Backend**
   - Add models
   - Create migrations
   - Add routes
   - Implement services

3. **Implement Frontend**
   - Create templates
   - Add static assets
   - Update navigation

4. **Add Tests**
   - Unit tests
   - Integration tests

### Example: Adding a New Feature

Let's say you want to add a "Projects" feature:

1. Create model (`app/models/project.py`):
   ```python
   from app import db
   
   class Project(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(64))
       description = db.Column(db.Text)
   ```

2. Create template (`app/templates/projects.html`):
   ```html
   {% extends "base.html" %}
   {% block content %}
   <h1>Projects</h1>
   <div class="projects-list">
       {% for project in projects %}
           <div class="project-card">
               <h2>{{ project.name }}</h2>
               <p>{{ project.description }}</p>
           </div>
       {% endfor %}
   </div>
   {% endblock %}
   ```

3. Add routes (`app/routes/projects.py`):
   ```python
   from flask import Blueprint, render_template
   from app.models.project import Project
   
   bp = Blueprint('projects', __name__)
   
   @bp.route('/projects')
   def index():
       projects = Project.query.all()
       return render_template('projects.html', projects=projects)
   ```

4. Add API endpoints (`app/routes/api/v1/projects.py`):
   ```python
   from flask import Blueprint, jsonify
   from app.models.project import Project
   
   bp = Blueprint('projects_api', __name__)
   
   @bp.route('/api/v1/projects', methods=['GET'])
   def list_projects():
       projects = Project.query.all()
       return jsonify([{
           'id': p.id,
           'name': p.name,
           'description': p.description
       } for p in projects])
   ```

## Templates and Pages

The application uses a template inheritance system:

### Template Structure
```
app/templates/
├── base.html          # Base template with common elements
├── index.html         # Home page
├── cluster.html       # Cluster management
├── settings.html      # Settings page
└── auth/
    └── login.html     # Authentication pages
```

### Creating New Pages with Templates

1. **Create Template File**:
   ```html
   {% extends "base.html" %}
   
   {% block title %}Your Page Title{% endblock %}
   
   {% block content %}
   <div class="container">
       <h1>Your Content</h1>
       <!-- Your page content here -->
   </div>
   {% endblock %}
   ```

2. **Add Static Assets** (if needed):
   - Place CSS in `app/static/css/`
   - Place JavaScript in `app/static/js/`
   - Place images in `app/static/images/`

3. **Create Route**:
   ```python
   from flask import render_template
   
   @app.route('/your-page')
   def your_page():
       # Add any required data processing here
       return render_template('your-page.html', data=your_data)
   ```

4. **Update Navigation**:
   Edit `base.html` to add your page to the navigation menu:
   ```html
   <nav>
       <ul>
           <li><a href="{{ url_for('index') }}">Home</a></li>
           <li><a href="{{ url_for('your_page') }}">Your Page</a></li>
       </ul>
   </nav>
