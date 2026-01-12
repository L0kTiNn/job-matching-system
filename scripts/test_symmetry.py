import sys
sys.path.append('.')

from backend.app.database import DatabaseManager

db = DatabaseManager()
db.connect()

print("🔍 ТЕСТ СИММЕТРИЧНОСТИ:\n")

# Находим ID резюме и вакансии Data Scientist
db.cursor.execute("SELECT id FROM resumes WHERE title LIKE '%Data Scientist%' LIMIT 1")
resume_id = db.cursor.fetchone()[0]

db.cursor.execute("SELECT id FROM vacancies WHERE title LIKE '%Data Scientist%' LIMIT 1")
vacancy_id = db.cursor.fetchone()[0]

print(f"📄 Резюме Data Scientist ID: {resume_id}")
print(f"💼 Вакансия Data Scientist ID: {vacancy_id}\n")

# 1. Резюме → Вакансия (как работает сейчас)
print("📊 РЕЗЮМЕ → ВАКАНСИЯ:")
similar_vacancies = db.find_similar_vacancies(resume_id, limit=5)
for vac in similar_vacancies:
    if vac[0] == vacancy_id:
        print(f"  ✅ Вакансия #{vac[0]}: {vac[1]} - {round(vac[-1] * 100, 1)}%")

# 2. Вакансия → Резюме (как работает сейчас)
print("\n📊 ВАКАНСИЯ → РЕЗЮМЕ:")
similar_resumes = db.find_similar_resumes(vacancy_id, limit=5)
for res in similar_resumes:
    if res[0] == resume_id:
        print(f"  ✅ Резюме #{res[0]}: {res[1]} - {round(res[-1] * 100, 1)}%")

# 3. ПРЯМОЙ SQL (должен быть симметричным!)
print("\n🔬 ПРЯМАЯ ПРОВЕРКА SQL:\n")

# Резюме → Вакансия
db.cursor.execute("""
    SELECT 1 - (v.embedding <=> r.embedding) as similarity
    FROM resumes r, vacancies v
    WHERE r.id = %s AND v.id = %s
""", (resume_id, vacancy_id))
sim1 = db.cursor.fetchone()[0]
print(f"  Резюме #{resume_id} → Вакансия #{vacancy_id}: {round(sim1 * 100, 1)}%")

# Вакансия → Резюме (должно быть ТО ЖЕ САМОЕ!)
db.cursor.execute("""
    SELECT 1 - (r.embedding <=> v.embedding) as similarity
    FROM resumes r, vacancies v
    WHERE r.id = %s AND v.id = %s
""", (resume_id, vacancy_id))
sim2 = db.cursor.fetchone()[0]
print(f"  Вакансия #{vacancy_id} → Резюме #{resume_id}: {round(sim2 * 100, 1)}%")

print(f"\n{'✅ СИММЕТРИЧНО!' if abs(sim1 - sim2) < 0.01 else '❌ НЕ СИММЕТРИЧНО!'}")

# 4. Проверяем, есть ли эмбеддинги
db.cursor.execute("""
    SELECT 
        r.embedding IS NOT NULL as resume_has_emb,
        v.embedding IS NOT NULL as vacancy_has_emb
    FROM resumes r, vacancies v
    WHERE r.id = %s AND v.id = %s
""", (resume_id, vacancy_id))
emb_check = db.cursor.fetchone()
print(f"\n📦 ЭМБЕДДИНГИ:")
print(f"  Резюме: {'✅ ЕСТЬ' if emb_check[0] else '❌ НЕТ'}")
print(f"  Вакансия: {'✅ ЕСТЬ' if emb_check[1] else '❌ НЕТ'}")

db.close()
