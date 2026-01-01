const API_URL = 'http://localhost:8000/api';

document.getElementById('vacancyForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const messageDiv = document.getElementById('message');
    const submitButton = e.target.querySelector('button[type="submit"]');

    // Собираем данные из формы
    const vacancyData = {
        employer_id: parseInt(document.getElementById('employer_id').value),
        title: document.getElementById('title').value.trim(),
        description: document.getElementById('description').value.trim(),
        requirements: document.getElementById('requirements').value.trim(),
        location: document.getElementById('location').value.trim()
    };

    // Добавляем зарплату если указана
    const salaryMin = document.getElementById('salary_min').value;
    const salaryMax = document.getElementById('salary_max').value;

    if (salaryMin) {
        vacancyData.salary_min = parseInt(salaryMin);
    }
    if (salaryMax) {
        vacancyData.salary_max = parseInt(salaryMax);
    }

    try {
        submitButton.disabled = true;
        submitButton.textContent = 'Отправка...';

        const response = await fetch(`${API_URL}/vacancies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(vacancyData)
        });

        if (response.ok) {
            const result = await response.json();

            // Показываем успех
            messageDiv.style.display = 'block';
            messageDiv.style.background = '#d4edda';
            messageDiv.style.color = '#155724';
            messageDiv.textContent = `Вакансия успешно создана! ID: ${result.id}`;

            // Очищаем форму
            document.getElementById('vacancyForm').reset();
            document.getElementById('employer_id').value = '3';

            // Перенаправляем через 2 секунды
            setTimeout(() => {
                window.location.href = 'vacancies.html';
            }, 2000);

        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при создании вакансии');
        }

    } catch (error) {
        messageDiv.style.display = 'block';
        messageDiv.style.background = '#f8d7da';
        messageDiv.style.color = '#721c24';
        messageDiv.textContent = `Ошибка: ${error.message}`;

        submitButton.disabled = false;
        submitButton.textContent = 'Опубликовать вакансию';
    }
});
