import pdfplumber
import re
import os


def clean_resume_text(text: str) -> str:
    """
    Cleans resume text for NLP usage.
    Removes emails, phone numbers, links, and extra spaces.
    """
    if not text:
        return ""
    
    text = text.lower()

    # Remove emails
    text = re.sub(r"\S+@\S+", " ", text)
   
    # Remove phone numbers
    text = re.sub(r"\+?\d[\d\s\-\(\)]{8,}\d", " ", text)

    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts and cleans text from a PDF resume.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("File must be a PDF")
    
    full_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF has no pages")
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                    continue

        if not full_text.strip():
            raise ValueError("No text could be extracted from PDF. It might be an image-based PDF.")
        
        cleaned = clean_resume_text(full_text)
        
        if len(cleaned) < 50:
            raise ValueError("Extracted text is too short. Please ensure your PDF contains actual text content.")
        
        return cleaned
        
    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Error reading PDF: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "Gaurav-G-FlowCV-Resume-20251212.pdf"

    try:
        resume_text = extract_text_from_pdf(pdf_path)

        with open("resume_text.txt", "w", encoding="utf-8") as f:
            f.write(resume_text)

        print("✅ Resume extracted successfully")
        print("📄 Saved as resume_text.txt")
        print(f"\nExtracted {len(resume_text)} characters")
        print("\nPreview:\n")
        print(resume_text[:500])
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)