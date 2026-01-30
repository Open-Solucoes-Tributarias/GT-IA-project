# GT-IA: Plataforma de Inteligência Artificial para Gestão Tributária

## Visão Geral
O **GT-IA** é uma plataforma avançada desenvolvida para automatizar a auditoria fiscal e a recuperação de créditos tributários. 
Utilizando Inteligência Artificial (RAG - Retrieval-Augmented Generation) e um motor de cálculo tributário robusto, o sistema analisa dados históricos das empresas, simula regimes tributários (Simples, Presumido, Real) e gera relatórios detalhados com fundamentação jurídica.

## Funcionalidades Principais
1.  **Auditoria Fiscal Automatizada:** Análise de faturamento, folha e despesas.
2.  **Simulação de Cenários:** Comparativo entre regimes tributários para identificar a opção mais econômica.
3.  **Recuperação de Créditos:** Identificação de créditos de PIS/COFINS (Insumos) e pagamentos a maior.
4.  **Fundamentação Jurídica (IA):** Consulta automática à legislação e jurisprudência via RAG.
5.  **Relatórios Premium:** Geração de PDFs profissionais com gráficos e matriz de risco.
6.  **API REST:** Integração fácil com plataformas externas (Frontend/Sites Legados).

## Estrutura do Projeto
```
GT-IA/
├── main.py                 # API FastAPI (Entrypoint)
├── requirements.txt        # Dependências do Projeto
├── .env                    # Variáveis de Ambiente (Segurança)
├── logo.png                # Logotipo da Empresa
├── relatorio_recuperacao.pdf # Exemplo de Saída
├── py/                     # Módulos Core
│   ├── tax_engine.py       # Motor de Cálculo
│   ├── legal_advisor.py    # IA & RAG (LangChain/ChromaDB)
│   ├── credit_recovery.py  # Orquestrador & Gerador de Relatórios
│   └── setup_db.py         # Script de Configuração do Banco
└── legal_docs/             # PDFs de Legislação para a IA
```

## Instalação e Configuração

### 1. Pré-requisitos
- Python 3.10+
- PostgreSQL (Instalado e Rodando)

### 2. Instalação das Dependências
```bash
pip install -r requirements.txt
```

### 3. Configuração do Ambiente (.env)
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```env
# Banco de Dados
DB_HOST=localhost
DB_NAME=gt_ia_db
DB_USER=seu_usuario
DB_PASS=sua_senha

# Integração IA
OPENAI_API_KEY=sk-sua-chave-openai

# Segurança da API
GT_IA_API_KEY=minha_chave_secreta_segura
```

### 4. Configuração do Banco de Dados
Execute o script para criar as tabelas necessárias:
```bash
python py/setup_db.py
```

## Executando a Aplicação
Inicie o servidor da API:
```bash
uvicorn main:app --reload
```
A API estará disponível em: `http://localhost:8000`

## Documentação da API

### **1. Verificar Status**
- **Endpoint:** `GET /status`
- **Descrição:** Verifica se o serviço está online.

### **2. Análise Completa (Integração Frontend)**
- **Endpoint:** `POST /analise-completa`
- **Headers:** 
    - `x-api-key`: [Sua Chave Definida no .env]
    - `Content-Type`: `application/json`

**Exemplo de Corpo da Requisição (JSON):**
```json
{
  "company": {
    "name": "Empresa Teste Ltda",
    "cnpj": "12.345.678/0001-90",
    "activity_code": "62000",
    "regime": "LUCRO_PRESUMIDO"
  },
  "history": [
    {
      "period": "01/2024",
      "revenue": 100000.00,
      "payroll": 20000.00,
      "paid_amount": 15000.00,
      "paid_regime": "LUCRO_PRESUMIDO",
      "costs": {
        "energia_eletrica": 5000.00,
        "insumos_diretos": 40000.00
      }
    }
  ]
}
```

**Exemplo de Resposta:**
```json
{
  "message": "Análise concluída com sucesso.",
  "total_savings_potential": "R$ 12.450,00",
  "download_link": "/download-report"
}
```

## Integração com Frontend (Exemplo JavaScript/Fetch)
Para conectar seu site atual ao GT-IA, utilize o seguinte snippet:

```javascript
const API_URL = "http://localhost:8000/analise-completa";
const API_KEY = "minha_chave_secreta_segura";

async function solicitarAnalise(dadosEmpresa) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY
    },
    body: JSON.stringify(dadosEmpresa)
  });

  const resultado = await response.json();
  console.log("Economia Identificada:", resultado.total_savings_potential);
  // Redirecionar para download do PDF
  window.open("http://localhost:8000" + resultado.download_link);
}
```

---
**Desenvolvido pela Equipe GT-IA**
