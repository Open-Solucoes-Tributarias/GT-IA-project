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
    query = """
        INSERT INTO fiscal_data (id, company_id, period, revenue, payroll, taxes_paid, other_costs)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    data_id = str(uuid.uuid4())
    costs_json = json.dumps(month_data.costs.dict()) if month_data.costs else "{}"
    
    cur.execute(query, (
        data_id, company_id, month_data.period, 
        month_data.revenue, month_data.payroll, month_data.paid_amount, 
        costs_json
    ))
    # Note: we are not strictly checking for duplicates on period here for speed/MVP
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
            'Periodo (MM/AAAA)': 'periodo',
            'Faturamento Total': 'faturamento',
            'Custo Folha Pagamento': 'folha',
            'Impostos Pagos': 'impostos_pagos',
            'Regime Tributario': 'regime_pagto',
            'Custo Energia': 'custo_energia',
            'Custo Insumos': 'custo_insumos', 
            'Custo Aluguel': 'custo_aluguel'
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
                if isinstance(val, (float, int)): return float(val)
                return float(str(val).replace(',', '.'))

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
                    persist_fiscal_data(conn, company_id, fm)
                except Exception as e:
                    print(f"Skipped persisting row: {e}")
            conn.close()

        # 2. Execute Analysis
        agent = CreditRecoveryAgent()
        analysis_result = agent.analyze_credits(history_dicts)
        
        # 3. Generate PDF
        pdf_filename = "relatorio_recuperacao.pdf" 
        agent.generate_report(analysis_result, filename=pdf_filename)
        
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
