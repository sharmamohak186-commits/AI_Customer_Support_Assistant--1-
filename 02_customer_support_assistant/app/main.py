import json
import os
import sqlite3
from contextlib import closing
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()
app = FastAPI(title="AI Customer Support Assistant", version="1.0.0")
DB_PATH = os.getenv("DATABASE_PATH", "tickets.db")


class TicketRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=5, max_length=3000)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with closing(get_connection()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                suggested_reply TEXT NOT NULL
            )
        """)
        conn.commit()


@app.on_event("startup")
def startup():
    initialize_database()


def fallback_analysis(message: str):
    text = message.lower()
    if any(word in text for word in ["payment", "refund", "billing", "charged"]):
        category = "Billing"
    elif any(word in text for word in ["login", "password", "account", "sign in"]):
        category = "Account"
    elif any(word in text for word in ["broken", "error", "not working", "bug"]):
        category = "Technical"
    else:
        category = "General"
    priority = "High" if any(word in text for word in ["urgent", "immediately", "blocked", "cannot access"]) else "Normal"
    reply = f"Hi, thank you for contacting support. We have received your {category.lower()} request and will review it. Please share any relevant details so we can help."
    return category, priority, reply


async def analyze_with_openai(message: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_analysis(message)
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        result = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": 'Classify the support message. Return only JSON with keys "category" (Billing, Account, Technical, General), "priority" (High or Normal), and "reply" (a short polite suggested response).'},
                {"role": "user", "content": message}
            ],
            temperature=0.2,
        )
        data = json.loads(result.choices[0].message.content or "{}")
        allowed_categories = {"Billing", "Account", "Technical", "General"}
        category = data.get("category", "General")
        priority = data.get("priority", "Normal")
        if category not in allowed_categories:
            category = "General"
        if priority not in {"High", "Normal"}:
            priority = "Normal"
        reply = str(data.get("reply", "Thank you for contacting support. We will review your request."))[:1000]
        return category, priority, reply
    except Exception:
        # A service/API failure should not prevent ticket creation.
        return fallback_analysis(message)


@app.get("/")
def health():
    return {"status": "ok", "docs": "/docs"}


@app.post("/tickets")
async def create_ticket(ticket: TicketRequest):
    category, priority, reply = await analyze_with_openai(ticket.message)
    try:
        with closing(get_connection()) as conn:
            cursor = conn.execute(
                "INSERT INTO tickets (customer_name, message, category, priority, suggested_reply) VALUES (?, ?, ?, ?, ?)",
                (ticket.customer_name, ticket.message, category, priority, reply),
            )
            conn.commit()
            ticket_id = cursor.lastrowid
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")
    return {"id": ticket_id, "category": category, "priority": priority, "suggested_reply": reply}


@app.get("/tickets")
def list_tickets():
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT id, customer_name, message, category, priority, suggested_reply FROM tickets ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]
