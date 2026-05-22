import json
import os
import re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:
    raise ImportError(
        "pypdf is required to extract text from PDF files. "
        "Install it with `pip install pypdf` or add it to requirements.txt."
    ) from exc


STATE_DB_DIR = Path(__file__).resolve().parent / "state_law_databases"
PDF_GLOB = "*.pdf"

CHAPTER_RE = re.compile(
    r'^(?:CHAPTER|Chapter)\s+([IVXLCDM0-9]+)(?:[\.\-–—:\s]+(.+))?$'
)
SECTION_RE = re.compile(
    r'^(?:Section|SECTION)\s+([0-9]+[A-Za-z0-9\.-/]*)(?:[\.\-–—:\s]+(.+))?$'
)


def normalize_state_name(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r'[\W_]+', '_', stem).strip('_')
    return stem.lower() or 'state'


def friendly_state_name(filename: str) -> str:
    stem = Path(filename).stem
    clean = re.sub(r'[\-_]+', ' ', stem)
    clean = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean or stem


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        pages.append(page_text)
    return "\n".join(pages)


def parse_state_law_text(raw_text: str) -> list[dict]:
    if not raw_text:
        return []

    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in text.split('\n')]

    sections = []
    current_chapter = ''
    current_section = None
    current_section_text = []

    def flush_section():
        nonlocal current_section, current_section_text
        if current_section is None:
            return
        sections.append({
            'section': current_section['number'],
            'title': current_section['title'],
            'chapter': current_chapter,
            'text': '\n'.join(current_section_text).strip(),
        })
        current_section = None
        current_section_text = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            if current_section is not None:
                current_section_text.append('')
            i += 1
            continue

        chapter_match = CHAPTER_RE.match(line)
        section_match = SECTION_RE.match(line)

        if chapter_match:
            flush_section()
            chapter_number = chapter_match.group(1).strip()
            chapter_title = (chapter_match.group(2) or '').strip()
            current_chapter = f"Chapter {chapter_number}" if not chapter_title else f"Chapter {chapter_number}: {chapter_title}"
            i += 1
            continue

        if section_match:
            flush_section()
            section_number = section_match.group(1).strip()
            section_title = (section_match.group(2) or '').strip()

            if not section_title:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and not SECTION_RE.match(lines[j]) and not CHAPTER_RE.match(lines[j]):
                    section_title = lines[j].strip()
                    i = j

            current_section = {
                'number': section_number,
                'title': section_title,
            }
            current_section_text = []
            i += 1
            continue

        if current_section is not None:
            current_section_text.append(line)
        i += 1

    flush_section()
    return sections


def build_state_databases(root_path: Path) -> None:
    STATE_DB_DIR.mkdir(exist_ok=True)
    pdf_files = sorted(root_path.glob(PDF_GLOB))
    combined = []

    if not pdf_files:
        print('No PDF files found in the project root to process.')
        return

    for pdf_file in pdf_files:
        state_name = friendly_state_name(pdf_file.name)
        state_key = normalize_state_name(pdf_file.name)
        print(f'Processing {pdf_file.name} -> {state_name}')

        raw_text = extract_text_from_pdf(pdf_file)
        sections = parse_state_law_text(raw_text)

        if not sections:
            print(f'  Warning: no section headings found in {pdf_file.name}. Saving full text fallback.')
            sections = [{
                'section': 'FULL_TEXT',
                'title': pdf_file.stem,
                'chapter': '',
                'text': raw_text.strip(),
            }]

        for section in sections:
            section['state'] = state_name
            section['source_file'] = pdf_file.name

        out_path = STATE_DB_DIR / f'law_database_{state_key}.json'
        with open(out_path, 'w', encoding='utf-8') as out_file:
            json.dump(sections, out_file, indent=2, ensure_ascii=False)

        combined.extend(sections)
        print(f'  Saved {len(sections)} sections to {out_path}')

    combined_path = root_path / 'law_database_all_states.json'
    with open(combined_path, 'w', encoding='utf-8') as combined_file:
        json.dump(combined, combined_file, indent=2, ensure_ascii=False)
    print(f'Combined file written: {combined_path} ({len(combined)} sections total)')


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent
    build_state_databases(project_root)
