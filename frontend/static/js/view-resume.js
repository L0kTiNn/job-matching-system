const API_URL = 'http://localhost:8000';

// Получаем ID резюме из URL
const urlParams = new URLSearchParams(window.location.search);
const resumeId = urlParams.get('id');

if (!resumeId) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').innerHTML = `
        <div class="error-message">
             ID резюме не указан
        </div>
    `;
    document.getElementById('error').style.display = 'block';
} else {
    loadResume(resumeId);
}

async function loadResume(id) {
    try {
        const response = await fetch(`${API_URL}/api/resumes/${id}`);

        if (!response.ok) {
            throw new Error('Резюме не найдено');
        }

        const resume = await response.json();
        displayResume(resume);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').innerHTML = `
            <div class="error-message">
                 Ошибка загрузки резюме: ${error.message}
            </div>
        `;
        document.getElementById('error').style.display = 'block';
    }
}

function displayResume(resume) {
    // Скрываем загрузку
    document.getElementById('loading').style.display = 'none';
    document.getElementById('resumeContent').style.display = 'block';

    // Заголовок
    document.getElementById('resumeTitle').textContent = resume.title;

    // Мета-информация
    let metaInfo = [];
    if (resume.location) {
        metaInfo.push(`· ${resume.location}`);
    }
    if (resume.desired_salary) {
        metaInfo.push(`💰 от ${resume.desired_salary.toLocaleString()} ₽`);
    }
    if (resume.created_at) {
        const date = new Date(resume.created_at);
        metaInfo.push(`📅 Создано: ${date.toLocaleDateString('ru-RU')}`);
    }

    if (metaInfo.length > 0) {
        document.getElementById('resumeLocation').textContent = metaInfo[0];
        if (metaInfo.length > 1) {
            document.getElementById('resumeSalary').textContent = ' • ' + metaInfo[1];
        }
        if (metaInfo.length > 2) {
            document.getElementById('resumeDate').textContent = ' • ' + metaInfo[2];
        }
    }

    // О себе
    if (resume.summary) {
        document.getElementById('resumeSummary').textContent = resume.summary;
        document.getElementById('summarySection').style.display = 'block';
    }

    // Навыки
    if (resume.skills) {
        document.getElementById('resumeSkills').textContent = resume.skills;
        document.getElementById('skillsSection').style.display = 'block';
    }

    // Опыт
    if (resume.experience) {
        document.getElementById('resumeExperience').textContent = resume.experience;
        document.getElementById('experienceSection').style.display = 'block';
    }

    // Образование
    if (resume.education) {
        document.getElementById('resumeEducation').textContent = resume.education;
        document.getElementById('educationSection').style.display = 'block';
    }

    // Кнопка редактирования
    document.getElementById('editBtn').href = `edit-resume.html?id=${resume.id}`;
}
