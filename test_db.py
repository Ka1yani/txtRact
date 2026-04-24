import fitz
from database import init_db, search_database
from extractor import process_pdf

def create_sample_pdf(filename):
    doc = fitz.open()
    doc.set_metadata({"title": "Sample DB PDF", "author": "Tester"})
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text((50, 50), "This is the first page discussing general text extraction capabilities.")
    
    # Page 2
    page2 = doc.new_page()
    page2.insert_text((50, 50), "PostgreSQL full-text search utilizes to_tsvector and tsquery for efficient matching.")
    
    doc.save(filename)
    doc.close()

def run_test():
    print("Initializing Database...")
    init_db()
    
    filename = "test_doc.pdf"
    print(f"Creating {filename}...")
    create_sample_pdf(filename)
    
    print(f"Processing {filename}...")
    process_pdf(filename, filename)
    
    print("Searching for 'PostgreSQL tsquery'...")
    results = search_database("PostgreSQL tsquery")
    for r in results:
        print(f"Match found on page {r['page_number']} of {r['document_name']} (rank {r['rank']}):")
        print(f"Text: {r['page_text']}")
        print(f"Metadata: {r['metadata']}")
        print("---")

if __name__ == "__main__":
    run_test()
