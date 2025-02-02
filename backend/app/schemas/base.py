from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)

class BaseAPISchema(BaseSchema):
    """Base schema for API responses"""
    id: int
    created: datetime
    last_updated: datetime
