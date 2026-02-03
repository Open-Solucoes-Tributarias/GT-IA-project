from py.tax_engine import TaxEngine
from decimal import Decimal
import sys

def run_diag():
    engine = TaxEngine()

    revenue = Decimal("5200000.00")
    payroll = Decimal("800000.00")
    paid_amount = Decimal("350000.00")
    
    detailed_costs = {
        'energia_eletrica': Decimal("45000.00"),
        'insumos_diretos': Decimal("2100000.00"),
        'aluguel_predios': Decimal("15000.00")
    }

    results = []
    results.append("--- DIAGNOSTIC RESULTS ---")

    # A. INSS
    lp_inss = engine.calculate_inss_patronal(payroll, 'LUCRO_PRESUMIDO')
    lr_inss = engine.calculate_inss_patronal(payroll, 'LUCRO_REAL')
    results.append(f"INSS LP: {lp_inss} | LR: {lr_inss}")

    # B. PIS/COFINS
    lp_pc = engine.calculate_pis_cofins(revenue, 'LUCRO_PRESUMIDO', detailed_costs)
    lr_pc = engine.calculate_pis_cofins(revenue, 'LUCRO_REAL', detailed_costs)
    results.append(f"PIS/COFINS LP: {lp_pc} | LR: {lr_pc}")

    # C. IRPJ/CSLL
    # Lucro Real Deduction Assumption
    total_deductible = sum(detailed_costs.values()) + payroll
    
    lp_ircsll = engine.calculate_irrf_csll(revenue, total_deductible, 'LUCRO_PRESUMIDO')
    lr_ircsll = engine.calculate_irrf_csll(revenue, total_deductible, 'LUCRO_REAL')
    results.append(f"IRPJ/CSLL LP: {lp_ircsll} | LR: {lr_ircsll}")

    # D. ISS
    lp_iss = engine.calculate_iss(revenue)
    lr_iss = engine.calculate_iss(revenue)
    results.append(f"ISS: {lp_iss}")

    # E. Totals
    total_lp = lp_inss + lp_pc['pis'] + lp_pc['cofins'] + lp_ircsll['irpj'] + lp_ircsll['csll'] + lp_iss
    total_lr = lr_inss + lr_pc['pis'] + lr_pc['cofins'] + lr_ircsll['irpj'] + lr_ircsll['csll'] + lr_iss
    
    results.append(f"TOTAL TAX LP: {total_lp}")
    results.append(f"TOTAL TAX LR: {total_lr}")
    results.append(f"USER PAID: {paid_amount}")
    
    if total_lp < total_lr:
        results.append("OPTIMAL: LUCRO PRESUMIDO")
    else:
        results.append("OPTIMAL: LUCRO REAL")
        
    diff = paid_amount - min(total_lp, total_lr)
    results.append(f"DIFF (Paid - Optimal): {diff}")

    with open("results.log", "w") as f:
        f.write("\n".join(results))
    print("Done.")

if __name__ == "__main__":
    try:
        run_diag()
    except Exception as e:
        with open("results.log", "w") as f:
            f.write(f"ERROR: {e}")
        print(f"Error: {e}")
