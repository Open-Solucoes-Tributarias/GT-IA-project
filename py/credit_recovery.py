import os
from decimal import Decimal
from typing import List, Dict, Any
from fpdf import FPDF
from datetime import datetime
import matplotlib
matplotlib.use('Agg') # Server safety
import matplotlib.pyplot as plt
import tempfile

# Import Modules
# Import Modules
try:
    from tax_engine import TaxEngine
except ImportError:
    from py.tax_engine import TaxEngine
# from legal_advisor import LegalAdvisor (Not used yet, avoiding circular or unused import issues)

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
        # Custom Logo Handling
        logo_path = "logo.png"
        if not os.path.exists(logo_path) and os.path.exists("py/logo.png"):
            logo_path = "py/logo.png"

        if os.path.exists(logo_path):
            self.image(logo_path, x=85, y=20, w=40)
        else:
            # Placeholder visual se não tiver imagem
            self.set_fill_color(200, 200, 200)
            self.rect(105, 40, 30, 30, 'F')
        
        self.set_text_color(255, 255, 255)
        self.ln(80)
        
        # Título Principal
        self.set_font("Arial", 'B', 28)
        self.multi_cell(0, 12, "Relatório de Diagnóstico Fiscal\ne Recuperação de Créditos", 0, 'C')
        self.ln(10)
        self.set_font("Arial", '', 14)
        self.cell(0, 10, "Auditoria de Inteligência Artificial", 0, 1, 'C')
        
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

    def section_executive_summary(self, total_savings, opportunities_count):
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
        
        # Card 2 Content (Riscos/Oportunidades)
        self.set_xy(110, y_cards + 8)
        self.set_font("Arial", '', 10)
        self.set_text_color(100)
        self.cell(90, 5, "Pontos de Atenção / Oportunidades", 0, 1, 'C')
        
        self.set_xy(110, y_cards + 18)
        self.set_font("Arial", 'B', 20)
        self.set_text_color(200, 0, 0) # Red/Orange
        self.cell(90, 15, f"{opportunities_count} Detectados", 0, 1, 'C')
        
        self.set_y(y_cards + 50)

    def section_visual_analysis(self, bar_chart_path, pie_chart_path):
        self.add_page()
        self.chapter_title("2. Análise Visual")
        
        self.set_font("Arial", 'B', 12)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "Distribuição de Oportunidades", 0, 1, 'L')
        
        # Gráfico Pizza (Maior destaque)
        if pie_chart_path:
             self.image(pie_chart_path, x=40, y=self.get_y(), w=130)
             self.ln(100) 
        else:
             self.ln(10)
             self.cell(0, 10, "(Não há oportunidades suficientes para gerar gráfico)", 0, 1, 'C')
             self.ln(20)

        self.set_font("Arial", 'B', 12)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "Comparativo de Custo Anual (Regimes)", 0, 1, 'L')
        
        # Gráfico Barras
        if bar_chart_path:
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
            if risk_pt == 'ALTO': self.set_text_color(200, 0, 0)
            elif risk_pt == 'BAIXO': self.set_text_color(0, 128, 0)
            else: self.set_text_color(0)
            
            self.cell(col_w[4], row_h, risk_pt, 1, 0, 'C')
            self.set_text_color(0)
            
            self.ln()
            self.set_y(y_start + row_h)

    def section_risk_scenarios(self, current_savings, format_currency_func):
        self.add_page()
        self.chapter_title("4. Projeção de Cenários e Riscos")
        
        # 1. Projeção Financeira
        self.set_font("Arial", 'B', 11)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "Simulação de Economia Acumulada (12 Meses):", 0, 1)
        
        # Headers
        self.set_fill_color(245, 245, 245)
        self.set_font("Arial", 'B', 10)
        self.cell(90, 8, "Cenário Atual", 1, 0, 'C', 1)
        self.cell(90, 8, "Cenário Otimista (+20% Faturamento)", 1, 1, 'C', 1)
        
        # Body
        try:
            current_val = Decimal(str(current_savings))
            projected_val = current_val * Decimal("1.20")
        except:
            current_val = Decimal(0)
            projected_val = Decimal(0)
            
        self.set_font("Arial", 'B', 14)
        self.set_text_color(0, 128, 0)
        self.cell(90, 15, format_currency_func(current_val), 1, 0, 'C')
        self.cell(90, 15, format_currency_func(projected_val), 1, 1, 'C')
        self.set_text_color(0)
        self.ln(15)
        
        # 2. Matriz de Risco Detalhada
        self.set_font("Arial", 'B', 11)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "Matriz de Risco da Operação:", 0, 1)
        
        # Table of Risks
        self.set_font("Arial", 'B', 10)
        self.set_fill_color(230, 230, 235)
        self.cell(50, 8, "Dimensão", 1, 0, 'L', 1)
        self.cell(140, 8, "Avaliação Técnica", 1, 1, 'L', 1)
        
        self.set_font("Arial", '', 10)
        self.set_fill_color(255, 255, 255)
        
        # Row 1
        self.cell(50, 10, "Segurança Jurídica", 1, 0, 'L')
        self.cell(140, 10, " ALTA - Baseado em Teses Pacificadas (STF Tema 69/STJ)", 1, 1, 'L')
        
        # Row 2
        self.cell(50, 10, "Documentação", 1, 0, 'L')
        self.cell(140, 10, " MÉDIA - Requer retificação de obrigações (Sped Contributions)", 1, 1, 'L')
        
        # Row 3
        self.cell(50, 10, "Prob. Fiscalização", 1, 0, 'L')
        self.cell(140, 10, " BAIXA - Compliance prévio realizado via Cruzamento GT-IA", 1, 1, 'L')
        
        self.ln(5)
        self.set_font("Arial", 'I', 9)
        self.multi_cell(0, 5, "Nota: A recuperação de créditos tributários via via administrativa é segura quando fundamentada em legislação vigente e jurisprudência consolidada. A GT-IA recomenda a revisão dos arquivos XML antes da compensação.".replace("via via", "via"))
class CreditRecoveryAgent:
    def __init__(self):
        self.tax_engine = TaxEngine()

    def _format_currency(self, val: Any) -> str:
        value = Decimal(str(val))
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _generate_bar_chart(self, comparison_data):
        try:
            plt.clf() # Clear current figure
            regimes = list(comparison_data.keys())
            values = [float(v) for v in comparison_data.values()]
            
            plt.figure(figsize=(10, 6)) 
            colors = ['#2E7D32', '#1976D2', '#D32F2F'] # Green, Blue, Red
            bars = plt.bar(regimes, values, color=colors, width=0.6)
            
            plt.title('Comparativo de Carga Tributária Anual Estimada', fontsize=12, fontweight='bold', pad=20)
            plt.ylabel('Valor Total (R$)', fontsize=10)
            plt.grid(axis='y', linestyle='--', alpha=0.5)
            
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                         f'R$ {height:,.0f}'.replace(',', '.'),
                         ha='center', va='bottom', fontsize=9)
            
            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.tight_layout()
            plt.savefig(temp.name, dpi=300)
            plt.close('all') # Force close all
            return temp.name
        except Exception as e:
            print(f"Error generating bar chart: {e}")
            return None

    def _generate_pie_chart(self, opportunities):
        try:
            if not opportunities: return None
            
            plt.clf()
            types = {}
            for opp in opportunities:
                t = opp['type']
                types[t] = types.get(t, 0) + float(opp['value'])
            
            if not types: return None

            labels = [f"{k}\n(R$ {v:,.0f})" for k,v in types.items()]
            sizes = list(types.values())
            
            plt.figure(figsize=(8, 6))
            colors = ['#FFC107', '#03A9F4', '#E91E63']
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 10})
            plt.title('Distribuição da Economia por Tipo', fontsize=12, fontweight='bold')
            
            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp.name, dpi=300)
            plt.close('all')
            return temp.name
        except: return None

    def analyze_credits(self, history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        opportunities = []
        total_savings = Decimal("0.00")
        regime_totals = {'Simples Nacional': Decimal(0), 'Lucro Presumido': Decimal(0), 'Lucro Real': Decimal(0)}
        
        periods = []

        for month_data in history_data:
            period = month_data.get('period', 'N/A')
            periods.append(period)
            
            try:
                paid = Decimal(str(month_data.get('paid_amount', 0)))
            except: paid = Decimal("0.00")
            
            used_regime = month_data.get('paid_regime', 'LUCRO_PRESUMIDO')
            
            # Validate numeric inputs for simulation
            rev_val = month_data.get('revenue', 0)
            pay_val = month_data.get('payroll', 0)
            cost_val = month_data.get('costs', 0)
            
            if not rev_val: rev_val = 0
            if not pay_val: pay_val = 0
            
            sim_input = {'revenue': rev_val, 'payroll': pay_val, 'costs': cost_val}
            sim = self.tax_engine.simulate_regimes(sim_input)
            
            for r, v in sim['results'].items():
                regime_totals[r] += Decimal(v)
            
            best = sim['recommendation']
            optimal = Decimal(sim['results'][best])
            
            # Logic: If they paid more than the optimal regime, that's savings
            # Note: This is simplified. Real world needs to know if they COULD be in that regime.
            # Assuming 'paid' is what they actually paid.
            
            if paid > optimal:
                diff = paid - optimal
                # Only count meaningful savings
                if diff > 10: 
                    total_savings += diff
                    opportunities.append({
                        'type': 'REGIME_MISMATCH',
                        'period': period,
                        'description': f"Empresa pagou R$ {paid:,.2f} no {used_regime}, mas poderia pagar R$ {optimal:,.2f} no {best}.",
                        'value': diff,
                        'legal_basis': "Planejamento Tributário / Elisão Fiscal",
                        'risk': 'LOW'
                    })
                
                
            # Logic: PIS/COFINS Credits in Lucro Real
            # If the BEST regime is Lucro Real, we highlight specific credits found
            if best == 'Lucro Real':
                credits_lr = Decimal(sim.get('credits_found_lr', 0))
                if credits_lr > 0:
                     opportunities.append({
                        'type': 'CREDITO_INSUMO',
                        'period': period,
                        'description': "Créditos PIS/COFINS sobre Insumos Operacionais (Energia, Aluguel, etc).",
                        'value': credits_lr,
                        'legal_basis': "Leis 10.637/02 e 10.833/03",
                        'risk': 'LOW'
                     })

            # --- OPORTUNIDADES ADICIONAIS (TESES JURÍDICAS) ---
            # 1. Exclusão do ICMS da Base de Cálculo do PIS/COFINS (Tese do Século - STF RE 574.706)
            # Aplicável para Lucro Real e Presumido (embora mais comum no Real, a tese foca no conceito de Receita)
            # Estimativa: ICMS médio de 18% sobre o faturamento.
            rev_decimal = Decimal(str(rev_val))
            icms_estimate = rev_decimal * Decimal("0.18")
            pis_cofins_rate = Decimal("0.0925") if used_regime == 'LUCRO_REAL' else Decimal("0.0365")
            
            # Se for Simples, não se aplica da mesma forma (tem regra específica)
            if used_regime != 'Simples Nacional':
                excluding_icms_savings = icms_estimate * pis_cofins_rate
                if excluding_icms_savings > 0:
                    total_savings += excluding_icms_savings
                    opportunities.append({
                        'type': 'EXCLUSAO_ICMS',
                        'period': period,
                        'description': "Exclusão do ICMS da base de cálculo do PIS/COFINS (Tese do Século).",
                        'value': excluding_icms_savings,
                        'legal_basis': "STF RE 574.706 (Tema 69)",
                        'risk': 'LOW'
                    })

            # 2. Segregação de Receitas Monofásicas (Estimativa 5% do faturamento)
            # Produtos com tributação concentrada (Bebidas, Autopeças, Farmácia) não devem pagar PIS/COFINS novamente.
            monofasic_base = rev_decimal * Decimal("0.05")
            monofasic_savings = monofasic_base * pis_cofins_rate
            
            if monofasic_savings > 0:
                total_savings += monofasic_savings
                opportunities.append({
                'type': 'MONOFASICO',
                    'period': period,
                    'description': "Segregação de receitas monofásicas (PIS/COFINS recolhido na indústria).",
                    'value': monofasic_savings,
                    'legal_basis': "Lei 10.147/00 (Autopeças/Farmácia/Cosméticos)",
                    'risk': 'MEDIUM' # Requer revisão NCM a NCM
                })
            
            # 3. Credito de PIS/COFINS sobre Marketing (ALTO RISCO)
            # Mapeamento do main.py: costs['outros'] recebeu 'Custo Marketing'
            if isinstance(cost_val, dict):
                 mkt_cost = Decimal(str(cost_val.get('outros', 0)))
                 if mkt_cost > 0:
                      # Rate 9.25% (Simulated for Lucro Real potential)
                      pis_cofins_rate = Decimal("0.0925") if used_regime == 'LUCRO_REAL' else Decimal("0.0365")
                      mkt_savings = mkt_cost * pis_cofins_rate
                      if mkt_savings > 100:
                           total_savings += mkt_savings
                           opportunities.append({
                               'type': 'CREDITO_MARKETING',
                               'period': period,
                               'description': "Crédito PIS/COFINS sobre despesas de Marketing (Conceito estendido de Insumo - CARF).",
                               'value': mkt_savings,
                               'legal_basis': "Tese Jurídica Controvertida (Risco de Glosa)",
                               'risk': 'HIGH'
                           })

        # Calculate Period Range
        period_str = "Período Desconhecido"
        if periods and len(periods) > 0:
            try:
                # Sort by date (assuming MM/YYYY)
                sorted_p = sorted(periods, key=lambda x: datetime.strptime(x, "%m/%Y"))
                period_str = f"{sorted_p[0]} a {sorted_p[-1]}"
            except:
                period_str = f"{periods[0]} a {periods[-1]}"

        return {
            'total_savings': total_savings, 
            'opportunities': opportunities, 
            'regime_comparison': regime_totals,
            'period_range': period_str
        }

    def generate_report(self, analysis_result, company_info=None, filename="relatorio_recuperacao.pdf"):
        if company_info is None:
            company_info = {"name": "Empresa Cliente", "cnpj": "00.000.000/0000-00"}

        pdf = PDFReportGenerator()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # 1. Capa Dinâmica
        pdf.draw_cover_page(
            company_name=company_info.get("name", "Empresa Cliente"), 
            cnpj=company_info.get("cnpj", ""), 
            period=analysis_result.get('period_range', "Período não identificado")
        )
        
        # 2. Sumário Executivo
        savings_fmt = self._format_currency(analysis_result['total_savings'])
        opp_count = len(analysis_result['opportunities'])
        pdf.section_executive_summary(savings_fmt, opp_count)
        
        # 3. Análise Visual
        bar_chart = self._generate_bar_chart(analysis_result['regime_comparison'])
        pie_chart = self._generate_pie_chart(analysis_result['opportunities'])
        
        try:
            pdf.section_visual_analysis(bar_chart, pie_chart)
        except Exception as e:
            print(f"Error adding visual section: {e}")
        
        # Clean up
        try:
            if bar_chart and os.path.exists(bar_chart): os.remove(bar_chart)
            if pie_chart and os.path.exists(pie_chart): os.remove(pie_chart)
        except: pass
        
        # 4. Detalhamento (Sorted by Risk/Type)
        # Sort so that Low risk ones appear first (or grouped by type) to avoid jarring stripes
        # Primary Sort: Risk (LOW -> MEDIUM -> HIGH)
        # Secondary Sort: Type
        sorted_opportunities = sorted(analysis_result['opportunities'], key=lambda x: (x['risk'], x['type']))
        
        pdf.section_detailed_opportunities(sorted_opportunities, self._format_currency)
        
        # 5. Projeção Avançada
        pdf.section_risk_scenarios(analysis_result['total_savings'], self._format_currency)

        pdf.output(filename)
        return filename

if __name__ == "__main__":
    agent = CreditRecoveryAgent()
    # Mock Data Test
    mock_history = [
        {'period': '01/2024', 'paid_amount': 50000, 'paid_regime': 'LUCRO_PRESUMIDO', 'revenue': 250000, 'payroll': 60000, 'costs': {'energia_eletrica': 8000, 'insumos_diretos': 100000}},
    ]
    res = agent.analyze_credits(mock_history)
    agent.generate_report(res)
