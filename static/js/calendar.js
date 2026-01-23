// Calendar and Date Management Logic

let currentTargetInputId = null;
let currentAutoSave = false;
let calendarDate = new Date();
let selectedDateStr = "";

// Define currentPeriod globally or pass it from the template if needed
// For now, we'll need to rely on the template injecting the variable or reading it from a data attribute.
// Best practice: The calling template should set a global or pass it to an init function.
// For this refactor, we will read it from a global variable `globalCurrentPeriod` if set.

function openTimeSetDialog(id, explicitValue, autoSave = false, hasSubtasks = false) {
    currentAutoSave = autoSave;
    currentTargetInputId = 'due-at-' + id;
    const targetInput = document.getElementById(currentTargetInputId);
    let currentValue = (explicitValue !== undefined && explicitValue !== '') ? explicitValue : (targetInput ? targetInput.value : '');

    const dialog = document.getElementById('task-time-set-dialog');
    const timeInput = document.getElementById('due-time-input');

    // Handle shift-subtasks checkbox
    const shiftSubtasksContainer = document.getElementById('shift-subtasks-container');
    const shiftSubtasksCheckbox = document.getElementById('shift-subtasks-checkbox');
    if (shiftSubtasksContainer && shiftSubtasksCheckbox) {
        if (hasSubtasks) {
            shiftSubtasksContainer.style.display = 'flex';
            shiftSubtasksCheckbox.checked = true;
        } else {
            shiftSubtasksContainer.style.display = 'none';
            shiftSubtasksCheckbox.checked = false;
        }
    }

    if (currentValue) {
        let d;
        if (currentValue.includes('T')) {
            d = new Date(currentValue);
        } else {
            d = new Date(currentValue.replace(' ', 'T'));
        }

        if (!isNaN(d.getTime())) {
            calendarDate = new Date(d);
            selectedDateStr = d.toISOString().split('T')[0];
            timeInput.value = d.toTimeString().split(' ')[0].substring(0, 5);
        } else {
            calendarDate = new Date();
            selectedDateStr = "";
            timeInput.value = "";
        }
    } else {
        calendarDate = new Date();
        selectedDateStr = "";
        timeInput.value = "";
    }

    renderCalendar();
    dialog.style.display = 'flex';
}

function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    const monthYearLabel = document.getElementById('calendar-month-year');
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    monthYearLabel.innerText = months[calendarDate.getMonth()] + " " + calendarDate.getFullYear();

    grid.innerHTML = "";
    const dayHeaders = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
    dayHeaders.forEach(day => {
        const div = document.createElement('div');
        div.className = 'calendar-day-header';
        div.innerText = day;
        grid.appendChild(div);
    });

    const firstDayOfMonth = new Date(calendarDate.getFullYear(), calendarDate.getMonth(), 1).getDay();
    const daysInMonth = new Date(calendarDate.getFullYear(), calendarDate.getMonth() + 1, 0).getDate();

    // Prev month days padding
    for (let i = 0; i < firstDayOfMonth; i++) {
        const div = document.createElement('div');
        div.className = 'calendar-day prev-next';
        grid.appendChild(div);
    }

    const today = new Date().toISOString().split('T')[0];

    for (let day = 1; day <= daysInMonth; day++) {
        const div = document.createElement('div');
        div.className = 'calendar-day';
        div.innerText = day;

        const currentStr = calendarDate.getFullYear() + "-" + String(calendarDate.getMonth() + 1).padStart(2, '0') + "-" + String(day).padStart(2, '0');

        if (currentStr === selectedDateStr) div.classList.add('selected');
        if (currentStr === today) div.classList.add('today');

        div.onclick = () => {
            selectedDateStr = currentStr;
            renderCalendar();
        };
        grid.appendChild(div);
    }
}

function changeMonth(delta) {
    calendarDate.setMonth(calendarDate.getMonth() + delta);
    renderCalendar();
}

function closeTimeSetDialog() {
    document.getElementById('task-time-set-dialog').style.display = 'none';
}

function saveTimeSet() {
    const timeInput = document.getElementById('due-time-input').value;
    const targetInputId = currentTargetInputId;
    const targetInput = document.getElementById(targetInputId);
    const previewId = targetInputId.replace('due-at-', 'due-preview-');
    const previewSpan = document.getElementById(previewId);

    const shiftSubtasksCheckbox = document.getElementById('shift-subtasks-checkbox');
    const doShift = shiftSubtasksCheckbox ? shiftSubtasksCheckbox.checked : false;

    let finalValue = "";
    if (selectedDateStr && timeInput) {
        finalValue = selectedDateStr + ' ' + timeInput + ':00';
    } else if (selectedDateStr) {
        finalValue = selectedDateStr + ' 00:00:00';
    }

    targetInput.value = finalValue;
    if (previewSpan) {
        if (finalValue) {
            const textSpan = previewSpan.querySelector('.due-preview-text');
            if (textSpan) textSpan.innerText = formatDueDisplay(finalValue);
            previewSpan.style.display = 'inline-block';
        } else {
            previewSpan.style.display = 'none';
        }
    }

    if (currentAutoSave && targetInput && targetInput.form) {
        // Add hidden field for shift_subtasks if true
        if (doShift) {
            let hiddenInput = targetInput.form.querySelector('input[name="shift_subtasks"]');
            if (!hiddenInput) {
                hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'shift_subtasks';
                targetInput.form.appendChild(hiddenInput);
            }
            hiddenInput.value = 'true';
        } else {
            let hiddenInput = targetInput.form.querySelector('input[name="shift_subtasks"]');
            if (hiddenInput) {
                hiddenInput.value = 'false';
            }
        }
        targetInput.form.submit();
    }

    closeTimeSetDialog();
}

function clearTimeSet() {
    const targetInputId = currentTargetInputId;
    document.getElementById(targetInputId).value = '';
    const previewId = targetInputId.replace('due-at-', 'due-preview-');
    const previewSpan = document.getElementById(previewId);
    if (previewSpan) {
        previewSpan.style.display = 'none';
    }
    closeTimeSetDialog();
}

function formatDueDisplay(dueString) {
    if (!dueString) return "";
    const isoString = dueString.includes('T') ? dueString : dueString.replace(' ', 'T');
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return dueString;

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const targetDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());

    let datePart = "";
    if (targetDate.getTime() === today.getTime()) {
        datePart = "Today";
    } else if (targetDate.getTime() === tomorrow.getTime()) {
        datePart = "Tomorrow";
    } else {
        const day = d.getDate();
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const month = monthNames[d.getMonth()];
        const year = String(d.getFullYear()).substring(2);
        datePart = `${day} ${month} ${year}`;
    }

    const hours = d.getHours();
    const minutes = d.getMinutes();

    if (hours === 0 && minutes === 0) {
        return datePart;
    } else {
        return `${datePart} ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    }
}

function setDateToday() {
    const now = new Date();
    selectedDateStr = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, '0') + "-" + String(now.getDate()).padStart(2, '0');
    saveTimeSet();
}

function shiftDate(days, months) {
    // Parse selectedDateStr manually to avoid UTC issues
    let d;
    if (selectedDateStr) {
        const parts = selectedDateStr.split('-');
        d = new Date(parts[0], parts[1] - 1, parts[2]);
    } else {
        const now = new Date();
        d = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    if (months) {
        d.setMonth(d.getMonth() + months);
    }
    if (days) {
        d.setDate(d.getDate() + days);
    }

    selectedDateStr = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, '0') + "-" + String(d.getDate()).padStart(2, '0');
    saveTimeSet();
}

function initCalendar() {
    console.log("Calendar JS: initCalendar called");
    // Format all existing due badges
    const badges = document.querySelectorAll('.due-tag');
    console.log("Calendar JS: Found badges:", badges.length);
    badges.forEach(badge => {
        const raw = badge.getAttribute('data-due-at');
        const textSpan = badge.querySelector('.due-display-text');

        // Log individual badge details for debugging
        // console.log("Processing badge:", raw, textSpan);

        if (raw && textSpan && raw !== 'None' && raw !== '') {
            try {
                textSpan.innerText = formatDueDisplay(raw);
            } catch (e) {
                console.error("Error formatting date:", raw, e);
                textSpan.innerText = raw; // Fallback
            }
        }
    });

    // Format all existing previews in edit forms
    const previews = document.querySelectorAll('.due-preview');
    console.log("Calendar JS: Found previews:", previews.length);
    previews.forEach(preview => {
        const raw = preview.getAttribute('data-due-at');
        const textSpan = preview.querySelector('.due-preview-text');
        if (raw && textSpan && raw !== 'None' && raw !== '') {
            textSpan.innerText = formatDueDisplay(raw);
            preview.style.display = 'inline-block';
        }
    });

    // Pre-populate default due date based on current_period
    // Uses globalCurrentPeriod set in index.html
    const dueAtRoot = document.getElementById('due-at-root');
    const duePreviewRoot = document.getElementById('due-preview-root');

    if (dueAtRoot && !dueAtRoot.value && typeof window.globalCurrentPeriod !== 'undefined') {
        let date = new Date();
        let setDate = false;

        const currentPeriod = window.globalCurrentPeriod;
        console.log("Calendar JS: Current period:", currentPeriod);

        if (currentPeriod === 'today' || currentPeriod === '' || !currentPeriod) {
            setDate = true;
        } else if (currentPeriod === 'tomorrow') {
            date.setDate(date.getDate() + 1);
            setDate = true;
        } else if (currentPeriod === 'this_week') {
            setDate = true;
        } else if (currentPeriod === 'next_week') {
            // Next Monday
            let daysToMonday = (8 - date.getDay()) % 7;
            if (daysToMonday === 0) daysToMonday = 7;
            date.setDate(date.getDate() + daysToMonday);
            setDate = true;
        }

        if (setDate) {
            // Format as YYYY-MM-DD 00:00:00
            const dateStr = date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, '0') + "-" + String(date.getDate()).padStart(2, '0') + " 00:00:00";
            dueAtRoot.value = dateStr;
            if (duePreviewRoot) {
                const textSpan = duePreviewRoot.querySelector('.due-preview-text');
                if (textSpan) textSpan.innerText = formatDueDisplay(dateStr);
                duePreviewRoot.style.display = 'inline-block';
            }
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", initCalendar);
} else {
    initCalendar();
}
