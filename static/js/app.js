function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

// Избранное обновляется без полной перезагрузки страницы.
document.addEventListener('click', async function (event) {
    const button = event.target.closest('.favorite-button');
    if (!button) return;

    event.preventDefault();
    button.disabled = true;

    try {
        const response = await fetch(button.dataset.url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Не удалось сохранить избранное');

        button.textContent = data.is_favorite ? 'Убрать из избранного' : 'В избранное';
        button.classList.toggle('btn-danger', data.is_favorite);
        button.classList.toggle('btn-outline-danger', !data.is_favorite);
    } catch (error) {
        console.error(error);
        alert('Не удалось изменить избранное. Обновите страницу и попробуйте снова.');
    } finally {
        button.disabled = false;
    }
});

// Статус чтения сохраняется через fetch().

document.addEventListener('change', async function (event) {
    const select = event.target.closest('.book-status');
    if (!select) return;

    const message = select.closest('.card-body')
        .querySelector('.status-message');

    const previousValue = select.dataset.previousValue || select.value;

    select.disabled = true;
    message.className = 'small text-secondary mt-2 status-message';
    message.textContent = 'Сохранение...';

    try {
        const response = await fetch(select.dataset.apiUrl, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                status: select.value
            })
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const errorText = data
                ? Object.values(data).flat().join(' ')
                : 'Не удалось сохранить статус';

            throw new Error(errorText);
        }

        select.dataset.previousValue = select.value;
        message.className = 'small text-success mt-2 status-message';
        message.textContent = 'Статус сохранён';
    } catch (error) {
        select.value = previousValue;
        message.className = 'small text-danger mt-2 status-message';
        message.textContent = error.message;
        console.error('Ошибка сохранения статуса:', error);
    } finally {
        select.disabled = false;
    }
});


document.addEventListener('click', async function (event) {
    const button = event.target.closest('.delete-book-status');
    if (!button) return;

    const confirmed = confirm(
        `Удалить книгу «${button.dataset.bookTitle}» из раздела «Мои книги»?`
    );

    if (!confirmed) return;

    button.disabled = true;

    try {
        const response = await fetch(button.dataset.apiUrl, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const data = await response.json().catch(() => null);
            const errorText = data
                ? Object.values(data).flat().join(' ')
                : 'Не удалось удалить запись';

            throw new Error(errorText);
        }

        const card = button.closest('.col-sm-6');
        if (card) {
            card.remove();
        }

        const remainingCards = document.querySelectorAll(
            '.delete-book-status'
        );

        if (remainingCards.length === 0) {
            window.location.reload();
        }
    } catch (error) {
        console.error('Ошибка удаления книги:', error);
        alert(error.message);
        button.disabled = false;
    }
});


// Обработчик удаления
document.addEventListener('click', async function (event) {
    const button = event.target.closest('.delete-book-status');
    if (!button) return;

    const confirmed = confirm(
        `Удалить книгу «${button.dataset.bookTitle}» из раздела «Мои книги»?`
    );

    if (!confirmed) return;

    button.disabled = true;

    try {
        const response = await fetch(button.dataset.apiUrl, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const data = await response.json().catch(() => null);
            const errorText = data
                ? Object.values(data).flat().join(' ')
                : 'Не удалось удалить запись';
            throw new Error(errorText);
        }

        const card = button.closest('.col-sm-6');
        if (card) card.remove();

        const remainingCards = document.querySelectorAll(
            '.delete-book-status'
        );

        if (remainingCards.length === 0) {
            window.location.reload();
            return;
        }

        alert('Книга удалена из раздела «Мои книги».');
    } catch (error) {
        alert(error.message);
        button.disabled = false;
    }
});


document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.book-status').forEach(function (select) {
        select.dataset.previousValue = select.value;
    });

    // Фрагмент каждый раз загружается с сервера, поэтому показываются
    // последние данные, добавленные или изменённые в админ-панели.
    const button = document.querySelector('.snippet-button');
    const output = document.getElementById('book-snippet');
    if (button && output) {
        const storageKey = 'booktracker_snippet_open_' + button.dataset.url;
        const savedOpenState = localStorage.getItem(storageKey) === 'true';

        function setOpenState(isOpen) {
            output.hidden = !isOpen;
            button.setAttribute('aria-expanded', String(isOpen));
            button.textContent = isOpen ? 'Скрыть фрагмент' : 'Показать фрагмент';
            localStorage.setItem(storageKey, String(isOpen));
        }

        async function loadSnippet() {
            button.disabled = true;
            output.hidden = false;
            output.textContent = 'Загрузка фрагмента...';

            try {
                const response = await fetch(button.dataset.url, {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                if (!response.ok) throw new Error('HTTP ' + response.status);
                const data = await response.json();

                output.textContent = data.snippet && data.snippet.trim()
                    ? data.snippet
                    : 'Фрагмент для этой книги пока не добавлен.';
                setOpenState(true);
            } catch (error) {
                output.textContent = 'Не удалось загрузить фрагмент. Попробуйте ещё раз.';
                console.error(error);
            } finally {
                button.disabled = false;
            }
        }

        setOpenState(savedOpenState);
        if (savedOpenState) loadSnippet();

        button.addEventListener('click', function () {
            if (!output.hidden) {
                setOpenState(false);
                return;
            }
            loadSnippet();
        });
    }

    // Запоминаем поисковый запрос между посещениями каталога.
    const form = document.getElementById('book-search-form');
    const searchInput = document.getElementById('book-search');
    if (!form || !searchInput) return;

    const storageKey = 'booktracker_search';
    const url = new URL(window.location.href);
    const queryFromUrl = url.searchParams.get('q');

    if (queryFromUrl !== null) {
        searchInput.value = queryFromUrl;
        localStorage.setItem(storageKey, queryFromUrl);
    } else {
        const savedQuery = localStorage.getItem(storageKey);
        if (savedQuery) {
            searchInput.value = savedQuery;
            url.searchParams.set('q', savedQuery);
            window.location.replace(url.toString());
            return;
        }
    }

    searchInput.addEventListener('input', function () {
        localStorage.setItem(storageKey, searchInput.value);
    });
    form.addEventListener('submit', function () {
        localStorage.setItem(storageKey, searchInput.value.trim());
    });
});



