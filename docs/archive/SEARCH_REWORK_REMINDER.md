# ⚠️ REMINDER: Search Feature Rework Needed

## Status: OPEN ISSUE

The search feature has been implemented but has known issues that need to be addressed at the end of all phases.

## Known Issues

1. **Search Relevance**: Results may include files based on folder path, not just filename
2. **User Confusion**: Search behavior not always intuitive
3. **Performance**: May need optimization for large file sets

## Decision Point

At the end of all Phase 3 implementations, we need to decide:
- **Option A**: Rework search to fix issues (invest 8-12 hours)
- **Option B**: Remove search feature entirely (simpler maintenance)

## Files Involved

- `src/core/search_engine.py` - Search indexing and query logic
- `src/ui/search_dialog.py` - Search UI and results display
- `src/ui/main_window.py` - Search button integration

## User Feedback

User reported: "search feature is not reliant...shows irrelevant results"

---

**Date Logged**: January 25, 2026  
**Review Date**: End of Phase 3.x (All phases complete)
