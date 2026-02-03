import os
import sys
import shutil
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import uuid

# FastAPI & Pydantic
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response

# ... (omitted lines)


from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import pandas as pd
import io
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Adjust Path to import modules from 'py' directory
sys.path.append(os.path.join(os.getcwd(), 'py'))

# Import Project Modules
# Note: credit_recovery.py inside py/ might import tax_engine using standard import.
# Adding 'py' to sys.path helps resolve this.
try:
    from credit_recovery import CreditRecoveryAgent
    from tax_engine import TaxEngine
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Fallback/Debug note: Ensure running from project root

# --- Configurations ---
load_dotenv()
API_KEY_SECRET = os.getenv("GT_IA_API_KEY", "minha_chave_secreta_padrao")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "gt_ia_db")

app = FastAPI(
    title="GT-IA Tax Intelligence API",
    description="API para análise tributária, recuperação de créditos e auditoria automatizada.",
    version="1.0.0"
)

# --- CORS ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://meusiteatual.com.br", # Adicione o domínio do seu site aqui
    "http://127.0.0.1:5500", # VS Code Live Server
    "http://localhost:5500", # VS Code Live Server
    "*" # Permissivo para dev/teste
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files (Frontend) ---
# Mount the 'frontend' directory at the root for static access (styles, js)
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

# --- Root Redirect ---
@app.get("/")
async def read_root():
    return FileResponse('frontend/index.html')

@app.get("/dashboard.html")
async def read_dashboard():
    return FileResponse('frontend/dashboard.html')

# --- Pydantic Models for Input ---

class CompanyInput(BaseModel):
    name: str
    cnpj: str
    activity_code: str # CNAE
    regime: str # e.g. "LUCRO_PRESUMIDO"

class DetailedCosts(BaseModel):
    energia_eletrica: Optional[float] = 0.0
    insumos_diretos: Optional[float] = 0.0
    aluguel_predios: Optional[float] = 0.0
    maquinas_equipamentos: Optional[float] = 0.0
    outros: Optional[float] = 0.0

class FiscalMonth(BaseModel):
    period: str # "MM/YYYY"
    revenue: float
    payroll: float
    paid_amount: float
    paid_regime: str
    costs: Optional[DetailedCosts] = None

class AnalysisRequest(BaseModel):
    company: CompanyInput
    history: List[FiscalMonth]

# --- Security Dependency ---
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# --- Helper DB Functions ---
def get_db_connection():
    try:
        conn = psycopg2.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, dbname=DB_NAME)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None

def persist_company(conn, comp: CompanyInput):
    cur = conn.cursor()
    query = """
        INSERT INTO companies (id, cnpj, name, regime, activity_code)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (cnpj) DO UPDATE 
        SET name = EXCLUDED.name, regime = EXCLUDED.regime, updated_at = NOW()
        RETURNING id;
    """
    comp_id = str(uuid.uuid4())
    # On Conflict we ideally want to get the existing ID, currently the query might return new ID or update.
    # Simplified logic:
    try:
        cur.execute(query, (comp_id, comp.cnpj, comp.name, comp.regime, comp.activity_code))
        result = cur.fetchone()
        comp_id = result[0]
    except Exception as e:
        print(f"Error persisting company: {e}")
    cur.close()
    return comp_id

def persist_fiscal_data(conn, company_id: str, month_data: FiscalMonth):
    cur = conn.cursor()
    # Corrected columns based on schema.sql
    query = """
        INSERT INTO fiscal_data (id, company_id, period_date, revenue_amount, payroll_amount, tax_withholding_amount, operational_costs_amount)
        VALUES (%s, %s, TO_DATE(%s, 'MM/YYYY'), %s, %s, %s, %s)
        RETURNING id;
    """
    data_id = str(uuid.uuid4())
    # costs_json logic removed -> mapped to single operational_costs_amount for now or specific columns if schema had them.
    # Schema has operational_costs_amount. Let's sum detailed costs.
    op_costs = 0.0
    if month_data.costs:
        op_costs = sum([
            month_data.costs.energia_eletrica or 0,
            month_data.costs.insumos_diretos or 0,
            month_data.costs.aluguel_predios or 0,
            month_data.costs.maquinas_equipamentos or 0,
            month_data.costs.outros or 0
        ])

    try:
        cur.execute(query, (
            data_id, company_id, month_data.period, 
            month_data.revenue, month_data.payroll, month_data.paid_amount, 
            op_costs
        ))
    except Exception as e:
        print(f"Error persisting fiscal data: {e}")
        # Fallback for dev if DB is strict: might fail.
        
    cur.close()
    return data_id

# --- Endpoints ---

@app.get("/status")
def get_status():
    return {
        "status": "online",
        "service": "GT-IA API",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analise-completa", dependencies=[Depends(verify_api_key)])
def run_full_analysis(request: AnalysisRequest):
    """
    Recebe dados da empresa e histórico fiscal.
    Salva no banco.
    Executa análises (Tax Engine + RAG + Credit Recovery).
    Gera PDF.
    Retorna resumo e link do PDF.
    """
    
    # 1. Persist Data
    conn = get_db_connection()
    last_data_id = None
    if conn:
        company_id = persist_company(conn, request.company)
        for month in request.history:
            last_data_id = persist_fiscal_data(conn, company_id, month)
        conn.close()
    else:
        print("Warning: Running without DB persistence (Connection failed).")

    # 2. Prepare Data for CreditRecoveryAgent
    history_dicts = []
    for h in request.history:
        costs_dict = h.costs.dict() if h.costs else {}
        history_dicts.append({
            'period': h.period,
            'paid_amount': h.paid_amount,
            'paid_regime': h.paid_regime,
            'revenue': h.revenue,
            'payroll': h.payroll,
            'costs': costs_dict
        })

    # 3. Execute Analysis
    agent = CreditRecoveryAgent()
    analysis_result = agent.analyze_credits(history_dicts)
    
    # 4. Generate PDF
    pdf_filename = "relatorio_recuperacao.pdf" 
    comp_info = {
        "name": request.company.name,
        "cnpj": request.company.cnpj
    }
    agent.generate_report(analysis_result, company_info=comp_info, filename=pdf_filename)
    
    # 5. Log Decision (Dashboard)
    if last_data_id:
        try:
            from legal_advisor import LegalAdvisor
            advisor = LegalAdvisor()
            advisor.log_decision(last_data_id, {}, float(analysis_result['total_savings']))
        except Exception as e:
            print(f"Failed to log decision: {e}")

    # Check if created
    if not os.path.exists(pdf_filename):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")

    return {
        "message": "Análise concluída com sucesso.",
        "company": request.company.name,
        "total_savings_potential": f"R$ {analysis_result['total_savings']:,.2f}",
        "opportunities_count": len(analysis_result['opportunities']),
        "download_link": f"/download-report" 
    }

@app.get("/dashboard-data")
def get_dashboard_data():
    """
    Retorna métricas para o Dashboard:
    - Total Economia
    - Empresas Auditadas
    - Distribuição de Risco
    - Histórico Recente
    """
    conn = get_db_connection()
    if not conn:
        return {"error": "DB Connection Failed"}
    
    cur = conn.cursor()
    
    # 1. KPIs
    cur.execute("SELECT COUNT(*) FROM companies")
    total_companies = cur.fetchone()[0]
    
    cur.execute("SELECT SUM(estimated_savings) FROM ai_decision_logs")
    total_savings = cur.fetchone()[0] or 0.0
    
    # 2. Risk Distribution
    cur.execute("SELECT risk_level, COUNT(*) FROM ai_decision_logs GROUP BY risk_level")
    risks = {row[0]: row[1] for row in cur.fetchall()}
    
    # 3. Recent Audits
    query_history = """
        SELECT c.name, a.created_at, a.estimated_savings, a.risk_level
        FROM ai_decision_logs a
        JOIN fiscal_data f ON a.fiscal_data_id = f.id
        JOIN companies c ON f.company_id = c.id
        ORDER BY a.created_at DESC
        LIMIT 5
    """
    cur.execute(query_history)
    recent_audits = [
        {
            "company": row[0],
            "date": row[1].strftime("%d/%m/%Y"),
            "savings": float(row[2] or 0),
            "risk": row[3]
        }
        for row in cur.fetchall()
    ]
    
    cur.close()
    conn.close()
    
    return {
        "kpis": {
            "companies": total_companies,
            "savings": total_savings,
            "risk_high": risks.get('HIGH', 0),
            "risk_low": risks.get('LOW', 0)
        },
        "recent_audits": recent_audits
    }

class ChatRequest(BaseModel):
    question: str
    context_data: Optional[Dict[str, Any]] = None

@app.post("/ask-legal", dependencies=[Depends(verify_api_key)])
def ask_legal_advisor(request: ChatRequest):
    """
    Endpoint para Chat Jurídico (RAG).
    """
    try:
        from legal_advisor import LegalAdvisor
        advisor = LegalAdvisor()
        
        # Ingest if empty (Lazy Check)
        if not advisor.vector_store:
             print("Vector Store empty, attempting to ingest...")
             advisor.ingest_documents() # This might take time, ideal for async, but ok for MVP
             advisor._initialize_vector_store()

        response = advisor.analyze_scenario(request.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-csv", dependencies=[Depends(verify_api_key)])
async def upload_csv(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    cnpj: str = Form(...),
    regime: str = Form(...),
    activity_code: str = Form(...)
):
    """
    Processa um arquivo CSV com dados fiscais em massa e gera o relatório.
    """
# ... (upload_csv implementation remains same until next chunk)
# Inserting Chat endpoint BEFORE upload_csv or AFTER. Let's put it after run_full_analysis for logical grouping.

# --- Reformulating strategy to avoid huge blocks in replace ---
# I will append the new class and endpoint at the end of the file or before upload_csv if easier.
# Let's verify existing file content again.

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie um arquivo CSV.")
    
    try:
        content = await file.read()
        # Tenta ler com separador ';' (padrão Excel BR) ou ','
        try:
            df = pd.read_csv(io.BytesIO(content), sep=';')
            if 'Faturamento Total' not in df.columns and 'faturamento' in df.columns:
                 df = pd.read_csv(io.BytesIO(content), sep=',')
        except:
             df = pd.read_csv(io.BytesIO(content), sep=',')

        # Mapeamento de Colunas (Nome Amigável -> Nome Interno)
        column_map = {
            'Periodo': 'periodo',
            'Periodo (MM/AAAA)': 'periodo',
            'Faturamento': 'faturamento',
            'Faturamento Total': 'faturamento',
            'Folha': 'folha',
            'Custo Folha Pagamento': 'folha',
            'Impostos Pagos': 'impostos_pagos',
            'Regime Pagto': 'regime_pagto',
            'Regime Tributario': 'regime_pagto',
            'Custo Energia': 'custo_energia',
            'Custo Insumos': 'custo_insumos',
            'Custo Aluguel': 'custo_aluguel',
            'Custo Aluguel Predios': 'custo_aluguel'
        }
        df.rename(columns=column_map, inplace=True)
        
        # Validar colunas minimas (agora usando nomes internos normalizados)
        required_cols = ['periodo', 'faturamento', 'folha', 'impostos_pagos']
        missing = [col for col in required_cols if col not in df.columns]
        if missing and not all(col in df.columns for col in required_cols):
             raise HTTPException(status_code=400, detail=f"CSV precisa das colunas: {required_cols}")

        # Normalizar para History Format
        history_dicts = []
        for _, row in df.iterrows():
            costs = {}
            if 'custo_energia' in df.columns: costs['energia_eletrica'] = float(str(row['custo_energia']).replace(',', '.')) if pd.notna(row['custo_energia']) else 0.0
            if 'custo_insumos' in df.columns: costs['insumos_diretos'] = float(str(row['custo_insumos']).replace(',', '.')) if pd.notna(row['custo_insumos']) else 0.0
            if 'custo_aluguel' in df.columns: costs['aluguel_predios'] = float(str(row['custo_aluguel']).replace(',', '.')) if pd.notna(row['custo_aluguel']) else 0.0

            def parse_float(val):
                if pd.isna(val) or val == '': return 0.0
                if isinstance(val, (float, int)): return float(val)
                s = str(val).replace('R$', '').replace(' ', '')
                # Handle 1.000,00 -> 1000.00
                if ',' in s and '.' in s:
                    s = s.replace('.', '').replace(',', '.')
                elif ',' in s:
                    s = s.replace(',', '.')
                return float(s)

            history_dicts.append({
                'period': str(row['periodo']),
                'paid_amount': parse_float(row['impostos_pagos']),
                'paid_regime': str(row.get('regime_pagto', regime)), 
                'revenue': parse_float(row['faturamento']),
                'payroll': parse_float(row['folha']),
                'costs': costs
            })
            
        # 1. Persist Data (Simplified for MVP)
        conn = get_db_connection()
        last_data_id = None
        if conn:
            comp_obj = CompanyInput(name=company_name, cnpj=cnpj, regime=regime, activity_code=activity_code)
            company_id = persist_company(conn, comp_obj)
            for h_dict in history_dicts:
                try:
                    c_model = DetailedCosts(**h_dict['costs'])
                    fm = FiscalMonth(
                        period=h_dict['period'], revenue=h_dict['revenue'], payroll=h_dict['payroll'],
                        paid_amount=h_dict['paid_amount'], paid_regime=h_dict['paid_regime'], costs=c_model
                    )
                    last_data_id = persist_fiscal_data(conn, company_id, fm)
                except Exception as e:
                    print(f"Skipped persisting row: {e}")
            conn.close()

        # 2. Execute Analysis
        agent = CreditRecoveryAgent()
        analysis_result = agent.analyze_credits(history_dicts)
        
        # 3. Generate PDF
        pdf_filename = "relatorio_recuperacao.pdf" 
        comp_info = {
            "name": company_name,
            "cnpj": cnpj
        }
        agent.generate_report(analysis_result, company_info=comp_info, filename=pdf_filename)
        
        # 4. Log Decision (Dashboard)
        if last_data_id:
            try:
                from legal_advisor import LegalAdvisor
                advisor = LegalAdvisor()
                advisor.log_decision(last_data_id, {}, float(analysis_result['total_savings']))
            except Exception as e:
                print(f"Failed to log decision: {e}")

        return {
            "message": "Análise em massa concluída.",
            "company": company_name,
            "total_savings_potential": f"R$ {analysis_result['total_savings']:,.2f}",
            "opportunities_count": len(analysis_result['opportunities']),
            "download_link": "/download-report" 
        }

    except Exception as e:
        print(f"CSV Process Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-template")
def download_template():
    # CSV Otimizado para Excel BR (Separador ; e Cabeçalhos Claros)
    # \ufeff é o BOM (Byte Order Mark) para forçar o Excel a abrir como UTF-8
    csv_content = """\ufeffPeriodo (MM/AAAA);Faturamento Total;Custo Folha Pagamento;Impostos Pagos;Regime Tributario;Custo Energia;Custo Insumos;Custo Aluguel
01/2024;100000.00;20000.00;5000.00;LUCRO_PRESUMIDO;1000.00;30000.00;2000.00
02/2024;120000.00;22000.00;6000.00;LUCRO_PRESUMIDO;1100.00;35000.00;2000.00"""
    
    return Response(content=csv_content, media_type='text/csv', headers={"Content-Disposition": "attachment; filename=modelo_auditoria_gt_ia.csv"})

@app.get("/download-report")
def download_report():
    file_path = "relatorio_recuperacao.pdf"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename="Relatorio_GT_IA.pdf")
    return {"error": "Report not found. Run analysis first."}

if __name__ == "__main__":
    import uvicorn
    # Hot reload enabled for dev
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
