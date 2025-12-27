@"
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(20) CHECK (role IN ('jobseeker', 'employer')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    skills TEXT,
    experience TEXT,
    education TEXT,
    desired_position VARCHAR(255),
    desired_salary INTEGER,
    location VARCHAR(255),
    embedding vector(768),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vacancies (
    id SERIAL PRIMARY KEY,
    employer_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    location VARCHAR(255),
    embedding vector(768),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    cover_letter TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resume_id, vacancy_id)
);

CREATE INDEX idx_resumes_user ON resumes(user_id);
CREATE INDEX idx_resumes_embedding ON resumes USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_vacancies_employer ON vacancies(employer_id);
CREATE INDEX idx_vacancies_embedding ON vacancies USING hnsw (embedding vector_cosine_ops);
"@ | Out-File -FilePath database/schema.sql -Encoding UTF8
