const API_URL = 'http://localhost:8000';

// Scroll to vacancies
function scrollToVacancies() {
    document.getElementById('vacancies').scrollIntoView({ behavior: 'smooth' });
}

// Scroll to how it works
function scrollToHow() {
    document.getElementById('howItWorks').scrollIntoView({ behavior: 'smooth' });
}

// Load vacancies
async function loadVacancies() {
    try {
        const response = await fetch(`${API_URL}/api/vacancies/all`);

        if (!response.ok) {
            throw new Error('Ошибка загрузки вакансий');
        }

        const vacancies = await response.json();
        displayVacancies(vacancies);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('vacanciesList').innerHTML = `
            <div class="error-message">
                Не удалось загрузить вакансии. Пожалуйста, попробуйте позже.
            </div>
        `;
    }
}

// Display vacancies
function displayVacancies(vacancies) {
    const container = document.getElementById('vacanciesList');

    if (!vacancies || vacancies.length === 0) {
        container.innerHTML = '<div class="loading">Вакансий пока нет</div>';
        return;
    }

    container.innerHTML = vacancies.map(vacancy => `
        <div class="vacancy-card" onclick="showVacancyDetails(${vacancy.id})">
            <h3 class="vacancy-title">${vacancy.title}</h3>
            <div class="vacancy-details">
                <div class="detail-item">
                    📍 ${vacancy.location || 'Не указано'}
                </div>
            </div>
            ${vacancy.description ? `
                <p class="vacancy-company">${vacancy.description.substring(0, 100)}...</p>
            ` : ''}
            <div class="vacancy-salary">
                ${formatSalary(vacancy.salary_min, vacancy.salary_max)}
            </div>
        </div>
    `).join('');
}

// Format salary
function formatSalary(min, max) {
    if (!min && !max) return 'Зарплата не указана';
    if (min && max) return `${min.toLocaleString()} - ${max.toLocaleString()} ₽`;
    if (min) return `от ${min.toLocaleString()} ₽`;
    return `до ${max.toLocaleString()} ₽`;
}

// Show vacancy details
function showVacancyDetails(id) {
    alert(`Вакансия #${id}. Функционал просмотра в разработке.`);
}

// Search
document.getElementById('searchInput')?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.vacancy-card');

    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? 'block' : 'none';
    });
});

// Load on page load
if (document.getElementById('vacanciesList')) {
    loadVacancies();
}
