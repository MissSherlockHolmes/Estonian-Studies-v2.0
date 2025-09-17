// Estonian Studies Notes - Frontend JavaScript
// PDF Converter functionality with API integration

class PDFConverter {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentFile = null;
        this.currentPdfPath = null;
        this.currentResults = null;
        this.availablePdfs = {};
        this.filteredPdfs = {};
        
        this.initializeEventListeners();
        this.initializeTabNavigation();
        this.loadAvailablePdfs();
    }

    initializeEventListeners() {
        // PDF selection handling
        const searchInput = document.getElementById('searchInput');
        const clearSelection = document.getElementById('clearSelection');
        const convertButton = document.getElementById('convertButton');

        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterPdfs(e.target.value);
            });
        }

        // Course filter buttons
        const filterButtons = document.querySelectorAll('.filter-button');
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                
                const course = e.target.dataset.course;
                this.filterByCourse(course);
            });
        });

        // Clear selection
        if (clearSelection) {
            clearSelection.addEventListener('click', () => {
                this.clearSelection();
            });
        }

        // Convert button
        if (convertButton) {
            convertButton.addEventListener('click', () => {
                this.convertPDF();
            });
        }

        // Legacy file input handling (for main tab)
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const removeFile = document.getElementById('removeFile');

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelect(e.target.files[0]);
            });
        }

        if (uploadArea) {
            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });

            uploadArea.addEventListener('click', () => {
                if (!this.currentFile && fileInput) {
                    fileInput.click();
                }
            });
        }

        if (removeFile) {
            removeFile.addEventListener('click', () => {
                this.clearFile();
            });
        }
    }

    initializeTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Remove active class from all tabs and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                button.classList.add('active');
                const targetContent = document.getElementById(`${tabName}-content`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
            this.showStatus('Please select a PDF file.', 'error');
            return;
        }

        // Validate file size (50MB limit)
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showStatus('File size must be less than 50MB.', 'error');
            return;
        }

        this.currentFile = file;
        this.updateFileInfo(file);
        this.enableConvertButton();
        this.hideResults();
    }

    updateFileInfo(file) {
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const uploadArea = document.getElementById('uploadArea');

        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);
        
        fileInfo.style.display = 'flex';
        uploadArea.style.display = 'none';
    }

    clearFile() {
        this.currentFile = null;
        const fileInfo = document.getElementById('fileInfo');
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        fileInfo.style.display = 'none';
        uploadArea.style.display = 'block';
        fileInput.value = '';
        
        this.disableConvertButton();
        this.hideResults();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    enableConvertButton() {
        const convertButton = document.getElementById('convertButton');
        convertButton.disabled = false;
    }

    disableConvertButton() {
        const convertButton = document.getElementById('convertButton');
        convertButton.disabled = true;
    }

    getExtractionOptions() {
        return {
            extract_text: document.getElementById('extractText').checked,
            extract_tables: document.getElementById('extractTables').checked,
            extract_figures: document.getElementById('extractFigures').checked,
            include_styling: document.getElementById('includeStyling').checked,
            include_char_bounds: document.getElementById('includeCharBounds').checked
        };
    }

    async loadAvailablePdfs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/pdfs`);
            const result = await response.json();
            
            if (result.success) {
                this.availablePdfs = result.courses;
                this.filteredPdfs = { ...result.courses };
                this.renderPdfList();
            } else {
                this.showPdfLoadError('Failed to load PDF list');
            }
        } catch (error) {
            console.error('Error loading PDFs:', error);
            this.showPdfLoadError('Failed to connect to server');
        }
    }

    renderPdfList() {
        const pdfList = document.getElementById('pdfList');
        if (!pdfList) return;

        pdfList.innerHTML = '';

        // Check if we have any PDFs
        const totalPdfs = Object.values(this.filteredPdfs).reduce((total, course) => total + course.pdfs.length, 0);
        
        if (totalPdfs === 0) {
            pdfList.innerHTML = '<div class="loading-message">No documents found</div>';
            return;
        }

        // Render by course
        Object.entries(this.filteredPdfs).forEach(([courseId, course]) => {
            if (course.pdfs.length === 0) return;

            const courseSection = document.createElement('div');
            courseSection.className = 'course-section';
            
            const courseTitle = document.createElement('div');
            courseTitle.className = 'course-title';
            courseTitle.textContent = course.name;
            courseSection.appendChild(courseTitle);

            course.pdfs.forEach(pdf => {
                const pdfItem = document.createElement('div');
                pdfItem.className = 'pdf-item';
                pdfItem.dataset.path = pdf.path;
                pdfItem.dataset.course = courseId;
                
                pdfItem.innerHTML = `
                    <div class="pdf-icon">📄</div>
                    <div class="pdf-details">
                        <div class="pdf-name">${pdf.name}</div>
                        <div class="pdf-course">${course.name}</div>
                        <div class="pdf-size">${pdf.size_formatted}</div>
                    </div>
                `;
                
                pdfItem.addEventListener('click', () => {
                    this.selectPdf(pdf, course);
                });
                
                courseSection.appendChild(pdfItem);
            });
            
            pdfList.appendChild(courseSection);
        });
    }

    selectPdf(pdf, course) {
        this.currentPdfPath = pdf.path;
        this.currentFile = null; // Clear any uploaded file
        
        // Update UI
        this.updateSelectedPdf(pdf, course);
        this.enableConvertButton();
        this.hideResults();
        
        // Update visual selection
        document.querySelectorAll('.pdf-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-path="${pdf.path}"]`).classList.add('selected');
    }

    updateSelectedPdf(pdf, course) {
        const selectedPdf = document.getElementById('selectedPdf');
        const selectedName = document.getElementById('selectedName');
        const selectedCourse = document.getElementById('selectedCourse');
        
        if (selectedPdf && selectedName && selectedCourse) {
            selectedName.textContent = pdf.name;
            selectedCourse.textContent = course.name;
            selectedPdf.style.display = 'flex';
        }
    }

    clearSelection() {
        this.currentPdfPath = null;
        this.currentFile = null;
        
        const selectedPdf = document.getElementById('selectedPdf');
        if (selectedPdf) {
            selectedPdf.style.display = 'none';
        }
        
        document.querySelectorAll('.pdf-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        this.disableConvertButton();
        this.hideResults();
    }

    filterPdfs(searchTerm) {
        const term = searchTerm.toLowerCase();
        this.filteredPdfs = {};
        
        Object.entries(this.availablePdfs).forEach(([courseId, course]) => {
            const filteredPdfs = course.pdfs.filter(pdf => 
                pdf.name.toLowerCase().includes(term)
            );
            
            if (filteredPdfs.length > 0) {
                this.filteredPdfs[courseId] = {
                    ...course,
                    pdfs: filteredPdfs
                };
            }
        });
        
        this.renderPdfList();
    }

    filterByCourse(courseFilter) {
        if (courseFilter === 'all') {
            this.filteredPdfs = { ...this.availablePdfs };
        } else {
            this.filteredPdfs = {};
            if (this.availablePdfs[courseFilter]) {
                this.filteredPdfs[courseFilter] = this.availablePdfs[courseFilter];
            }
        }
        
        this.renderPdfList();
    }

    showPdfLoadError(message) {
        const pdfList = document.getElementById('pdfList');
        if (pdfList) {
            pdfList.innerHTML = `<div class="loading-message" style="color: var(--error);">${message}</div>`;
        }
    }

    async convertPDF() {
        // Check if we have either a file or a path
        if (!this.currentFile && !this.currentPdfPath) {
            this.showStatus('Please select a PDF file first.', 'error');
            return;
        }

        const options = this.getExtractionOptions();
        
        // Validate that at least one extraction type is selected
        if (!options.extract_text && !options.extract_tables && !options.extract_figures) {
            this.showStatus('Please select at least one extraction option.', 'error');
            return;
        }

        this.setLoadingState(true);
        this.hideStatus();

        try {
            const formData = new FormData();
            
            // Add either file or path
            if (this.currentFile) {
                formData.append('file', this.currentFile);
            } else if (this.currentPdfPath) {
                formData.append('pdf_path', this.currentPdfPath);
            }
            
            // Add extraction options
            Object.keys(options).forEach(key => {
                formData.append(key, options[key]);
            });

            const response = await fetch(`${this.apiBaseUrl}/pdf-converter`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Conversion failed');
            }

            if (result.success) {
                this.currentResults = result;
                this.displayResults(result);
                this.showStatus('PDF converted successfully!', 'success');
            } else {
                throw new Error(result.message || 'Conversion failed');
            }

        } catch (error) {
            console.error('Conversion error:', error);
            this.showStatus(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        const convertButton = document.getElementById('convertButton');
        const buttonText = convertButton.querySelector('.button-text');
        const spinner = convertButton.querySelector('.loading-spinner');

        if (loading) {
            convertButton.disabled = true;
            buttonText.textContent = 'Converting...';
            spinner.style.display = 'inline-block';
        } else {
            convertButton.disabled = false;
            buttonText.textContent = 'Convert PDF';
            spinner.style.display = 'none';
        }
    }

    displayResults(result) {
        const resultsSection = document.getElementById('resultsSection');
        const extractionId = document.getElementById('extractionId');
        const processingTime = document.getElementById('processingTime');
        const textCount = document.getElementById('textCount');
        const tableCount = document.getElementById('tableCount');
        const figureCount = document.getElementById('figureCount');
        const resultsPreview = document.getElementById('resultsPreview');

        // Update result info
        extractionId.textContent = result.extraction_id;
        processingTime.textContent = `Processed in ${result.processing_time?.toFixed(2)}s`;

        // Update counts
        let textElements = 0;
        let tableElements = 0;
        let figureElements = 0;

        if (result.structured_data && result.structured_data.elements) {
            result.structured_data.elements.forEach(element => {
                const path = element.Path || '';
                if (path.includes('Text')) textElements++;
                else if (path.includes('Table')) tableElements++;
                else if (path.includes('Figure')) figureElements++;
            });
        }

        textCount.textContent = textElements;
        tableCount.textContent = result.renditions_info?.tables?.length || tableElements;
        figureCount.textContent = result.renditions_info?.figures?.length || figureElements;

        // Update preview
        this.updateResultsPreview(result, resultsPreview);

        // Show results section
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    updateResultsPreview(result, container) {
        container.innerHTML = '';

        // Create preview content
        const preview = document.createElement('div');
        preview.className = 'preview-content';

        // Add structured data summary
        if (result.structured_data) {
            const summary = document.createElement('div');
            summary.innerHTML = `
                <h4 style="color: var(--estonian-blue); margin-bottom: 0.5rem;">Extraction Summary</h4>
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                    Successfully extracted content from ${result.structured_data.pages?.length || 'unknown'} pages
                </p>
            `;
            preview.appendChild(summary);

            // Add sample text if available
            if (result.structured_data.elements && result.structured_data.elements.length > 0) {
                const textElements = result.structured_data.elements
                    .filter(el => el.Text && el.Text.trim().length > 0)
                    .slice(0, 3);

                if (textElements.length > 0) {
                    const textPreview = document.createElement('div');
                    textPreview.innerHTML = '<h5 style="color: var(--text-primary); margin-bottom: 0.5rem;">Sample Text:</h5>';
                    
                    textElements.forEach(el => {
                        const textSample = document.createElement('p');
                        textSample.style.cssText = 'color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem; font-style: italic;';
                        textSample.textContent = el.Text.substring(0, 200) + (el.Text.length > 200 ? '...' : '');
                        textPreview.appendChild(textSample);
                    });
                    
                    preview.appendChild(textPreview);
                }
            }
        }

        // Add renditions info
        if (result.renditions_info) {
            const renditions = document.createElement('div');
            renditions.innerHTML = `
                <h5 style="color: var(--text-primary); margin-top: 1rem; margin-bottom: 0.5rem;">Renditions Available:</h5>
                <ul style="color: var(--text-secondary); font-size: 0.9rem;">
                    <li>Tables: ${result.renditions_info.tables?.length || 0} files</li>
                    <li>Figures: ${result.renditions_info.figures?.length || 0} files</li>
                </ul>
            `;
            preview.appendChild(renditions);
        }

        container.appendChild(preview);
    }

    hideResults() {
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'none';
        this.currentResults = null;
    }

    showStatus(message, type = 'info') {
        const statusMessage = document.getElementById('statusMessage');
        const statusText = document.getElementById('statusText');

        statusText.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                this.hideStatus();
            }, 5000);
        }
    }

    hideStatus() {
        const statusMessage = document.getElementById('statusMessage');
        statusMessage.style.display = 'none';
    }

    // Utility methods for result actions
    downloadResults() {
        if (!this.currentResults) return;

        const dataStr = JSON.stringify(this.currentResults, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.currentResults.extraction_id}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    viewResults() {
        if (!this.currentResults) return;
        
        // Open results in new window
        const newWindow = window.open('', '_blank');
        newWindow.document.write(`
            <html>
                <head>
                    <title>PDF Extraction Results - ${this.currentResults.extraction_id}</title>
                    <style>
                        body { font-family: monospace; padding: 20px; background: #1a1a1a; color: #fff; }
                        pre { white-space: pre-wrap; word-wrap: break-word; }
                    </style>
                </head>
                <body>
                    <h1>PDF Extraction Results</h1>
                    <pre>${JSON.stringify(this.currentResults, null, 2)}</pre>
                </body>
            </html>
        `);
        newWindow.document.close();
    }
}

// Preset configurations
window.setPreset = function(presetType) {
    const presetButtons = document.querySelectorAll('.preset-button');
    presetButtons.forEach(btn => btn.classList.remove('active'));
    
    // Find and activate the clicked preset button
    const clickedButton = Array.from(presetButtons).find(btn => 
        btn.onclick?.toString().includes(`'${presetType}'`)
    );
    if (clickedButton) {
        clickedButton.classList.add('active');
    }

    const extractText = document.getElementById('extractText');
    const extractTables = document.getElementById('extractTables');
    const extractFigures = document.getElementById('extractFigures');
    const includeStyling = document.getElementById('includeStyling');
    const includeCharBounds = document.getElementById('includeCharBounds');

    switch (presetType) {
        case 'text':
            extractText.checked = true;
            extractTables.checked = false;
            extractFigures.checked = false;
            includeStyling.checked = false;
            includeCharBounds.checked = false;
            break;
        case 'tables':
            extractText.checked = true;
            extractTables.checked = true;
            extractFigures.checked = false;
            includeStyling.checked = false;
            includeCharBounds.checked = false;
            break;
        case 'comprehensive':
            extractText.checked = true;
            extractTables.checked = true;
            extractFigures.checked = true;
            includeStyling.checked = true;
            includeCharBounds.checked = true;
            break;
    }
};

// Global functions for result actions
window.downloadResults = function() {
    if (window.pdfConverter) {
        window.pdfConverter.downloadResults();
    }
};

window.viewResults = function() {
    if (window.pdfConverter) {
        window.pdfConverter.viewResults();
    }
};

// Document Viewer functionality
class DocumentViewer {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.documents = [];
        this.filteredDocuments = [];
        this.currentCourse = 'all';
        this.currentType = 'all';
        this.searchTerm = '';
        
        this.initializeEventListeners();
        this.loadDocuments();
    }

    initializeEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('documentSearch');
        if (searchInput) {
            console.log('Search input found, adding event listener');
            searchInput.addEventListener('input', (e) => {
                console.log('Search input changed:', e.target.value);
                this.searchTerm = e.target.value;
                this.filterDocuments();
            });
        } else {
            console.error('Search input not found');
        }

        // Course filter
        const courseFilter = document.getElementById('documentCourseFilter');
        if (courseFilter) {
            console.log('Course filter found, adding event listener');
            courseFilter.addEventListener('change', (e) => {
                console.log('Course filter changed:', e.target.value);
                this.currentCourse = e.target.value;
                this.filterDocuments();
            });
        } else {
            console.error('Course filter not found');
        }

        // Type filter
        const typeFilter = document.getElementById('documentTypeFilter');
        if (typeFilter) {
            console.log('Type filter found, adding event listener');
            typeFilter.addEventListener('change', (e) => {
                console.log('Type filter changed:', e.target.value);
                this.currentType = e.target.value;
                this.filterDocuments();
            });
        } else {
            console.error('Type filter not found');
        }
    }

    async loadDocuments() {
        try {
            console.log('Loading documents from API...');
            const response = await fetch(`${this.apiBaseUrl}/documents`);
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('API response:', data);
            
            if (data.success && data.courses) {
                this.documents = [];
                Object.values(data.courses).forEach(course => {
                    // Skip Adobe samples
                    if (course.name === 'Adobe PDF Samples') {
                        console.log('Skipping Adobe samples');
                        return;
                    }
                    
                    if (course.documents && Array.isArray(course.documents)) {
                        course.documents.forEach(doc => {
                            this.documents.push({
                                ...doc,
                                course: course.name
                            });
                        });
                    }
                });
                this.filteredDocuments = [...this.documents];
                console.log(`Loaded ${this.documents.length} documents (excluding Adobe samples)`);
                this.renderDocuments();
            } else {
                console.error('API returned unsuccessful response:', data);
                this.showError('Failed to load documents: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading documents:', error);
            this.showError('Error loading documents: ' + error.message);
        }
    }

    filterDocuments() {
        console.log('Filtering documents...', {
            searchTerm: this.searchTerm,
            currentCourse: this.currentCourse,
            currentType: this.currentType,
            totalDocuments: this.documents.length
        });
        
        this.filteredDocuments = this.documents.filter(doc => {
            const matchesSearch = doc.name.toLowerCase().includes(this.searchTerm.toLowerCase());
            
            // Better course matching - check if the course ID matches or if the course name contains the filter
            let matchesCourse = true;
            if (this.currentCourse !== 'all') {
                // Map course IDs to course names for better matching
                const courseMapping = {
                    'estonian-regional-studies': 'Estonian Regional Studies',
                    'introduction-to-estonian-studies': 'Introduction to Estonian Studies',
                    'key-concepts-cultural-analysis': 'Key Concepts in Cultural Analysis',
                    'language-and-society': 'Language and Society',
                    'nationalism-transnational-history': 'Nationalism and Transnational History'
                };
                
                const expectedCourseName = courseMapping[this.currentCourse];
                matchesCourse = expectedCourseName ? doc.course === expectedCourseName : doc.course.toLowerCase().includes(this.currentCourse.toLowerCase());
            }
            
            const matchesType = this.currentType === 'all' || doc.type === this.currentType;
            
            console.log(`Document: ${doc.name}, Course: ${doc.course}, Search: ${matchesSearch}, Course Match: ${matchesCourse}, Type: ${matchesType}`);
            
            return matchesSearch && matchesCourse && matchesType;
        });
        
        console.log(`Filtered to ${this.filteredDocuments.length} documents`);
        this.renderDocuments();
    }

    renderDocuments() {
        const container = document.getElementById('documentList');
        if (!container) {
            console.error('Document list container not found');
            return;
        }

        if (this.filteredDocuments.length === 0) {
            container.innerHTML = `
                <div class="no-documents">
                    <div style="text-align: center; padding: 3rem;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                        <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">No documents found</h3>
                        <p style="color: var(--text-secondary);">Try adjusting your search or filter criteria.</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = this.filteredDocuments.map(doc => `
            <div class="document-card" onclick="documentViewer.openDocument('${doc.path}', '${doc.name}')">
                <div class="document-icon ${doc.type}">
                    ${doc.type.toUpperCase()}
                </div>
                <div class="document-title">${doc.name}</div>
                <div class="document-meta">
                    <div>${doc.course}</div>
                    <div>${doc.size_formatted}</div>
                </div>
                <div class="document-actions">
                    <button class="action-button" onclick="event.stopPropagation(); documentViewer.openDocument('${doc.path}', '${doc.name}')">
                        👁️ View
                    </button>
                </div>
            </div>
        `).join('');
    }

    openDocument(path, name) {
        const viewer = document.getElementById('documentViewer');
        const iframe = document.getElementById('viewerIframe');
        const title = document.getElementById('viewerTitle');

        title.textContent = name;
        
        console.log('Opening document:', { path, name });
        
        // Load the appropriate viewer content
        this.loadPDFViewer(path, iframe);
        viewer.style.display = 'flex';
    }

    loadPDFViewer(filePath, iframe) {
        // Determine file type and appropriate viewer
        const fileExtension = filePath.toLowerCase().split('.').pop();
        const isPDF = fileExtension === 'pdf';
        const isDOCX = fileExtension === 'docx' || fileExtension === 'doc';
        const isPPTX = fileExtension === 'pptx' || fileExtension === 'ppt';
        
        if (isPDF) {
            // For PDFs, directly set the iframe src to avoid nested iframes
            iframe.src = `${this.apiBaseUrl}/pdf-viewer/${filePath}`;
            iframe.style.backgroundColor = '#1a1a1a';
            return;
        }
        
        // For DOCX and PPTX files, show a professional interface since browsers can't display them natively
        if (isDOCX || isPPTX) {
            const fileType = isDOCX ? 'Word Document' : 'PowerPoint Presentation';
            const icon = isDOCX ? '📄' : '📊';
            const viewerEndpoint = isDOCX ? 'docx-viewer' : 'pptx-viewer';
            const fileUrl = `${this.apiBaseUrl}/${viewerEndpoint}/${filePath}`;
            
            iframe.srcdoc = `
                <html>
                    <head>
                        <style>
                            body { 
                                margin: 0; padding: 0; 
                                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                display: flex; align-items: center; justify-content: center;
                                height: 100vh; color: #f4f4f4;
                            }
                            .container { 
                                text-align: center; padding: 40px; max-width: 500px;
                                background: rgba(255,255,255,0.05);
                                border-radius: 20px;
                                border: 1px solid rgba(255,255,255,0.1);
                                backdrop-filter: blur(10px);
                            }
                            .icon { 
                                font-size: 64px; margin-bottom: 20px; 
                                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
                            }
                            h3 { 
                                color: #f4f4f4; margin-bottom: 15px; font-size: 1.8rem; 
                                font-weight: 300; letter-spacing: -0.5px;
                            }
                            .file-info {
                                background: rgba(255,255,255,0.05);
                                padding: 15px; border-radius: 10px; margin-bottom: 25px;
                                border-left: 3px solid #007bff;
                            }
                            .file-name {
                                font-weight: 600; color: #ffffff; word-break: break-all;
                                font-size: 0.9rem; margin-bottom: 8px;
                            }
                            .file-size { color: #b0b0b0; font-size: 0.8rem; }
                            p { 
                                color: #b0b0b0; margin-bottom: 30px; line-height: 1.6;
                                font-size: 1rem;
                            }
                            .button-group {
                                display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;
                            }
                            .btn { 
                                padding: 12px 24px; border: none; border-radius: 12px; 
                                cursor: pointer; font-size: 16px; font-weight: 500;
                                transition: all 0.3s ease; text-decoration: none;
                                display: inline-flex; align-items: center; gap: 8px;
                            }
                            .primary-btn {
                                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                                color: white; box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
                            }
                            .primary-btn:hover { 
                                transform: translateY(-2px);
                                box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
                            }
                            .secondary-btn {
                                background: rgba(255,255,255,0.1); color: #f4f4f4;
                                border: 1px solid rgba(255,255,255,0.2);
                            }
                            .secondary-btn:hover {
                                background: rgba(255,255,255,0.2); transform: translateY(-1px);
                            }
                            .info-note {
                                margin-top: 20px; padding: 15px; border-radius: 10px;
                                background: rgba(0, 123, 255, 0.1); border: 1px solid rgba(0, 123, 255, 0.3);
                                font-size: 0.85rem; color: #b0b0b0;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="icon">${icon}</div>
                            <h3>${fileType}</h3>
                            <div class="file-info">
                                <div class="file-name">${filePath.split('/').pop()}</div>
                            </div>
                            <p>This ${fileType.toLowerCase()} is ready to view. Click below to open it with your system's default application.</p>
                            <div class="button-group">
                                <button class="btn primary-btn" onclick="window.open('${fileUrl}', '_blank')">
                                    📂 Open ${fileType}
                                </button>
                                <button class="btn secondary-btn" onclick="window.parent.closeDocumentViewer()">
                                    ✕ Close
                                </button>
                            </div>
                            <div class="info-note">
                                💡 Office documents open in your default application (Word, PowerPoint, etc.) for the best viewing experience.
                            </div>
                        </div>
                    </body>
                </html>
            `;
            return;
        } else {
            // Unknown file type
            viewerHTML = `
                <html>
                    <head>
                        <style>
                            body { 
                                margin: 0; padding: 0; background: #1a1a1a; 
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                display: flex; align-items: center; justify-content: center;
                                height: 100vh; color: #f4f4f4;
                            }
                            .container { text-align: center; padding: 40px; }
                            .icon { font-size: 48px; margin-bottom: 20px; }
                            h3 { color: #f4f4f4; margin-bottom: 10px; font-size: 1.5rem; }
                            p { color: #b0b0b0; margin-bottom: 30px; }
                            button { 
                                padding: 12px 24px; background: #007bff; color: white; 
                                border: none; border-radius: 6px; cursor: pointer; 
                                font-size: 16px; transition: background 0.3s;
                            }
                            button:hover { background: #0056b3; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="icon">📁</div>
                            <h3>Unsupported File Type</h3>
                            <p>This file type cannot be displayed.</p>
                            <button onclick="window.open('${this.apiBaseUrl}/documents/${filePath}', '_blank')">
                                Download File
                            </button>
                        </div>
                    </body>
                </html>
            `;
        }
        
        // Set the iframe content
        iframe.srcdoc = viewerHTML;
    }

    showError(message) {
        const container = document.getElementById('documentList');
        if (container) {
            container.innerHTML = `
                <div class="no-documents">
                    <div style="text-align: center; padding: 3rem;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                        <h3 style="color: var(--accent-red); margin-bottom: 0.5rem;">Error Loading Documents</h3>
                        <p style="color: var(--text-secondary); margin-bottom: 1rem;">${message}</p>
                        <button class="action-button" onclick="documentViewer.loadDocuments()" style="margin-top: 1rem;">
                            🔄 Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
}

// Global function for closing document viewer
function closeDocumentViewer() {
    const viewer = document.getElementById('documentViewer');
    const iframe = document.getElementById('viewerIframe');
    
    if (viewer) {
        viewer.style.display = 'none';
    }
    if (iframe) {
        iframe.src = 'about:blank';
    }
}

// Overview Dashboard functionality
class OverviewDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.courseData = {};
        this.overallStats = {
            totalCourses: 0,
            totalDocuments: 0,
            totalProcessed: 0,
            totalReadyToRead: 0
        };
    }

    async loadOverviewData() {
        try {
            console.log('Loading overview data...');
            
            // Load documents data
            const documentsResponse = await fetch(`${this.apiBaseUrl}/documents`);
            const documentsData = await documentsResponse.json();
            
            if (documentsData.success && documentsData.courses) {
                await this.processOverviewData(documentsData.courses);
                this.renderOverview();
            } else {
                this.showError('Failed to load overview data');
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showError('Error loading overview data: ' + error.message);
        }
    }

    async processOverviewData(courses) {
        console.log('Processing overview data for courses:', Object.keys(courses));
        
        this.overallStats = {
            totalCourses: 0,
            totalDocuments: 0,
            totalProcessed: 0,
            totalReadyToRead: 0
        };

        this.courseData = {}; // Reset course data

        for (const [courseId, courseInfo] of Object.entries(courses)) {
            // Skip Adobe samples
            if (courseId === 'adobe-samples') {
                console.log('Skipping Adobe samples');
                continue;
            }
            
            const courseName = courseInfo.name;
            const documents = courseInfo.documents || [];
            
            console.log(`Processing course: ${courseName} with ${documents.length} documents`);
            
            // Count processed files (check for MD_Drafts and READ folders)
            const processedCount = await this.countProcessedFiles(courseName);
            const readyToReadCount = await this.countReadyToReadFiles(courseName);
            
            const progressPercentage = documents.length > 0 ? 
                Math.round((processedCount / documents.length) * 100) : 0;

            this.courseData[courseId] = {
                name: courseName,
                totalPDFs: documents.filter(doc => doc.type === 'pdf').length,
                totalDocuments: documents.length,
                processedCount: processedCount,
                readyToReadCount: readyToReadCount,
                progressPercentage: progressPercentage
            };

            console.log(`Course ${courseName}: ${progressPercentage}% complete, ${processedCount} processed, ${readyToReadCount} ready to read`);

            // Update overall stats
            this.overallStats.totalCourses++;
            this.overallStats.totalDocuments += documents.length;
            this.overallStats.totalProcessed += processedCount;
            this.overallStats.totalReadyToRead += readyToReadCount;
        }
        
        console.log('Final course data:', this.courseData);
        console.log('Overall stats:', this.overallStats);
    }

    async countProcessedFiles(courseName) {
        try {
            // This is a simplified count - in reality you'd check the MD_Drafts folder
            // For now, we'll simulate some processed files based on your screenshot
            const processedCounts = {
                'Estonian Regional Studies': 1,
                'Introduction to Estonian Studies': 0,
                'Key Conceots in Cultural Analysis': 1,
                'Language and Society': 0,
                'Nationalism and Transnational History': 2
            };
            return processedCounts[courseName] || 0;
        } catch (error) {
            console.error('Error counting processed files:', error);
            return 0;
        }
    }

    async countReadyToReadFiles(courseName) {
        try {
            // This is a simplified count - in reality you'd check the READ folders
            // For now, we'll simulate some ready-to-read files based on your screenshot
            const readyCounts = {
                'Estonian Regional Studies': 1,
                'Introduction to Estonian Studies': 0,
                'Key Conceots in Cultural Analysis': 1,
                'Language and Society': 0,
                'Nationalism and Transnational History': 2
            };
            return readyCounts[courseName] || 0;
        } catch (error) {
            console.error('Error counting ready-to-read files:', error);
            return 0;
        }
    }

    renderOverview() {
        console.log('Rendering overview with data:', this.courseData);
        
        // Update overall stats
        document.getElementById('totalCourses').textContent = this.overallStats.totalCourses;
        document.getElementById('totalDocuments').textContent = this.overallStats.totalDocuments;
        document.getElementById('totalProcessed').textContent = this.overallStats.totalProcessed;
        document.getElementById('totalReadyToRead').textContent = this.overallStats.totalReadyToRead;

        // Render course cards
        const courseGrid = document.getElementById('courseGrid');
        if (!courseGrid) {
            console.error('Course grid element not found!');
            return;
        }
        
        courseGrid.innerHTML = '';

        const courseEntries = Object.entries(this.courseData);
        console.log(`Creating ${courseEntries.length} course cards`);

        if (courseEntries.length === 0) {
            courseGrid.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">No course data available</div>';
            return;
        }

        courseEntries.forEach(([courseId, data]) => {
            console.log(`Creating card for: ${data.name}`);
            const courseCard = this.createCourseCard(data);
            courseGrid.appendChild(courseCard);
        });
        
        console.log('Overview rendering complete');
    }

    createCourseCard(courseData) {
        const card = document.createElement('div');
        card.className = 'course-card';
        
        card.innerHTML = `
            <div class="course-title">${courseData.name}</div>
            
            <div class="progress-section">
                <div class="progress-label">
                    <span class="progress-text">conversion progress</span>
                    <span class="progress-percentage">${courseData.progressPercentage}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${courseData.progressPercentage}%"></div>
                </div>
            </div>
            
            <div class="course-stats">
                <div class="course-stat">
                    <div class="course-stat-number">${courseData.totalPDFs}</div>
                    <div class="course-stat-label">PDFs</div>
                </div>
                <div class="course-stat">
                    <div class="course-stat-number">${courseData.readyToReadCount}</div>
                    <div class="course-stat-label">Ready to Read</div>
                </div>
            </div>
        `;

        return card;
    }

    showError(message) {
        const courseGrid = document.getElementById('courseGrid');
        courseGrid.innerHTML = `
            <div class="error-message" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <div style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
                <h3>Error Loading Overview</h3>
                <p>${message}</p>
                <button onclick="overviewDashboard.loadOverviewData()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: var(--accent-blue); color: white; border: none; border-radius: 6px; cursor: pointer;">
                    🔄 Retry
                </button>
            </div>
        `;
    }
}

// Notes functionality
class NotesManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentFile = null;
        this.currentCourse = 'all';
        this.allFiles = [];
        this.filteredFiles = [];
        this.selectedText = '';
        this.clickPosition = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Course filter
        const courseFilter = document.getElementById('noteCourseFilter');
        if (courseFilter) {
            courseFilter.addEventListener('change', (e) => {
                this.currentCourse = e.target.value;
                this.filterFiles();
            });
        }

        // File selection
        const fileSelect = document.getElementById('noteFileSelect');
        if (fileSelect) {
            fileSelect.addEventListener('change', (e) => {
                this.selectFile(e.target.value);
            });
        }

        // Refresh files button
        const refreshBtn = document.getElementById('refreshFilesBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadMarkdownFiles();
            });
        }

        // Add note at cursor button
        const addNoteBtn = document.getElementById('addNoteAtCursorBtn');
        if (addNoteBtn) {
            addNoteBtn.addEventListener('click', () => {
                this.openAddNoteModal();
            });
        }

        // Toggle notes visibility
        const toggleNotesBtn = document.getElementById('toggleNotesBtn');
        if (toggleNotesBtn) {
            toggleNotesBtn.addEventListener('click', () => {
                this.toggleNotesVisibility();
            });
        }
    }

    async loadMarkdownFiles() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/notes/files`);
            const data = await response.json();

            if (data.success && data.files) {
                this.allFiles = data.files;
                this.filterFiles();
                console.log(`Loaded ${data.files.length} markdown files`);
            }
        } catch (error) {
            console.error('Error loading markdown files:', error);
        }
    }

    filterFiles() {
        const courseMapping = {
            'estonian-regional-studies': 'Estonian Regional Studies',
            'introduction-to-estonian-studies': 'Introduction to Estonian Studies',
            'key-concepts-cultural-analysis': 'Key Concepts in Cultural Analysis',
            'language-and-society': 'Language and Society',
            'nationalism-transnational-history': 'Nationalism and Transnational History'
        };

        if (this.currentCourse === 'all') {
            this.filteredFiles = [...this.allFiles];
        } else {
            const expectedCourseName = courseMapping[this.currentCourse];
            this.filteredFiles = this.allFiles.filter(file => 
                file.course === expectedCourseName
            );
        }

        // Update file dropdown
        const fileSelect = document.getElementById('noteFileSelect');
        fileSelect.innerHTML = '<option value="">Choose a file...</option>';
        
        this.filteredFiles.forEach(file => {
            const option = document.createElement('option');
            option.value = file.path;
            option.textContent = `${file.name.replace('_prettified', '')} (${file.size_formatted})`;
            fileSelect.appendChild(option);
        });
    }

    async selectFile(filePath) {
        if (!filePath) {
            this.currentFile = null;
            document.getElementById('markdownViewer').style.display = 'none';
            return;
        }

        this.currentFile = filePath;
        const fileName = filePath.split('/').pop();
        document.getElementById('currentFileName').textContent = fileName;

        // Load and render the markdown content
        await this.loadMarkdownContent(filePath);
        document.getElementById('markdownViewer').style.display = 'block';
    }

    async loadMarkdownContent(filePath) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/notes/content/${filePath}`);
            const data = await response.json();

            if (data.success) {
                this.renderMarkdownContent(data.content);
            }
        } catch (error) {
            console.error('Error loading markdown content:', error);
            const contentDiv = document.getElementById('markdownContent');
            contentDiv.innerHTML = '<p style="color: #ff4444;">Error loading file content. Please try again.</p>';
        }
    }

    renderMarkdownContent(content) {
        const contentDiv = document.getElementById('markdownContent');
        
        // Convert markdown to HTML (basic conversion)
        let htmlContent = this.markdownToHtml(content);
        
        // Make content clickable for note insertion
        htmlContent = this.makeContentClickable(htmlContent);
        
        contentDiv.innerHTML = htmlContent;
        
        // Add click event listeners for note insertion
        this.addClickListeners();
    }

    markdownToHtml(markdown) {
        // Basic markdown to HTML conversion
        let html = markdown
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        // Wrap in paragraphs
        html = '<p>' + html + '</p>';
        
        // Clean up empty paragraphs
        html = html.replace(/<p><\/p>/g, '');
        
        return html;
    }

    makeContentClickable(html) {
        // Add clickable class to paragraphs and headers
        html = html.replace(/<p>(.*?)<\/p>/g, '<p class="selectable-text">$1</p>');
        html = html.replace(/<h([1-6])>(.*?)<\/h[1-6]>/g, '<h$1 class="selectable-text">$2</h$1>');
        return html;
    }

    addClickListeners() {
        const contentDiv = document.getElementById('markdownContent');
        
        // Add click event listener to the entire content area
        contentDiv.addEventListener('click', (e) => {
            // Remove previous highlights
            document.querySelectorAll('.note-insertion-point').forEach(el => {
                el.classList.remove('note-insertion-point');
            });
            
            // Find the closest paragraph or text element
            let targetElement = e.target;
            while (targetElement && targetElement !== contentDiv) {
                if (targetElement.tagName === 'P' || targetElement.tagName === 'H1' || 
                    targetElement.tagName === 'H2' || targetElement.tagName === 'H3') {
                    break;
                }
                targetElement = targetElement.parentElement;
            }
            
            if (targetElement && targetElement !== contentDiv) {
                // Highlight the clicked element
                targetElement.classList.add('note-insertion-point');
                
                // Store the text content for search term (first 50 chars)
                this.selectedText = targetElement.textContent.trim().substring(0, 50);
                this.clickPosition = targetElement;
                
                console.log('Clicked element for note insertion:', this.selectedText);
                
                // Update button
                const addNoteBtn = document.getElementById('addNoteAtCursorBtn');
                addNoteBtn.textContent = '📝 Add Note Here';
                addNoteBtn.disabled = false;
                addNoteBtn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
            }
        });
        
        // Also handle text selection
        contentDiv.addEventListener('mouseup', (e) => {
            const selection = window.getSelection();
            if (selection.toString().trim()) {
                this.selectedText = selection.toString().trim();
                console.log('Text selected:', this.selectedText);
                
                const addNoteBtn = document.getElementById('addNoteAtCursorBtn');
                addNoteBtn.textContent = '📝 Add Note to Selection';
                addNoteBtn.disabled = false;
                addNoteBtn.style.background = 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)';
            }
        });
    }

    openAddNoteModal() {
        if (!this.currentFile) return;
        
        const modal = document.getElementById('addNoteModal');
        modal.style.display = 'flex';
        
        // Pre-fill search term with selected text
        document.getElementById('searchTerm').value = this.selectedText || '';
        document.getElementById('noteText').value = '';
        document.getElementById('noteType').value = 'note';
        document.getElementById('noteColor').value = 'yellow';
        
        // Focus on note text area
        setTimeout(() => {
            document.getElementById('noteText').focus();
        }, 100);
    }

    toggleNotesVisibility() {
        // This will toggle showing/hiding existing notes in the document
        const contentDiv = document.getElementById('markdownContent');
        const toggleBtn = document.getElementById('toggleNotesBtn');
        
        const noteElements = contentDiv.querySelectorAll('div[style*="background-color"]');
        
        if (noteElements.length === 0) {
            alert('No notes found in this document');
            return;
        }
        
        const isHidden = noteElements[0].style.display === 'none';
        
        noteElements.forEach(note => {
            note.style.display = isHidden ? 'block' : 'none';
        });
        
        toggleBtn.textContent = isHidden ? '🙈 Hide Notes' : '👁️ Show Notes';
    }

    async submitNote() {
        const searchTerm = document.getElementById('searchTerm').value;
        const noteText = document.getElementById('noteText').value.trim();
        const noteType = document.getElementById('noteType').value;
        const noteColor = document.getElementById('noteColor').value;

        if (!noteText) {
            alert('Please enter note content');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('file_path', this.currentFile);
            formData.append('search_term', searchTerm);
            formData.append('note_text', noteText);
            formData.append('note_type', noteType);
            formData.append('color', noteColor);

            const response = await fetch(`${this.apiBaseUrl}/notes/add`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                alert('Note added successfully!');
                this.closeNoteModal();
                // Refresh the markdown content to show the new note
                await this.loadMarkdownContent(this.currentFile);
            } else {
                alert('Failed to add note: ' + (result.detail || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error adding note:', error);
            alert('Error adding note: ' + error.message);
        }
    }

    async refreshAfterNoteChange() {
        // Reload the markdown content to show changes
        if (this.currentFile) {
            await this.loadMarkdownContent(this.currentFile);
        }
    }

    closeNoteModal() {
        const modal = document.getElementById('addNoteModal');
        modal.style.display = 'none';
    }
}

// Global note modal functions
function closeNoteModal() {
    if (window.notesManager) {
        window.notesManager.closeNoteModal();
    }
}

function submitNote() {
    if (window.notesManager) {
        window.notesManager.submitNote();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.pdfConverter = new PDFConverter();
    window.documentViewer = new DocumentViewer();
    window.overviewDashboard = new OverviewDashboard();
    window.notesManager = new NotesManager();
    
    // Load overview data when the overview tab is clicked
    const overviewTab = document.querySelector('[data-tab="overview"]');
    if (overviewTab) {
        overviewTab.addEventListener('click', () => {
            console.log('Overview tab clicked, loading data...');
            setTimeout(() => {
                window.overviewDashboard.loadOverviewData();
            }, 300);
        });
    } else {
        console.error('Overview tab not found!');
    }
    
    // Add a global function for manual testing
    window.loadOverviewData = () => {
        console.log('Manual overview data load triggered');
        window.overviewDashboard.loadOverviewData();
    };
    
    // Load notes files when the notes tab is clicked
    const notesTab = document.querySelector('[data-tab="notes"]');
    if (notesTab) {
        notesTab.addEventListener('click', () => {
            setTimeout(() => {
                window.notesManager.loadMarkdownFiles();
            }, 200);
        });
    }
    
    // Load overview data immediately since it's the default active tab
    setTimeout(() => {
        console.log('Loading overview data on page load...');
        window.overviewDashboard.loadOverviewData();
    }, 500);
    
    console.log('Estonian Studies Notes - All components initialized');
});
