import os
import pickle
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import TFIDFRetriever

def main():
    data_dir = os.path.join("data", "M&I RAG", "Files")
    print(f"Loading PDFs from {data_dir}...")
    loader = PyPDFDirectoryLoader(data_dir)
    documents = loader.load()
    print(f"Loaded {len(documents)} document pages.")

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Building TFIDF Retriever (skipping heavy ML embeddings due to Windows DLL constraints)...")
    retriever = TFIDFRetriever.from_documents(chunks)
    retriever.k = 5
    
    with open("tfidf_retriever.pkl", "wb") as f:
        pickle.dump(retriever, f)
    print("Retriever saved locally to tfidf_retriever.pkl")

if __name__ == "__main__":
    main()
