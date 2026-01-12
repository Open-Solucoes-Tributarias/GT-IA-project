from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

class TaxEngine:
    """
    Motor de Cálculo Tributário (GT-IA Bloco 2).
    Responsável por calcular impostos (INSS, IRRF, CSLL, PIS, COFINS, ISS)
    e simular comparativos entre regimes tributários.
    """

    def __init__(self):
        # Configuration constants could be loaded from DB or config file
        pass

    def _to_decimal(self, value) -> Decimal:
        """Helper to ensure safe Decimal usage."""
        if value is None:
            return Decimal("0.00")
        if isinstance(value, float):
            return Decimal(str(value))
        return Decimal(value)

    def calculate_inss_patronal(self, payroll_amount: Decimal, regime: str = 'LUCRO_PRESUMIDO') -> Decimal:
        """
        Calcula o INSS Patronal (CPP) sobre a folha.
        Regra Geral: 20% sobre a folha de salários (Art. 22 Lei 8.212/91).
        
        Args:
            payroll_amount: Valor total da folha de salários.
            regime: Regime tributário (Simples Nacional pode ter imunidade no anexo).
        """
        payroll = self._to_decimal(payroll_amount)

        if regime == 'SIMPLES_NACIONAL':
            # Simples Nacional Anexos I, II, III, V geralmente isentam a CPP direta (está no DAS),
            # exceto Anexo IV (Construção Civil, Vigilância, etc).
            # PROJETO MVP: Assumindo isenção padrão do Anexo III (Serviços)
            return Decimal("0.00")
        
        # Lucro Presumido ou Real
        rate = Decimal("0.20") # 20%
        return (payroll * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_pis_cofins(self, revenue_amount: Decimal, regime: str) -> Dict[str, Decimal]:
        """
        Calcula PIS e COFINS baseado na cumulatividade ou não-cumulatividade.
        
        Args:
            revenue_amount: Faturamento mensal.
            regime: 'LUCRO_PRESUMIDO' (Cumulativo) ou 'LUCRO_REAL' (Não-Cumulativo).
            
        Returns:
            Dict com valores de 'pis' e 'cofins'.
        """
        revenue = self._to_decimal(revenue_amount)
        
        if regime == 'LUCRO_PRESUMIDO':
            # Regime Cumulativo (Lei 9.718/98)
            # PIS: 0.65%, COFINS: 3.00%
            pis_rate = Decimal("0.0065")
            cofins_rate = Decimal("0.0300")
        elif regime == 'LUCRO_REAL':
            # Regime Não-Cumulativo (Leis 10.637/02 e 10.833/03)
            # PIS: 1.65%, COFINS: 7.60%
            pis_rate = Decimal("0.0165")
            cofins_rate = Decimal("0.0760")
        else:
            # Simples Nacional (incluso no DAS)
            return {'pis': Decimal("0.00"), 'cofins': Decimal("0.00")}

        pis = revenue * pis_rate
        cofins = revenue * cofins_rate
        
        return {
            'pis': pis.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            'cofins': cofins.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        }

    def calculate_irrf_csll(self, revenue_amount: Decimal, operational_costs: Decimal, regime: str, is_service: bool = True) -> Dict[str, Decimal]:
        """
        Calcula IRPJ e CSLL.
        
        Args:
            revenue_amount: Faturamento bruto.
            operational_costs: Custos/Despesas dedutíveis (importante para Lucro Real).
            regime: 'LUCRO_PRESUMIDO' ou 'LUCRO_REAL'.
            is_service: Se True, usa base de cálculo de serviço (32%). 
        """
        revenue = self._to_decimal(revenue_amount)
        costs = self._to_decimal(operational_costs)
        
        irpj = Decimal("0.00")
        csll = Decimal("0.00")
        
        if regime == 'SIMPLES_NACIONAL':
            return {'irpj': irpj, 'csll': csll}

        # Definição da Base de Cálculo
        calculation_base_ir = Decimal("0.00")
        calculation_base_csll = Decimal("0.00")

        if regime == 'LUCRO_PRESUMIDO':
            # Presunção: Serviços = 32% (Art. 15 Lei 9.249/95)
            # Presunção: Comércio = 8% (IR) e 12% (CSLL) -> MVP focado em Serviços
            presumption = Decimal("0.32") if is_service else Decimal("0.08")
            
            calculation_base_ir = revenue * presumption
            calculation_base_csll = revenue * Decimal("0.32") # CSLL 32% para serviços
            
        elif regime == 'LUCRO_REAL':
            # Lucro Contábil/Fiscal Aproximado
            profit = revenue - costs
            if profit < 0:
                profit = Decimal("0.00")
            
            calculation_base_ir = profit
            calculation_base_csll = profit

        # Cálculo do IR (Base * 15%) + Adicional 10% sobre excedente de 20k/mês
        basic_ir = calculation_base_ir * Decimal("0.15")
        additional_ir = Decimal("0.00")
        
        # Considerando cálculo mensal (limite 20.000)
        threshold = Decimal("20000.00")
        if calculation_base_ir > threshold:
            additional_ir = (calculation_base_ir - threshold) * Decimal("0.10")
            
        irpj = basic_ir + additional_ir
        
        # Cálculo da CSLL (Base * 9%)
        csll = calculation_base_csll * Decimal("0.09")
        
        return {
            'irpj': irpj.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            'csll': csll.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        }

    def calculate_iss(self, revenue_amount: Decimal, city_rate: float = 5.0) -> Decimal:
        """
        Calcula ISS (Imposto Sobre Serviços).
        
        Args:
           revenue_amount: Valor do serviço.
           city_rate: Alíquota municipal em % (Máx 5%, Min 2%).
        """
        revenue = self._to_decimal(revenue_amount)
        rate = self._to_decimal(city_rate) / Decimal("100")
        
        return (revenue * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def simulate_regimes(self, annual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulador Comparativo de Regimes Tributários.
        
        Args:
            annual_data: Dict contendo:
                'revenue': Faturamento Anual
                'payroll': Folha Anual
                'costs': Custos Operacionais Anuais
        """
        revenue = self._to_decimal(annual_data.get('revenue', 0))
        payroll = self._to_decimal(annual_data.get('payroll', 0))
        costs = self._to_decimal(annual_data.get('costs', 0))
        
        # --- 1. SIMPLES NACIONAL (Anexo III - Serviços) ---
        # Tabela 2024 (Simplificada para MVP)
        # RBT12 (Receita Bruta Total 12 meses)
        
        # Faixa 3 exemplo (180k a 360k) -> Aliq Nominal 13.5%, Dedução 9360
        # Faixa 5 exemplo (1.8M a 3.6M) -> Aliq Nominal 21.0%, Dedução 125640
        # MVP: Usando uma média efetiva de ~10% para simplificação se não tivermos a tabela completa
        # TODO: Implementar tabela completa do Anexo III
        
        simples_rate = Decimal("0.10") 
        if revenue > 3600000:
            simples_rate = Decimal("0.30") # Penalty for high revenue
            
        total_simples = revenue * simples_rate
        
        # --- 2. LUCRO PRESUMIDO ---
        # INSS (20% folha) + PIS/COFINS (3.65% fat) + IRPJ/CSLL (aprox 11.33% fat) + ISS (5% fat)
        lp_inss = self.calculate_inss_patronal(payroll, 'LUCRO_PRESUMIDO')
        lp_piscofins = self.calculate_pis_cofins(revenue, 'LUCRO_PRESUMIDO')
        lp_ir_csll = self.calculate_irrf_csll(revenue, costs, 'LUCRO_PRESUMIDO')
        lp_iss = self.calculate_iss(revenue) # Assume 5% max
        
        total_presumido = lp_inss + lp_piscofins['pis'] + lp_piscofins['cofins'] + \
                          lp_ir_csll['irpj'] + lp_ir_csll['csll'] + lp_iss

        # --- 3. LUCRO REAL ---
        # INSS (20% folha) + PIS/COFINS (9.25% nao-cumulativo) + IRPJ/CSLL (24% ou 34% sobre lucro)
        lr_inss = self.calculate_inss_patronal(payroll, 'LUCRO_REAL')
        lr_piscofins = self.calculate_pis_cofins(revenue, 'LUCRO_REAL') 
        # Note: Non-cumulative credits often reduce this effectively. Assuming 30% credit efficiency for MVP
        lr_piscofins_total = lr_piscofins['pis'] + lr_piscofins['cofins']
        lr_piscofins_total = lr_piscofins_total * Decimal("0.7") 
        
        lr_ir_csll = self.calculate_irrf_csll(revenue, costs, 'LUCRO_REAL')
        lr_iss = self.calculate_iss(revenue)

        total_real = lr_inss + lr_piscofins_total + lr_ir_csll['irpj'] + lr_ir_csll['csll'] + lr_iss
        
        # Recommendation
        regimes = {
            'Simples Nacional': total_simples,
            'Lucro Presumido': total_presumido,
            'Lucro Real': total_real
        }
        best_regime = min(regimes, key=regimes.get)
        
        return {
            'inputs': {'revenue': str(revenue), 'payroll': str(payroll), 'profit': str(revenue - costs)},
            'results': {k: str(v.quantize(Decimal("0.01"))) for k, v in regimes.items()},
            'recommendation': best_regime,
            'savings': str((max(regimes.values()) - min(regimes.values())).quantize(Decimal("0.01")))
        }

# Exemplo de uso
if __name__ == "__main__":
    engine = TaxEngine()
    test_data = {
        'revenue': 100000,   # 100k/mês -> 1.2M/ano
        'payroll': 20000,    # 20k/mês
        'costs': 40000       # 40k/mês
    }
    
    print("--- Simulação de Cálculo ---")
    simulation = engine.simulate_regimes(test_data)
    print(f"Melhor Regime: {simulation['recommendation']}")
    print(f"Resultados: {simulation['results']}")
