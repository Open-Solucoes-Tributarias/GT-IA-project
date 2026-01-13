import os
import shutil
from typing import List, Dict, Any
import json
from decimal import Decimal
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

class LegalAdvisor:
    """
    GT-IA Module: Legal Intelligence (Bloco 3).
    Responsible for RAG (Retrieval-Augmented Generation) to provide
    legal basis for tax decisions.
    
    Robustness: Uses lazy imports to avoid crashing if LangChain is missing.
    """

    def __init__(self, doc_path: str = "./legal_docs", db_path: str = "./chroma_db"):
        self.doc_path = doc_path
        self.db_path = db_path
        self.vector_store = None
        self.embeddings = None
        self._Chroma = None
        
        # Lazy Import for LangChain
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import Chroma
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            self._Chroma = Chroma 
        except ImportError as e:
            print(f"RAG dependencies missing: {e}. LegalAdvisor running in MOCK mode.")
            return

        # Ensure legal_docs folder exists
        if not os.path.exists(self.doc_path):
            os.makedirs(self.doc_path)

        # Initialize or Load Vector Store
        self._initialize_vector_store()
        
    def _initialize_vector_store(self):
        """Loads existing vector store or initializes a new one if empty."""
        if not self._Chroma: return

        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            print("Loading existing Vector Store...")
            self.vector_store = self._Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        else:
            print("Vector Store not found. Run ingest_documents().")

    def ingest_documents(self):
        """Reads PDFs from legal_docs, splits them, and creates embeddings."""
        try:
            from langchain_community.document_loaders import PyPDFDirectoryLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            print("LangChain loaders missing.")
            return

        print(f"Scanning '{self.doc_path}' for PDFs...")
        loader = PyPDFDirectoryLoader(self.doc_path)
        documents = loader.load()

        if not documents:
            print("No documents found to ingest.")
            return

        print(f"Loaded {len(documents)} document pages. Splitting...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        print(f"Creating embeddings for {len(chunks)} chunks...")
        # Persist ChromaDB
        if self._Chroma:
            self.vector_store = self._Chroma.from_documents(
                documents=chunks, 
                embedding=self.embeddings, 
                persist_directory=self.db_path
            )
            print("Ingestion complete.")

    def analyze_scenario(self, scenario_description: str) -> Dict[str, Any]:
        """
        Consults the "Brain" (LLM + VectorDB).
        """
        if not self.vector_store:
            return {
                "decision_summary": "Legal Advisor offline or empty DB. Analysis skipped.",
                "risk_level": "UNKNOWN",
                "applied_law_bases": []
            }
        
        try:
            from langchain_openai import ChatOpenAI
            from langchain.prompts import PromptTemplate
            from langchain.chains import RetrievalQA
        except ImportError:
            try:
                from langchain_core.prompts import PromptTemplate
                from langchain.chains import RetrievalQA
                from langchain_openai import ChatOpenAI
            except ImportError:
                 return {"error": "LangChain modules missing for analysis."}

        # Retrieval
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        prompt_template = """
        You are a Senior Tax Lawyer.
        Context:
        {context}
        
        Question: {question}
        
        Return JSON:
        {{
            "decision_summary": "...",
            "risk_level": "LOW/MEDIUM/HIGH",
            "confidence_score": 0.95,
            "applied_law_bases": ["Lei X"]
        }}
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        try:
            print("Consulting AI Advisor...")
            result_str = qa_chain.run(scenario_description)
            clean_json = result_str.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            return {"error": f"Failed to generate analysis: {e}"}

    def log_decision(self, fiscal_data_id: str, analysis_result: Dict[str, Any]):
        db_host = os.getenv("DB_HOST", "localhost")
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "postgres")
        db_name = os.getenv("DB_NAME", "gt_ia_db")
        
        try:
            conn = psycopg2.connect(user=db_user, password=db_pass, host=db_host, dbname=db_name)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            query = """INSERT INTO ai_decision_logs (fiscal_data_id, decision_summary, risk_level, confidence_score, applied_law_bases) VALUES (%s, %s, %s, %s, %s)"""
            cur.execute(query, (
                fiscal_data_id,
                analysis_result.get('decision_summary', 'N/A'),
                analysis_result.get('risk_level', 'HIGH'),
                analysis_result.get('confidence_score', 0.0),
                analysis_result.get('applied_law_bases', [])
            ))
            cur.close()
            conn.close()
        except Exception:
            pass # logging fail shouldn't stop flow

if __name__ == "__main__":
    adv = LegalAdvisor()
    print("LegalAdvisor Initialized.")
