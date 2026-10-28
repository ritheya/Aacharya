# Aacharya - AI Teaching Co-Pilot
Run:  pip install -r requirements.txt && python seed.py && uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
Real AI: set ANTHROPIC_API_KEY (without it, a mock generator is used)
PostgreSQL: set DATABASE_URL=postgresql://user:pass@localhost/aacharya
