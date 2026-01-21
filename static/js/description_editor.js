/**
 * Description Editor Module (Quill Version)
 * Handles Quill initialization, image resizing, PDF drop, and auto-save.
 */

const DescriptionEditor = {
    taskId: null,
    editorId: 'task-description-editor',
    saveUrl: '/update_task',
    quill: null,
    saveTimeout: null,

    init: function (taskId) {
        this.taskId = taskId;
        this.initQuill();
    },

    initQuill: function () {
        // Initialize Quill with Image Resize module
        this.quill = new Quill('#' + this.editorId, {
            theme: 'snow',
            modules: {
                imageResize: {
                    displaySize: true
                },
                toolbar: false // User requested to hide toolbar
            }
        });

        // Setup PDF Drag and Drop Handler
        this.setupDragAndDrop();

        // Setup Image Paste Handler (Compression)
        this.setupPaste();

        // Setup Auto-Save
        this.setupAutoSave();

        // Setup Ctrl+S Shortcut
        this.quill.root.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveDescription();
            }
        });
    },

    setupPaste: function () {
        this.quill.root.addEventListener('paste', (e) => {
            const files = e.clipboardData.files;
            if (files && files.length > 0) {
                // Check for images
                for (let i = 0; i < files.length; i++) {
                    if (files[i].type.startsWith('image/')) {
                        e.preventDefault(); // Prevent default base64 paste
                        this.compressAndInsertImage(files[i]);
                    }
                }
            }
        });
    },

    setupDragAndDrop: function () {
        this.quill.root.addEventListener('drop', (e) => {
            e.preventDefault();

            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                const file = files[0];

                if (file.type === 'application/pdf') {
                    // Handle PDF Drop: Insert Link Placeholder
                    const range = this.quill.getSelection(true) || { index: this.quill.getLength() - 1 };
                    this.quill.insertText(range.index, `[Attached PDF: ${file.name}]`, 'link', '#');
                    this.quill.insertText(range.index + `[Attached PDF: ${file.name}]`.length, ' ');

                    console.log('PDF Drop intercepted:', file.name);
                    this.saveDescription();

                } else if (file.type.startsWith('image/')) {
                    // Handle Image Drop: Compress and Insert
                    this.compressAndInsertImage(file);
                }
            }
        }, true);

        // Prevent default dragover
        this.quill.root.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
    },

    compressAndInsertImage: function (file) {
        console.log(`Original Image Size: ${(file.size / 1024).toFixed(2)} KB`);

        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                // Max dimensions
                const MAX_WIDTH = 1200;
                const MAX_HEIGHT = 1200;
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }
                } else {
                    if (height > MAX_HEIGHT) {
                        width *= MAX_HEIGHT / height;
                        height = MAX_HEIGHT;
                    }
                }

                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);

                // Compress to JPEG 70%
                const dataUrl = canvas.toDataURL('image/jpeg', 0.7);

                // Calculate compressed size
                const compressedSize = Math.round((dataUrl.length * 3) / 4); // Approx base64 size
                console.log(`Compressed Image Size: ${(compressedSize / 1024).toFixed(2)} KB`);

                // Insert into editor
                const range = this.quill.getSelection(true) || { index: this.quill.getLength() - 1 };
                this.quill.insertEmbed(range.index, 'image', dataUrl);
                this.quill.setSelection(range.index + 1);

                // Trigger save
                this.saveDescription();
            };
        };
    },

    setupAutoSave: function () {
        // Save on text change (debounced)
        this.quill.on('text-change', (delta, oldDelta, source) => {
            if (source === 'user') {
                if (this.saveTimeout) clearTimeout(this.saveTimeout);
                this.saveTimeout = setTimeout(() => {
                    this.saveDescription();
                }, 2000); // Auto-save after 2 seconds of inactivity
            }
        });

        // Save on blur
        this.quill.root.addEventListener('blur', () => {
            this.saveDescription();
        });
    },

    saveDescription: function () {
        if (this.saveTimeout) clearTimeout(this.saveTimeout);

        console.log('Saving description...');
        const statusEl = document.getElementById('save-status');
        if (statusEl) {
            statusEl.innerText = 'Saving...';
            statusEl.style.color = '#999';
            statusEl.style.display = 'inline';
        }

        // Get HTML content
        const content = this.quill.root.innerHTML;

        const formData = new FormData();
        formData.append('task_id', this.taskId);
        formData.append('description', content);

        fetch(this.saveUrl, {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (response.ok) {
                    console.log('Description saved successfully.');
                    if (statusEl) {
                        statusEl.innerText = 'Saved';
                        statusEl.style.color = 'green';
                        setTimeout(() => { statusEl.style.display = 'none'; }, 2000);
                    }
                } else {
                    console.error('Failed to save description:', response.status, response.statusText);
                    if (statusEl) {
                        statusEl.innerText = 'Error saving: ' + response.status;
                        statusEl.style.color = 'red';
                        statusEl.style.display = 'inline';
                    }
                    return response.text().then(text => console.error('Error detail:', text));
                }
            })
            .catch(error => {
                console.error('Error saving description:', error);
                if (statusEl) {
                    statusEl.innerText = 'Error saving';
                    statusEl.style.color = 'red';
                    statusEl.style.display = 'inline';
                }
            });
    }
};
