#!/usr/bin/env python3
"""
Convert evidence markdown files into canonical HTML pages with site styling.

Usage:
    python3 scripts/convert_evidence_to_html.py
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>CATY - {title} | Evidence Repository</title>
    <link rel=\"stylesheet\" href=\"{css_path}styles/caty-equity-research.css\">
</head>
<body>
    <a class=\"skip-link\" href=\"#main-content\">Skip to main content</a>

    <button class=\"theme-toggle\" type=\"button\" onclick=\"toggleTheme()\" aria-label=\"Toggle dark mode\" role=\"switch\" aria-checked=\"false\">
        <span id=\"theme-icon\" aria-hidden=\"true\">🌙</span>
        <span id=\"theme-text\">Dark Mode</span>
    </button>

    <header>
        <div class=\"header-content\">
            <h1 class=\"page-title\">Cathay General Bancorp (NASDAQ: CATY)</h1>
            <p class=\"page-subtitle\">{subtitle}</p>
            <p class=\"page-meta\">{meta}</p>
        </div>
    </header>

    <main class=\"container\" id=\"main-content\" tabindex=\"-1\">
        <nav aria-label=\"Breadcrumb\" class=\"breadcrumb\">
            <a href=\"{home_path}index.html\">← Main Report</a>
            <span aria-hidden=\"true\"> / </span>
            <span aria-current=\"page\">Evidence: {short_title}</span>
        </nav>

        {content}

    </main>

    <footer class=\"evidence-footer\">
        <p class=\"footer-text\">Evidence documentation for CFA IRC equity research challenge</p>
        <p class=\"footer-meta\">{footer_meta}</p>
    </footer>

    <script src=\"{js_path}scripts/theme.js\"></script>
</body>
</html>
"""

METADATA_PATTERN = re.compile(r"^\*\*(?P<key>[^:]+):\*\*\s*(?P<value>.+)$")
TABLE_ROW_PATTERN = re.compile(r"^\s*\|.*\|\s*$")
TABLE_DIVIDER_PATTERN = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$"
)
BULLET_PATTERN = re.compile(r"^(?P<indent>[ \t]*)([-*+])\s+(?P<content>.+)$")
ORDERED_PATTERN = re.compile(r"^(?P<indent>[ \t]*)(?P<number>\d+)\.\s+(?P<content>.+)$")
INLINE_LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")
INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
STRONG_PATTERN = re.compile(r"\*\*(.+?)\*\*")
EM_PATTERN = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def html_escape(text: str) -> str:
    """HTML-escape helper with default behaviour."""
    return html.escape(text, quote=False)


def parse_frontmatter(lines: list[str]) -> dict[str, str]:
    """Extract metadata key/value pairs from the first few lines."""
    metadata: dict[str, str] = {}
    for line in lines[:15]:
        match = METADATA_PATTERN.match(line.strip())
        if match:
            key = match.group("key").strip().lower()
            value = match.group("value").strip()
            metadata[key] = value
    return metadata


def extract_body(lines: list[str]) -> tuple[str | None, str]:
    """Remove frontmatter blocks and return title plus markdown body."""
    title: str | None = None
    body_lines: list[str] = []
    metadata_section = True

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        if title is None and line.startswith("# "):
            title = line[2:].strip()
            continue

        if metadata_section:
            if METADATA_PATTERN.match(line.strip()):
                continue
            if line.strip() == "---":
                metadata_section = False
                continue
            if not line.strip():
                continue
            metadata_section = False

        body_lines.append(raw_line)

    body = "".join(body_lines).lstrip("\n")
    return title, body


def parse_inline(text: str) -> str:
    """Process inline markdown patterns into HTML."""
    escaped = html_escape(text)

    def replace_code(match: re.Match[str]) -> str:
        return f"<code>{match.group(1)}</code>"

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        if url.lower().endswith(".md"):
            url = url[:-3] + ".html"
        return f"<a href=\"{url}\">{label}</a>"

    escaped = INLINE_CODE_PATTERN.sub(replace_code, escaped)
    escaped = INLINE_LINK_PATTERN.sub(replace_link, escaped)
    escaped = STRONG_PATTERN.sub(r"<strong>\1</strong>", escaped)
    escaped = EM_PATTERN.sub(r"<em>\1</em>", escaped)
    return escaped


def parse_table(lines: list[str]) -> str:
    """Transform a markdown table into HTML."""
    clean_lines = [line.strip() for line in lines if line.strip()]
    if not clean_lines:
        return ""

    rows: list[list[str]] = []
    for line in clean_lines:
        if TABLE_DIVIDER_PATTERN.match(line):
            continue
        cells = [cell.strip() for cell in re.split(r"\s*\|\s*", line.strip().strip("|"))]
        rows.append(cells)

    if not rows:
        return ""

    header = rows[0]
    body_rows = rows[1:]
    col_count = max(len(row) for row in rows)

    def pad(row: list[str]) -> list[str]:
        return row + ["" for _ in range(col_count - len(row))]

    header = pad(header)
    body_rows = [pad(row) for row in body_rows]

    parts: list[str] = ["<table class=\"data-table\">", "<thead>", "<tr>"]
    parts.extend(f"<th>{parse_inline(cell)}</th>" for cell in header)
    parts.extend(["</tr>", "</thead>"])

    parts.append("<tbody>")
    for row in body_rows:
        parts.append("<tr>")
        parts.extend(f"<td>{parse_inline(cell)}</td>" for cell in row)
        parts.append("</tr>")
    parts.append("</tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def close_lists(
    html_lines: list[str],
    list_stack: list[tuple[str, int]],
    target_indent: int | None = None,
) -> None:
    """Close open lists down to a target indentation (None closes all)."""
    while list_stack and (target_indent is None or list_stack[-1][1] > target_indent):
        tag, _ = list_stack.pop()
        html_lines.append(f"</{tag}>")


def flush_blockquote(html_lines: list[str], blockquote_lines: list[str]) -> None:
    if not blockquote_lines:
        return
    quote_html = "<br>".join(parse_inline(line) for line in blockquote_lines)
    html_lines.append(f"<blockquote class=\"evidence-quote\">{quote_html}</blockquote>")
    blockquote_lines.clear()


def markdown_to_html(md_content: str) -> str:
    """Convert markdown text to HTML according to project rules."""
    html_lines: list[str] = []
    list_stack: list[tuple[str, int]] = []
    blockquote_lines: list[str] = []
    table_buffer: list[str] = []
    in_table = False
    in_code_block = False
    code_language = ""
    code_buffer: list[str] = []

    lines = md_content.splitlines()

    for line in lines:
        stripped = line.rstrip()

        if in_code_block:
            if stripped.startswith("```"):
                language_class = f" language-{code_language}" if code_language else ""
                code_html = "\n".join(code_buffer)
                html_lines.append(
                    f"<pre class=\"code-block\"><code{language_class}>{code_html}</code></pre>"
                )
                code_buffer = []
                in_code_block = False
                code_language = ""
            else:
                code_buffer.append(html_escape(line))
            continue

        if stripped.startswith("```"):
            flush_blockquote(html_lines, blockquote_lines)
            close_lists(html_lines, list_stack, target_indent=None)
            in_code_block = True
            code_language = stripped[3:].strip()
            code_buffer = []
            continue

        if TABLE_ROW_PATTERN.match(stripped):
            flush_blockquote(html_lines, blockquote_lines)
            close_lists(html_lines, list_stack, target_indent=None)
            in_table = True
            table_buffer.append(stripped)
            continue
        if in_table and not TABLE_ROW_PATTERN.match(stripped):
            html_lines.append(parse_table(table_buffer))
            table_buffer = []
            in_table = False

        if not stripped and in_table:
            html_lines.append(parse_table(table_buffer))
            table_buffer = []
            in_table = False

        if not stripped:
            flush_blockquote(html_lines, blockquote_lines)
            close_lists(html_lines, list_stack, target_indent=None)
            html_lines.append("")
            continue

        bullet_match = BULLET_PATTERN.match(line)
        ordered_match = ORDERED_PATTERN.match(line)

        if bullet_match:
            flush_blockquote(html_lines, blockquote_lines)
            indent = len(bullet_match.group("indent").replace("\t", "    "))
            content = parse_inline(bullet_match.group("content"))

            close_lists(html_lines, list_stack, target_indent=indent)
            if not list_stack or indent > list_stack[-1][1]:
                html_lines.append("<ul>")
                list_stack.append(("ul", indent))
            elif list_stack[-1][0] != "ul":
                close_lists(html_lines, list_stack, target_indent=None)
                html_lines.append("<ul>")
                list_stack.append(("ul", indent))
            html_lines.append(f"<li>{content}</li>")
            continue

        if ordered_match:
            flush_blockquote(html_lines, blockquote_lines)
            indent = len(ordered_match.group("indent").replace("\t", "    "))
            content = parse_inline(ordered_match.group("content"))

            close_lists(html_lines, list_stack, target_indent=indent)
            if not list_stack or indent > list_stack[-1][1]:
                html_lines.append("<ol>")
                list_stack.append(("ol", indent))
            elif list_stack[-1][0] != "ol":
                close_lists(html_lines, list_stack, target_indent=None)
                html_lines.append("<ol>")
                list_stack.append(("ol", indent))
            html_lines.append(f"<li>{content}</li>")
            continue

        flush_blockquote(html_lines, blockquote_lines)

        if stripped.startswith("> "):
            blockquote_lines.append(stripped[2:].strip())
            continue
        if blockquote_lines:
            flush_blockquote(html_lines, blockquote_lines)

        close_lists(html_lines, list_stack, target_indent=None)

        if stripped.startswith("### "):
            html_lines.append(f"<h4>{parse_inline(stripped[4:].strip())}</h4>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h3>{parse_inline(stripped[3:].strip())}</h3>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h2>{parse_inline(stripped[2:].strip())}</h2>")
        elif stripped == "---":
            html_lines.append("<hr>")
        else:
            html_lines.append(f"<p>{parse_inline(stripped)}</p>")

    if in_code_block:
        language_class = f" language-{code_language}" if code_language else ""
        code_html = "\n".join(code_buffer)
        html_lines.append(f"<pre class=\"code-block\"><code{language_class}>{code_html}</code></pre>")

    if in_table and table_buffer:
        html_lines.append(parse_table(table_buffer))

    flush_blockquote(html_lines, blockquote_lines)
    close_lists(html_lines, list_stack, target_indent=None)

    cleaned = [line for line in html_lines if line is not None]
    return "\n".join(cleaned)


def build_meta(metadata: dict[str, str]) -> tuple[str, str, str, str]:
    """Prepare subtitle, meta line, footer meta, and short title."""
    author = metadata.get("analyst") or metadata.get("author") or "Nirvan Chitnis"
    date = metadata.get("date") or metadata.get("created") or "October 2025"
    purpose = metadata.get("purpose") or metadata.get("category") or "Evidence documentation"
    subtitle = metadata.get("title") or metadata.get("subtitle")
    return author, date, purpose, subtitle


def convert_file(md_path: Path, output_path: Path) -> None:
    """Convert a single markdown file to HTML."""
    with md_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    metadata = parse_frontmatter(lines)
    extracted_title, body = extract_body(lines)

    if extracted_title:
        metadata.setdefault("title", extracted_title)

    html_content = markdown_to_html(body)

    author, date, purpose, subtitle_override = build_meta(metadata)
    subtitle = subtitle_override or (extracted_title or md_path.stem.replace("_", " "))
    meta_line = f"Author: {author} | Date: {date} | Purpose: {purpose}"
    short_title = subtitle[:80]

    depth = len(output_path.relative_to("evidence").parts) - 1
    prefix = "../" * (depth + 1)

    footer_meta = f"Author: {author} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Source: {md_path.name}"

    html_output = TEMPLATE.format(
        title=subtitle,
        subtitle=subtitle,
        meta=meta_line,
        short_title=subtitle,
        content=html_content,
        footer_meta=footer_meta,
        css_path=prefix,
        home_path=prefix,
        js_path=prefix,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(html_output)


def main() -> None:
    evidence_dir = Path("evidence")
    md_files = sorted(evidence_dir.rglob("*.md"))
    if not md_files:
        print("No markdown files found in evidence/ directory.")
        return

    print(f"Found {len(md_files)} .md files in evidence/")

    converted = 0
    errors: list[tuple[Path, str]] = []

    for md_path in md_files:
        html_path = md_path.with_suffix(".html")
        try:
            convert_file(md_path, html_path)
            converted += 1
            rel_path = md_path.relative_to(evidence_dir)
            print(f"✓ {rel_path} → {html_path.name}")
        except Exception as exc:  # noqa: BLE001
            errors.append((md_path, str(exc)))
            rel_path = md_path.relative_to(evidence_dir)
            print(f"✗ {rel_path}: {exc}")

    print(f"\nConversion complete: {converted}/{len(md_files)} files")
    if errors:
        print("Errors encountered:")
        for path, message in errors:
            print(f"  - {path}: {message}")


if __name__ == "__main__":
    main()
