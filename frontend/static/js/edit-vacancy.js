const API_URL = 'http://localhost:8000';

// Получаем ID вакансии из URL
const urlParams = new URLSearchParams(window.location.search);
const vacancyId = urlParams.get('id');

if (!vacancyId) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('message').innerHTML = `
        <div class="error-message">
             ID вакансии не указан
        </div>
    `;
} else {
    loadVacancy(vacancyId);
}

// Загрузка данных вакансии
async function loadVacancy(id) {
    try {
        const response = await fetch(`${API_URL}/api/vacancies/${id}`);

        if (!response.ok) {
            throw new Error('Вакансия не найдена');
        }

        const vacancy = await response.json();
        fillForm(vacancy);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('message').innerHTML = `
            <div class="error-message">
                 Ошибка загрузки вакансии: ${error.message}
            </div>
        `;
    }
}

// Заполнение формы данными
function fillForm(vacancy) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('editVacancyForm').style.display = 'block';

    document.getElementById('title').value = vacancy.title || '';
    document.getElementById('description').value = vacancy.description || '';
    document.getElementById('requirements').value = vacancy.requirements || '';
    document.getElementById('salary_min').value = vacancy.salary_min || '';
    document.getElementById('salary_max').value = vacancy.salary_max || '';
    document.getElementById('location').value = vacancy.location || '';
}

// Обработка отправки формы
document.getElementById('editVacancyForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = ' Сохранение...';

    const formData = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        requirements: document.getElementById('requirements').value || null,
        salary_min: parseInt(document.getElementById('salary_min').value) || null,
        salary_max: parseInt(document.getElementById('salary_max').value) || null,
        location: document.getElementById('location').value || null
    };

    try {
        const response = await fetch(`${API_URL}/api/vacancies/${vacancyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Ошибка обновления вакансии');
        }

        const result = await response.json();

        // Успешное сообщение
        document.getElementById('message').innerHTML = `
            <div class="success-message">
                 Вакансия успешно обновлена!<br>
                Перенаправляем на страницу просмотра...
            </div>
        `;

        // Редирект на просмотр
        setTimeout(() => {
            window.location.href = `view-vacancy.html?id=${vacancyId}`;
        }, 1500);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').innerHTML = `
            <div class="error-message">
                 Ошибка при обновлении вакансии. Проверьте подключение к API.
            </div>
        `;
        submitBtn.disabled = false;
        submitBtn.textContent = ' Сохранить изменения';
    }
});
