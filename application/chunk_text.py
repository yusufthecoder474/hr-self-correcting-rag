import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

pdf_path = "documents/vit/VIT_HR_Conditions_of_Service.pdf"

doc = pymupdf.open(pdf_path)

text = ""

for page in doc:
    text += page.get_text()

doc.close()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

chunks = splitter.split_text(text)

print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks[:5]):
    print("\n--- Chunk", i + 1, "---")
    print(chunk)