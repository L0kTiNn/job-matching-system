const API_URL = 'http://localhost:8000';

// Получаем параметры из URL
const urlParams = new URLSearchParams(window.location.search);
const resumeId = urlParams.get('id');
const vacancyId = urlParams.get('vacancy_id'); // Новый параметр для анализа

if (!resumeId) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').innerHTML = `
        <div class="error-message">
            ❌ ID резюме не указан
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

        // Если есть vacancy_id - загружаем анализ совпадения
        if (vacancyId) {
            await loadMatchAnalysis(id, vacancyId);
        }

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').innerHTML = `
            <div class="error-message">
                ❌ Ошибка загрузки резюме: ${error.message}
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
        metaInfo.push(`📍 ${resume.location}`);
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

// Новая функция: загрузка анализа совпадения
async function loadMatchAnalysis(resumeId, vacancyId) {
    try {
        const response = await fetch(`${API_URL}/api/vacancies/${vacancyId}/resumes/${resumeId}/match-analysis`);

        if (!response.ok) {
            console.warn('Анализ совпадения не найден');
            return;
        }

        const analysis = await response.json();
        displayMatchAnalysis(analysis);

    } catch (error) {
        console.error('Match analysis error:', error);
        // Не показываем ошибку пользователю, просто логируем
    }
}

// Новая функция: отображение анализа совпадения
function displayMatchAnalysis(analysis) {
    const matchSection = document.getElementById('matchAnalysis');
    matchSection.style.display = 'block';

    // Процент совпадения
    const percentage = Math.round(analysis.match_percentage || 0);
    const matchDiv = document.getElementById('matchPercentage');
    matchDiv.textContent = ` ${percentage}%`;
    matchDiv.style.textAlign = 'right';
    matchDiv.style.paddingRight = '20px';

    // Класс по проценту
    if (percentage >= 80) {
        matchDiv.className = 'match-percentage excellent';
    } else if (percentage >= 60) {
        matchDiv.className = 'match-percentage good';
    } else if (percentage >= 40) {
        matchDiv.className = 'match-percentage medium';
    } else {
        matchDiv.className = 'match-percentage low';
    }

    // Совпавшие навыки
    if (analysis.matched_skills && analysis.matched_skills.length > 0) {
        document.getElementById('matchedSkillsSection').style.display = 'block';
        document.getElementById('matchedSkills').innerHTML = analysis.matched_skills
            .map(skill => `<span class="skill-badge skill-matched">✓ ${skill}</span>`)
            .join('');
    }

    // Дополнительные навыки (дают преимущество)
    if (analysis.extra_skills && analysis.extra_skills.length > 0) {
        document.getElementById('extraSkillsSection').style.display = 'block';
        document.getElementById('extraSkills').innerHTML = analysis.extra_skills
            .map(skill => `<span class="skill-badge skill-extra">+ ${skill}</span>`)
            .join('');
    }

    // Недостающие навыки
    if (analysis.missing_skills && analysis.missing_skills.length > 0) {
        document.getElementById('missingSkillsSection').style.display = 'block';
        document.getElementById('missingSkills').innerHTML = analysis.missing_skills
            .map(skill => `<span class="skill-badge skill-missing">− ${skill}</span>`)
            .join('');
    }

    // Критически недостающие навыки (если есть отдельное поле)
    if (analysis.critical_missing_skills && analysis.critical_missing_skills.length > 0) {
        const criticalHtml = analysis.critical_missing_skills
            .map(skill => `<span class="skill-badge skill-critical">⚠ ${skill}</span>`)
            .join('');

        // Добавляем к недостающим навыкам
        document.getElementById('missingSkills').innerHTML += criticalHtml;
    }

    // Рекомендации
    if (analysis.recommendations) {
        document.getElementById('recommendationsSection').style.display = 'block';
        document.getElementById('recommendations').textContent = analysis.recommendations;
    }
}
