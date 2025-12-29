#!/usr/bin/env python3
"""
NotebookLM Project Sanitizer
============================
Safe mirroring, sanitization, and batch preparation for AI ingestion.

SAFETY: READ-ONLY operations on source. All writes go to destination only.

Usage:
    python sanitizer.py --source "G:\\path\\to\\project" --dest "C:\\AI_Staging\\ProjectName"
    python sanitizer.py -s "D:\\Work\\Project" -d "C:\\Output\\Project" --max-size 100
    python sanitizer.py --interactive

Author: AquaBrain Engineering
Version: 1.0.0
"""

import os
import sys
import shutil
import csv
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# ============== CONFIGURATION ==============

DEFAULT_CONFIG = {
    # Whitelist - allowed formats for AI ingestion
    "whitelist": {'.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.pptx', '.ppt', '.md', '.rtf'},

    # Blacklist - explicitly excluded (logged in manifest)
    "blacklist": {'.dwg', '.rvt', '.exe', '.zip', '.rar', '.7z', '.psd', '.ai', '.skp', '.bak', '.tmp'},

    # Size limit in MB (NotebookLM = 200MB)
    "max_size_mb": 200,

    # Batch splitting rules (regex patterns for discipline detection)
    "discipline_patterns": {
        "Plumbing_WSS": r"^Plumbing_WSS",
        "Plumbing_SPR": r"^Plumbing_(SPR|Sprinkler)",
        "Plumbing_Other": r"^Plumbing_",
        "Coordination": r"^Coordination",
        "Electrical": r"^(ELEC|Electrical)",
        "Mechanical": r"^(MECH|Mechanical|HVAC)",
        "Structural": r"^(STR|Structural)",
        "Architecture": r"^(ARCH|Architecture)",
        "Civil": r"^(Civil|Site)",
        "DOC": r"^DOC",
        "GIS": r"^GIS",
        "Hydrology": r"^Hydrology",
    },

    # Building code patterns for sub-batching
    "building_patterns": {
        "TowerA": r"_TA_|_TA\.|Tower.?A",
        "TowerB": r"_TB_|_TB\.|Tower.?B",
        "TowerC": r"_TC_|_TC\.|Tower.?C",
        "BuildingA": r"_BA_|_BA\.|Building.?A",
        "BuildingB": r"_BB_|_BB\.|Building.?B",
        "BuildingC": r"_BC_|_BC\.|Building.?C",
        "BASE": r"_BASE_|_BASE\.|Basement|Foundation",
    },

    # Split large batches by building if they exceed this file count
    "split_threshold": 100,
}


# ============== HELPER FUNCTIONS ==============

def bytes_to_mb(size_bytes: int) -> float:
    """Convert bytes to megabytes."""
    return round(size_bytes / (1024 * 1024), 2)


def sanitize_filename(original_path: str, source_root: str) -> str:
    """Convert folder path to contextual filename."""
    rel_path = os.path.relpath(original_path, source_root)
    sanitized = rel_path.replace(os.sep, '_').replace('/', '_').replace('\\', '_')
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    return sanitized.lstrip('_')


def detect_discipline(filename: str, patterns: dict) -> str:
    """Detect discipline from filename using regex patterns."""
    for discipline, pattern in patterns.items():
        if re.search(pattern, filename, re.IGNORECASE):
            return discipline
    return "Other"


def detect_building(filename: str, patterns: dict) -> Optional[str]:
    """Detect building code from filename using regex patterns."""
    for building, pattern in patterns.items():
        if re.search(pattern, filename, re.IGNORECASE):
            return building
    return None


def print_banner():
    """Print application banner."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     NOTEBOOKLM PROJECT SANITIZER                             ║
║                                                                              ║
║  Safe file mirroring & preparation for AI ingestion                          ║
║  READ-ONLY source access | Context-preserving filenames | Auto-batching      ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


# ============== MAIN WORKFLOW ==============

def run_sanitizer(source: str, dest: str, config: dict, project_name: str = "") -> dict:
    """
    Main sanitization workflow.

    Args:
        source: Source directory path (READ-ONLY)
        dest: Destination directory path
        config: Configuration dictionary
        project_name: Optional project name (auto-detected if empty)

    Returns:
        Dictionary with statistics
    """
    project_name = project_name or os.path.basename(source)

    print("=" * 70)
    print("PROCESSING PROJECT")
    print("=" * 70)
    print(f"Project:     {project_name}")
    print(f"Source:      {source}")
    print(f"Destination: {dest}")
    print(f"Max Size:    {config['max_size_mb']} MB")
    print("-" * 70)

    # Verify source
    if not os.path.exists(source):
        print(f"ERROR: Source path does not exist:\n{source}")
        return {"error": "Source not found"}

    # Create destination
    os.makedirs(dest, exist_ok=True)

    # Initialize tracking
    manifest_data = []
    discipline_files = defaultdict(list)
    stats = {
        'project_name': project_name,
        'copied': 0,
        'skipped_format': 0,
        'skipped_size': 0,
        'errors': 0,
        'total_size_mb': 0
    }

    print("\n[1/5] Scanning source directory...")

    # Deep scan and copy
    for root, dirs, files in os.walk(source):
        for filename in files:
            original_path = os.path.join(root, filename)

            try:
                file_size = os.path.getsize(original_path)
                file_ext = os.path.splitext(filename)[1].lower()
                size_mb = bytes_to_mb(file_size)

                # Determine status
                if file_ext in config["blacklist"]:
                    status = f"Skipped - Blacklisted ({file_ext})"
                    stats['skipped_format'] += 1
                elif file_ext not in config["whitelist"]:
                    status = f"Skipped - Not Whitelisted ({file_ext})"
                    stats['skipped_format'] += 1
                elif size_mb > config["max_size_mb"]:
                    status = f"Skipped - Too Large ({size_mb} MB)"
                    stats['skipped_size'] += 1
                else:
                    status = "Copied"

                # Generate new filename
                new_filename = sanitize_filename(original_path, source)

                if status == "Copied":
                    dest_file = os.path.join(dest, new_filename)
                    shutil.copy2(original_path, dest_file)
                    stats['copied'] += 1
                    stats['total_size_mb'] += size_mb

                    # Track by discipline
                    discipline = detect_discipline(new_filename, config["discipline_patterns"])
                    discipline_files[discipline].append((new_filename, size_mb))

                manifest_data.append({
                    'Original_Path': original_path,
                    'New_Filename': new_filename if status == "Copied" else "N/A",
                    'File_Size_MB': size_mb,
                    'Status': status
                })

            except Exception as e:
                stats['errors'] += 1
                manifest_data.append({
                    'Original_Path': original_path,
                    'New_Filename': "N/A",
                    'File_Size_MB': 0,
                    'Status': f"Error - {str(e)}"
                })

    print(f"    Copied: {stats['copied']} files ({stats['total_size_mb']:.1f} MB)")
    print(f"    Skipped: {stats['skipped_format']} (format) + {stats['skipped_size']} (size)")

    # Generate manifest
    print("\n[2/5] Generating manifest...")
    manifest_path = os.path.join(dest, "Project_Manifest.csv")
    with open(manifest_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['Original_Path', 'New_Filename', 'File_Size_MB', 'Status'])
        writer.writeheader()
        writer.writerows(manifest_data)
    print(f"    Saved: Project_Manifest.csv")

    # Create batches
    print("\n[3/5] Creating discipline batches...")
    batch_info = []

    for discipline, files in sorted(discipline_files.items()):
        batch_name = f"Batch_{discipline}"
        batch_path = os.path.join(dest, batch_name)
        os.makedirs(batch_path, exist_ok=True)

        batch_size = 0
        for filename, size_mb in files:
            src_file = os.path.join(dest, filename)
            if os.path.exists(src_file):
                shutil.move(src_file, os.path.join(batch_path, filename))
                batch_size += size_mb

        batch_info.append((batch_name, len(files), batch_size))
        print(f"    {batch_name}: {len(files)} files ({batch_size:.1f} MB)")

        # Split large batches by building
        if len(files) > config["split_threshold"]:
            print(f"      → Splitting by building code...")
            split_batch_by_building(batch_path, config["building_patterns"])

    # Generate context document
    print("\n[4/5] Generating context document...")
    generate_context_doc(dest, project_name, stats, discipline_files, config)
    print(f"    Saved: PROJECT_CONTEXT_FOR_AI.md")

    # Generate upload checklist
    print("\n[5/5] Generating upload checklist...")
    generate_checklist(dest, project_name, batch_info)
    print(f"    Saved: UPLOAD_CHECKLIST.md")

    # Summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Files copied:      {stats['copied']}")
    print(f"Total size:        {stats['total_size_mb']:.1f} MB")
    print(f"Batches created:   {len(batch_info)}")
    print(f"Destination:       {dest}")
    print("=" * 70)

    stats['batches'] = len(batch_info)
    return stats


def split_batch_by_building(batch_path: str, building_patterns: dict):
    """Split a batch folder by building codes."""
    files = os.listdir(batch_path)
    building_files = defaultdict(list)

    for filename in files:
        building = detect_building(filename, building_patterns)
        if building:
            building_files[building].append(filename)
        else:
            building_files["Other"].append(filename)

    # Only split if there are multiple buildings
    if len(building_files) > 1:
        base_name = os.path.basename(batch_path)
        parent = os.path.dirname(batch_path)

        for building, bfiles in building_files.items():
            if len(bfiles) > 0:
                sub_batch = os.path.join(parent, f"{base_name}_{building}")
                os.makedirs(sub_batch, exist_ok=True)
                for f in bfiles:
                    src = os.path.join(batch_path, f)
                    if os.path.exists(src):
                        shutil.move(src, os.path.join(sub_batch, f))
                print(f"        {building}: {len(bfiles)} files")

        # Remove original batch if empty
        remaining = os.listdir(batch_path)
        if not remaining:
            os.rmdir(batch_path)


def generate_context_doc(dest: str, project_name: str, stats: dict,
                         discipline_files: dict, config: dict):
    """Generate AI context document."""

    content = f"""# Project Context Document - {project_name}

## Project Overview
- **Project Name**: {project_name}
- **Sanitization Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Total Documents**: {stats['copied']}
- **Total Size**: {stats['total_size_mb']:.1f} MB

---

## Document Distribution by Discipline

| Discipline | Files | Size (MB) |
|------------|------:|----------:|
"""

    for discipline, files in sorted(discipline_files.items()):
        total_size = sum(f[1] for f in files)
        content += f"| {discipline} | {len(files)} | {total_size:.1f} |\n"

    content += f"""
---

## File Naming Convention

Files have been renamed to preserve folder context:
```
[Discipline]_[SubFolder]_[Date]_[Type]_[OriginalName].[ext]
```

Path separators are replaced with underscores to maintain hierarchy context.

---

## Allowed File Formats

{', '.join(sorted(config['whitelist']))}

---

## How to Query This Project

- By discipline: "Show me all Plumbing documents"
- By building: "What exists for Tower B?"
- By date: "Find documents from 2024"
- By system: "Explain the drainage system"

---

*This document provides context for AI systems to understand the project structure.*
"""

    context_path = os.path.join(dest, "PROJECT_CONTEXT_FOR_AI.md")
    with open(context_path, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_checklist(dest: str, project_name: str, batch_info: list):
    """Generate upload checklist."""

    content = f"""# NotebookLM Upload Checklist
## Project: {project_name}
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Upload Order

| # | Batch | Files | Size (MB) | Status |
|:-:|-------|------:|----------:|:------:|
"""

    # Sort batches: Context first, then by size (smallest first)
    sorted_batches = sorted(batch_info, key=lambda x: (not x[0].startswith("Batch_Context"), x[2]))

    for i, (name, files, size) in enumerate(sorted_batches, 1):
        content += f"| {i} | `{name}` | {files} | {size:.1f} | [ ] |\n"

    total_files = sum(b[1] for b in batch_info)
    total_size = sum(b[2] for b in batch_info)

    content += f"""
---

## Summary

- **Total Batches**: {len(batch_info)}
- **Total Files**: {total_files}
- **Total Size**: {total_size:.1f} MB

---

## Post-Upload Verification

Test these queries after upload:
1. "What is this project about?"
2. "What disciplines are covered?"
3. "List all buildings/structures"

---

## Location

```
{dest}
```
"""

    checklist_path = os.path.join(dest, "UPLOAD_CHECKLIST.md")
    with open(checklist_path, 'w', encoding='utf-8') as f:
        f.write(content)


def interactive_mode():
    """Run in interactive mode - prompt for source path."""
    print_banner()

    print("Enter the full source path (or 'q' to quit):")
    source = input("> ").strip().strip('"').strip("'")

    if source.lower() == 'q':
        print("Exiting.")
        return

    if not os.path.exists(source):
        print(f"ERROR: Path does not exist: {source}")
        return

    # Auto-generate destination name
    project_name = os.path.basename(source)
    # Clean project name for folder
    clean_name = re.sub(r'[^\w\s-]', '', project_name).strip()
    clean_name = re.sub(r'[-\s]+', '_', clean_name)

    default_dest = f"C:\\AI_Staging\\{clean_name}"

    print(f"\nDestination [{default_dest}]:")
    dest_input = input("> ").strip().strip('"').strip("'")
    dest = dest_input if dest_input else default_dest

    # Run sanitizer
    run_sanitizer(source, dest, DEFAULT_CONFIG, project_name)

    # Ask to open folder
    print("\nOpen destination folder? [Y/n]:")
    if input("> ").strip().lower() != 'n':
        os.system(f'start "" "{dest}"')


# ============== CLI INTERFACE ==============

def main():
    parser = argparse.ArgumentParser(
        description="Sanitize project files for NotebookLM ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sanitizer.py --source "G:\\Projects\\MyProject" --dest "C:\\AI_Staging\\MyProject"
  python sanitizer.py -s "D:\\Work\\Project" -d "C:\\Output" --max-size 100
  python sanitizer.py --interactive
  python sanitizer.py -i
        """
    )

    parser.add_argument('--source', '-s', type=str, help='Source directory path')
    parser.add_argument('--dest', '-d', type=str, help='Destination directory path')
    parser.add_argument('--max-size', type=int, default=200, help='Max file size in MB (default: 200)')
    parser.add_argument('--name', '-n', type=str, help='Project name (default: auto-detect)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or (not args.source and not args.dest):
        interactive_mode()
        return

    # Validate required paths
    if not args.source or not args.dest:
        print("ERROR: Both --source and --dest are required.")
        parser.print_help()
        sys.exit(1)

    # Update config
    config = DEFAULT_CONFIG.copy()
    config["max_size_mb"] = args.max_size

    # Run sanitizer
    stats = run_sanitizer(args.source, args.dest, config, args.name or "")

    sys.exit(0 if 'error' not in stats else 1)


if __name__ == "__main__":
    main()
