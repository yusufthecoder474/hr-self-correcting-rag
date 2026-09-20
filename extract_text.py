import pymupdf

pdf_path = "documents/vit/VIT_HR_Conditions_of_Service.pdf"

doc = pymupdf.open(pdf_path)

for page in doc:
    print(page.get_text())

doc.close()