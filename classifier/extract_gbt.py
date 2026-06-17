#!/usr/bin/env python3
"""
从 GB/T 4754-2017 标准 PDF 中提取所有"小类"（4位代码+名称）到 TXT 文件。
"""

import re
import fitz


def extract_subclasses(pdf_path, output_path):
    doc = fitz.open(pdf_path)

    # Main classification table (表1) starts between page 9-10.
    # Subsequent pages (appendix A/B/C etc.) have different headers.
    # Detect start: page containing "表1" + "国民经济行业分类和代码"
    # Detect end: page containing "附录A" or "附  录 A"
    table_start = None
    table_end = len(doc)
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if table_start is None and "表1" in text and "国民经济行业分类和代码" in text:
            table_start = page_num
        if table_start is not None and page_num > table_start:
            if "附录A" in text.replace(" ", "") or "GB/T 4754-2011" in text:
                table_end = page_num
                break

    all_lines = []
    for page_num in range(table_start, table_end):
        text = doc[page_num].get_text()
        lines = text.split("\n")
        all_lines.extend(lines)

    # Parse: find 4-digit codes followed by their name
    code_pattern = re.compile(r"^\s*(\d{4})\s*$")
    name_pattern = re.compile(r"^\s{2,}(\S.+)")  # indented line = name
    flat_pattern = re.compile(r"^\s*(\d{4})\s{2,}(\S.+)")  # code + name on same line

    results = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i]

        # Case 1: code and name on same line (e.g., "  0111  稻谷种植")
        m = flat_pattern.match(line)
        if m:
            code = m.group(1)
            name = m.group(2).strip()
            # name may have trailing description after multiple spaces
            name = re.split(r"\s{2,}", name)[0].strip()
            results.append((code, name))
            i += 1
            continue

        # Case 2: code on its own line, name on next line(s)
        m = code_pattern.match(line)
        if m:
            code = m.group(1)
            # Look ahead for the name (skip empty lines)
            j = i + 1
            name = ""
            while j < len(all_lines):
                nl = all_lines[j]
                # Skip empty lines
                if not nl.strip():
                    j += 1
                    continue
                # If next line is also a code, stop
                if code_pattern.match(nl):
                    break
                # If next line starts with "指" or "包括", it's a description, stop
                # Name should be the first non-empty, non-code line
                name = nl.strip()
                # Clean: remove leading indentation artifacts
                name = re.sub(r"^\s+", "", name)
                # If name looks like a description, skip it (description starts with "指" or "包括")
                if name.startswith("指") or name.startswith("包括"):
                    name = ""
                    j += 1
                    continue
                break
            if name and not re.match(r"^\d", name):
                results.append((code, name))
            i = j if name else i + 1
            continue

        i += 1

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for code, name in results:
        key = f"{code} {name}"
        if key not in seen:
            seen.add(key)
            unique.append((code, name))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"GB/T 4754-2017 国民经济行业分类 —— 小类（共{len(unique)}条）\n")
        f.write("=" * 60 + "\n\n")
        for code, name in unique:
            f.write(f"{code} {name}\n")

    print(f"提取完成，共 {len(unique)} 个小类，保存到 {output_path}")
    return unique


if __name__ == "__main__":
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "classifier/GBT4754-2017.pdf"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "classifier/gbt4754_2017_小类.txt"
    extract_subclasses(pdf_path, output_path)
