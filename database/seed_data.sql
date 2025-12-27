@"
INSERT INTO users (email, password_hash, full_name, phone, role) VALUES
('ivanov@example.com', '`$2b`$12`$hash1', 'Иванов Иван Иванович', '+79001234567', 'jobseeker'),
('petrov@example.com', '`$2b`$12`$hash2', 'Петров Петр Петрович', '+79007654321', 'jobseeker'),
('hr@techcorp.ru', '`$2b`$12`$hash3', 'Сидорова Анна', '+79001112233', 'employer');

INSERT INTO resumes (user_id, title, summary, skills, desired_position, location) VALUES
(1, 'Python Backend Developer',
 '5 лет опыта разработки на Python',
 'Python, Django, FastAPI, PostgreSQL, Docker',
 'Senior Backend Developer',
 'Москва');

INSERT INTO vacancies (employer_id, title, description, requirements, salary_min, salary_max, location) VALUES
(3, 'Senior Python Developer',
 'Требуется опытный Python-разработчик',
 'Опыт от 3 лет, знание Django/FastAPI',
 200000, 300000, 'Москва');
"@ | Out-File -FilePath database/seed_data.sql -Encoding UTF8
