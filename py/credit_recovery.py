import os
from decimal import Decimal
from typing import List, Dict, Any
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import tempfile

# Import Modules
from py.tax_engine import TaxEngine
from py.legal_advisor import LegalAdvisor

# --- Constants & Config ---
# Paleta de Cores Institucionais
COLOR_PRIMARY = (10, 25, 60)      # Azul Marinho Profundo (Background Capa / Cabeçalhos)
COLOR_SECONDARY = (60, 60, 60)    # Cinza Escuro (Textos)
COLOR_ACCENT = (0, 102, 204)      # Azul Vibrante (Destaques)
COLOR_TABLE_HEADER = (230, 230, 235) # Cinza Claro (Tabelas)

RISK_TRANSLATION = {
    'LOW': 'BAIXO',
    'MEDIUM': 'MÉDIO',
    'HIGH': 'ALTO',
    'UNKNOWN': 'DESCONHECIDO'
}

class PDFReportGenerator(FPDF):
    """
    Motor de Geração de Relatórios PDF Premium GT-IA.
    Estrutura Multi-Página.
    """
    def header(self):
        if self.page_no() > 1: # Header discreto apenas nas páginas internas
            self.set_font('Arial', '', 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, 'GT-IA | Relatório de Diagnóstico Fiscal', 0, 0, 'R')
            self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        self.set_x(-120)
        self.cell(0, 10, 'Gerado por IA - Validar com Consultor Jurídico', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, title, 0, 1, 'L')
        # Linha decorativa fina
        self.set_fill_color(*COLOR_ACCENT)
        self.cell(15, 1.5, '', 0, 1, 'L', fill=True) 
        self.ln(10)

    def draw_cover_page(self, company_name, cnpj, period, consultant_name="IA Advisor"):
        self.add_page()
        
        # Fundo Capa
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, 210, 297, 'F')
        
        # Placeholder Logotipo (Fundo Branco para contraste se tiver logo)
        # Caminho do logo: substituir 'logo.png' pelo arquivo real se existir
        if os.path.exists('logo.png'):
            self.image('logo.png', x=150, y=10, w=40)
        else:
            # Placeholder visual se não tiver imagem
            self.set_fill_color(255, 255, 255)
            self.circle(180, 30, 15, 'F')
        
        self.set_text_color(255, 255, 255)
        self.ln(80)
        
        # Título Principal
        self.set_font("Arial", 'B', 28)
        self.multi_cell(0, 12, "Relatório de Diagnóstico Fiscal\ne Recuperação de Créditos", 0, 'L')
        self.ln(10)
        self.set_font("Arial", '', 14)
        self.cell(0, 10, "Auditoria de Inteligência Artificial", 0, 1, 'L')
        
        # Detalhes do Cliente (Rodapé da Capa)
        self.set_y(220)
        self.set_font("Arial", 'B', 11)
        self.cell(50, 10, "EMPRESA:", 0, 0, 'L')
        self.set_font("Arial", '', 11)
        self.cell(0, 10, f"{company_name} (CNPJ: {cnpj})", 0, 1, 'L')
        
        self.set_font("Arial", 'B', 11)
        self.cell(50, 10, "PERÍODO ANÁLISE:", 0, 0, 'L')
        self.set_font("Arial", '', 11)
        self.cell(0, 10, f"{period}", 0, 1, 'L')
        
        self.set_font("Arial", 'B', 11)
        self.cell(50, 10, "CONSULTOR:", 0, 0, 'L')
        self.set_font("Arial", '', 11)
        self.cell(0, 10, f"{consultant_name}", 0, 1, 'L')

    def section_executive_summary(self, total_savings):
        self.add_page()
        self.chapter_title("1. Sumário Executivo")
        
        # Texto Introdutório
        self.set_font("Arial", '', 11)
        self.set_text_color(*COLOR_SECONDARY)
        intro_text = (
            "Este relatório apresenta o resultado da auditoria fiscal automatizada realizada pelo sistema GT-IA. "
            "Através do cruzamento de dados fiscais (NF-e, Folha, Sped) com a legislação vigente e jurisprudências "
            "atualizadas, identificamos oportunidades de otimização tributária e pontos de risco."
        )
        self.multi_cell(0, 7, intro_text)
        self.ln(10)
        
        # Indicadores de Destaque (Cards Layout)
        # Draw Outlines
        y_cards = self.get_y()
        self.set_draw_color(200, 200, 200)
        self.rect(10, y_cards, 90, 40)  # Card 1 Outline
        self.rect(110, y_cards, 90, 40) # Card 2 Outline
        
        # Card 1 Content (Economia)
        self.set_xy(10, y_cards + 8)
        self.set_font("Arial", '', 10)
        self.set_text_color(100)
        self.cell(90, 5, "Potencial Total de Economia", 0, 1, 'C')
        
        self.set_xy(10, y_cards + 18)
        self.set_font("Arial", 'B', 20)
        self.set_text_color(0, 150, 0) # Green
        self.cell(90, 15, total_savings, 0, 1, 'C')
        
        # Card 2 Content (Riscos)
        self.set_xy(110, y_cards + 8)
        self.set_font("Arial", '', 10)
        self.set_text_color(100)
        self.cell(90, 5, "Pontos de Atenção Críticos", 0, 1, 'C')
        
        self.set_xy(110, y_cards + 18)
        self.set_font("Arial", 'B', 20)
        self.set_text_color(200, 0, 0) # Red
        self.cell(90, 15, "02 Detectados", 0, 1, 'C')
        
        self.set_y(y_cards + 50)

    def section_visual_analysis(self, bar_chart_path, pie_chart_path):
        self.add_page()
        self.chapter_title("2. Análise Visual")
        
        self.set_font("Arial", 'B', 12)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "Distribuição de Oportunidades", 0, 1, 'L')
        
        # Gráfico Pizza (Maior destaque)
        self.image(pie_chart_path, x=40, y=self.get_y(), w=130)
        self.ln(100) 
        
        self.set_font("Arial", 'B', 12)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "Comparativo de Custo Anual (Regimes)", 0, 1, 'L')
        
        # Gráfico Barras
        self.image(bar_chart_path, x=30, y=self.get_y(), w=150)

    def section_detailed_opportunities(self, opportunities, format_currency_func):
        self.add_page()
        self.chapter_title("3. Detalhamento de Oportunidades")
        
        # Table Header
        self.set_fill_color(*COLOR_TABLE_HEADER)
        self.set_text_color(*COLOR_PRIMARY)
        self.set_font("Arial", 'B', 9)
        
        # Widths: Periodo(25), Descricao(80), Valor(35), Risco(30), Base(20) -> Review widths: Total 190
        # Layout ajustado: Periodo(20), Descricao(75), Fundamentacao(45), Valor(30), Risco(20)
        col_w = [20, 75, 45, 30, 20]
        
        self.cell(col_w[0], 10, "Período", 1, 0, 'C', 1)
        self.cell(col_w[1], 10, "Descrição da Oportunidade", 1, 0, 'L', 1)
        self.cell(col_w[2], 10, "Fudamentação Legal", 1, 0, 'L', 1)
        self.cell(col_w[3], 10, "Valor (R$)", 1, 0, 'C', 1)
        self.cell(col_w[4], 10, "Risco", 1, 0, 'C', 1)
        self.ln()
        
        # Rows
        self.set_text_color(0)
        self.set_font("Arial", '', 8)
        
        for opp in opportunities:
            # Calculate height based on description length
            # Simple simulation: 5mm per line approx
            lines = max(len(opp['description']) // 40, len(opp['legal_basis']) // 25, 1) + 1
            row_h = lines * 5
            
            x_start = self.get_x()
            y_start = self.get_y()
            
            # Check page break
            if y_start + row_h > 270:
                self.add_page()
                y_start = self.get_y()
                x_start = self.get_x()
            
            # 1. Periodo
            self.cell(col_w[0], row_h, str(opp['period']), 1, 0, 'C')
            
            # 2. Descricao (MultiCell manual placement)
            x_desc = self.get_x()
            self.multi_cell(col_w[1], 5, opp['description'], 1, 'L')
            self.set_xy(x_desc + col_w[1], y_start) # Restore cursor
            
            # 3. Fundamentacao (MultiCell)
            x_base = self.get_x()
            self.multi_cell(col_w[2], 5, opp['legal_basis'], 1, 'L')
            self.set_xy(x_base + col_w[2], y_start)
            
            # 4. Valor
            self.cell(col_w[3], row_h, format_currency_func(opp['value']), 1, 0, 'R')
            
            # 5. Risco
            risk_pt = RISK_TRANSLATION.get(opp['risk'], 'DESCONHECIDO')
            self.set_text_color(200, 0, 0) if risk_pt == 'ALTO' else self.set_text_color(0, 128, 0) if risk_pt == 'BAIXO' else self.set_text_color(0)
            self.cell(col_w[4], row_h, risk_pt, 1, 0, 'C')
            self.set_text_color(0)
            
            self.ln()
            # Ensure Y is updated to the max height of the row logic manually if needed (FPDF standard flow usually handles next line based on last cell, but MultiCell breaks flow. 
            # For robust MultiCell in row, we usually force Y. 
            # Simplified MVP: force Y to y_start + row_h
            self.set_y(y_start + row_h)

class CreditRecoveryAgent:
    def __init__(self):
        self.tax_engine = TaxEngine()
        self.legal_advisor = None # Lazy loaded if needed

    def _format_currency(self, val: Any) -> str:
        value = Decimal(str(val))
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _generate_bar_chart(self, comparison_data):
        regimes = list(comparison_data.keys())
        values = [float(v) for v in comparison_data.values()]
        
        plt.figure(figsize=(10, 6)) # High Res
        colors = ['#2E7D32', '#1976D2', '#D32F2F'] # Green, Blue, Red
        bars = plt.bar(regimes, values, color=colors, width=0.6)
        
        plt.title('Comparativo de Carga Tributária Anual Estimada', fontsize=12, fontweight='bold', pad=20)
        plt.ylabel('Valor Total (R$)', fontsize=10)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Add values on top
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                     f'R$ {height:,.0f}'.replace(',', '.'),
                     ha='center', va='bottom', fontsize=9)
        
        temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.tight_layout()
        plt.savefig(temp.name, dpi=300) # High DPI
        plt.close()
        return temp.name

    def _generate_pie_chart(self, opportunities):
        types = {}
        for opp in opportunities:
            t = opp['type']
            types[t] = types.get(t, 0) + float(opp['value'])
            
        labels = [f"{k}\n(R$ {v:,.0f})" for k,v in types.items()]
        sizes = list(types.values())
        
        plt.figure(figsize=(8, 6))
        colors = ['#FFC107', '#03A9F4', '#E91E63']
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 10})
        plt.title('Distribuição da Economia por Tipo', fontsize=12, fontweight='bold')
        
        temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp.name, dpi=300)
        plt.close()
        return temp.name

    def analyze_credits(self, history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Reuse logic from previous step, abbreviated for brevity in this file update
        # Assuming same logic as before
        opportunities = []
        total_savings = Decimal("0.00")
        regime_totals = {'Simples Nacional': Decimal(0), 'Lucro Presumido': Decimal(0), 'Lucro Real': Decimal(0)}
        
        for month_data in history_data:
            period = month_data.get('period', 'N/A')
            paid = Decimal(str(month_data.get('paid_amount', 0)))
            used_regime = month_data.get('paid_regime', 'LUCRO_PRESUMIDO')
            
            sim_input = {'revenue': month_data.get('revenue', 0), 'payroll': month_data.get('payroll', 0), 'costs': month_data.get('costs', 0)}
            sim = self.tax_engine.simulate_regimes(sim_input)
            
            for r, v in sim['results'].items():
                regime_totals[r] += Decimal(v)
            
            best = sim['recommendation']
            optimal = Decimal(sim['results'][best])
            
            if used_regime != best and paid > optimal:
                diff = paid - optimal
                total_savings += diff
                opportunities.append({
                    'type': 'REGIME_MISMATCH',
                    'period': period,
                    'description': f"Empresa no {used_regime}. {best} seria ideal.",
                    'value': diff,
                    'legal_basis': "Planejamento Tributário Lícito / Elisão Fiscal (Art. X CTN)",
                    'risk': 'LOW'
                })
                
            if best == 'Lucro Real':
                credits = Decimal(sim.get('credits_found_lr', 0))
                if credits > 0:
                     total_savings += credits
                     opportunities.append({
                        'type': 'CREDITO_INSUMO',
                        'period': period,
                        'description': "Créditos PIS/COFINS sobre Insumos não tomados.",
                        'value': credits,
                        'legal_basis': "Leis 10.637/02 e 10.833/03 (Não-Cumulatividade)",
                        'risk': 'LOW'
                     })
                     
        return {'total_savings': total_savings, 'opportunities': opportunities, 'regime_comparison': regime_totals}

    def generate_report(self, analysis_result, filename="relatorio_recuperacao.pdf"):
        pdf = PDFReportGenerator()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # 1. Capa
        pdf.draw_cover_page(
            company_name="Empresa Exemplo Ltda", 
            cnpj="12.345.678/0001-90", 
            period="Janeiro a Dezembro 2024"
        )
        
        # 2. Sumário Executivo
        savings_fmt = self._format_currency(analysis_result['total_savings'])
        pdf.section_executive_summary(savings_fmt)
        
        # 3. Análise Visual
        bar_chart = self._generate_bar_chart(analysis_result['regime_comparison'])
        pie_chart = self._generate_pie_chart(analysis_result['opportunities'])
        pdf.section_visual_analysis(bar_chart, pie_chart)
        os.remove(bar_chart)
        os.remove(pie_chart)
        
        # 4. Detalhamento
        pdf.section_detailed_opportunities(analysis_result['opportunities'], self._format_currency)
        
        # 5. Projeção (Pagina Extra Solicitada)
        pdf.add_page()
        pdf.chapter_title("4. Projeção de Cenários e Riscos")
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, "Simulação considerando crescimento de 20% no faturamento para o próximo exercício:")
        pdf.ln(5)
        
        # Matriz Risco (Placeholder visual)
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(10, pdf.get_y(), 190, 60, 'F')
        pdf.set_xy(20, pdf.get_y()+20)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Matriz de Risco: BAIXO", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, "A maioria das oportunidades identificadas segue jurisprudência pacificada.", 0, 1, 'C')

        pdf.output(filename)
        print(f"Relatório Premium gerado: {filename}")

if __name__ == "__main__":
    agent = CreditRecoveryAgent()
    
    # Dados Mock
    mock_history = [
        {'period': '01/2024', 'paid_amount': 30000, 'paid_regime': 'LUCRO_PRESUMIDO', 'revenue': 250000, 'payroll': 60000, 'costs': {'energia_eletrica': 8000, 'insumos_diretos': 100000}},
        {'period': '02/2024', 'paid_amount': 32000, 'paid_regime': 'LUCRO_PRESUMIDO', 'revenue': 260000, 'payroll': 62000, 'costs': {'energia_eletrica': 8500, 'insumos_diretos': 110000}}
    ]
    
    res = agent.analyze_credits(mock_history)
    agent.generate_report(res)
