import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import create_document, get_documents, db
from schemas import InterviewSession
import random

app = FastAPI(title="AI Interview Prep API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Interview Prep Backend is running"}

@app.get("/test")
def test_database():
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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
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
    return response

# Simple in-app prompt templates for question generation per field
FIELD_QUESTION_BANK = {
    "Software Engineering": [
        "Explain the difference between processes and threads.",
        "What is a race condition and how do you prevent it?",
        "Describe SOLID principles.",
        "What is Big-O notation? Give examples.",
        "How does garbage collection work in managed languages?",
        "Explain REST vs GraphQL.",
        "What is a microservice and when would you use it?",
        "How does a hash table work?"
    ],
    "Data Science": [
        "Bias-variance tradeoff explanation.",
        "Difference between L1 and L2 regularization.",
        "How do you handle class imbalance?",
        "Explain precision, recall, and F1-score.",
        "What is cross-validation and why use it?",
        "When to use random forest vs gradient boosting?",
        "Interpretation of a confusion matrix.",
        "What is PCA and when to use it?"
    ],
    "Product Management": [
        "How do you prioritize a roadmap?",
        "Describe a time you handled conflicting stakeholder interests.",
        "How do you define success metrics for a feature?",
        "Walk through writing a PRD.",
        "How do you size a market?",
        "What is the difference between OKRs and KPIs?",
        "How do you run user interviews effectively?",
        "How would you analyze a drop in conversion?"
    ],
}

class GenerateRequest(BaseModel):
    field: str
    count: int = 6

class SessionCreateRequest(BaseModel):
    field: str
    questions: List[str]
    answers: Optional[List[str]] = None

@app.post("/api/generate")
def generate_questions(payload: GenerateRequest):
    bank = FIELD_QUESTION_BANK.get(payload.field)
    if not bank:
        raise HTTPException(status_code=400, detail="Unknown field")
    # Pick unique questions up to requested count
    k = min(len(bank), max(1, payload.count))
    qs = random.sample(bank, k)
    return {"questions": qs}

@app.post("/api/sessions")
def create_session(payload: SessionCreateRequest):
    session = InterviewSession(field=payload.field, questions=payload.questions, answers=payload.answers)
    inserted_id = create_document("interviewsession", session)
    return {"id": inserted_id}

@app.get("/api/sessions")
def list_sessions(limit: int = 20):
    docs = get_documents("interviewsession", {}, limit)
    # Convert ObjectId to string if present
    def serialize(doc):
        d = dict(doc)
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        return d
    return {"items": [serialize(d) for d in docs]}

