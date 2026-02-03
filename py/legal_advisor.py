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
            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            print("LangChain loaders missing.")
            return

        print(f"Scanning '{self.doc_path}' for PDFs...")
        
        documents = []
        if not os.path.exists(self.doc_path):
            print("Docs folder not found.")
            return

        for filename in os.listdir(self.doc_path):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(self.doc_path, filename)
                try:
                    print(f"Loading {filename}...")
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

        if not documents:
            print("No valid documents found to ingest.")
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
        try:
            if not self.vector_store:
                return {
                    "decision_summary": "Legal Advisor offline or empty DB. Analysis skipped.",
                    "risk_level": "UNKNOWN",
                    "applied_law_bases": []
                }
            
            result_str = ""

            # Try Standard LangChain RAG
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import PromptTemplate
                from langchain.chains import RetrievalQA
                
                # ... (Standard Implementation)
                llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                prompt_template = """You are a Senior Tax Lawyer. Context: {context}. Question: {question}. Return JSON: {{ "decision_summary": "...", "risk_level": "LOW/MEDIUM/HIGH", "confidence_score": 0.95, "applied_law_bases": ["Lei X"] }}"""
                PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
                qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, chain_type_kwargs={"prompt": PROMPT})
                
                print("Consulting AI Advisor (LangChain)...")
                result_str = qa_chain.run(scenario_description)
                
            except ImportError as e:
                # Fallback: Manual RAG (Direct OpenAI + Chroma)
                print(f"LangChain Chains failed ({e}). Switching to Manual RAG.")
                try:
                    import openai
                    client = openai.OpenAI()
                    
                    # 1. Retrieve
                    docs = self.vector_store.similarity_search(scenario_description, k=3)
                    context_text = "\n\n".join([d.page_content for d in docs])
                    
                    # 2. Generate
                    sys_prompt = "You are a Senior Tax Lawyer. Return JSON with decision_summary, risk_level, confidence_score, applied_law_bases."
                    user_prompt = f"Context:\n{context_text}\n\nQuestion: {scenario_description}"
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0
                    )
                    result_str = response.choices[0].message.content
                    
                except Exception as ex:
                    print(f"Manual RAG Failed: {ex}")
                    return {"error": f"Erro Crítico (Manual RAG): {ex}"}
            except Exception as e:
                 print(f"LangChain Execution Failed: {e}")
                 return {"error": f"Erro Crítico (LangChain): {e}"}

            # Parse JSON (Common for both methods)
            try:
                print(f"LLM Raw Output: {result_str}")
                clean_json = result_str.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                return parsed
            except Exception as e:
                return {"decision_summary": f"Erro no Parse: {result_str}", "risk_level": "HIGH"}

        except Exception as global_e:
            import traceback
            print(f"CRITICAL UNHANDLED ERROR: {traceback.format_exc()}")
            return {"error": f"Erro Interno Fatal: {str(global_e)}"}

    def log_decision(self, fiscal_data_id: str, analysis_result: Dict[str, Any], savings: float = 0.0):
        db_host = os.getenv("DB_HOST", "localhost")
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "postgres")
        db_name = os.getenv("DB_NAME", "gt_ia_db")
        
        try:
            conn = psycopg2.connect(user=db_user, password=db_pass, host=db_host, dbname=db_name)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            query = """INSERT INTO ai_decision_logs (fiscal_data_id, decision_summary, risk_level, confidence_score, applied_law_bases, estimated_savings) VALUES (%s, %s, %s, %s, %s, %s)"""
            cur.execute(query, (
                fiscal_data_id,
                analysis_result.get('decision_summary', 'Análise Automática'),
                analysis_result.get('risk_level', 'LOW'), # Default to LOW if analysis didn't run fully
                analysis_result.get('confidence_score', 1.0),
                analysis_result.get('applied_law_bases', []),
                savings
            ))
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Log Decision Error: {e}")
        except Exception:
            pass # logging fail shouldn't stop flow

if __name__ == "__main__":
    adv = LegalAdvisor()
    print("LegalAdvisor Initialized.")
