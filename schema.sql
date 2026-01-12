-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Table: companies (Cadastro de Empresas)
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cnpj VARCHAR(14) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    cnae_primary VARCHAR(10), -- e.g., '6202-3/00'
    tax_regime VARCHAR(50) NOT NULL CHECK (tax_regime IN ('SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', 'LUCRO_REAL')),
    state CHAR(2) NOT NULL,
    city VARCHAR(100) NOT NULL,
    is_public_entity BOOLEAN DEFAULT FALSE, -- Crucial for 'natureza do tomador'
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- 2. Table: fiscal_data (Importação de Dados Fiscais)
CREATE TABLE IF NOT EXISTS fiscal_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    period_date DATE NOT NULL, -- The first day of the month/year this data refers to
    revenue_amount DECIMAL(15, 2) DEFAULT 0.00, -- Faturamento
    payroll_amount DECIMAL(15, 2) DEFAULT 0.00, -- Folha de salários
    pro_labore_amount DECIMAL(15, 2) DEFAULT 0.00,
    tax_withholding_amount DECIMAL(15, 2) DEFAULT 0.00,
    operational_costs_amount DECIMAL(15, 2) DEFAULT 0.00, -- For deductions
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- 3. Table: tax_rules (Regras e Alíquotas)
CREATE TABLE IF NOT EXISTS tax_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('INSS', 'IRRF', 'CSLL', 'PIS', 'COFINS', 'ISS')),
    description TEXT NOT NULL,
    base_legal TEXT, -- Citation of Law, e.g., "Lei 10.833/2003, Art. 30"
    rate DECIMAL(5, 2) NOT NULL, -- Percentage, e.g., 4.65
    conditions JSONB DEFAULT '{}'::jsonb, -- Flexible rules: {"min_revenue": 5000, "regime_exception": ["SIMPLES_NACIONAL"]}
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- 4. Table: ai_decision_logs (Logs de Decisão da IA)
CREATE TABLE IF NOT EXISTS ai_decision_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiscal_data_id UUID NOT NULL REFERENCES fiscal_data(id) ON DELETE CASCADE,
    decision_summary TEXT NOT NULL,
    risk_level VARCHAR(20) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    confidence_score DECIMAL(3, 2), -- 0.00 to 1.00
    applied_law_bases TEXT[], -- Array of strings referencing laws used
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_companies_cnpj ON companies(cnpj);
CREATE INDEX idx_fiscal_data_company_period ON fiscal_data(company_id, period_date);
CREATE INDEX idx_tax_rules_type ON tax_rules(tax_type);
CREATE INDEX idx_ai_logs_fiscal_data ON ai_decision_logs(fiscal_data_id);
