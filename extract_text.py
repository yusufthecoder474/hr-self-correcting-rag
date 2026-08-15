import pymupdf

pdf_path = "documents/NexaCore_HR_Policy_Handbook.pdf"

doc = pymupdf.open(pdf_path)

for page in doc:
    print(page.get_text())

doc.close()