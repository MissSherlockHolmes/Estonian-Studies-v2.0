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
        
        // Create a URL for the document using our API
        const fileExtension = path.split('.').pop().toLowerCase();
        let viewerUrl;

        if (fileExtension === 'pdf') {
            // Use PDF.js viewer with our API endpoint
            const apiUrl = `${this.apiBaseUrl}/documents/${path}`;
            viewerUrl = `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(apiUrl)}`;
        } else if (fileExtension === 'docx' || fileExtension === 'doc') {
            // Use Microsoft Office Online viewer with our API
            const apiUrl = `${this.apiBaseUrl}/documents/${path}`;
            viewerUrl = `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(apiUrl)}`;
        } else if (fileExtension === 'pptx' || fileExtension === 'ppt') {
            // Use Microsoft Office Online viewer with our API
            const apiUrl = `${this.apiBaseUrl}/documents/${path}`;
            viewerUrl = `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(apiUrl)}`;
        } else {
            // Fallback to direct API access
            viewerUrl = `${this.apiBaseUrl}/documents/${path}`;
        }

        iframe.src = viewerUrl;
        viewer.style.display = 'flex';
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

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.pdfConverter = new PDFConverter();
    window.documentViewer = new DocumentViewer();
    console.log('Estonian Studies Notes - PDF Converter and Document Viewer initialized');
});
