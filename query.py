import os
import argparse
import pandas as pd
import pickle
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class QARunner:
    def __init__(self, retriever, llm, prompt):
        self.retriever = retriever
        self.llm = llm
        self.prompt = prompt

    def invoke(self, inputs):
        query = inputs["query"]
        docs = self.retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)
        formatted_prompt = self.prompt.format(context=context, question=query)
        answer = self.llm.invoke(formatted_prompt)
        return {"result": answer.content, "source_documents": docs}

def setup_qa_chain():
    print("Loading TFIDF retriever...")
    with open("tfidf_retriever.pkl", "rb") as f:
        retriever = pickle.load(f)
        
    print("Initializing Groq model...")
    llm = ChatGroq(
        api_key=os.environ.get("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0.1
    )
    
    prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Answer:"""
    PROMPT = PromptTemplate.from_template(prompt_template)
    return QARunner(retriever, llm, PROMPT)

def run_interactive(qa_chain):
    print("\nRAG System Ready. Type 'exit' to quit.\n")
    while True:
        query = input("Ask a question about the RCAs: ")
        if query.lower() in ['exit', 'quit']:
            break
        
        print("\nSearching and generating answer...")
        result = qa_chain.invoke({"query": query})
        
        print("\n--- Answer ---")
        print(result["result"])
        
        print("\n--- Sources ---")
        for i, doc in enumerate(result["source_documents"]):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            print(f"{i+1}. {os.path.basename(source)} (Page {page})")
        print("-" * 50 + "\n")

def run_batch(qa_chain, excel_path):
    print(f"Reading queries from {excel_path}...")
    df = pd.read_excel(excel_path, header=1)
    
    query_col = None
    for col in df.columns:
        if 'query' in str(col).lower() or 'question' in str(col).lower():
            query_col = col
            break
            
    if not query_col:
        if 'Description ' in df.columns:
            print("Using 'Description ' column as queries since no explicit query column was found.")
            query_col = 'Description '
        else:
            print("Could not find a column named 'Query' in the Excel file.")
            print("Columns found:", df.columns.tolist())
            return

    import time
    results = []
    for index, row in df.iterrows():
        query = str(row[query_col])
        if pd.isna(row[query_col]) or query.strip() == "" or query.lower() == "nan":
            results.append("N/A")
            continue
            
        print(f"Processing query {index+1}/{len(df)}: {query}")
        
        # Simple retry logic for Rate Limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = qa_chain.invoke({"query": query})
                results.append(result["result"])
                break
            except Exception as e:
                if "Rate limit" in str(e) or "429" in str(e):
                    print(f"Rate limit hit on attempt {attempt+1}. Waiting 10 seconds...")
                    time.sleep(10)
                else:
                    print(f"Error on query {index+1}: {e}")
                    results.append("Error")
                    break
        else:
            results.append("Rate Limit Failed")
            
        # Small delay between queries to avoid hitting TPM limits quickly
        time.sleep(1)
        
    df["RAG Answer"] = results
    output_path = "data/M&I RAG/Results.xlsx"
    df.to_excel(output_path, index=False)
    print(f"Batch processing complete. Results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the RCA RAG system.")
    parser.add_argument("--batch", type=str, help="Path to an excel file containing queries.")
    args = parser.parse_args()
    
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable not set.")
        print("Please set it using: set GROQ_API_KEY=your_key")
        exit(1)
        
    qa_chain = setup_qa_chain()
    
    if args.batch:
        run_batch(qa_chain, args.batch)
    else:
        run_interactive(qa_chain)
