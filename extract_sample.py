import PyPDF2

def extract_text_from_pdf(pdf_path, max_pages=10):
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = min(len(pdf_reader.pages), max_pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text

if __name__ == "__main__":
    pdf_path = "westbengal.pdf"
    extracted_text = extract_text_from_pdf(pdf_path, 10)
    print(extracted_text[:5000])