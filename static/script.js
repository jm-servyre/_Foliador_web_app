// static/script.js

document.addEventListener('DOMContentLoaded', function() {
    
    // === ELEMENTOS ===
    const form = document.getElementById('foliator-form'); 
    const fileInput = document.getElementById('pdf_file'); 
    const submitButton = document.getElementById('submit-button');
    const previewImage = document.getElementById('preview-image');
    const previewContainer = document.getElementById('preview-container');
    const previewMessage = document.getElementById('preview-message');

    const dragDropZone = document.getElementById('drag-drop-label');
    const dragFileInput = document.getElementById('pdf_file_drag'); 

    const loadingModal = document.getElementById('loading-modal');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressText = document.getElementById('progress-text');

    const fileUploadSection = document.getElementById('action-row'); 
    const configPreviewSection = document.getElementById('config-and-preview-section'); 
    
    const currentFolioDisplay = document.getElementById('current-folio-number'); 
    const startNumberInput = document.getElementById('start_number'); 

    // CONSTANTES DE LÍMITE
    const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024; // 2 GB para LAN
    const MAX_PREVIEW_SIZE_BYTES = 30 * 1024 * 1024;   // 30 MB para Vista Previa en Nube
    
    const controls = document.querySelectorAll('#foliator-form input:not([type="hidden"]):not(#pdf_file), #foliator-form select');
    
    let previewTimeout;
    const DEBOUNCE_DELAY = 750;

    // ----------------------------------------------------------------------
    // --- FUNCIONES DE UTILIDAD ---
    // ----------------------------------------------------------------------

    function updateSimulatedFolio() {
        const startNumber = parseInt(startNumberInput.value) || 1;
        let simulatedFolio = String(startNumber).padStart(4, '0');
        if (currentFolioDisplay) {
            currentFolioDisplay.textContent = `#${simulatedFolio}`;
        }
    }

    function updateSubmitButtonState() {
        const fileValid = fileInput.files.length > 0 && fileInput.files[0].size <= MAX_FILE_SIZE_BYTES;
        submitButton.disabled = !fileValid;
        return fileValid;
    }
    
    function validateFileSize() {
        if (fileInput.files.length === 0) return true; 

        const file = fileInput.files[0];
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        if (file.size > MAX_FILE_SIZE_BYTES) {
            alert(`🚨 ERROR: El archivo excede el límite máximo de 2 GB. Tu archivo es de ${fileSizeMB} MB.`);
            resetToHome();
            return false;
        }
        return true;
    }

    function resetToHome() {
        fileInput.value = ''; 
        dragFileInput.value = ''; 
        updateSubmitButtonState();
        configPreviewSection.style.display = 'none';
        fileUploadSection.style.display = 'block';
        previewImage.style.display = 'none';
        previewMessage.textContent = 'Sube un PDF para ver la previsualización.';
        dragDropZone.innerHTML = '<span class="drag-icon">📁</span> Arrastra tu archivo PDF aquí o haz clic para seleccionar.';
    }

    // ----------------------------------------------------------------------
    // --- LÓGICA DE VISTA PREVIA (AJAX) ---
    // ----------------------------------------------------------------------
    function generatePreview() {
        if (fileInput.files.length === 0 || fileInput.files[0].type !== "application/pdf") {
            previewImage.style.display = 'none';
            previewMessage.textContent = 'Sube un PDF para ver la previsualización.';
            return;
        }

        const file = fileInput.files[0];

        // --- PROTECCIÓN DE MEMORIA PARA RENDER ---
        if (file.size > MAX_PREVIEW_SIZE_BYTES) {
            previewImage.style.display = 'none';
            previewMessage.innerHTML = `
                <div style="color: #dc3545; padding: 15px; border: 1px solid #f8d7da; border-radius: 5px; background: #f8f9fa;">
                    <strong>⚠️ VISTA PREVIA DESHABILITADA</strong><br>
                    El archivo es muy pesado (${(file.size / (1024*1024)).toFixed(1)} MB).<br>
                    Para evitar errores en la nube, procese directamente o use la versión local.
                </div>`;
            return; // Bloquea la petición fetch
        }

        updateSimulatedFolio(); 

        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(() => {
            const formData = new FormData();
            formData.append('pdf_file', file);
            
            controls.forEach(control => {
                formData.append(control.name + '_prev', control.value);
            });
            
            previewMessage.innerHTML = 'Generando vista previa... <span class="loading">Cargando.</span>';
            previewImage.style.display = 'none';

            fetch('/preview', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) return response.blob(); 
                return response.text().then(text => { throw new Error(text || `Error ${response.status}`); });
            })
            .then(imageBlob => {
                const imageUrl = URL.createObjectURL(imageBlob);
                previewImage.src = imageUrl;
                previewMessage.textContent = 'Previsualización de la primera página:';
                previewImage.style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                previewMessage.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
            });

        }, DEBOUNCE_DELAY); 
    }
    
    // ----------------------------------------------------------------------
    // --- LÓGICA DE SUBIDA XHR ---
    // ----------------------------------------------------------------------
    function handleFileUpload(event) {
        event.preventDefault(); 
        if (!validateFileSize() || fileInput.files.length === 0) return;

        loadingModal.style.display = 'flex';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';

        const formData = new FormData(form);
        const xhr = new XMLHttpRequest();

        xhr.upload.onprogress = function(event) {
            if (event.lengthComputable) {
                const percent = Math.round((event.loaded / event.total) * 100);
                progressBar.style.width = percent + '%';
                progressText.textContent = percent + '%';
            }
        };

        xhr.onload = function() {
            loadingModal.style.display = 'none'; 
            if (xhr.status === 200) {
                const blob = new Blob([xhr.response], { type: 'application/pdf' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = "Foliado_" + fileInput.files[0].name;
                link.click();
                window.location.reload();
            } else {
                alert(`Error ${xhr.status} al procesar. Intente con un archivo más pequeño en la nube.`);
                window.location.reload();
            }
        };

        xhr.onerror = () => { alert('Error de red.'); loadingModal.style.display = 'none'; };
        
        xhr.open('POST', form.action);
        xhr.responseType = 'arraybuffer';
        xhr.send(formData);
    }

    // ----------------------------------------------------------------------
    // --- TRANSICIONES Y LISTENERS ---
    // ----------------------------------------------------------------------

    function transferFile(fileList) {
        if (fileList.length > 0) {
            const file = fileList[0];
            dragDropZone.classList.add('file-loaded'); 
            dragDropZone.innerHTML = '<span class="drag-icon">⏳</span> Cargando...'; 
            
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files; 
            
            updateSubmitButtonState();
            
            setTimeout(() => {
                fileUploadSection.style.display = 'none'; 
                configPreviewSection.style.display = 'grid'; 
                generatePreview();
            }, 500); 
        }
    }

    form.addEventListener('submit', handleFileUpload); 
    dragFileInput.addEventListener('change', function() { transferFile(this.files); });
    
    controls.forEach(control => {
        control.addEventListener('change', () => { updateSimulatedFolio(); generatePreview(); });
        if (control.type === 'number') {
            control.addEventListener('keyup', () => { updateSimulatedFolio(); generatePreview(); });
        }
    });

    if (dragDropZone) {
        dragDropZone.addEventListener('dragover', (e) => { e.preventDefault(); dragDropZone.classList.add('dropzone-highlight'); });
        dragDropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dragDropZone.classList.remove('dropzone-highlight'); });
        dragDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dragDropZone.classList.remove('dropzone-highlight');
            transferFile(e.dataTransfer.files);
        });
    }

    updateSubmitButtonState();
    updateSimulatedFolio();
});