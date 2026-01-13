import os
from decimal import Decimal
from typing import List, Dict, Any
from fpdf import FPDF
from datetime import datetime

# Impor Modules
from tax_engine import TaxEngine
from legal_advisor import LegalAdvisor

class CreditRecoveryAgent:
    """
    Agente de Recuperação de Créditos (GT-IA Bloco 4).
    Analisa histórico fiscal e gera matriz de oportunidades com fundamentação legal.
    """

    def __init__(self):
        self.tax_engine = TaxEngine()
        # Initialize LegalAdvisor. Note: It might need the vector store to be ready.
        try:
            self.legal_advisor = LegalAdvisor()
        except Exception as e:
            print(f"Warning: LegalAdvisor could not be initialized fully (check API Key/Env): {e}")
            self.legal_advisor = None

    def _format_currency(self, val: Any) -> str:
        """Helper to format currency for PDF."""
        value = Decimal(str(val))
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def analyze_credits(self, history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa uma série de dados mensais para encontrar créditos.
        
        Args:
            history_data: Lista de dicts com 'period', 'paid_amount', 'paid_regime', e dados fiscais.
        """
        opportunities = []
        total_potential_savings = Decimal("0.00")
        
        for month_data in history_data:
            period = month_data.get('period', 'Unknown')
            paid_amount = Decimal(str(month_data.get('paid_amount', 0)))
            used_regime = month_data.get('paid_regime', 'LUCRO_PRESUMIDO') # O que a empresa usou
            
            # 1. Simular o cenário ideal para este mês
            simulation_input = {
                'revenue': month_data.get('revenue', 0),
                'payroll': month_data.get('payroll', 0),
                'costs': month_data.get('costs', 0) # Could be dict or total
            }
            
            sim_result = self.tax_engine.simulate_regimes(simulation_input)
            
            best_regime = sim_result['recommendation']
            optimal_amount = Decimal(sim_result['results'][best_regime])
            
            # 2. Verificar se houve pagamento a maior (Erro de Regime)
            # Se o regime usado não foi o melhor E o valor pago > valor ideal
            if used_regime != best_regime and paid_amount > optimal_amount:
                savings = paid_amount - optimal_amount
                total_potential_savings += savings
                
                opportunities.append({
                    'type': 'REGIME_MISMATCH',
                    'period': period,
                    'description': f"Empresa pagou pelo {used_regime}, mas {best_regime} seria mais econômico.",
                    'value': savings,
                    'legal_basis': "Planejamento Tributário / Elisão Fiscal Lícita",
                    'risk': 'LOW'
                })
                
            # 3. Analisar Créditos Específicos (ex: PIS/COFINS no Lucro Real)
            # Se a empresa já está no Lucro Real (ou o ideal é Real), verifique se tomou todos os créditos
            if best_regime == 'Lucro Real' and 'credits_found_lr' in sim_result:
                credits_lr = Decimal(sim_result['credits_found_lr'])
                
                # Supondo que a empresa não aproveitou 100% desses créditos (simulação)
                # Na prática, precisaria do dado 'credits_taken' no input
                credits_opportunity = credits_lr # MVP assumption: finding hidden credits
                
                if credits_opportunity > 0:
                     # Ask Legal Advisor about specific credits if detailed costs provided
                    costs_input = month_data.get('costs', {})
                    legal_note = "Lei 10.637/02 e 10.833/03 (Princípio da Não-Cumulatividade)"
                    risk_level = "LOW"
                    
                    if isinstance(costs_input, dict) and self.legal_advisor:
                         # Example: check electricity or inputs if strictly needed
                         if 'energia_eletrica' in costs_input:
                             query = "Posso tomar crédito de PIS/COFINS sobre energia elétrica na produção?"
                             # Keeping LLM calls minimal for MVP speed, or uncomment below:
                             # advisor_res = self.legal_advisor.analyze_scenario(query) 
                             # legal_note = advisor_res.get('applied_law_bases', [legal_note])[0]
                             # risk_level = advisor_res.get('risk_level', 'LOW')
                             pass

                    total_potential_savings += credits_opportunity
                    opportunities.append({
                        'type': 'MISSED_CREDITS',
                        'period': period,
                        'description': "Créditos de PIS/COFINS não aproveitados sobre insumos/custos.",
                        'value': credits_opportunity,
                        'legal_basis': legal_note,
                        'risk': risk_level
                    })

        return {
            'total_savings': total_potential_savings,
            'opportunities': opportunities
        }

    def generate_report(self, analysis_result: Dict[str, Any], filename="relatorio_recuperacao.pdf"):
        """Gera PDF com os resultados."""
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Relatorio de Recuperacao de Creditos - GT-IA", ln=True, align='C')
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Resumo Executivo", ln=True)
        pdf.set_font("Arial", '', 11)
        
        savings = self._format_currency(analysis_result['total_savings'])
        pdf.cell(0, 10, f"Potencial Total de Economia Identificado: {savings}", ln=True)
        pdf.ln(5)
        
        # Table Header
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 10, "Periodo", 1, 0, 'C', 1)
        pdf.cell(80, 10, "Descricao", 1, 0, 'C', 1)
        pdf.cell(35, 10, "Valor", 1, 0, 'C', 1)
        pdf.cell(25, 10, "Risco", 1, 0, 'C', 1)
        pdf.ln()
        
        # Table Rows
        pdf.set_font("Arial", '', 9)
        for opp in analysis_result['opportunities']:
            # Multiline handling for description is tricky in basic FPDF, truncating for MVP
            desc = (opp['description'][:40] + '...') if len(opp['description']) > 40 else opp['description']
            
            pdf.cell(30, 10, str(opp['period']), 1)
            pdf.cell(80, 10, desc, 1)
            pdf.cell(35, 10, self._format_currency(opp['value']), 1)
            pdf.cell(25, 10, str(opp['risk']), 1)
            pdf.ln()

        # Footer / Legal Disclaimer
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 8)
        pdf.multi_cell(0, 5, "Este relatorio e gerado automaticamente por Inteligencia Artificial (GT-IA). As informacoes devem ser validadas por um consultor juridico antes de qualquer compensacao tributaria.")
        
        try:
            pdf.output(filename)
            print(f"Relatório gerado com sucesso: {filename}")
        except Exception as e:
            print(f"Erro ao salvar PDF: {e}")

# Exemplo de Uso
if __name__ == "__main__":
    agent = CreditRecoveryAgent()
    
    # Dados Históricos Simulados (Empresa operando no Lucro Presumido mas com alta folha/custos)
    mock_history = [
        {
            'period': '01/2025',
            'paid_amount': 25000.00, # Pagou isso no Presumido (simulado)
            'paid_regime': 'LUCRO_PRESUMIDO',
            'revenue': 200000,
            'payroll': 50000,
            'costs': {'energia_eletrica': 5000, 'insumos_diretos': 80000}
        },
        {
            'period': '02/2025',
            'paid_amount': 26000.00,
            'paid_regime': 'LUCRO_PRESUMIDO',
            'revenue': 210000,
            'payroll': 55000,
            'costs': {'energia_eletrica': 6000, 'insumos_diretos': 90000}
        }
    ]
    
    print("--- Iniciando Análise de Recuperação ---")
    analysis = agent.analyze_credits(mock_history)
    
    print(f"Economia Total: {analysis['total_savings']}")
    agent.generate_report(analysis)
