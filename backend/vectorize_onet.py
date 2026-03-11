import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Configuration
SOURCE_DIR = "/Users/juanfelipe/Documents/Affila/Bounce/ONET"
PERSIST_DIRECTORY = "/Users/juanfelipe/Documents/Affila/Bounce/backend/chroma_db"
COLLECTION_NAME = "onet_career_data"

def vectorize_onet_data():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory {SOURCE_DIR} not found.")
        return

    # Note: ensure GOOGLE_API_KEY is set in the environment
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Load and split PDF documents
    documents = []
    for file in os.listdir(SOURCE_DIR):
        if file.endswith(".pdf"):
            print(f"Loading {file}...")
            loader = PyPDFLoader(os.path.join(SOURCE_DIR, file))
            documents.extend(loader.load())

    if not documents:
        print("No PDF documents found to vectorize.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    
    print(f"Vectorizing {len(splits)} chunks into ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY,
        collection_name=COLLECTION_NAME
    )
    print("Vectorization complete.")

if __name__ == "__main__":
    vectorize_onet_data()
