# Estonian Studies Notes - Frontend

A sleek, dark-themed frontend interface inspired by the Estonian flag colors for the PDF Content Extraction system.

## 🎨 Design Features

### Estonian Flag Color Palette
- **Primary Blue**: `#0072CE` (Estonian Blue)
- **Accent Black**: `#000000` 
- **Highlight White**: `#FFFFFF`
- **Dark Theme**: Custom dark variations for modern UI

### Visual Elements
- **Flag Accent**: Miniature Estonian flag in header
- **Dark Mode**: Optimized for comfortable viewing
- **Modern Typography**: Inter font family
- **Smooth Animations**: Hover effects and transitions
- **Responsive Design**: Mobile-friendly layout

## 📁 File Structure

```
├── index.html              # Main application with 8 tabs
├── pdf_converter.html       # Standalone PDF converter page
├── styles.css              # Complete styling with Estonian theme
├── script.js               # JavaScript functionality and API integration
└── frontend_README.md      # This documentation
```

## 🚀 Pages Overview

### 1. Main Application (`index.html`)
- **Header**: "Estonian Studies Notes" with flag accent
- **8 Navigation Tabs**:
  1. Overview (placeholder)
  2. Documents (placeholder)  
  3. **PDF Converter** (fully implemented)
  4. Analysis (placeholder)
  5. Research (placeholder)
  6. Timeline (placeholder)
  7. References (placeholder)
  8. Settings (placeholder)

### 2. Standalone PDF Converter (`pdf_converter.html`)
- Dedicated full-page interface for PDF processing
- Enhanced upload area with animations
- API status indicator
- Back navigation to main app

## 🔧 PDF Converter Features

### Upload Interface
- **Drag & Drop**: Visual feedback and animations
- **File Validation**: PDF type and size checking (50MB limit)
- **File Info Display**: Name and size with remove option

### Extraction Options
- **Content Types**: Text, Tables, Figures
- **Advanced Options**: Styling info, Character bounds
- **Quick Presets**: Text-only, With Tables, Comprehensive

### Results Display
- **Processing Stats**: Extraction ID, processing time
- **Content Summary**: Element counts with visual cards
- **Preview**: Sample extracted content
- **Export Options**: Download JSON, View detailed results

### Status Management
- **Loading States**: Button animations and spinners
- **Error Handling**: Clear error messages with styling
- **Success Feedback**: Confirmation messages
- **API Status**: Real-time connection indicator

## 🎯 User Experience

### Interactive Elements
- **Hover Effects**: Smooth transitions on all interactive elements
- **Visual Feedback**: Color changes, shadows, and transforms
- **Loading Indicators**: Spinners and progress states
- **Responsive Layout**: Adapts to different screen sizes

### Accessibility
- **High Contrast**: Dark theme with sufficient color contrast
- **Clear Typography**: Readable fonts and sizing
- **Keyboard Navigation**: Tab-friendly interface
- **Screen Reader Friendly**: Semantic HTML structure

## 🔌 API Integration

### Connection Management
- **Base URL**: `http://localhost:8000`
- **Health Checks**: Automatic API status monitoring
- **Error Handling**: Graceful degradation when API is offline
- **Timeout Handling**: 60-second request timeout

### Supported Endpoints
- `GET /` - Health check
- `POST /pdf-converter` - Main extraction endpoint
- `POST /pdf-converter/text-only` - Text-only extraction
- `POST /pdf-converter/with-tables` - Text and tables
- `POST /pdf-converter/comprehensive` - Full extraction

### Request Handling
- **FormData Upload**: Proper file handling
- **Option Parameters**: Dynamic extraction settings
- **Progress Tracking**: Loading states and feedback
- **Result Processing**: JSON response parsing and display

## 🚦 Getting Started

### 1. Start the API Server
```bash
# In your API directory
python main.py
```

### 2. Open the Frontend
```bash
# Option 1: Main application
open index.html

# Option 2: Standalone PDF converter
open pdf_converter.html
```

### 3. Test the Interface
1. Ensure API is running (check status indicator)
2. Select a PDF file
3. Choose extraction options or use presets
4. Click "Start Extraction" or "Convert PDF"
5. View results and download JSON

## 📱 Responsive Breakpoints

- **Desktop**: > 768px (full layout)
- **Tablet**: 768px (adjusted spacing)
- **Mobile**: < 768px (single column, compressed layout)

## 🎨 Customization

### Color Variables
All colors are defined as CSS custom properties in `:root`:
```css
--estonian-blue: #0072CE;
--estonian-blue-dark: #005BA6;
--estonian-blue-light: #339FDB;
--bg-primary: #0A0A0A;
--text-primary: #FFFFFF;
```

### Typography Scale
- **Headers**: 2.5rem → 1.5rem (responsive)
- **Body**: 1rem base with 1.6 line height
- **Small Text**: 0.875rem for secondary info

## 🔧 Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## 📊 Performance Features

- **CSS Grid**: Efficient layouts
- **Flexbox**: Responsive components  
- **CSS Animations**: Hardware-accelerated transitions
- **Optimized Images**: Estonian flag as CSS gradient
- **Minimal JavaScript**: Efficient DOM manipulation

## 🛠️ Development Notes

### File Organization
- Styles are centralized in `styles.css`
- JavaScript is modular with class-based architecture
- HTML is semantic and accessible

### Code Quality
- **Consistent Naming**: BEM-inspired CSS classes
- **Modern JavaScript**: ES6+ features
- **Error Handling**: Comprehensive try-catch blocks
- **Documentation**: Inline comments and clear function names

This frontend provides a professional, Estonian-themed interface for the PDF extraction system with excellent user experience and robust functionality.
