# AutoFolder AI - TODO & Roadmap

## Phase 1: MVP (Current) ✅

### Core Features
- [x] File organization engine
- [x] Rule-based categorization
- [x] Multiple profiles (Downloads, Media, Gaming, Work, Date)
- [x] Preview mode
- [x] Undo support
- [x] Conflict resolution
- [x] PySide6 UI
- [x] Configuration system
- [x] Logging

### AI Features
- [x] Local AI classifier (sentence-transformers)
- [x] Content-based categorization
- [x] Smart folder naming
- [x] Duplicate detection

### Safety & UX
- [x] Preview before organize
- [x] Undo journal
- [x] Never delete files
- [x] Progress indication
- [x] Error handling

### Documentation
- [x] README
- [x] User Guide
- [x] Development Guide
- [x] Building Guide
- [x] Sales Page Copy
- [x] Quick Start

---

## Phase 2: Polish & Testing (Next 2 weeks)

### Testing
- [ ] Unit tests for all core modules
- [ ] Integration tests
- [ ] UI tests with pytest-qt
- [ ] Test on clean Windows machines
- [ ] Test with large folders (10k+ files)
- [ ] Test edge cases (permissions, locked files, etc.)

### UI Improvements
- [ ] Add progress bar for AI operations
- [ ] Better error messages
- [ ] Loading indicators
- [ ] Keyboard shortcuts
- [ ] Dark theme support
- [ ] Settings dialog

### Performance
- [ ] Optimize for large folders
- [ ] Cache AI embeddings
- [ ] Parallel file processing
- [ ] Memory optimization

### Bug Fixes
- [ ] Handle locked/in-use files gracefully
- [ ] Fix any path encoding issues
- [ ] Handle special characters in filenames
- [ ] Test and fix undo edge cases

---

## Phase 3: Packaging & Distribution (Next 1 week)

### Build Process
- [ ] Create build spec files
- [ ] Build Base version EXE
- [ ] Build Pro version EXE
- [ ] Test built EXEs on multiple machines
- [ ] Optimize file size
- [ ] Create installer (optional)

### Assets
- [ ] Design application icon
- [ ] Create product screenshots
- [ ] Make demo video
- [ ] Design banner/logo

### Distribution
- [ ] Set up Gumroad account
- [ ] Create product pages
- [ ] Upload builds
- [ ] Set pricing
- [ ] Write product descriptions
- [ ] Add screenshots

---

## Phase 4: Launch (Next 1 week)

### Pre-Launch
- [ ] Test payment flow
- [ ] Prepare launch announcement
- [ ] Set up support email
- [ ] Create changelog system
- [ ] Prepare FAQ

### Launch Day
- [ ] Publish on Gumroad
- [ ] Post on relevant forums (Reddit r/productivity, r/software)
- [ ] Share on Twitter/LinkedIn
- [ ] Post in Facebook groups
- [ ] Submit to product directories

### Post-Launch
- [ ] Monitor for bug reports
- [ ] Respond to customer questions
- [ ] Collect feedback
- [ ] Track sales
- [ ] Iterate based on feedback

---

## Future Features (Version 1.1+)

### User Requests (Add based on feedback)

### High Priority
- [ ] Custom rule creation UI
- [ ] Batch folder processing
- [ ] Schedule automatic organization
- [ ] Folder monitoring (auto-organize on new files)
- [ ] Export/import profiles
- [ ] Statistics dashboard

### Medium Priority
- [ ] Context menu integration (right-click → Organize)
- [ ] Browser extension (auto-organize downloads)
- [ ] Cloud backup integration
- [ ] Multi-language support
- [ ] Regex rule builder UI
- [ ] File tagging system

### Low Priority (Nice to have)
- [ ] Mobile app (view/remote trigger)
- [ ] Network folder support
- [ ] Team/shared profiles
- [ ] Advanced AI models
- [ ] Plugin system
- [ ] macOS version

---

## Known Limitations

### Current Version
- Windows only (no macOS/Linux)
- Single folder at a time
- No scheduling
- No context menu integration
- AI model requires ~500MB disk space

### Acceptable Trade-offs (for MVP)
- ✅ No cloud sync (offline is a feature!)
- ✅ No mobile app (desktop tool)
- ✅ No subscription (one-time only)
- ✅ No support guarantee (documented well)

---

## Version Numbering

### 1.0.0 - MVP Launch
- Core features complete
- Stable and tested
- Ready for sale

### 1.1.0 - First Update
- User-requested features
- Bug fixes
- Performance improvements

### 1.2.0 - Custom Rules
- UI for custom rule creation
- Rule import/export
- Advanced options

### 2.0.0 - Major Update
- Folder monitoring
- Scheduling
- Context menu integration
- Significant new features

---

## Success Metrics

### Month 1 Goals
- [ ] 30+ sales
- [ ] ₹15,000+ revenue
- [ ] <5% refund rate
- [ ] Positive feedback

### Month 3 Goals
- [ ] 100+ sales
- [ ] ₹50,000+ revenue
- [ ] Product-market fit validated
- [ ] Version 1.1 released

### Month 6 Goals
- [ ] 300+ sales
- [ ] ₹150,000+ revenue
- [ ] Steady income stream
- [ ] Consider version 2.0

---

## Development Priorities

### Priority 1 (Must Have)
- Stability and bug fixes
- Testing on real user scenarios
- Documentation quality

### Priority 2 (Should Have)
- Performance optimization
- UI polish
- Better error messages

### Priority 3 (Nice to Have)
- Advanced features
- Integrations
- Additional platforms

---

## Questions to Answer

- [ ] Base price: ₹399 or ₹499?
- [ ] Pro price: ₹999 or ₹1299?
- [ ] Launch discount? How much?
- [ ] Gumroad only or also Itch.io?
- [ ] Code signing certificate worth it?
- [ ] Create installer or keep portable?
- [ ] Reddit ads or organic only?

---

## Notes

**Focus Areas:**
1. Stability > Features
2. Documentation > Marketing
3. User experience > Advanced options
4. Offline > Cloud
5. Privacy > Convenience

**Don't Add:**
- Subscription model
- Required account
- Analytics/telemetry
- Cloud dependencies
- Bloated features

**Keep It Simple:**
- One purpose: organize files
- One payment: no recurring
- One click: easy to use
- Zero support: self-service

---

Last Updated: 2026-01-24
