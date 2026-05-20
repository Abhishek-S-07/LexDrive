import json
import re

def parse_mv_act(source_file):
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by lines for easier processing
    lines = content.split('\n')
    
    # Initialize data structures
    sections = []
    current_chapter = ""
    current_section = None
    current_section_text = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for chapter heading
        if line.startswith('## Chapter '):
            # Save previous section if exists
            if current_section is not None:
                sections.append({
                    "section": current_section["number"],
                    "title": current_section["title"],
                    "chapter": current_chapter,
                    "text": '\n'.join(current_section_text).strip()
                })
            
            # Extract chapter name
            current_chapter = line.replace('## Chapter ', '').split(' (')[0].strip()
            current_section = None
            current_section_text = []
            
        # Check for section heading
        elif line.startswith('## Section '):
            # Save previous section if exists
            if current_section is not None:
                sections.append({
                    "section": current_section["number"],
                    "title": current_section["title"],
                    "chapter": current_chapter,
                    "text": '\n'.join(current_section_text).strip()
                })
            
            # Extract section number and title
            section_match = re.match(r'## Section (\S+): (.+)', line)
            if section_match:
                section_num = section_match.group(1)
                section_title = section_match.group(2)
                
                current_section = {
                    "number": section_num,
                    "title": section_title
                }
                current_section_text = []
                
                # Look for Clause in next few lines
                j = i + 1
                while j < len(lines) and j < i + 5:  # Check next few lines
                    clause_line = lines[j].strip()
                    if clause_line.startswith('**Clause**:'):
                        # Start collecting clause text
                        k = j + 1
                        while k < len(lines):
                            next_line = lines[k].strip()
                            # Stop at next section or chapter
                            if next_line.startswith('## Section ') or next_line.startswith('## Chapter '):
                                break
                            current_section_text.append(lines[k])  # Keep original line for formatting
                            k += 1
                        # Set i to continue after the clause text
                        i = k - 1
                        break
                    j += 1
        
        i += 1
    
    # Don't forget the last section
    if current_section is not None:
        sections.append({
            "section": current_section["number"],
            "title": current_section["title"],
            "chapter": current_chapter,
            "text": '\n'.join(current_section_text).strip()
        })
    
    return sections

if __name__ == "__main__":
    source_file = r"C:\Users\abhis\.local\share\kilo\tool-output\tool_e454815b0001rbAywb5QBlZ4Bp"
    output_file = r"C:\Users\abhis\Downloads\Roadsafety\law_database.json"
    
    print(f"Parsing {source_file}...")
    sections = parse_mv_act(source_file)
    
    print(f"Found {len(sections)} sections")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)
    
    print(f"Written to {output_file}")