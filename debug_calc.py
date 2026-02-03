import pandas as pd
import sys
import os

# Simulating the parsing logic from main.py
def parse_float(val):
    if pd.isna(val) or val == '': return 0.0
    if isinstance(val, (float, int)): return float(val)
    s = str(val).replace('R$', '').replace(' ', '')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    return float(s)

try:
    file_path = "legal_docs/exemplo_auditoria.csv"
    print(f"Reading {file_path}...")
    
    df = pd.read_csv(file_path, sep=';', encoding='utf-8')
    print("Columns:", df.columns.tolist())
    
    column_map = {
        'Periodo': 'periodo',
        'Periodo (MM/AAAA)': 'periodo',
        'Faturamento': 'faturamento',
        'Faturamento Total': 'faturamento',
        'Folha': 'folha',
        'Custo Folha Pagamento': 'folha',
        'Impostos Pagos': 'impostos_pagos',
        'Regime Pagto': 'regime_pagto',
        'Regime Tributario': 'regime_pagto',
        'Custo Energia': 'custo_energia',
        'Custo Insumos': 'custo_insumos',
        'Custo Aluguel': 'custo_aluguel'
    }
    
    df.rename(columns=column_map, inplace=True)
    print("Mapped Columns:", df.columns.tolist())
    
    # Check for required
    required = ['faturamento', 'folha', 'impostos_pagos']
    missing = [c for c in required if c not in df.columns]
    
    if missing:
        print(f"MISSING COLUMNS: {missing}")
    else:
        print("Required columns found.")
        
        # Test Value Parsing
        row = df.iloc[0]
        revenue = parse_float(row['faturamento'])
        print(f"Row 0 Revenue Raw: {row['faturamento']} -> Parsed: {revenue}")
        
    print("Debug complete.")
    
except Exception as e:
    print(f"Error: {e}")
