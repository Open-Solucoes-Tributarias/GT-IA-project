from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Union

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
        if isinstance(value, Decimal):
            return value
        return Decimal(value)

    def calculate_inss_patronal(self, payroll_amount: Decimal, regime: str = 'LUCRO_PRESUMIDO') -> Decimal:
        """
        Calcula o INSS Patronal (CPP) sobre a folha.
        Regra Geral: 20% sobre a folha de salários (Art. 22 Lei 8.212/91).
        """
        payroll = self._to_decimal(payroll_amount)

        if regime == 'SIMPLES_NACIONAL':
            # Assumindo isenção padrão do Anexo III (Serviços) para MVP
            return Decimal("0.00")
        
        # Lucro Presumido ou Real
        rate = Decimal("0.20") # 20%
        return (payroll * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_pis_cofins(self, revenue_amount: Decimal, regime: str, detailed_costs: Dict[str, Any] = None) -> Dict[str, Decimal]:
        """
        Calcula PIS e COFINS baseado na cumulatividade ou não-cumulatividade.
        Aceita custos detalhados para calcular créditos no Lucro Real.
        
        Args:
            revenue_amount: Faturamento mensal.
            regime: 'LUCRO_PRESUMIDO' (Cumulativo) ou 'LUCRO_REAL' (Não-Cumulativo).
            detailed_costs: Dicionário com custos por categoria para cálculo de créditos.
                            Ex: {'energia_eletrica': 1000, 'insumos_diretos': 5000}
            
        Returns:
            Dict com valores de 'pis', 'cofins' e 'total_credits'.
        """
        revenue = self._to_decimal(revenue_amount)
        
        pis_credit = Decimal("0.00")
        cofins_credit = Decimal("0.00")
        
        if regime == 'LUCRO_PRESUMIDO':
            # Regime Cumulativo (Lei 9.718/98) - Sem direito a crédito
            # PIS: 0.65%, COFINS: 3.00%
            pis_rate = Decimal("0.0065")
            cofins_rate = Decimal("0.0300")
            
            pis_debit = revenue * pis_rate
            cofins_debit = revenue * cofins_rate
            
        elif regime == 'LUCRO_REAL':
            # Regime Não-Cumulativo (Leis 10.637/02 e 10.833/03)
            # PIS: 1.65%, COFINS: 7.60%
            pis_rate = Decimal("0.0165")
            cofins_rate = Decimal("0.0760")
            
            pis_debit = revenue * pis_rate
            cofins_debit = revenue * cofins_rate
            
            # Cálculo de Créditos
            if detailed_costs:
                # Categorias elegíveis para crédito (Leis 10.637 e 10.833)
                # Exemplos: Energia Elétrica, Aluguéis de prédios (PJ), Máquinas (Depreciação), Insumos
                credit_categories = [
                    'energia_eletrica', 
                    'aluguel_predios', 
                    'maquinas_equipamentos', 
                    'insumos_diretos'
                ]
                
                total_base_credito = Decimal("0.00")
                
                for category, val in detailed_costs.items():
                    if category in credit_categories:
                        total_base_credito += self._to_decimal(val)
                
                pis_credit = total_base_credito * pis_rate
                cofins_credit = total_base_credito * cofins_rate
            
        else:
            # Simples Nacional (incluso no DAS)
            return {'pis': Decimal("0.00"), 'cofins': Decimal("0.00"), 'total_credits': Decimal("0.00")}

        # Apuração final (Débito - Crédito)
        pis_final = max(pis_debit - pis_credit, Decimal("0.00"))
        cofins_final = max(cofins_debit - cofins_credit, Decimal("0.00"))
        
        return {
            'pis': pis_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            'cofins': cofins_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            'total_credits': (pis_credit + cofins_credit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        }

    def calculate_irrf_csll(self, revenue_amount: Decimal, total_costs: Decimal, regime: str, is_service: bool = True) -> Dict[str, Decimal]:
        """
        Calcula IRPJ e CSLL.
        """
        revenue = self._to_decimal(revenue_amount)
        costs = self._to_decimal(total_costs)
        
        irpj = Decimal("0.00")
        csll = Decimal("0.00")
        
        if regime == 'SIMPLES_NACIONAL':
            return {'irpj': irpj, 'csll': csll}

        # Definição da Base de Cálculo
        calculation_base_ir = Decimal("0.00")
        calculation_base_csll = Decimal("0.00")

        if regime == 'LUCRO_PRESUMIDO':
            # Presunção: Serviços = 32%
            presumption = Decimal("0.32") if is_service else Decimal("0.08")
            
            calculation_base_ir = revenue * presumption
            calculation_base_csll = revenue * Decimal("0.32")
            
        elif regime == 'LUCRO_REAL':
            # Lucro Líquido
            profit = revenue - costs
            if profit < 0:
                profit = Decimal("0.00")
            
            calculation_base_ir = profit
            calculation_base_csll = profit

        # Cálculo do IR (Base * 15%) + Adicional 10%
        basic_ir = calculation_base_ir * Decimal("0.15")
        additional_ir = Decimal("0.00")
        
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
        """
        revenue = self._to_decimal(revenue_amount)
        rate = self._to_decimal(city_rate) / Decimal("100")
        
        return (revenue * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def simulate_regimes(self, annual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulador Comparativo.
        Args:
            annual_data: Dict contendo:
                'revenue': Faturamento Anual
                'payroll': Folha Anual
                'costs': Decimal (total) OU Dict (por categoria)
        """
        revenue = self._to_decimal(annual_data.get('revenue', 0))
        payroll = self._to_decimal(annual_data.get('payroll', 0))
        
        costs_input = annual_data.get('costs', 0)
        detailed_costs = {}
        total_param_costs = Decimal("0.00")

        # Handle Costs Format (Decimal or Dict)
        if isinstance(costs_input, dict):
            detailed_costs = costs_input
            total_param_costs = sum(self._to_decimal(v) for v in costs_input.values())
        else:
            total_param_costs = self._to_decimal(costs_input)
            # If simplistic input, no detailed credits in Lucro Real (assumption)
        
        # --- 1. SIMPLES NACIONAL ---
        simples_rate = Decimal("0.10") 
        if revenue > 3600000:
            simples_rate = Decimal("0.30")
        total_simples = revenue * simples_rate
        
        # --- 2. LUCRO PRESUMIDO ---
        lp_inss = self.calculate_inss_patronal(payroll, 'LUCRO_PRESUMIDO')
        lp_piscofins = self.calculate_pis_cofins(revenue, 'LUCRO_PRESUMIDO', detailed_costs)
        lp_ir_csll = self.calculate_irrf_csll(revenue, total_param_costs, 'LUCRO_PRESUMIDO')
        lp_iss = self.calculate_iss(revenue)
        
        total_presumido = lp_inss + lp_piscofins['pis'] + lp_piscofins['cofins'] + \
                          lp_ir_csll['irpj'] + lp_ir_csll['csll'] + lp_iss

        # --- 3. LUCRO REAL ---
        lr_inss = self.calculate_inss_patronal(payroll, 'LUCRO_REAL')
        # Here we pass the detailed costs to correctly calculate CREDITS
        lr_piscofins = self.calculate_pis_cofins(revenue, 'LUCRO_REAL', detailed_costs) 
        
        lr_ir_csll = self.calculate_irrf_csll(revenue, total_param_costs, 'LUCRO_REAL')
        lr_iss = self.calculate_iss(revenue)

        total_real = lr_inss + lr_piscofins['pis'] + lr_piscofins['cofins'] + \
                     lr_ir_csll['irpj'] + lr_ir_csll['csll'] + lr_iss
        
        # Recommendation
        regimes = {
            'Simples Nacional': total_simples,
            'Lucro Presumido': total_presumido,
            'Lucro Real': total_real
        }
        best_regime = min(regimes, key=regimes.get)
        
        return {
            'inputs': {'revenue': str(revenue), 'payroll': str(payroll), 'total_costs': str(total_param_costs)},
            'credits_found_lr': str(lr_piscofins.get('total_credits', '0.00')),
            'results': {k: str(v.quantize(Decimal("0.01"))) for k, v in regimes.items()},
            'recommendation': best_regime,
            'savings': str((max(regimes.values()) - min(regimes.values())).quantize(Decimal("0.01")))
        }

    # --- NOVOS MÉTODOS (FOCO OPEN SOLUÇÕES TRIBUTÁRIAS) ---
    # Este bloco foca no core da Open: Retenções e Encargos de Terceiros

    def calculate_retentions_on_invoice(self, 
                                     service_value: float, 
                                     provider_regime: str, 
                                     is_public_entity: bool = False,
                                     city_iss_rate: float = 5.0) -> Dict[str, Any]:
        """
        Realiza o Diagnóstico de Entrada: identifica retenções obrigatórias por nota fiscal.
        Alinhado ao sistema Gestão Tributária (GT) da Open.
        """
        val = self._to_decimal(service_value)
        
        # Alíquotas baseadas nas normas de retenção (INSS, IRRF, CSRF)
        rates = {
            "CSRF": Decimal("0.0465"), # PIS (0,65%) + COFINS (3,0%) + CSLL (1,0%)
            "INSS_RET": Decimal("0.11"),
            "IRRF_SRV": Decimal("0.015")
        }

        results = {
            "base_value": val,
            "retentions": {},
            "total_liquid": val,
            "warnings": []
        }

        # Regra de Retenção para Simples Nacional (Geralmente dispensada para CSRF/IRRF)
        # Normalizando provider_regime para evitar erros de case/formato
        norm_regime = provider_regime.upper().replace(' ', '_')
        if "SIMPLES" in norm_regime:
            results["retentions"]["CSRF"] = Decimal("0.00")
            results["retentions"]["IRRF"] = Decimal("0.00")
            results["warnings"].append("Prestador Simples Nacional: Dispensada retenção de IRRF/CSRF conforme IN RFB.")
        else:
            # Cálculo de CSRF com verificação de limite de R$ 10,00 para dispensa
            csrf_calc = (val * rates["CSRF"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if csrf_calc < Decimal("10.00"):
                results["retentions"]["CSRF"] = Decimal("0.00")
                results["warnings"].append("Valor de CSRF abaixo de R$ 10,00: Retenção dispensada.")
            else:
                results["retentions"]["CSRF"] = csrf_calc
            
            # IRRF (1,5% padrão para serviços profissionais)
            results["retentions"]["IRRF"] = (val * rates["IRRF_SRV"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Retenção de INSS (Lei 8.212/91 - 11% sobre cessão de mão de obra)
        results["retentions"]["INSS"] = (val * rates["INSS_RET"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # ISS (Município - Variável de 2% a 5%)
        iss_rate = self._to_decimal(city_iss_rate) / Decimal("100")
        results["retentions"]["ISS"] = (val * iss_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Cálculo do Valor Líquido Final
        total_retentions = sum(results["retentions"].values())
        results["total_liquid"] = val - total_retentions
        
        return results

if __name__ == "__main__":
    engine = TaxEngine()
    
    # Exemplo com Custos Detalhados (O Cenário Favorável ao Lucro Real)
    test_data = {
        'revenue': 2000000,   # 2M
        'payroll': 400000,    # 400k
        'costs': {
            'energia_eletrica': 150000,
            'insumos_diretos': 800000,
            'material_escritorio': 5000, # Não dá crédito
            'aluguel_predios': 50000
        }
    }
    
    print("--- Simulação com Créditos Detalhados ---")
    simulation = engine.simulate_regimes(test_data)
    print(f"Melhor Regime: {simulation['recommendation']}")
    print(f"Créditos Identificados (Lucro Real): R$ {simulation['credits_found_lr']}")
    print(f"Resultados: {simulation['results']}")
