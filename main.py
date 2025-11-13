import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from database import create_document, get_documents, db
from schemas import User, Blogpost, Contactmessage

app = FastAPI(title="Car Rental SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Car Rental SaaS Backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Auth (minimal mock — in real apps you'd hash/verify server-side)
class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password: str

@app.post("/api/auth/register")
def register_user(payload: RegisterPayload):
    # Note: we store only hash in a real app; here we keep plain for demo but put into password_hash field
    user_doc = User(name=payload.name, email=payload.email, password_hash=payload.password)
    try:
        inserted_id = create_document("user", user_doc)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Blog endpoints
@app.get("/api/blog", response_model=List[dict])
def list_blog_posts(limit: int = 10):
    try:
        posts = get_documents("blogpost", {}, limit)
        # Convert ObjectId to string for safe JSON
        for p in posts:
            if "_id" in p:
                p["id"] = str(p.pop("_id"))
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BlogCreatePayload(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: str
    cover_image: Optional[str] = None
    tags: Optional[List[str]] = []

@app.post("/api/blog")
def create_blog_post(payload: BlogCreatePayload):
    try:
        post = Blogpost(**payload.model_dump())
        inserted_id = create_document("blogpost", post)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Contact form
class ContactPayload(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

@app.post("/api/contact")
def submit_contact(payload: ContactPayload):
    try:
        msg = Contactmessage(**payload.model_dump())
        inserted_id = create_document("contactmessage", msg)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
