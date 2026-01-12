import os
import shutil
from typing import List, Dict, Any
import json
from decimal import Decimal

# LangChain & ChromaDB
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# DB Connection for logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

class LegalAdvisor:
    """
    GT-IA Module: Legal Intelligence (Bloco 3).
    Responsible for RAG (Retrieval-Augmented Generation) to provide
    legal basis for tax decisions.
    """

    def __init__(self, doc_path: str = "./legal_docs", db_path: str = "./chroma_db"):
        self.doc_path = doc_path
        self.db_path = db_path
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = None
        
        # Ensure legal_docs folder exists
        if not os.path.exists(self.doc_path):
            os.makedirs(self.doc_path)
            print(f"Directory '{self.doc_path}' created. Place PDF laws here.")

        # Initialize or Load Vector Store
        self._initialize_vector_store()
        
    def _initialize_vector_store(self):
        """Loads existing vector store or initializes a new one if empty."""
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            print("Loading existing Vector Store...")
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        else:
            print("Vector Store not found. Waiting for documents to ingest.")
            # Can be initialized empty, but usually we want to ingest first.

    def ingest_documents(self):
        """Reads PDFs from legal_docs, splits them, and creates embeddings."""
        print(f"Scanning '{self.doc_path}' for PDFs...")
        loader = PyPDFDirectoryLoader(self.doc_path)
        documents = loader.load()

        if not documents:
            print("No documents found to ingest.")
            return

        print(f"Loaded {len(documents)} document pages. Splitting...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        print(f"Creating embeddings for {len(chunks)} chunks. This may take a moment...")
        # Create and persist ChromaDB
        self.vector_store = Chroma.from_documents(
            documents=chunks, 
            embedding=self.embeddings, 
            persist_directory=self.db_path
        )
        print("Ingestion complete. Database persisted.")

    def analyze_scenario(self, scenario_description: str) -> Dict[str, Any]:
        """
        Consults the "Brain" (LLM + VectorDB) to analyze a fiscal scenario.
        
        Args:
           scenario_description: Text describing the situation (e.g. "Is there credit for PIS on electricity?")
           
        Returns:
           Dict with 'summary', 'risk', 'citations'.
        """
        if not self.vector_store:
            return {"error": "Vector Store not initialized. Run ingest_documents() first."}

        # Retrieval
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Generation Prompt
        prompt_template = """
        You are a Senior Tax Lawyer and Specialist in Brazilian Tax Law (Direito Tributário Brasileiro).
        Use the following pieces of context (laws, court decisions) to answer the user's question.
        
        Context:
        {context}
        
        Question: {question}
        
        Instructions:
        1. Identify the legal basis (laws, articles, Súmulas STJ/STF).
        2. Determine the risk level (LOW, MEDIUM, HIGH) for taking credit or not paying.
        3. Explain the reasoning clearly.
        4. Return the output strictly in the following JSON format:
        {{
            "decision_summary": "Your explanation here...",
            "risk_level": "LOW/MEDIUM/HIGH",
            "confidence_score": 0.95,
            "applied_law_bases": ["Lei X, Art Y", "Súmula Z"]
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
            result_json_str = qa_chain.run(scenario_description)
            # Parse JSON from string response (LLM usually wraps in markdown code blocks, simplistic stripping here)
            clean_json = result_json_str.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            return {"error": f"Failed to generate analysis: {e}"}

    def log_decision(self, fiscal_data_id: str, analysis_result: Dict[str, Any]):
        """Logs the AI decision to the PostgreSQL database."""
        db_host = os.getenv("DB_HOST", "localhost")
        db_name = os.getenv("DB_NAME", "gt_ia_db")
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "postgres")
        
        try:
            conn = psycopg2.connect(
                user=db_user, password=db_pass, host=db_host, dbname=db_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            query = """
                INSERT INTO ai_decision_logs 
                (fiscal_data_id, decision_summary, risk_level, confidence_score, applied_law_bases)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cur.execute(query, (
                fiscal_data_id,
                analysis_result.get('decision_summary', 'Error in analysis'),
                analysis_result.get('risk_level', 'HIGH'),
                analysis_result.get('confidence_score', 0.0),
                analysis_result.get('applied_law_bases', [])
            ))
            
            print(f"Decision logged for Fiscal Data ID: {fiscal_data_id}")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Failed to log decision: {e}")

# Example Usage
if __name__ == "__main__":
    # Ensure you have OPENAI_API_KEY in .env
    advisor = LegalAdvisor()
    
    # 1. Ingest (Only needs to run once or when docs change)
    # advisor.ingest_documents()
    
    # 2. Query
    scenario = "Posso tomar crédito de PIS e COFINS sobre despesas com energia elétrica na indústria?"
    result = advisor.analyze_scenario(scenario)
    
    print("\n--- Parecer Jurídico IA ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
