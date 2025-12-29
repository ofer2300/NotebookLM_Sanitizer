# NotebookLM Project Sanitizer

Safe file mirroring, sanitization, and batch preparation for Google NotebookLM AI ingestion.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This tool prepares construction project files (or any document collection) for upload to Google NotebookLM by:

- **Safe Mirroring**: READ-ONLY access to source files, COPY-only operations
- **Smart Filtering**: Whitelist/blacklist file formats, enforce size limits (200MB for NotebookLM)
- **Context Preservation**: Embeds folder hierarchy into filenames (critical for flattened uploads)
- **Auto-Batching**: Groups files by discipline (Plumbing, Architecture, etc.)
- **Building Sub-splits**: Large batches split by building codes (Tower A, B, BASE)
- **Documentation**: Generates manifest CSV, context document, and upload checklist

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ofer2300/NotebookLM_Sanitizer.git
cd NotebookLM_Sanitizer

# No dependencies required - uses only Python standard library!
# Optionally install as package:
pip install -e .
```

### Usage

#### Interactive Mode (Recommended)
```bash
python sanitizer.py -i
```
Just paste the source path and the tool handles everything.

#### Command Line
```bash
python sanitizer.py --source "G:\Projects\MyProject" --dest "C:\AI_Staging\MyProject"
```

#### With Options
```bash
python sanitizer.py \
  --source "G:\path\to\project" \
  --dest "C:\AI_Staging\ProjectName" \
  --max-size 100 \
  --name "My Custom Project Name"
```

## Features

### 1. Safe File Operations
- **READ-ONLY** access to source directory
- **COPY-ONLY** operations (never move/delete source files)
- All output goes to a separate destination

### 2. Smart Filtering

**Whitelist (Included)**:
- Documents: `.pdf`, `.docx`, `.doc`, `.txt`, `.md`, `.rtf`
- Spreadsheets: `.xlsx`, `.xls`
- Presentations: `.pptx`, `.ppt`

**Blacklist (Excluded)**:
- CAD: `.dwg`, `.rvt`, `.skp`
- Archives: `.zip`, `.rar`, `.7z`
- Executables: `.exe`
- Temp files: `.bak`, `.tmp`

### 3. Context-Preserving Filenames

NotebookLM flattens folder structures. We solve this by embedding the path:

```
Original:  G:\Projects\Building\Plumbing\Floor1\Plan.pdf
Sanitized: Building_Plumbing_Floor1_Plan.pdf
```

This preserves context for AI queries like "Show me Plumbing documents for Floor 1".

### 4. Auto-Batching by Discipline

Files are automatically grouped into folders:
```
Output/
├── Batch_Plumbing_WSS/     (Water Supply & Sewage)
├── Batch_Plumbing_SPR/     (Sprinkler/Fire)
├── Batch_Architecture/
├── Batch_Structural/
├── Batch_Coordination/
├── Batch_DOC/
└── Batch_Other/
```

### 5. Generated Documentation

| File | Purpose |
|------|---------|
| `Project_Manifest.csv` | Complete inventory with original paths & status |
| `PROJECT_CONTEXT_FOR_AI.md` | Context document for AI understanding |
| `UPLOAD_CHECKLIST.md` | Tracking checklist for NotebookLM upload |

## Output Structure

```
C:\AI_Staging\ProjectName\
├── PROJECT_CONTEXT_FOR_AI.md    # Upload first - establishes context
├── UPLOAD_CHECKLIST.md          # Track your upload progress
├── Project_Manifest.csv         # Full file inventory
├── Batch_Plumbing_WSS/          # Discipline batches
│   ├── file1.pdf
│   └── file2.pdf
├── Batch_Architecture/
└── Batch_Other/
```

## Configuration

Edit `DEFAULT_CONFIG` in `sanitizer.py` to customize:

```python
DEFAULT_CONFIG = {
    "whitelist": {'.pdf', '.docx', '.xlsx', ...},
    "blacklist": {'.dwg', '.rvt', '.exe', ...},
    "max_size_mb": 200,  # NotebookLM limit
    "discipline_patterns": {...},  # Regex for auto-batching
    "building_patterns": {...},    # Regex for sub-splitting
    "split_threshold": 100,        # Files before auto-split
}
```

## Use Cases

### Construction Projects
Perfect for engineering firms with:
- Multiple disciplines (Plumbing, Electrical, Structural)
- Multiple buildings (Tower A, B, C)
- Large file collections on shared drives

### Document Archives
Any document collection that needs:
- Format filtering
- Size validation
- Organized batching
- AI-ready preparation

## Upload to NotebookLM

1. **Start with context**: Upload `PROJECT_CONTEXT_FOR_AI.md` first
2. **Upload manifest**: Add `Project_Manifest.csv` as table of contents
3. **Upload batches**: Start with smallest, work up to largest
4. **Verify**: Test with queries like "What is this project about?"

## Requirements

- Python 3.8 or higher
- No external dependencies (stdlib only)
- Windows/macOS/Linux compatible

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Author

**AquaBrain Engineering**

---

*Built for the construction industry, useful for anyone preparing documents for AI.*
