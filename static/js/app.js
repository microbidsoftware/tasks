/**
 * app.js - Shared application logic
 * Contains functions used in both index.html and task_detail.html
 */

function toggleSidebarSection(id, icon) {
    const content = document.getElementById(id);
    content.classList.toggle('open');
    icon.classList.toggle('rotated');
}

function toggleForm(id) {
    const form = document.getElementById(id);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function openSubtaskForm(taskId, runAi) {
    const form = document.getElementById('subtask-form-' + taskId);
    const aiInput = document.getElementById('run-ai-' + taskId);
    const titleInput = form.querySelector('input[name="title"]');

    if (aiInput) {
        aiInput.value = runAi ? 'true' : 'false';
    }

    form.style.display = 'block';
    if (titleInput) {
        titleInput.focus();
    }
}

function toggleHideMenu(id) {
    // Close all other dropdowns
    var dropdowns = document.getElementsByClassName("dropdown-content");
    for (var i = 0; i < dropdowns.length; i++) {
        var openDropdown = dropdowns[i];
        if (openDropdown.id !== id && openDropdown.classList.contains('show')) {
            openDropdown.classList.remove('show');
        }
    }
    document.getElementById(id).classList.toggle("show");
}

function toggleTaskMenu(taskId) {
    event.stopPropagation(); // Prevent row click

    // Close all other menus first
    const allMenus = document.querySelectorAll('.menu-dropdown');
    const currentMenu = document.getElementById('menu-' + taskId);

    allMenus.forEach(menu => {
        if (menu !== currentMenu) {
            menu.classList.remove('show');
        }
    });

    if (currentMenu) {
        currentMenu.classList.toggle('show');
    }
}

// Close menus when clicking outside - Document listener
document.addEventListener('click', function (event) {
    // Existing dropdown closer (Hide Menu)
    if (!event.target.matches('.icon-btn')) {
        var dropdowns = document.getElementsByClassName("dropdown-content");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
    // New menu closer (3-dot menu)
    if (!event.target.matches('.menu-trigger') && !event.target.closest('.menu-dropdown')) {
        var dropdowns = document.getElementsByClassName("menu-dropdown");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }

    // Settings menu closer
    if (!event.target.closest('.settings-dropdown')) {
        const settingsMenu = document.getElementById('settings-menu');
        if (settingsMenu && settingsMenu.classList.contains('show-dropdown')) {
            settingsMenu.classList.remove('show-dropdown');
        }
    }
});

function enableEdit(id) {
    const displayEl = document.getElementById('display-' + id);
    const editEl = document.getElementById('edit-' + id);
    if (displayEl) displayEl.style.display = 'none';
    if (editEl) {
        editEl.style.display = 'block';
        const inputProp = document.getElementById('input-text-' + id);
        if (inputProp) inputProp.focus();
    }
}

function disableEdit(id) {
    const displayEl = document.getElementById('display-' + id);
    const editEl = document.getElementById('edit-' + id);
    if (displayEl) displayEl.style.display = 'block';
    if (editEl) editEl.style.display = 'none';
}

function handleSuggestionKey(event, id) {
    if (event.key === 'Escape') {
        disableEdit(id);
    }
}

function toggleSettingsMenu() {
    const menu = document.getElementById('settings-menu');
    if (menu) menu.classList.toggle('show-dropdown');
}

function toggleTaskFolding(taskId) {
    const toggle = document.getElementById('toggle-' + taskId);
    const children = document.getElementById('children-' + taskId);

    if (!children) return;

    const isFolded = toggle.classList.toggle('folded');
    children.style.display = isFolded ? 'none' : 'block';

    // Persist to server
    fetch('/toggle_folding/' + taskId)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Failed to persist folding state for task ' + taskId);
            }
        })
        .catch(err => console.error('Error persisting folding state:', err));
}
