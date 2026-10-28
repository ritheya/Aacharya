from database import Base, engine, SessionLocal
from models import Student, Topic, Mark, Resource
Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
db = SessionLocal()
db.add_all([Student(name=n) for n in ["Anu", "Bala", "Charan", "Divya"]])
db.add_all([Topic(name=n) for n in ["Algebra", "Geometry", "Probability"]])
db.flush()
# (student, topic, exam, score, attendance)
data = [
 (1,1,1,80,95),(1,2,1,75,95),(1,1,2,82,96),(1,2,2,78,96),          # Anu: fine
 (2,1,1,70,80),(2,2,1,65,80),(2,1,2,40,78),(2,2,2,35,78),          # Bala: big drop
 (3,1,1,30,60),(3,3,1,35,60),(3,1,2,28,58),(3,3,2,32,58),          # Charan: low + low attendance
 (4,1,1,55,90),(4,3,1,45,90),(4,1,2,58,91),(4,3,2,48,91),          # Divya: ok
]
db.add_all([Mark(student_id=s,topic_id=t,exam_no=e,score=sc,attendance=a) for s,t,e,sc,a in data])
db.add_all([Resource(topic_id=1,title="Khan Academy: Algebra basics",url="https://www.khanacademy.org/math/algebra"),
            Resource(topic_id=3,title="Khan Academy: Probability",url="https://www.khanacademy.org/math/statistics-probability")])
db.commit(); print("Seeded.")
