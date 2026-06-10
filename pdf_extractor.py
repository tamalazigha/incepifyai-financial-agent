import fitz  # PyMuPDF — installed as the pymupdf package
 
 
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF file.
    Returns the full text as a single string.
    Works on text-based PDFs (most bank financial statements).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
 
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():  # skip blank pages
            pages_text.append(
                f"=== PAGE {page_num + 1} ===\n{text.strip()}"
            )
 
    doc.close()
    return "\n\n".join(pages_text)
 
 
def extract_tables_from_pdf(pdf_bytes: bytes) -> list:
    """
    Attempt to extract structured tables from PDF pages.
    Useful for balance sheets and P&L statements with clear grid formatting.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_tables = []
 
    for page_num, page in enumerate(doc):
        tabs = page.find_tables()
        if tabs.tables:
            for tab in tabs.tables:
                all_tables.append({
                    "page": page_num + 1,
                    "rows": tab.extract()
                })
 
    doc.close()
    return all_tables
 
 
def get_pdf_info(pdf_bytes: bytes) -> dict:
    """Get basic metadata — page count and whether the PDF has selectable text."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    info = {
        "page_count": len(doc),
        "title": doc.metadata.get("title", "Unknown"),
        "has_text": any(page.get_text().strip() for page in doc)
    }
    doc.close()
    return info
