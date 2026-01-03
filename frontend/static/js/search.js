// Ждем загрузки страницы
window.addEventListener('DOMContentLoaded', function() {
    const API_URL = 'http://localhost:8000';
    let searchTimeout;

    const searchInput = document.getElementById('searchInput');
    if (!searchInput) {
        console.error('searchInput не найден!');
        return;
    }

    // Создаем dropdown
    let dropdown = document.getElementById('searchDropdown');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'searchDropdown';
        dropdown.style.cssText = 'display: none; position: fixed; background: white; border: 2px solid #e0e0e0; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); z-index: 1000;';
        document.body.appendChild(dropdown);
    }

    console.log('Поиск инициализирован');

    // Поиск при вводе
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        console.log('Ввод:', query);

        if (query.length < 2) {
            dropdown.style.display = 'none';
            return;
        }

        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            fetch(API_URL + '/api/vacancies/all')
                .then(response => response.json())
                .then(vacancies => {
                    console.log('Получено вакансий:', vacancies.length);

                    // ИСПРАВЛЕНО: поиск по названию, описанию и локации
                    const filtered = vacancies.filter(v =>
                        v.title.toLowerCase().includes(query.toLowerCase()) ||
                        (v.description && v.description.toLowerCase().includes(query.toLowerCase())) ||
                        (v.location && v.location.toLowerCase().includes(query.toLowerCase()))
                    ).slice(0, 3);

                    console.log('Отфильтровано:', filtered.length);

                    if (filtered.length === 0) {
                        dropdown.innerHTML = '<div style="padding: 15px; color: #666;">Ничего не найдено</div>';
                    } else {
                        dropdown.innerHTML = filtered.map(v => `
                            <div onclick="window.location.href='view-vacancy.html?id=${v.id}'"
                                 style="padding: 15px; border-bottom: 1px solid #f0f0f0; cursor: pointer;">
                                <div style="font-weight: 600; color: #2d2d2d; margin-bottom: 5px;">${v.title}</div>
                                <div style="font-size: 14px; color: #666;">📍 ${v.location || 'Не указано'}</div>
                            </div>
                        `).join('');
                    }

                    const rect = searchInput.parentElement.getBoundingClientRect();
                    dropdown.style.top = rect.bottom + 'px';
                    dropdown.style.left = rect.left + 'px';
                    dropdown.style.width = rect.width + 'px';
                    dropdown.style.display = 'block';
                })
                .catch(err => {
                    console.error('Ошибка:', err);
                    dropdown.innerHTML = '<div style="padding: 15px; color: #666;">Ошибка загрузки</div>';
                    dropdown.style.display = 'block';
                });
        }, 300);
    });

    // Клик по лупе
    const lupa = document.querySelector('.search-box span');
    if (lupa) {
        lupa.style.cursor = 'pointer';
        lupa.addEventListener('click', function() {
            const query = searchInput.value.trim();
            window.location.href = query ? `vacancies.html?search=${encodeURIComponent(query)}` : 'vacancies.html';
        });
    }

    // Закрыть dropdown
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box')) {
            dropdown.style.display = 'none';
        }
    });

    console.log('Все обработчики установлены');
});
