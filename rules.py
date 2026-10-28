"""Rule engine: plain Python rules, NOT ML. Every flag carries its reasons (explainable)."""
from collections import defaultdict
from models import Mark, Student

LOW_AVG = 40         # average score below this
LOW_ATTENDANCE = 80  # attendance below this
DROP_POINTS = 10     # score fell by this much between last two exams

def evaluate(db):
    marks = db.query(Mark).order_by(Mark.student_id, Mark.exam_no).all()
    by_student = defaultdict(list)
    for m in marks:
        by_student[m.student_id].append(m)

    names = {s.id: s.name for s in db.query(Student).all()}
    flagged = []
    for sid, rows in by_student.items():
        reasons = []
        avg = sum(r.score for r in rows) / len(rows)
        att = sum(r.attendance for r in rows) / len(rows)

        if avg < LOW_AVG:
            reasons.append(f"Average score {avg:.0f} is below {LOW_AVG}")
        if att < LOW_ATTENDANCE:
            reasons.append(f"Attendance {att:.0f}% is below {LOW_ATTENDANCE}%")

        # compare average of the latest exam vs the one before it
        exams = sorted({r.exam_no for r in rows})
        if len(exams) >= 2:
            def exam_avg(n): 
                s = [r.score for r in rows if r.exam_no == n]
                return sum(s) / len(s)
            drop = exam_avg(exams[-2]) - exam_avg(exams[-1])
            if drop >= DROP_POINTS:
                reasons.append(f"Score dropped {drop:.0f} points in the latest exam")

        if reasons:
            level = "high" if len(reasons) >= 2 else "medium"
            flagged.append({"student_id": sid, "name": names[sid], "risk": level, "reasons": reasons})
    return sorted(flagged, key=lambda f: -len(f["reasons"]))
