from pypdf import PdfReader

pdf = r"../main_full.pdf"
reader = PdfReader(pdf)
print("PAGES", len(reader.pages))
for term in ["10.2", "11.1", "12.2", "24.1", "29.1", "33.2"]:
    hits = []
    for i, page in enumerate(reader.pages):
        if term in (page.extract_text() or ""):
            hits.append(i + 1)
    print(term, hits)
