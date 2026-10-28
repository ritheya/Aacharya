from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Paper, Question, AuditLog, Mark, Resource, Topic
import rules, ai

Base.metadata.create_all(engine)
app = FastAPI(title="Aacharya - AI Teaching Co-Pilot")

# Allow the React dev server (and a locally opened page) to call this API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def audit(db, action, entity, entity_id, details=""):
    db.add(AuditLog(action=action, entity=entity, entity_id=entity_id, details=details))

# ---------- 1. AI question paper (always saved as DRAFT) ----------
class GenerateReq(BaseModel):
    subject: str
    topics: list[str]
    total_questions: int = Field(10, ge=1, le=50)
    bloom_mix: dict[str, int] = {"Remember": 30, "Apply": 40, "Analyze": 30}  # percentages

@app.post("/papers/generate")
def generate(req: GenerateReq, db: Session = Depends(get_db)):
    if sum(req.bloom_mix.values()) != 100:
        raise HTTPException(400, "bloom_mix must add up to 100")
    try:
        items = ai.validate(ai.generate_questions(req.subject, req.topics, req.total_questions, req.bloom_mix))
    except Exception as e:
        raise HTTPException(502, f"AI generation failed: {e}")
    paper = Paper(subject=req.subject, status="draft", questions=[Question(**q) for q in items])
    db.add(paper); db.flush()
    audit(db, "generated", "paper", paper.id, f"{len(items)} questions, status=draft")
    db.commit()
    return get_paper(paper.id, db)

@app.get("/papers")
def list_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).order_by(Paper.id.desc()).all()
    return [get_paper(p.id, db) for p in papers]

@app.get("/papers/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    p = db.get(Paper, paper_id)
    if not p: raise HTTPException(404, "Paper not found")
    return {"id": p.id, "subject": p.subject, "status": p.status,
            "questions": [{"id": q.id, "text": q.text, "bloom_level": q.bloom_level, "marks": q.marks} for q in p.questions]}

# ---------- 2. Human-in-the-loop approval ----------
class ReviewReq(BaseModel):
    decision: str  # "approve" or "reject"
    comment: str = ""

@app.post("/papers/{paper_id}/review")
def review(paper_id: int, req: ReviewReq, db: Session = Depends(get_db)):
    p = db.get(Paper, paper_id)
    if not p: raise HTTPException(404, "Paper not found")
    if req.decision not in ("approve", "reject"):
        raise HTTPException(400, "decision must be approve or reject")
    if p.status != "draft":
        raise HTTPException(409, f"Paper already {p.status}; cannot change")
    p.status = "approved" if req.decision == "approve" else "rejected"
    audit(db, req.decision, "paper", p.id, req.comment)
    db.commit()
    return {"id": p.id, "status": p.status}

# ---------- 3. At-risk students (rule engine) ----------
@app.get("/students/at-risk")
def at_risk(db: Session = Depends(get_db)):
    return rules.evaluate(db)

# ---------- 4. Resource recommendations by weak topic ----------
@app.get("/students/{student_id}/resources")
def recommend(student_id: int, db: Session = Depends(get_db)):
    weak = (db.query(Topic.id, Topic.name).join(Mark, Mark.topic_id == Topic.id)
            .filter(Mark.student_id == student_id).group_by(Topic.id, Topic.name)
            .having(func.avg(Mark.score) < 50).all())
    out = []
    for tid, tname in weak:
        res = db.query(Resource).filter(Resource.topic_id == tid).all()
        out.append({"weak_topic": tname, "resources": [{"title": r.title, "url": r.url} for r in res]})
    return out

# ---------- 5. Audit trail ----------
@app.get("/audit")
def audit_trail(db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).all()
    return [{"id": r.id, "action": r.action, "entity": f"{r.entity}#{r.entity_id}", "details": r.details, "at": r.created_at} for r in rows]