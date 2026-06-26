from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import pickle
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

app = Flask(__name__)
CORS(app)

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

# Global runner instance
qa_runner = None

def setup_backend():
    global qa_runner
    print("Loading TFIDF retriever...")
    try:
        with open("tfidf_retriever.pkl", "rb") as f:
            retriever = pickle.load(f)
    except FileNotFoundError:
        print("tfidf_retriever.pkl not found! Please run ingest.py first.")
        return False
        
    print("Initializing Groq model...")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY environment variable not set. Please set it in your environment or deployment settings.")
        api_key = None

    llm = ChatGroq(
        api_key=api_key,
        model_name="llama-3.1-8b-instant",
        temperature=0.1
    )
    
    prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Answer:"""
    PROMPT = PromptTemplate.from_template(prompt_template)
    qa_runner = QARunner(retriever, llm, PROMPT)
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    if qa_runner is None:
        return jsonify({"error": "Backend not initialized."}), 500
        
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter."}), 400
        
    query_text = data['query']
    try:
        result = qa_runner.invoke({"query": query_text})
        
        # Extract sources nicely
        sources = []
        for doc in result["source_documents"]:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            sources.append({
                "file": os.path.basename(source),
                "page": page
            })
            
        return jsonify({
            "answer": result["result"],
            "sources": sources
        })
    except Exception as e:
        print(f"Error querying: {e}")
        return jsonify({"error": str(e)}), 500

# Initialize the backend immediately so Gunicorn runs it when importing the app
setup_backend()

if __name__ == '__main__':
    print("Backend successfully started. Serving on port 5000.")
    app.run(debug=True, use_reloader=False)
