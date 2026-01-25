"""
Content Analyzer - Extract and analyze file content for smarter AI grouping.

Phase 3.7 Feature: Analyze actual file content (PDFs, images) to improve
AI classification accuracy from ~80% to 95%+.
"""

import logging
import os
import sys
import shutil
import ctypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    Analyze file content for better AI classification.
    
    Features:
    - PDF text extraction
    - OCR for scanned documents/images
    - Document type detection (Resume, Invoice, Contract, etc.)
    """
    
    # Document type keywords for classification
    DOCUMENT_TYPES = {
        'Resume': {
            'keywords': ['resume', 'curriculum vitae', 'cv', 'work experience', 
                        'education', 'skills', 'objective', 'career', 'qualifications',
                        'employment history', 'professional summary'],
            'min_matches': 2,
            'weight': 1.0
        },
        'Cover_Letter': {
            'keywords': ['cover letter', 'dear hiring', 'dear sir', 'dear madam',
                        'application for', 'i am writing', 'position', 'opportunity',
                        'sincerely', 'thank you for considering'],
            'min_matches': 2,
            'weight': 1.0
        },
        'Invoice': {
            'keywords': ['invoice', 'bill', 'amount due', 'total', 'payment',
                        'invoice number', 'invoice date', 'due date', 'subtotal',
                        'tax', 'balance due', 'remit to'],
            'min_matches': 3,
            'weight': 1.0
        },
        'Receipt': {
            'keywords': ['receipt', 'paid', 'transaction', 'thank you', 
                        'purchase', 'payment received', 'cash', 'change',
                        'subtotal', 'total amount'],
            'min_matches': 2,
            'weight': 0.9
        },
        'Contract': {
            'keywords': ['agreement', 'contract', 'party', 'terms', 'conditions',
                        'whereas', 'hereby', 'shall', 'obligations', 'liability',
                        'termination', 'witness', 'signed'],
            'min_matches': 3,
            'weight': 1.0
        },
        'Bank_Statement': {
            'keywords': ['statement', 'account', 'balance', 'transaction',
                        'deposit', 'withdrawal', 'opening balance', 'closing balance',
                        'credit', 'debit', 'bank'],
            'min_matches': 3,
            'weight': 1.0
        },
        'Salary_Slip': {
            'keywords': ['salary', 'payslip', 'pay slip', 'gross pay', 'net pay',
                        'deductions', 'earnings', 'employee', 'basic', 'allowance',
                        'pf', 'tax deducted', 'take home'],
            'min_matches': 3,
            'weight': 1.0
        },
        'ID_Document': {
            'keywords': ['passport', 'license', 'identity', 'id card', 'national id',
                        'date of birth', 'dob', 'address', 'valid until', 'issued'],
            'min_matches': 2,
            'weight': 0.8
        },
        'Certificate': {
            'keywords': ['certificate', 'certify', 'awarded', 'completion',
                        'achievement', 'hereby certify', 'successfully completed',
                        'awarded to', 'presented to'],
            'min_matches': 2,
            'weight': 0.9
        },
        'Report': {
            'keywords': ['report', 'analysis', 'findings', 'conclusion',
                        'executive summary', 'methodology', 'results', 'recommendations'],
            'min_matches': 2,
            'weight': 0.7
        },
        'Letter': {
            'keywords': ['dear', 'sincerely', 'regards', 'yours truly',
                        'to whom it may concern', 'subject:', 'reference:'],
            'min_matches': 2,
            'weight': 0.6
        },
        'Form': {
            'keywords': ['form', 'fill', 'application', 'please complete',
                        'signature', 'date:', 'name:', 'address:', 'checkbox'],
            'min_matches': 2,
            'weight': 0.6
        }
    }
    
    def __init__(self, config: Dict = None):
        """
        Initialize content analyzer.
        
        Args:
            config: Configuration dictionary with content_analysis settings
        """
        self.config = config or {}
        self.content_config = self.config.get('content_analysis', {})
        
        # Settings
        self.enabled = self.content_config.get('enabled', True)
        self.analyze_pdfs = self.content_config.get('analyze_pdfs', True)
        self.ocr_images = self.content_config.get('ocr_images', True)
        self.detect_document_types = self.content_config.get('detect_document_types', True)
        self.max_file_size_mb = self.content_config.get('max_file_size_mb', 50)
        self.ocr_language = self.content_config.get('ocr_language', 'eng')
        
        # Check available libraries
        self._pdf_available = False
        self._ocr_available = False
        self._check_dependencies()
        
        # Cache for extracted content
        self.content_cache: Dict[str, Dict] = {}
        
        logger.info(f"ContentAnalyzer initialized: PDF={self._pdf_available}, OCR={self._ocr_available}")
    
    def _check_dependencies(self):
        """Check which content analysis libraries are available."""
        # Check for PDF library (PyMuPDF/fitz)
        try:
            import fitz  # PyMuPDF
            self._pdf_available = True
            logger.info("PDF analysis available (PyMuPDF)")
        except ImportError:
            try:
                import pdfplumber
                self._pdf_available = True
                logger.info("PDF analysis available (pdfplumber)")
            except ImportError:
                logger.warning("No PDF library found. Install PyMuPDF: pip install PyMuPDF")
        
        # Check for OCR library (pytesseract)
        try:
            import pytesseract
            from PIL import Image

            # Try PATH first
            tesseract_on_path = shutil.which('tesseract')
            if tesseract_on_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_on_path
                logger.info(f"Found Tesseract on PATH: {tesseract_on_path}")
            
            # Try common installation + bundled locations
            current_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
            if not current_cmd or not os.path.exists(current_cmd):
                username = os.getenv('USERNAME', '')
                common_paths = [
                    os.getenv('TESSERACT_CMD'),
                    os.getenv('TESSERACT_PATH'),
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    f"C:\\Users\\{username}\\AppData\\Local\\Tesseract-OCR\\tesseract.exe",
                    r"C:\Tesseract-OCR\tesseract.exe",
                ]

                app_root = self._get_app_root()
                common_paths.extend([
                    str(app_root / 'tesseract.exe'),
                    str(app_root / 'Tesseract-OCR' / 'tesseract.exe'),
                    str(app_root / 'third_party' / 'tesseract.exe'),
                    str(app_root / 'third_party' / 'Tesseract-OCR' / 'tesseract.exe'),
                    str(app_root / 'third_party' / 'tesseract' / 'tesseract.exe'),
                ])

                for path in common_paths:
                    if path and os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Found Tesseract at: {path}")
                        break
            
            # Quick test to see if tesseract is installed
            try:
                pytesseract.get_tesseract_version()
                self._ocr_available = True
                logger.info("OCR analysis available (pytesseract + Tesseract-OCR)")
            except Exception as e:
                logger.warning(f"pytesseract installed but Tesseract-OCR software not found: {e}")
                bundled = self._find_bundled_tesseract_installer()
                if bundled:
                    logger.warning("Tesseract installer is bundled with this app.")
                    logger.warning("Open Tools → Install OCR (Tesseract), then restart.")
                else:
                    logger.warning("To enable OCR, download and install Tesseract from:")
                    logger.warning("https://github.com/UB-Mannheim/tesseract/wiki")
                    logger.warning("After installing, restart the application.")
        except ImportError:
            logger.warning("OCR not available. Install: pip install pytesseract Pillow")
            logger.warning("Then install Tesseract-OCR from: https://github.com/UB-Mannheim/tesseract/wiki")

    def _get_app_root(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[2]

    def _find_bundled_tesseract_installer(self) -> Optional[Path]:
        """Find a bundled Tesseract installer EXE if present."""
        roots = [self._get_app_root()]
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            roots.append(Path(meipass))

        patterns = [
            'tesseract-ocr-*-setup-*.exe',
            'tesseract*setup*.exe',
        ]

        for root in roots:
            third_party = root / 'third_party'
            for pattern in patterns:
                if third_party.exists():
                    for candidate in third_party.glob(pattern):
                        if candidate.is_file():
                            return candidate
                for candidate in root.glob(pattern):
                    if candidate.is_file():
                        return candidate
        return None

    def install_tesseract(self) -> Tuple[bool, str]:
        """Attempt to install Tesseract OCR on Windows using the bundled installer."""
        if os.name != 'nt':
            return False, "Tesseract auto-install is only supported on Windows."

        installer = self._find_bundled_tesseract_installer()
        if not installer:
            return False, "Bundled Tesseract installer not found."

        try:
            # Launch installer elevated (UAC) in silent mode.
            # The UB-Mannheim installer supports /S for silent.
            rc = ctypes.windll.shell32.ShellExecuteW(
                None,
                'runas',
                str(installer),
                '/S',
                str(installer.parent),
                1,
            )
            if rc <= 32:
                return False, f"Failed to launch installer (ShellExecute rc={rc})."

            return True, "Installer launched. Finish install, then restart AutoFolder AI."
        except Exception as e:
            return False, f"Failed to start installer: {e}"

    def refresh_dependencies(self):
        """Re-check OCR/PDF dependency availability."""
        self._pdf_available = False
        self._ocr_available = False
        self._check_dependencies()
    
    def is_available(self) -> bool:
        """Check if any content analysis is available."""
        return self._pdf_available or self._ocr_available
    
    def get_status(self) -> Dict[str, bool]:
        """Get status of content analysis features."""
        return {
            'enabled': self.enabled,
            'pdf_available': self._pdf_available,
            'ocr_available': self._ocr_available,
            'analyze_pdfs': self.analyze_pdfs and self._pdf_available,
            'ocr_images': self.ocr_images and self._ocr_available
        }
    
    def extract_text(self, file_path: Path) -> Optional[str]:
        """
        Extract text from a file based on its type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text or None if extraction failed
        """
        if not self.enabled:
            return None
        
        # Check cache
        cache_key = str(file_path)
        if cache_key in self.content_cache:
            return self.content_cache[cache_key].get('text')
        
        # Check file size
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                logger.debug(f"Skipping {file_path.name}: too large ({file_size_mb:.1f} MB)")
                return None
        except Exception:
            return None
        
        text = None
        suffix = file_path.suffix.lower()
        
        # PDF extraction
        if suffix == '.pdf' and self.analyze_pdfs and self._pdf_available:
            text = self._extract_pdf_text(file_path)
        
        # Image OCR
        elif suffix in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'] and self.ocr_images and self._ocr_available:
            text = self._extract_image_text(file_path)
        
        # Cache result
        if text:
            self.content_cache[cache_key] = {
                'text': text,
                'length': len(text)
            }
        
        return text
    
    def _extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """Extract text from PDF file."""
        try:
            # Try PyMuPDF first (faster)
            try:
                import fitz
                doc = fitz.open(str(pdf_path))
                text_parts = []
                
                # Limit to first 5 pages for speed
                max_pages = min(len(doc), 5)
                
                for page_num in range(max_pages):
                    page = doc[page_num]
                    text_parts.append(page.get_text())
                
                doc.close()
                text = "\n".join(text_parts)
                
                if text.strip():
                    logger.debug(f"Extracted {len(text)} chars from PDF: {pdf_path.name}")
                    return text[:10000]  # Limit to 10k chars
                    
            except ImportError:
                pass
            
            # Try pdfplumber as fallback
            try:
                import pdfplumber
                with pdfplumber.open(str(pdf_path)) as pdf:
                    text_parts = []
                    max_pages = min(len(pdf.pages), 5)
                    
                    for i in range(max_pages):
                        page_text = pdf.pages[i].extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    
                    text = "\n".join(text_parts)
                    
                    if text.strip():
                        logger.debug(f"Extracted {len(text)} chars from PDF (pdfplumber): {pdf_path.name}")
                        return text[:10000]
                        
            except ImportError:
                pass
            
            return None
            
        except Exception as e:
            logger.debug(f"PDF extraction failed for {pdf_path.name}: {e}")
            return None
    
    def _extract_image_text(self, image_path: Path) -> Optional[str]:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            # Open and preprocess image
            img = Image.open(str(image_path))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (for speed)
            max_dimension = 2000
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Run OCR
            text = pytesseract.image_to_string(img, lang=self.ocr_language)
            
            if text.strip():
                logger.debug(f"OCR extracted {len(text)} chars from: {image_path.name}")
                return text[:5000]  # Limit to 5k chars
            
            return None
            
        except Exception as e:
            logger.debug(f"OCR failed for {image_path.name}: {e}")
            return None
    
    def detect_document_type(self, text: str) -> Tuple[str, float]:
        """
        Detect document type from extracted text.
        
        Args:
            text: Extracted text content
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        if not text or not self.detect_document_types:
            return ('Unknown', 0.0)
        
        text_lower = text.lower()
        
        best_type = 'Unknown'
        best_score = 0.0
        
        for doc_type, config in self.DOCUMENT_TYPES.items():
            keywords = config['keywords']
            min_matches = config['min_matches']
            weight = config['weight']
            
            # Count keyword matches
            matches = 0
            for keyword in keywords:
                if keyword in text_lower:
                    matches += 1
            
            # Calculate score
            if matches >= min_matches:
                # Score based on matches and weight
                score = (matches / len(keywords)) * weight
                
                if score > best_score:
                    best_score = score
                    best_type = doc_type
        
        # Convert score to confidence (0-100)
        confidence = min(best_score * 100, 100)
        
        logger.debug(f"Document type detected: {best_type} (confidence: {confidence:.1f}%)")
        return (best_type, confidence)
    
    def analyze_file(self, file_path: Path) -> Dict:
        """
        Perform full content analysis on a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with analysis results:
            - text: Extracted text (truncated)
            - document_type: Detected document type
            - confidence: Confidence score
            - keywords_found: List of matched keywords
            - text_preview: First 200 chars of text
        """
        result = {
            'path': str(file_path),
            'filename': file_path.name,
            'text': None,
            'document_type': 'Unknown',
            'confidence': 0.0,
            'text_preview': None,
            'analyzed': False
        }
        
        if not self.enabled:
            return result
        
        # Extract text
        text = self.extract_text(file_path)
        
        if text:
            result['text'] = text
            result['text_preview'] = text[:200].replace('\n', ' ').strip()
            result['analyzed'] = True
            
            # Detect document type
            doc_type, confidence = self.detect_document_type(text)
            result['document_type'] = doc_type
            result['confidence'] = confidence
            
            # Find matched keywords for the detected type
            if doc_type != 'Unknown' and doc_type in self.DOCUMENT_TYPES:
                text_lower = text.lower()
                keywords = self.DOCUMENT_TYPES[doc_type]['keywords']
                result['keywords_found'] = [kw for kw in keywords if kw in text_lower]
        
        return result
    
    def analyze_files_batch(self, files: List[Path], progress_callback=None) -> Dict[Path, Dict]:
        """
        Analyze multiple files with progress tracking.
        
        Args:
            files: List of file paths
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Dictionary mapping file paths to analysis results
        """
        results = {}
        total = len(files)
        
        # Filter files that can be analyzed
        analyzable_files = []
        for f in files:
            suffix = f.suffix.lower()
            if suffix == '.pdf' and self._pdf_available and self.analyze_pdfs:
                analyzable_files.append(f)
            elif suffix in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'] and self._ocr_available and self.ocr_images:
                analyzable_files.append(f)
        
        logger.info(f"Analyzing {len(analyzable_files)} of {total} files for content")
        
        for i, file_path in enumerate(analyzable_files):
            if progress_callback:
                progress_callback(i + 1, len(analyzable_files), file_path.name)
            
            try:
                results[file_path] = self.analyze_file(file_path)
            except Exception as e:
                logger.error(f"Error analyzing {file_path.name}: {e}")
                results[file_path] = {
                    'path': str(file_path),
                    'filename': file_path.name,
                    'document_type': 'Unknown',
                    'confidence': 0.0,
                    'analyzed': False,
                    'error': str(e)
                }
        
        # Count results
        analyzed_count = sum(1 for r in results.values() if r.get('analyzed'))
        detected_count = sum(1 for r in results.values() if r.get('document_type') != 'Unknown')
        
        logger.info(f"Content analysis complete: {analyzed_count} analyzed, {detected_count} document types detected")
        
        return results
    
    def get_enhanced_text_for_ai(self, file_path: Path, analysis_result: Dict = None) -> str:
        """
        Get enhanced text for AI classification by combining filename + content + document type.
        
        Args:
            file_path: Path to the file
            analysis_result: Pre-computed analysis result (optional)
            
        Returns:
            Enhanced text string for AI embedding
        """
        parts = []
        
        # Always include filename
        parts.append(file_path.stem)
        
        # Add analysis if available
        if analysis_result is None:
            analysis_result = self.analyze_file(file_path)
        
        if analysis_result.get('analyzed'):
            # Add document type
            doc_type = analysis_result.get('document_type', 'Unknown')
            if doc_type != 'Unknown':
                parts.append(doc_type)
                parts.append(f"type_{doc_type}")
            
            # Add keywords found
            keywords = analysis_result.get('keywords_found', [])
            if keywords:
                parts.extend(keywords[:5])  # Max 5 keywords
            
            # Add text preview
            preview = analysis_result.get('text_preview', '')
            if preview:
                # Clean up and truncate
                preview = ' '.join(preview.split())[:200]
                parts.append(preview)
        
        return ' '.join(parts)
    
    def clear_cache(self):
        """Clear the content cache."""
        self.content_cache.clear()
        logger.info("Content cache cleared")


# Standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    analyzer = ContentAnalyzer()
    print(f"Status: {analyzer.get_status()}")
    
    # Test with a sample PDF if available
    test_path = Path(r"C:\Users\Praveen\OneDrive\Documents")
    if test_path.exists():
        pdfs = list(test_path.glob("**/*.pdf"))[:3]
        for pdf in pdfs:
            print(f"\nAnalyzing: {pdf.name}")
            result = analyzer.analyze_file(pdf)
            print(f"  Document Type: {result['document_type']} ({result['confidence']:.1f}% confident)")
            if result.get('text_preview'):
                print(f"  Preview: {result['text_preview'][:100]}...")
