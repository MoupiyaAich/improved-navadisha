import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

DOCUMENTS_FOLDER = "./documents"
VECTOR_DB_PATH="./legal_db"

def load_all_pdfs(folder_path):
    all_docs=[]
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDFs found in the documents folder!")
        return []
    print(f"Found {len(pdf_files)} PDF(s): {pdf_files}")

    for filename in pdf_files:
        file_path = os.path.join(folder_path, filename)
        print(f"    Loading {filename}...")
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            all_docs.extend(docs)
            print(f"    Loaded {len(docs)} pages from {filename}")
        except Exception as e:
            print(f"    Failed to load {filename}: {e}")
    return all_docs

def chunk_documents(docs):
    for doc in docs:
        doc.page_content = " ".join(doc.page_content.split())
    splitter=RecursiveCharacterTextSplitter(chunk_size=500, 
                                            chunk_overlap=50, 
                                            separators=["\n\n", "\n", ".", " "])
    chunks=splitter.split_documents(docs)
    print(f"\nSplit into {len(chunks)} chunks")
    return chunks

def build_vectorstore(chunks):
    print("\nBuilding embeddings (this takes a few minutes)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=VECTOR_DB_PATH)
    print(f"\nVector store saved to {VECTOR_DB_PATH}")
    return vectorstore

def test_query(vectorstore):
    print("\nTesting a sample query...")
    results = vectorstore.similarity_search("What are my rights if my employer doesn't pay me?", k=2)
    for i, doc in enumerate(results):
        print(f"\nResult {i+1} ")
        print(doc.page_content[:300])

if __name__ == "__main__":
    print("Starting Navadisha AI ingestion...\n")
    docs=load_all_pdfs(DOCUMENTS_FOLDER)
    if not docs:
        exit(1)
    chunks=chunk_documents(docs)
    vectorstore=build_vectorstore(chunks)
    test_query(vectorstore)

    print("\nIngestion complete! You can now ask questions using the RAG system.")