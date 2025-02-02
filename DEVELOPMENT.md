# Crumple Development Guide

This guide explains the codebase structure and how to add or modify functionality across different components.

## Project Structure

```
backend/
  ├── app/
  │   ├── api/v1/endpoints/   # API endpoints
  │   ├── core/              # Core functionality
  │   ├── models/            # Database models
  │   └── schemas/           # Pydantic schemas
frontend/
  ├── app.py                 # Flask application
  ├── static/                # Static assets
  └── templates/             # Jinja2 templates
```

## Backend Development

### Adding New API Endpoints

Location: `backend/app/api/v1/endpoints/`

1. Create or modify endpoint files following this pattern:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ....core.database import get_db
from ....models import YourModel
from ....schemas import YourSchema

router = APIRouter()

@router.post("/", response_model=YourSchema)
async def create_item(
    item: YourSchema,
    db: AsyncSession = Depends(get_db)
):
    db_item = YourModel(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
```

2. Register your router in `backend/app/api/v1/api.py`:

```python
from .endpoints import your_endpoint

api_router.include_router(
    your_endpoint.router,
    prefix="/your-endpoint",
    tags=["Your Tag"]
)
```

### Adding Database Models

Location: `backend/app/models/`

1. Create or modify model files:

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base

class YourModel(Base):
    __tablename__ = "your_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("parent_table.id"))
    
    parent = relationship("ParentModel", back_populates="children")
```

2. Create a migration after model changes:
```bash
alembic revision --autogenerate -m "add your table"
alembic upgrade head
```

### Adding Schemas

Location: `backend/app/schemas/`

1. Create or modify schema files:

```python
from pydantic import BaseModel
from typing import Optional, List

class YourBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None

class YourCreateSchema(YourBaseSchema):
    parent_id: Optional[int] = None

class YourSchema(YourBaseSchema):
    id: int
    
    class Config:
        orm_mode = True
```

## Frontend Development

### Adding Flask Routes

Location: `frontend/app.py`

1. Add new routes following this pattern:

```python
@app.route('/your-route')
def your_route():
    try:
        # Fetch data from backend API
        response = requests.get(f"{BACKEND_URL}/api/v1/your-endpoint/")
        data = response.json() if response.ok else []
        
        return render_template('your_template.html', data=data)
    except requests.exceptions.RequestException as e:
        return render_template('your_template.html', data=[], error=str(e))
```

2. Create corresponding template in `frontend/templates/`:

```html
{% extends "base.html" %}

{% block title %}Your Page{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto p-6">
    <!-- Your content here -->
</div>
{% endblock %}
```

### Adding JavaScript Functions

Location: `frontend/static/`

1. Create or modify JS files:

```javascript
function yourFunction() {
    fetch('/api/v1/your-endpoint/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            // Your data here
        })
    })
    .then(response => {
        if (response.ok) {
            showToast('Success message');
            // Handle success
        } else {
            showToast('Error message', 'error');
        }
    })
    .catch(error => {
        showToast('Error message', 'error');
        console.error('Error:', error);
    });
}
```

2. Include in your template:

```html
{% block scripts %}
<script src="{{ url_for('static', filename='your-script.js') }}"></script>
{% endblock %}
```

## Common Patterns

### API Endpoints

1. **CRUD Operations**:
   - GET /items/ - List all items
   - GET /items/{id} - Get single item
   - POST /items/ - Create item
   - PUT /items/{id} - Update item
   - DELETE /items/{id} - Delete item

2. **Query Parameters**:
   - Filtering: ?filter=value
   - Pagination: ?skip=0&limit=10
   - Sorting: ?sort=field

### Database Operations

1. **Querying**:
```python
result = await db.execute(
    select(Model).where(Model.field == value)
)
item = result.scalars().first()
```

2. **Relationships**:
```python
# One-to-Many
parent = relationship("Parent", back_populates="children")
children = relationship("Child", back_populates="parent")

# Many-to-Many
items = relationship("Item", secondary=association_table)
```

### Frontend Components

1. **Modal Pattern**:
```html
<div id="your-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <!-- Modal content -->
    </div>
</div>
```

2. **Form Handling**:
```javascript
document.getElementById('your-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    // Handle form submission
});
```

## Best Practices

1. **Error Handling**:
   - Use try/except blocks consistently
   - Return appropriate HTTP status codes
   - Provide meaningful error messages

2. **Database**:
   - Use async/await with SQLAlchemy
   - Properly close database connections
   - Use transactions for multiple operations

3. **Frontend**:
   - Follow Tailwind CSS patterns
   - Use consistent JavaScript patterns
   - Implement proper error handling and loading states

4. **API Design**:
   - Use consistent naming conventions
   - Implement proper validation
   - Document all endpoints

## Testing

1. **Backend Tests**:
```python
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_your_endpoint():
    response = client.get("/api/v1/your-endpoint/")
    assert response.status_code == 200
```

2. **Frontend Tests**:
```python
def test_your_route():
    response = client.get("/your-route")
    assert response.status_code == 200
    assert b"Expected Content" in response.data
```

## Common Tasks

1. **Adding a New Feature**:
   - Add models if needed
   - Create/update schemas
   - Implement API endpoints
   - Add frontend routes and templates
   - Implement frontend JavaScript
   - Add tests
   - Update documentation

2. **Modifying Existing Feature**:
   - Update models if needed
   - Run database migrations
   - Update API endpoints
   - Modify frontend code
   - Update tests
   - Update documentation

3. **Database Changes**:
   - Modify models
   - Create migration
   - Test migration
   - Update related code
   - Run migration in production

Remember to always:
- Follow existing patterns and conventions
- Write clear documentation
- Add appropriate tests
- Handle errors properly
- Consider security implications
