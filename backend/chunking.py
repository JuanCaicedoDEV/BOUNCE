"""
Section-aware document chunking.

For O*NET docs: splits by known section headers (Tasks, Skills, Education, etc.)
For university program PDFs: splits by detected headers (Title Case / ALL CAPS short lines)
Falls back to paragraph splitting if no sections found.
"""
import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class DocumentChunk:
    text: str
    section: str = ""
    metadata: dict = field(default_factory=dict)


# Known O*NET section headers (ordered by typical appearance)
ONET_SECTIONS = [
    "Tasks", "Technology Skills", "Knowledge", "Skills", "Abilities",
    "Work Activities", "Detailed Work Activities", "Work Context",
    "Job Zone", "Education", "Credentials", "Interests", "Work Styles",
    "Work Values", "Related Occupations", "Wages & Employment Trends",
    "Job Outlook", "Earnings", "Bright Outlook", "Overview", "Summary",
    "Occupation-Specific Information", "Sample of reported job titles",
]

# Regex: short line (≤60 chars), Title Case or ALL CAPS, not ending with period/comma
_HEADER_RE = re.compile(
    r'^(?:'
    # Known O*NET headers
    + '|'.join(re.escape(s) for s in ONET_SECTIONS)
    # Generic: ALL CAPS line
    + r'|[A-Z][A-Z &]{2,50}'
    # Generic: Title Case line (no period at end)
    + r'|(?:[A-Z][a-z]+)(?:\s+(?:&|and|of|for|the|[A-Z][a-z]+))*'
    + r')$',
    re.MULTILINE,
)

MAX_SECTION_CHARS = 1_200   # split long sections further
MIN_CHUNK_CHARS   = 80      # discard tiny fragments


def _split_long_section(text: str, max_chars: int = MAX_SECTION_CHARS) -> List[str]:
    """Split a long section by paragraphs; keep each piece ≤ max_chars."""
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If single paragraph is still too long, hard-split it
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i:i + max_chars])
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def split_by_sections(text: str, base_metadata: dict | None = None) -> List[DocumentChunk]:
    """
    Split document text into section-based chunks.
    Returns list of DocumentChunk with section label and metadata.
    """
    base_metadata = base_metadata or {}
    lines = text.split("\n")
    sections: List[tuple[str, List[str]]] = []   # [(section_name, [lines])]
    current_section = "Introduction"
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and _HEADER_RE.match(stripped) and len(stripped) < 65:
            # Save current section
            if current_lines:
                sections.append((current_section, current_lines))
            current_section = stripped
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_section, current_lines))

    # Fall back: no sections detected → use paragraph splitting
    if len(sections) <= 1:
        return _fallback_paragraph_chunks(text, base_metadata)

    chunks: List[DocumentChunk] = []
    for section_name, sec_lines in sections:
        body = "\n".join(sec_lines).strip()
        if len(body) < MIN_CHUNK_CHARS:
            continue
        for piece in _split_long_section(body):
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(DocumentChunk(
                text=f"{section_name}\n{piece}",
                section=section_name,
                metadata={**base_metadata, "section": section_name},
            ))
    return chunks if chunks else _fallback_paragraph_chunks(text, base_metadata)


def _fallback_paragraph_chunks(text: str, base_metadata: dict) -> List[DocumentChunk]:
    """Split by paragraphs when no section headers found."""
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if len(p.strip()) >= MIN_CHUNK_CHARS]
    chunks, current = [], ""
    for para in paras:
        if len(current) + len(para) + 2 <= MAX_SECTION_CHARS:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(DocumentChunk(text=current, metadata=base_metadata))
            current = para
    if current:
        chunks.append(DocumentChunk(text=current, metadata=base_metadata))
    return chunks
