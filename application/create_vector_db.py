import pymupdf
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Read PDF
pdf_path = "documents/vit/VIT_HR_Conditions_of_Service.pdf"

doc = pymupdf.open(pdf_path)

text = ""

for page in doc:
    text += page.get_text()

doc.close()

# 2. Split text into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

chunks = splitter.split_text(text)

print("Total chunks:", len(chunks))

# 3. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 4. Create ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="hr_policies"
)

# 5. Create embeddings
embeddings = model.encode(chunks).tolist()

# 6. Store chunks, embeddings, and metadata
ids = [f"chunk_{i}" for i in range(len(chunks))]

metadatas = [
    {
        "source": "VIT_HR_Conditions_of_Service.pdf",
        "chunk_id": i
    }
    for i in range(len(chunks))
]

collection.upsert(
    ids=ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadatas
)

print("Chunks stored in ChromaDB:", collection.count())