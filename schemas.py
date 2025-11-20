"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# App-specific schemas

class ContactMessage(BaseModel):
    """
    Contact form submissions
    Collection: "contactmessage"
    """
    name: str = Field(..., min_length=2, max_length=100, description="Meno odosielateľa")
    email: EmailStr = Field(..., description="Email odosielateľa")
    message: str = Field(..., min_length=5, max_length=2000, description="Správa")

class ChatMessage(BaseModel):
    """
    Public chat messages
    Collection: "chatmessage"
    """
    name: str = Field(..., min_length=2, max_length=60, description="Zobrazované meno")
    content: str = Field(..., min_length=1, max_length=500, description="Text správy")

class VideoItem(BaseModel):
    """
    Video items for the public gallery
    Collection: "videoitem"
    """
    title: str = Field(..., min_length=2, max_length=140, description="Názov videa")
    url: str = Field(..., description="URL na video (YouTube, MP4 alebo iné externé umiestnenie)")
    thumbnail: Optional[str] = Field(None, description="Náhľadový obrázok (URL)")
    description: Optional[str] = Field(None, max_length=500, description="Krátky popis videa")
    created_at: Optional[str] = Field(None, description="Čas pridania ISO8601")
