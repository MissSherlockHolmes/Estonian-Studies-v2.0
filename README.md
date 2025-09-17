# Estonian Studies v2.0

A comprehensive digital platform for Estonian Studies research and document management, featuring advanced PDF processing, AI-powered content extraction, and an intuitive web interface.

## 🌟 Features

### 📄 PDF Processing & Extraction
- **Adobe PDF Services SDK Integration** - Professional-grade PDF text, table, and figure extraction
- **Multi-format Support** - PDF, DOCX, PPTX document viewing and processing
- **Structured Data Output** - JSON format with organized content and metadata

### 🤖 AI-Powered Content Processing
- **Ollama Integration** - Local LLM processing with Granite 3.2 Vision model
- **Markdown Conversion** - Automatic conversion of extracted content to structured markdown
- **GPT Enhancement** - OpenAI-powered content prettification and formatting

### 🎨 Modern Web Interface
- **Sleek Dark Theme** - Estonian flag-inspired color scheme
- **Responsive Design** - Clean, modern UI with smooth animations
- **Document Viewer** - Inline PDF, DOCX, and PPTX viewing
- **Advanced Filtering** - Search and filter by course, document type, and content

### 📚 Course Management
- **Organized Structure** - Course-specific directories and file organization
- **Multi-format Support** - PDFs, Word documents, and PowerPoint presentations
- **Batch Processing** - Efficient handling of multiple documents

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for frontend development)
- Adobe PDF Services API credentials
- Ollama (for local AI processing)
- OpenAI API key (optional, for content enhancement)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MissSherlockHolmes/Estonian-Studies-v2.0.git
   cd Estonian-Studies-v2.0
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with your API credentials:
   ```env
   ADOBE_CLIENT_ID=your_adobe_client_id
   ADOBE_CLIENT_SECRET=your_adobe_client_secret
   OPENAI_API_KEY=your_openai_api_key
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **Start the backend server**
   ```bash
   python main.py
   ```

5. **Open the frontend**
   Open `index.html` in your web browser or serve it with a local server.

## 📁 Project Structure

```
Estonian-Studies-v2.0/
├── main.py                 # FastAPI backend server
├── index.html              # Main frontend interface
├── styles.css              # Styling and themes
├── script.js               # Frontend JavaScript
├── gpt_converter.py        # GPT content enhancement
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .gitignore             # Git ignore rules
├── README.md              # This file
│
├── Course Directories/
│   ├── Estonian Regional Studies/
│   │   ├── PDFS_Estonian_Regional_Studies/
│   │   ├── adobe_output/
│   │   ├── MD_Drafts/
│   │   └── READ_*/
│   ├── Introduction to Estonian Studies/
│   ├── Key Concepts in Cultural Analysis/
│   ├── Language and Society/
│   └── Nationalism and Transnational History/
│
└── PDFServicesSDK-PythonSamples/
    └── adobe-dc-pdf-services-sdk-python/
```

## 🔧 API Endpoints

### PDF Processing
- `POST /pdf-converter` - Process PDF with full extraction
- `POST /pdf-converter/text-only` - Extract text only
- `POST /pdf-converter/with-tables` - Extract text and tables
- `POST /pdf-converter/comprehensive` - Full extraction with all features

### Document Management
- `GET /documents` - List all available documents
- `GET /documents/{file_path}` - Serve document files
- `GET /pdfs` - List PDF files for conversion

## 🎯 Usage

### Document Processing Workflow

1. **Upload/Select PDF** - Choose a PDF from your course directories
2. **Adobe Extraction** - Extract text, tables, and figures using Adobe PDF Services
3. **Ollama Processing** - Convert extracted content to structured markdown
4. **GPT Enhancement** - Prettify and format the markdown content
5. **Save Results** - Store processed files in organized course directories

### Document Viewing

1. **Navigate to Documents Tab** - Access the document viewer
2. **Filter by Course/Type** - Use the filter controls to find specific documents
3. **Search Content** - Search by document name or content
4. **View Inline** - Click to view documents directly in the browser

## 🛠️ Configuration

### Adobe PDF Services
- Sign up at [Adobe PDF Services](https://developer.adobe.com/document-services/)
- Create credentials and add them to your `.env` file

### Ollama Setup
- Install [Ollama](https://ollama.ai/)
- Pull the Granite model: `ollama pull granite3.2-vision:latest`

### OpenAI Integration (Optional)
- Get API key from [OpenAI](https://platform.openai.com/)
- Add to `.env` file for content enhancement features

## 📊 Features in Detail

### PDF Extraction Capabilities
- **Text Extraction** - Clean, structured text with formatting preservation
- **Table Detection** - Automatic table identification and extraction
- **Figure Extraction** - Image and diagram capture with metadata
- **Layout Analysis** - Understanding of document structure and hierarchy

### AI Processing Pipeline
- **Content Chunking** - Smart text splitting for large documents
- **Markdown Generation** - Structured, readable markdown output
- **Content Enhancement** - GPT-powered formatting and organization
- **Quality Control** - Validation and error handling throughout the pipeline

### User Interface
- **Modern Design** - Clean, professional interface with Estonian flag colors
- **Responsive Layout** - Works on desktop, tablet, and mobile devices
- **Intuitive Navigation** - Easy-to-use tabs and controls
- **Real-time Feedback** - Progress indicators and status updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Adobe PDF Services** - For professional PDF processing capabilities
- **Ollama** - For local AI model hosting and processing
- **OpenAI** - For advanced content enhancement
- **FastAPI** - For the robust backend framework
- **Estonian Studies Community** - For inspiration and academic support

## 📞 Support

For support, questions, or feature requests, please open an issue on GitHub or contact the development team.

---

**Estonian Studies v2.0** - Empowering academic research through technology 🇪🇪