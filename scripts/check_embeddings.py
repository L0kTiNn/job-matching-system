import sys
sys.path.append('.')

from backend.app.database import DatabaseManager

db = DatabaseManager()
db.connect()

# Проверяем эмбеддинги вакансий
print(" ВАКАНСИИ С ЭМБЕДДИНГАМИ:")
db.cursor.execute("""
    SELECT id, title, 
           CASE WHEN embedding IS NULL THEN 'НЕТ' ELSE 'ЕСТЬ' END as has_embedding
    FROM vacancies
    ORDER BY id
""")
for row in db.cursor.fetchall():
    print(f"  Вакансия #{row[0]}: {row[1]} - эмбеддинг: {row[2]}")

# Проверяем эмбеддинги резюме
print("\n РЕЗЮМЕ С ЭМБЕДДИНГАМИ:")
db.cursor.execute("""
    SELECT id, title,
           CASE WHEN embedding IS NULL THEN 'НЕТ' ELSE 'ЕСТЬ' END as has_embedding
    FROM resumes
    ORDER BY id
""")
for row in db.cursor.fetchall():
    print(f"  Резюме #{row[0]}: {row[1]} - эмбеддинг: {row[2]}")

# Проверяем similarity напрямую
print("\n ПРЯМАЯ ПРОВЕРКА SIMILARITY:")
print("Вакансия 'Data Scientist' → Резюме 'Data Scientist':")

db.cursor.execute("""
    SELECT 
        v.id as vacancy_id, v.title as vacancy_title,
        r.id as resume_id, r.title as resume_title,
        1 - (r.embedding <=> v.embedding) as similarity
    FROM vacancies v
    CROSS JOIN resumes r
    WHERE v.title LIKE '%Data Scientist%'
      AND r.title LIKE '%Data Scientist%'
      AND v.embedding IS NOT NULL
      AND r.embedding IS NOT NULL
    LIMIT 1
""")

result = db.cursor.fetchone()
if result:
    print(f"  Similarity: {round(result[4] * 100, 1)}%")
    print(f"  Вакансия: {result[1]}")
    print(f"  Резюме: {result[3]}")
else:
    print("   НЕТ ДАННЫХ!")

db.close()
