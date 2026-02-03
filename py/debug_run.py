import sys
import os
import json

# Add py to path
sys.path.append(os.path.join(os.getcwd(), 'py'))

try:
    from credit_recovery import CreditRecoveryAgent
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def run_debug():
    print("Initializing Agent...")
    try:
        agent = CreditRecoveryAgent()
    except Exception as e:
        print(f"Agent Init Error: {e}")
        return

    print("Preparing Data...")
    history_data = [
        {
            'period': '03/2024',
            'paid_amount': 40000.00,
            'paid_regime': 'LUCRO_PRESUMIDO',
            'revenue': 500000.00,
            'payroll': 100000.00,
            'costs': {
                'energia_eletrica': 12000.00,
                'insumos_diretos': 150000.00,
                'aluguel_predios': 10000.00
            }
        }
    ]

    print("Running Analysis...")
    try:
        result = agent.analyze_credits(history_data)
        print("Analysis Result:", result['total_savings'])
    except Exception as e:
        print(f"Analysis Error: {e}")
        import traceback
        traceback.print_exc()
        return

    print("Generating Report...")
    try:
        agent.generate_report(result, filename="debug_report.pdf")
        print("Report Generated.")
    except Exception as e:
        print(f"Report Generation Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
