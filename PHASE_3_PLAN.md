# Phase 3: AI Semantic Grouping Implementation Plan

## 🎯 Goal
Add intelligent AI-powered semantic grouping that understands file content and creates meaningful groups.

## 🧠 How AI Will Work

### Current (Phase 2) - Rule Based:
```
Documents/
  ├── PDF/
  │   └── Jan-26/
  │       ├── resume.pdf
  │       ├── invoice_123.pdf
  │       └── vacation_receipt.pdf
```

### Phase 3 - AI Semantic Grouping:
```
Documents/
  ├── Career/              ← AI groups "resume", "cv", "cover letter"
  │   └── PDF/
  │       └── Jan-26/
  │           └── resume.pdf
  ├── Financial/           ← AI groups "invoice", "receipt", "bill"
  │   └── PDF/
  │       └── Jan-26/
  │           ├── invoice_123.pdf
  │           └── vacation_receipt.pdf
```

## 🔧 Implementation Steps

### 1. Enable Semantic Analysis
- ✅ AI model already loaded (sentence-transformers)
- ✅ `create_semantic_groups()` method exists
- ❌ Not connected to organization pipeline

### 2. Integration Points
**File**: `src/core/organizer.py`
- Modify `preview_organization()` to:
  1. Collect all files
  2. Call AI classifier to create semantic groups
  3. Store group mappings
  4. Pass group info to `_determine_target_folder()`

**File**: `src/ui/main_window.py`
- Add checkbox: "🤖 Enable AI Semantic Grouping"
- Toggle updates `self.use_ai_grouping`
- Re-analyze folder when toggled

### 3. AI Grouping Logic
```python
# For each batch of files:
1. Extract file descriptions (name + content preview)
2. Generate embeddings using sentence-transformers
3. Calculate cosine similarity between files
4. Cluster files with >65% similarity
5. Generate smart group name from common keywords
6. Map each file to its group
```

### 4. Folder Structure
```
Base Organization:
  Level 1: Category (Documents/Images/Code)
  Level 2: AI Semantic Group (Financial/Career/Personal)  ← NEW
  Level 3: File Type (PDF/DOCX/JPG)
  Level 4: Date (Jan-26/Feb-24)
```

## 📊 AI Model Details

**Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Type**: BERT-based neural network
- **Size**: ~80MB
- **Speed**: ~100 files/second
- **Accuracy**: 85%+ semantic similarity
- **Offline**: 100% local, no cloud APIs

**What It Understands**:
- Synonyms (resume = CV)
- Context (invoice + payment + bill = Financial)
- Themes (vacation + travel + trip = Travel)
- Purpose (report + analysis + presentation = Work)

## 🧪 Testing Strategy

### Test Case 1: Mixed Documents Folder
```
Input:
  - john_resume_2026.pdf
  - cover_letter.docx
  - electricity_bill.pdf
  - water_invoice.pdf
  - vacation_photos_thailand.jpg
  - beach_trip.jpg

Expected Output:
  Documents/
    ├── Career/
    │   ├── PDF/Jan-26/john_resume_2026.pdf
    │   └── DOCX/Jan-26/cover_letter.docx
    └── Financial/
        └── PDF/Jan-26/
            ├── electricity_bill.pdf
            └── water_invoice.pdf
  Images/
    └── Vacation/
        └── JPG/Jan-26/
            ├── vacation_photos_thailand.jpg
            └── beach_trip.jpg
```

### Test Case 2: Code Projects
```
Input:
  - api_server.py
  - database_handler.py
  - ui_components.tsx
  - button_styles.css

Expected Output:
  Code/
    ├── Backend/
    │   └── PY/Jan-26/
    │       ├── api_server.py
    │       └── database_handler.py
    └── Frontend/
        ├── TSX/Jan-26/ui_components.tsx
        └── CSS/Jan-26/button_styles.css
```

## ⚠️ Challenges & Solutions

### Challenge 1: Performance
**Issue**: AI processing 2612 files could be slow
**Solution**: 
- Process in batches of 500
- Cache embeddings
- Show progress bar
- Make it optional (checkbox)

### Challenge 2: Bad Groupings
**Issue**: AI might group unrelated files
**Solution**:
- Minimum group size = 2 files
- Similarity threshold = 65%
- Allow disabling AI grouping
- Fall back to rule-based if AI fails

### Challenge 3: Group Naming
**Issue**: Generated names might be unclear
**Solution**:
- Extract common keywords
- Filter stop words
- Use most frequent meaningful word
- Fallback to extension-based names

## 📝 Code Changes Required

### 1. `organizer.py`
```python
def preview_organization(self, folder_path, profile, use_ai_grouping=False):
    # ... existing code ...
    
    if use_ai_grouping and self.ai_classifier:
        logger.info("Creating AI semantic groups...")
        self.semantic_groups = self.ai_classifier.create_semantic_groups(files)
    else:
        self.semantic_groups = {}
    
    # Process files with group info
    for file in files:
        target = self._determine_target_folder(
            file, folder_path, rules, use_ai_grouping
        )
```

### 2. `_determine_target_folder()`
```python
def _determine_target_folder(self, file_path, base_folder, rules, use_ai_grouping=False):
    # Level 1: Category
    category_folder = self._get_category(file_path, rules)
    
    # Level 2: AI Group (NEW)
    if use_ai_grouping and self.semantic_groups:
        for group_name, group_files in self.semantic_groups.items():
            if file_path in group_files:
                category_folder = category_folder / group_name
                break
    
    # Level 3: Type
    type_folder = category_folder / file_path.suffix.upper()
    
    # Level 4: Date
    date_folder = type_folder / self._get_date_folder(file_path)
    
    return date_folder
```

### 3. `main_window.py`
```python
def _create_ai_options(self):
    checkbox = QCheckBox("🤖 AI Semantic Grouping")
    checkbox.stateChanged.connect(self._on_ai_toggle)
    return checkbox

def _on_ai_toggle(self, state):
    self.use_ai_grouping = (state == 2)
    if self.current_folder:
        self._analyze_folder()
```

## 🎬 Implementation Order
1. ✅ Backup Phase 2 (DONE)
2. ✅ Push to Git with tag (DONE)
3. Add AI grouping checkbox to UI
4. Update `preview_organization()` to call AI
5. Modify `_determine_target_folder()` to use groups
6. Test with small folder (10-20 files)
7. Test with Documents folder (2612 files)
8. Optimize performance if needed
9. Commit as Phase 3

## 🚦 Success Criteria
- [ ] AI checkbox works and triggers grouping
- [ ] Similar files grouped together intelligently
- [ ] Group names are meaningful
- [ ] Performance acceptable (<10 sec for 500 files)
- [ ] Can toggle on/off without errors
- [ ] Fallback to rule-based works
- [ ] All existing features still work
- [ ] Tested with 2612 files successfully

---
**Ready to start Phase 3 implementation** 🚀
