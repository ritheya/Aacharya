import os, json, re
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

def build_prompt(subject, topics, total, mix):
    counts = {lvl: round(total * pct / 100) for lvl, pct in mix.items()}
    return f"""You are an experienced teacher. Write a question paper for the subject "{subject}"
covering these topics: {", ".join(topics)}.

Create exactly these numbers of questions per Bloom's Taxonomy level: {json.dumps(counts)}.Write maths in plain text (for example x^2 or "integral of x dx"). Do not use LaTeX or backslashes.Write maths in plain text (for example x^2 or "integral of x dx"). Do not use LaTeX or backslashes.Write maths in plain text (for example x^2 or "integral of x dx"). Do not use LaTeX or backslashes.
Return ONLY a JSON array, no other text. Each item:
{{"text": "...", "bloom_level": "one of {BLOOM_LEVELS}", "marks": integer}}"""

def parse_json(text):
    """Pull the JSON out of the model's reply, even if it adds extra text."""
    text = text.strip().replace("```json", "").replace("```", "").strip()
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    # Models write maths like \int or \frac, which breaks JSON.
    # Double any backslash that is not already a valid escape.
    text = re.sub(r'\\(["\\/]|u[0-9a-fA-F]{4})|\\',
                  lambda m: m.group(0) if m.group(1) else "\\\\", text)
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("questions", [])
    return data

def generate_with_ollama(subject, topics, total, mix):
    import httpx
    r = httpx.post("http://localhost:11434/api/chat", timeout=300, json={
        "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
        "stream": False,
        "messages": [{"role": "user", "content": build_prompt(subject, topics, total, mix)}],
    })
    r.raise_for_status()
    return parse_json(r.json()["message"]["content"])

def generate_questions(subject, topics, total, mix):
    if os.getenv("USE_OLLAMA"):
        return generate_with_ollama(subject, topics, total, mix)
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:  # offline demo mode so the app still runs without a key
        return [{"text": f"[MOCK] {lvl} question on {topics[i % len(topics)]}", "bloom_level": lvl, "marks": 2}
                for i, lvl in enumerate([l for l, p in mix.items() for _ in range(round(total * p / 100))])]
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(model=MODEL, max_tokens=2000,
        messages=[{"role": "user", "content": build_prompt(subject, topics, total, mix)}])
    return parse_json(msg.content[0].text)

def validate(items):
    """Never trust AI output: check structure before saving."""
    clean = []
    for q in items:
        if not isinstance(q, dict) or not q.get("text"):
            continue
        if q.get("bloom_level") not in BLOOM_LEVELS:
            continue
        clean.append({"text": str(q["text"]), "bloom_level": q["bloom_level"], "marks": int(q.get("marks", 1))})
    if not clean:
        raise ValueError("AI returned no valid questions")
    return clean