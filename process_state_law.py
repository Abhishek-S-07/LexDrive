import PyPDF2
import re
import json

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file"""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text

def format_state_law_text(raw_text, state_name):
    """
    Format raw state law text into the expected structure:
    ## Chapter [name]
    ## Section [number]: [title]
    **Clause**:
    [clause text]
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
    
    # Try to identify chapters and sections
    # This is a simplified approach - in reality, you'd need more sophisticated parsing
    # based on the actual structure of each state's law document
    
    formatted_sections = []
    
    # Look for common patterns in motor vehicle rules
    # Pattern for chapters (often in all caps or numbered)
    chapter_patterns = [
        r'CHAPTER\s+[IVXLCDM]+',  # Roman numerals
        r'Chapter\s+\d+',         # Arabic numerals
        r'PART\s+[IVXLCDM]+',     # Sometimes called Parts
        r'SECTION\s+[IVXLCDM]+\s*[-–]\s*[A-Z]',  # Section with title
    ]
    
    # For now, create a basic structure
    # In a real implementation, you'd parse the actual document structure
    
    # Create a single section with the extracted text
    # This is a placeholder - real implementation would parse actual chapters/sections
    formatted_sections.append({
        "section": "1",
        "title": f"{state_name} Motor Vehicles Rules - Preliminary Provisions",
        "chapter": "Preliminary",
        "text": cleaned_text[:2000]  # Limit size for demo
    })
    
    return formatted_sections

def process_state_law_pdf(pdf_path, state_name, output_dir="state_law_jsons"):
    """Process a state law PDF and save as JSON"""
    import os
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Processing {state_name} law from {pdf_path}...")
    
    # Extract text
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(raw_text)} characters from {pdf_path}")
    
    # Format text
    formatted_sections = format_state_law_text(raw_text, state_name)
    print(f"Formatted into {len(formatted_sections)} sections")
    
    # Save as JSON
    output_file = os.path.join(output_dir, f"{state_name.lower().replace(' ', '_')}_law.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_sections, f, indent=2, ensure_ascii=False)
    
    print(f"Saved formatted law to {output_file}")
    return output_file

if __name__ == "__main__":
    # Example usage
    process_state_law_pdf("westbengal.pdf", "West Bengal")