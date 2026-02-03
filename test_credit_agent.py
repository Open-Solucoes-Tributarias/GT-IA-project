from py.credit_recovery import CreditRecoveryAgent
from decimal import Decimal

def run_test():
    agent = CreditRecoveryAgent()
    
    # Mock Data matching input
    history_data = [
        {
            'period': '01/2024',
            'paid_amount': 350000.0,
            'paid_regime': 'LUCRO_PRESUMIDO',
            'revenue': 5200000.0,
            'payroll': 800000.0,
            'costs': {
                'energia_eletrica': 45000.0, 
                'insumos_diretos': 2100000.0,
                'aluguel_predios': 15000.0
            }
        }
    ]
    
    result = agent.analyze_credits(history_data)
    print("--- ANALYSIS RESULT ---")
    print(f"Total Savings: {result['total_savings']}")
    print(f"Opportunities Found: {len(result['opportunities'])}")
    for opp in result['opportunities']:
        print(f"  - {opp['type']}: R$ {opp['value']:,.2f}")

if __name__ == "__main__":
    run_test()
