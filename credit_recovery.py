import os
from decimal import Decimal
from typing import List, Dict, Any
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import tempfile

# Import Modules
from tax_engine import TaxEngine
from legal_advisor import LegalAdvisor

# --- Constants & Config ---
COLOR_PRIMARY = (10, 25, 60)      # Azul Marinho Escuro
COLOR_SECONDARY = (100, 100, 100) # Cinza
COLOR_ACCENT = (50, 150, 255)     # Azul Claro
RISK_TRANSLATION = {
    'LOW': 'BAIXO',
    'MEDIUM': 'MÉDIO',
    'HIGH': 'ALTO',
    'UNKNOWN': 'DESCONHECIDO'
}

class PDFReportGenerator(FPDF):
    """
    Classe extendida do FPDF para gerar relatórios premium.
    """
    def header(self):
        if self.page_no() > 1: # Header simples nas páginas internas
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, 'GT-IA | Relatório de Inteligência Fiscal', 0, 0, 'R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        self.set_x(-100)
        self.cell(0, 10, 'Gerado por IA - Validar com Consultor Jurídico', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
        # Linha decorativa
        self.set_fill_color(*COLOR_ACCENT)
        self.cell(20, 1, '', 0, 1, 'L', fill=True) 
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.set_text_color(20)
        self.multi_cell(0, 6, body)
        self.ln()

class CreditRecoveryAgent:
    """
    Agente de Recuperação de Créditos.
    """

    def __init__(self):
        self.tax_engine = TaxEngine()
        try:
            self.legal_advisor = LegalAdvisor()
        except Exception as e:
            print(f"Warning: LegalAdvisor could not be initialized fully: {e}")
            self.legal_advisor = None

    def _format_currency(self, val: Any) -> str:
        value = Decimal(str(val))
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _generate_bar_chart(self, comparison_data):
        """Gera gráfico de barras comparativo."""
        regimes = list(comparison_data.keys())
        values = [float(v) for v in comparison_data.values()]
        
        plt.figure(figsize=(6, 4))
        bars = plt.bar(regimes, values, color=['#4CAF50', '#2196F3', '#FF9800'])
        plt.title('Comparativo Anual de Carga Tributária (R$)', fontsize=10)
        plt.ylabel('Valor Estimado')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp_file.name, dpi=100)
        plt.close()
        return temp_file.name

    def _generate_pie_chart(self, opportunities):
        """Gera gráfico de pizza da distribuição de economias."""
        types = {}
        for opp in opportunities:
            t = opp['type']
            types[t] = types.get(t, 0) + float(opp['value'])
            
        labels = list(types.keys())
        sizes = list(types.values())
        
        plt.figure(figsize=(5, 4))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#FFC107', '#03A9F4', '#E91E63'])
        plt.title('Distribuição da Economia Identificada', fontsize=10)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp_file.name, dpi=100)
        plt.close()
        return temp_file.name

    def analyze_credits(self, history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        opportunities = []
        total_potential_savings = Decimal("0.00")
        
        # Aggregate totals for the Bar Chart interaction
        annual_simulation = None 
        # For simplicity in this method, we'll assume the LAST month's simulation represents the Annual Projection or Aggregate
        # Ideally, we would sum up all months first. 
        
        regime_comparison_totals = {
            'Simples Nacional': Decimal(0),
            'Lucro Presumido': Decimal(0),
            'Lucro Real': Decimal(0)
        }

        for month_data in history_data:
            period = month_data.get('period', 'Unknown')
            paid_amount = Decimal(str(month_data.get('paid_amount', 0)))
            used_regime = month_data.get('paid_regime', 'LUCRO_PRESUMIDO')
            
            sim_input = {
                'revenue': month_data.get('revenue', 0),
                'payroll': month_data.get('payroll', 0),
                'costs': month_data.get('costs', 0)
            }
            
            sim_result = self.tax_engine.simulate_regimes(sim_input)
            
            # Aggregate for charts
            for r, val in sim_result['results'].items():
                regime_comparison_totals[r] += Decimal(val)

            best_regime = sim_result['recommendation']
            optimal_amount = Decimal(sim_result['results'][best_regime])
            
            if used_regime != best_regime and paid_amount > optimal_amount:
                savings = paid_amount - optimal_amount
                total_potential_savings += savings
                opportunities.append({
                    'type': 'REGIME_MISMATCH',
                    'period': period,
                    'description': f"Pagamento no {used_regime}. O {best_regime} seria mais econômico.",
                    'value': savings,
                    'legal_basis': "Planejamento Tributário (Elisão Fiscal)",
                    'risk': 'LOW'
                })
                
            if best_regime == 'Lucro Real' and 'credits_found_lr' in sim_result:
                credits_lr = Decimal(sim_result['credits_found_lr'])
                if credits_lr > 0:
                    legal_note = "Leis 10.637/02 e 10.833/03 (Princípio da Não-Cumulatividade)"
                    risk_level = "LOW"
                    # RAG call omitted for speed in this step, logic remains the same
                    
                    total_potential_savings += credits_lr
                    opportunities.append({
                        'type': 'MISSED_CREDITS',
                        'period': period,
                        'description': f"Créditos de PIS/COFINS (Insumos/Custos) não aproveitados.",
                        'value': credits_lr,
                        'legal_basis': legal_note,
                        'risk': risk_level
                    })

        return {
            'total_savings': total_potential_savings,
            'opportunities': opportunities,
            'regime_comparison': regime_comparison_totals
        }

    def generate_report(self, analysis_result: Dict[str, Any], filename="relatorio_recuperacao.pdf"):
        pdf = PDFReportGenerator()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- CAPA ---
        pdf.add_page()
        pdf.set_fill_color(*COLOR_PRIMARY)
        pdf.rect(0, 0, 210, 297, 'F') # Full dark background
        
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 24)
        pdf.ln(80)
        pdf.cell(0, 10, "Relatório de Inteligência Fiscal", 0, 1, 'C')
        pdf.set_font("Arial", '', 16)
        pdf.cell(0, 10, "GT-IA | Diagnóstico e Recuperação", 0, 1, 'C')
        
        pdf.ln(50)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
        
        # --- PÁGINA 2: Dashboard e Resumo ---
        pdf.add_page()
        pdf.set_text_color(0)
        
        pdf.chapter_title("1. Resumo Executivo")
        
        savings = self._format_currency(analysis_result['total_savings'])
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Potencial Total de Economia: {savings}", 0, 1)
        pdf.ln(5)
        
        # Charts placement
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, "Abaixo, a distribuição visual das análises realizadas:", 0, 1)
        
        # Generate charts
        bar_chart_path = self._generate_bar_chart(analysis_result['regime_comparison'])
        pie_chart_path = self._generate_pie_chart(analysis_result['opportunities'])
        
        pdf.image(bar_chart_path, x=10, y=pdf.get_y() + 5, w=90)
        pdf.image(pie_chart_path, x=110, y=pdf.get_y() + 5, w=90)
        pdf.ln(80) # Move cursor down past images
        
        # Cleanup temp files
        os.remove(bar_chart_path)
        os.remove(pie_chart_path)

        # --- PÁGINA 3: Matriz de Oportunidades ---
        pdf.add_page()
        pdf.chapter_title("2. Matriz de Oportunidades & Fundamentação")
        
        # Table Header
        pdf.set_fill_color(*COLOR_PRIMARY) 
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(25, 8, "Período", 1, 0, 'C', 1)
        pdf.cell(85, 8, "Descrição / Fundamentação", 1, 0, 'L', 1)
        pdf.cell(35, 8, "Valor Estimado", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Risco", 1, 0, 'C', 1)
        pdf.ln()

        # Rows
        pdf.set_text_color(0)
        pdf.set_font("Arial", '', 8)
        
        fill = False
        for opp in analysis_result['opportunities']:
            # Alternating colors row logic
            pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
            
            # Translate Risk
            risk_pt = RISK_TRANSLATION.get(opp['risk'], 'DESCONHECIDO')
            risk_color = (0, 100, 0) if risk_pt == 'BAIXO' else (200, 0, 0) # Green or Red usage just as logic concept, fpdf text color needs setting
            
            pdf.cell(25, 12, str(opp['period']), 1, 0, 'C', fill)
            
            # Multi-line cell handling using simple strings for MVP layout
            desc_text = f"{opp['description']}\nBase: {opp['legal_basis']}"
            
            # Save current pos
            x = pdf.get_x()
            y = pdf.get_y()
            
            pdf.multi_cell(85, 6, desc_text, 1, 'L', fill)
            
            # Reset pos for next cells
            pdf.set_xy(x + 85, y)
            
            pdf.cell(35, 12, self._format_currency(opp['value']), 1, 0, 'C', fill)
            
            pdf.set_text_color(*risk_color)
            pdf.cell(30, 12, risk_pt, 1, 0, 'C', fill)
            pdf.set_text_color(0) # reset
            
            pdf.ln()
            fill = not fill

        try:
            pdf.output(filename)
            print(f"Sucesso: {filename} gerado com layout premium.")
        except Exception as e:
            print(f"Erro ao salvar PDF: {e}")

if __name__ == "__main__":
    agent = CreditRecoveryAgent()
    
    mock_history = [
        {
            'period': '01/2025',
            'paid_amount': 25000.00, 
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
    
    analysis = agent.analyze_credits(mock_history)
    agent.generate_report(analysis)
