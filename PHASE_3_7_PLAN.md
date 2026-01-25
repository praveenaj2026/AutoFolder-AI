# 🚀 Phase 3.7 - Content-Based AI Analysis

## Overview
Implement content analysis to improve file organization accuracy by analyzing actual file content, not just filenames.

## Features to Implement

### Feature 1: Content-Based AI (Beyond Filenames)
**Priority**: ⭐⭐⭐⭐⭐

#### Description
Analyze actual file content for smarter grouping using:
- PDF text extraction
- OCR for scanned documents  
- Document type detection
- Content-based semantic grouping

#### Why This Feature?
Current AI grouping only uses filenames, which can be cryptic (e.g., IMG_20240115.jpg, Scan001.pdf). Analyzing actual content will:
- Identify documents by type (Resume, Invoice, Contract, etc.)
- Group related documents even with different filenames
- Improve accuracy from ~80% to ~95%+

#### Implementation Plan

##### 1. PDF Text Extraction
```python
# New file: src/core/content_analyzer.py
class ContentAnalyzer:
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF."""
        import PyMuPDF  # or pdfplumber
        
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
```

##### 2. OCR for Scanned Documents
```python
def extract_text_from_image(self, image_path: Path) -> str:
    """OCR for scanned documents."""
    import pytesseract
    from PIL import Image
    
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text
```

##### 3. Document Type Detection
```python
def detect_document_type(self, text: str) -> str:
    """Detect document type from content."""
    keywords = {
        'Resume': ['resume', 'cv', 'education', 'experience', 'skills'],
        'Invoice': ['invoice', 'bill', 'amount due', 'total'],
        'Contract': ['agreement', 'party', 'terms', 'conditions'],
        'Bank Statement': ['statement', 'balance', 'transaction'],
        'Salary Slip': ['salary', 'gross pay', 'deductions'],
        'Letter': ['dear', 'sincerely', 'regards']
    }
    
    text_lower = text.lower()
    for doc_type, kw_list in keywords.items():
        matches = sum(1 for kw in kw_list if kw in text_lower)
        if matches >= 2:  # At least 2 keywords match
            return doc_type
    
    return 'Unknown'
```

##### 4. Enhanced AI Grouping
```python
def create_content_based_groups(self, files: List[Path]) -> Dict[str, List[Path]]:
    """Group files by actual content."""
    file_data = []
    
    for file in files:
        # Extract text
        if file.suffix == '.pdf':
            text = self.extract_text_from_pdf(file)
        elif file.suffix in ['.jpg', '.png', '.jpeg']:
            text = self.extract_text_from_image(file)
        else:
            text = file.stem  # Fall back to filename
        
        # Detect document type
        doc_type = self.detect_document_type(text)
        
        # Combine filename + content + doc_type for AI embedding
        combined = f"{file.stem} {doc_type} {text[:500]}"  # First 500 chars
        
        file_data.append({
            'path': file,
            'text': combined,
            'doc_type': doc_type
        })
    
    # Use AI to create semantic groups with content
    # Much more accurate than filename-only
```

#### UI Changes

1. **Options Panel**
```
📄 Content Analysis

☑️ Analyze PDF content
☑️ OCR for scanned documents  
☑️ Detect document types

OCR Language: [English ▼]

⚠️ Note: Content analysis is slower but more accurate
Estimated time: 2-3 seconds per file
```

2. **Progress Dialog**
```
🤖 AI Organizing with Content Analysis...

Current: Analyzing Resume_2024.pdf
Operation: Extracting text from PDF
Document Type: Resume (detected)

Progress: 15 / 140 files (11%)
AI Groups: 3 created
Time remaining: ~5 minutes

[Cancel]
```

3. **Preview Enhancement**
```
Preview shows:
- Detected Document Type badge
- First line of extracted content
- Confidence score

Example:
📄 Scan_001.pdf
   🏷️ Resume (95% confident)
   "John Doe - Software Engineer with 5 years experience..."
```

#### Configuration
```yaml
# config/default_config.yaml

content_analysis:
  enabled: true
  analyze_pdfs: true
  ocr_images: true
  detect_document_types: true
  ocr_language: "eng"
  max_file_size_mb: 50  # Skip files larger than this
  cache_results: true
  cache_expiry_days: 30
```

#### Dependencies
```bash
pip install PyMuPDF  # PDF text extraction
pip install pytesseract  # OCR
pip install Pillow  # Image handling
```

For Windows, also install Tesseract OCR:
```powershell
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use: choco install tesseract
```

#### Files to Create
- `src/core/content_analyzer.py` - Main content analysis logic

#### Files to Modify
- `src/core/ai_classifier.py` - Integrate content analysis
- `src/core/organizer.py` - Add content analysis step
- `src/ui/main_window.py` - Add content analysis options
- `config/default_config.yaml` - Add content analysis settings

#### Implementation Steps

1. **Day 1-2**: PDF text extraction
   - Implement PyMuPDF integration
   - Handle errors gracefully (corrupted PDFs, encrypted PDFs)
   - Test with 20+ different PDF types

2. **Day 3-4**: OCR implementation
   - Set up pytesseract
   - Optimize for speed (resize images, limit resolution)
   - Handle different image formats

3. **Day 5-6**: Document type detection
   - Build keyword dictionary
   - Test accuracy on 50+ documents
   - Tune keyword weights

4. **Day 7-9**: Integration with AI classifier
   - Combine content + filename for embeddings
   - Update grouping logic
   - Test end-to-end

5. **Day 10-11**: UI implementation
   - Add options panel
   - Update progress dialog
   - Add document type badges

6. **Day 12-13**: Testing and refinement
   - Test with real user data
   - Measure accuracy improvement
   - Performance optimization

#### Expected Outcomes

**Before Content Analysis** (Filename only):
```
Resume/
  - IMG_20240115.jpg (❌ Should be Resume but no clue from filename)
  - Scan001.pdf (❌ Could be anything)
  - Document.pdf (❌ Too generic)
```

**After Content Analysis**:
```
Resume/
  - IMG_20240115.jpg (✅ Detected: Resume with photo)
  - Scan001.pdf (✅ Detected: Cover Letter)
  - Document.pdf (✅ Detected: CV with work experience)

Invoices/
  - Scan002.pdf (✅ Detected: Electricity bill)
  - Document2.pdf (✅ Detected: Water invoice)
```

#### Success Metrics
- **Accuracy**: 80% → 95%+ correct grouping
- **Document Type Detection**: 90%+ accuracy
- **Speed**: 2-3 seconds per file (acceptable)
- **User Satisfaction**: "AI finally understands my files!"

#### Estimated Time
- **Development**: 10-13 days (80-100 hours)
- **Testing**: 2-3 days
- **Total**: 12-16 days

#### Risk Assessment
- **Low Risk**: PDF text extraction (well-established libraries)
- **Medium Risk**: OCR accuracy (depends on scan quality)
- **Low Risk**: Document type detection (simple keyword matching)

---

## Phase 3.7 Goals

1. ✅ Implement PDF text extraction
2. ✅ Implement OCR for scanned documents
3. ✅ Build document type detection
4. ✅ Integrate with AI classifier
5. ✅ Add UI options and progress indicators
6. ✅ Test and refine accuracy

## Timeline

**Start Date**: TBD
**Target Duration**: 12-16 days
**Dependencies**: Phase 3.6 complete ✅

---

## Note from Phase 3.6

Phase 3.6 completed with:
- ✅ Extended Categories (21 total)
- ✅ Feature Simplification (removed Edit AI Groups + Auto Schedule)
- ✅ UI Improvements (preview columns, stats cleanup)
- ✅ Bug Fixes (duplicate handling, error reporting)

**Phase 3.7 will focus on AI accuracy improvements through content analysis.**

---

**Status**: 📝 PLANNED  
**Priority**: ⭐⭐⭐⭐⭐ (High value for accuracy)  
**Date Created**: January 25, 2026
