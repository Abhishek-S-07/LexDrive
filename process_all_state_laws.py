import PyPDF2
import re
import json
import os

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file"""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text

def parse_state_law_text(raw_text, state_name):
    """
    Parse state law text into structured format with chapters and sections
    Expected output format for each section:
    {
        "section": "section_number_or_identifier",
        "title": "section_title",
        "chapter": "chapter_name",
        "text": "full_section_text"
    }
    """
    
    # Clean up the text
    lines = raw_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:  # Skip empty lines
            cleaned_lines.append(line)
    
    # Join back with proper spacing
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Parse the document structure
    sections = []
    
    # Patterns to identify structural elements
    chapter_pattern = re.compile(r'^(CHAPTER\s+[IVXLCDM]+|Chapter\s+\d+|PART\s+[IVXLCDM]+|PART\s+\d+)', re.IGNORECASE)
    section_pattern = re.compile(r'^(\d+\.\s+[A-Z])', re.IGNORECASE)  # Matches "1. Short title" etc.
    subsection_pattern = re.compile(r'^\([a-z]\)')  # Matches "(a)", "(b)", etc.
    
    current_chapter = "Preliminary"
    current_section = None
    current_section_text = []
    current_section_num = ""
    current_section_title = ""
    
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]
        
        # Check for chapter heading
        chapter_match = chapter_pattern.match(line)
        if chapter_match:
            # Save previous section if exists
            if current_section is not None:
                sections.append({
                    "section": current_section_num,
                    "title": current_section_title,
                    "chapter": current_chapter,
                    "text": '\n'.join(current_section_text).strip()
                })
            
            # Start new chapter
            current_chapter = chapter_match.group(0).strip()
            current_section = None
            current_section_text = []
            i += 1
            continue
        
        # Check for section heading (like "1. Short title and application.")
        section_match = section_pattern.match(line)
        if section_match:
            # Save previous section if exists
            if current_section is not None:
                sections.append({
                    "section": current_section_num,
                    "title": current_section_title,
                    "chapter": current_chapter,
                    "text": '\n'.join(current_section_text).strip()
                })
            
            # Start new section
            current_section_num = section_match.group(1).strip().rstrip('.')
            # Extract title (everything after the number and dot)
            title_part = line[len(section_match.group(0)):].strip()
            current_section_title = title_part
            current_section_text = [line]  # Include the section heading in the text
            current_section = True
            i += 1
            continue
        
        # If we're in a section, add the line to current section text
        if current_section is not None:
            current_section_text.append(line)
        
        i += 1
    
    # Don't forget the last section
    if current_section is not None:
        sections.append({
            "section": current_section_num,
            "title": current_section_title,
            "chapter": current_chapter,
            "text": '\n'.join(current_section_text).strip()
        })
    
    # If no sections were found with the above logic, create a fallback
    if not sections:
        # Create a single section with all text
        sections.append({
            "section": "1",
            "title": f"{state_name} Motor Vehicles Rules",
            "chapter": "Full Document",
            "text": cleaned_text[:3000]  # Limit size
        })
    
    return sections

def process_state_law_pdf(pdf_path, state_name, output_dir="state_law_jsons"):
    """Process a state law PDF and save as JSON"""
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Processing {state_name} law from {pdf_path}...")
    
    # Extract text
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(raw_text)} characters from {pdf_path}")
    
    # Parse text into structured format
    formatted_sections = parse_state_law_text(raw_text, state_name)
    print(f"Parsed into {len(formatted_sections)} sections")
    
    # Show sample of what we parsed
    if formatted_sections:
        print(f"Sample section: {formatted_sections[0]['section']} - {formatted_sections[0]['title']}")
        print(f"Chapter: {formatted_sections[0]['chapter']}")
        print(f"Text preview: {formatted_sections[0]['text'][:200]}...")
    
    # Save as JSON
    output_file = os.path.join(output_dir, f"{state_name.lower().replace(' ', '_')}_law.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_sections, f, indent=2, ensure_ascii=False)
    
    print(f"Saved formatted law to {output_file}")
    return output_file

def process_all_state_laws(pdf_directory="."):
    """Process all state law PDFs in the directory"""
    
    # List of known state law PDFs from the git status
    state_pdfs = [
        ("westbengal.pdf", "West Bengal"),
        ("uttarpradesh.pdf", "Uttar Pradesh"),
        ("uttarkhand.pdf", "Uttarakhand"),
        ("tripura.pdf", "Tripura"),
        ("tnmvr1989.pdf", "Tamil Nadu"),
        ("rajasthan.pdf", "Rajasthan"),
        ("meghalaya_motor_transport_rules.pdf", "Meghalaya"),
        ("the-mizoram-motor-vehicle-rules-1995.pdf", "Mizoram"),
        ("theassammotorvehicle_rules2003_0_copy.pdf", "Assam"),
        ("haryana motor vehicles rules, 1993_copy.pdf", "Haryana"),
        ("the-nagaland-state-road-transport-act,-1966.pdf", "Nagaland"),
        ("motor-vehicles-acts_copy.pdf", "Motor Vehicles Act"),
        ("apmotorlaws.pdf", "Andhra Pradesh"),
        ("cmva_1988_copy.pdf", "Central Motor Vehicle Act"),
        ("showfile.pdf", "Showfile"),
        ("traffic rules and regulation pdf  e.pdf", "Traffic Rules")
    ]
    
    processed_files = []
    
    for pdf_file, state_name in state_pdfs:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        if os.path.exists(pdf_path):
            try:
                output_file = process_state_law_pdf(pdf_path, state_name)
                processed_files.append((state_name, output_file))
                print(f"✓ Successfully processed {state_name}\n")
            except Exception as e:
                print(f"✗ Error processing {state_name}: {str(e)}\n")
        else:
            print(f"✗ File not found: {pdf_file}")
    
    print(f"\nProcessing complete! Processed {len(processed_files)} state laws.")
    return processed_files

if __name__ == "__main__":
    # Process all state laws
    process_all_state_laws()