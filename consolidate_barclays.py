#!/usr/bin/env python3
r"""
Consolidate all Barclays CSV bank statements into a single deduplicated JSON file.
Reads from: C:\Users\lvqua\OneDrive\Desktop\Work Life Management\01 Life\01 Finance\Reconciliation with bank accounts\Barclays
Outputs:  barclays_consolidated.json  (in the same directory as this script)
"""

import csv
import json
import os
import glob
from pathlib import Path

BARCLAYS_ROOT = r"C:\Users\lvqua\OneDrive\Desktop\Work Life Management\01 Life\01 Finance\Reconciliation with bank accounts\Barclays"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "barclays_consolidated.json")

def parse_barclays_csv(filepath):
    """Parse a single Barclays CSV file and return list of transaction dicts."""
    transactions = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    lines = content.strip().split('\n')
    if len(lines) < 2:
        return []
    
    # Strip leading tabs and whitespace
    lines = [l.lstrip('\t').strip() for l in lines if l.strip()]
    
    # Parse header
    header = lines[0].lower().split(',')
    header = [h.strip().strip('"') for h in header]
    
    # Find column indices
    date_idx = next((i for i, h in enumerate(header) if 'date' in h), 1)
    account_idx = next((i for i, h in enumerate(header) if 'account' in h), 2)
    amount_idx = next((i for i, h in enumerate(header) if 'amount' in h), 3)
    subcat_idx = next((i for i, h in enumerate(header) if 'subcategory' in h or 'type' in h), 4)
    memo_idx = next((i for i, h in enumerate(header) if 'memo' in h or 'description' in h), 5)
    
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Parse CSV fields (handle quoted fields)
        row = []
        in_quote = False
        field = ''
        for ch in line:
            if ch == '"':
                in_quote = not in_quote
                continue
            if ch == ',' and not in_quote:
                row.append(field.strip())
                field = ''
                continue
            field += ch
        row.append(field.strip())
        
        if len(row) <= max(date_idx, amount_idx):
            continue
        
        raw_date = row[date_idx] if date_idx < len(row) else ''
        raw_amount = row[amount_idx] if amount_idx < len(row) else '0'
        account = row[account_idx] if account_idx < len(row) else ''
        subcategory = row[subcat_idx] if subcat_idx < len(row) else ''
        memo = row[memo_idx] if memo_idx < len(row) else ''
        
        # Clean memo: extract payee from tab-separated content
        if '\t' in memo:
            parts = [p.strip() for p in memo.split('\t') if p.strip()]
            payee = parts[0] if parts else memo
            reference = parts[1] if len(parts) > 1 else ''
        else:
            payee = memo
            reference = ''
        
        # Clean up payee name (remove trailing whitespace)
        payee = ' '.join(payee.split())
        
        # Parse amount
        try:
            amount = float(raw_amount.replace('£', '').replace('$', '').replace(',', ''))
        except ValueError:
            amount = 0.0
        
        if not raw_date and amount == 0:
            continue
        
        # Parse date DD/MM/YYYY -> YYYY-MM-DD
        parsed_date = raw_date
        parts = raw_date.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = '20' + year
            parsed_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        transactions.append({
            'date': parsed_date,
            'description': payee,
            'amount': amount,
            'subcategory': subcategory,
            'reference': reference,
            'account': account,
        })
    
    return transactions


def deduplicate(transactions):
    """Deduplicate transactions by (date, amount, description, reference)."""
    seen = set()
    unique = []
    for t in transactions:
        # Create a dedup key from date + amount + description + reference
        key = (t['date'], t['amount'], t['description'], t['reference'])
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


def main():
    all_transactions = []
    file_count = 0
    
    # Walk all subdirectories
    for root, dirs, files in os.walk(BARCLAYS_ROOT):
        for fname in files:
            if fname.lower().endswith('.csv'):
                filepath = os.path.join(root, fname)
                txns = parse_barclays_csv(filepath)
                subfolder = os.path.relpath(root, BARCLAYS_ROOT)
                print(f"  {subfolder}/{fname}: {len(txns)} transactions")
                all_transactions.extend(txns)
                file_count += 1
    
    print(f"\nTotal files: {file_count}")
    print(f"Total raw transactions: {len(all_transactions)}")
    
    # Deduplicate
    unique = deduplicate(all_transactions)
    print(f"After deduplication: {len(unique)}")
    
    # Sort by date descending
    unique.sort(key=lambda t: t['date'], reverse=True)
    
    # Get date range
    if unique:
        earliest = unique[-1]['date']
        latest = unique[0]['date']
        print(f"Date range: {earliest} to {latest}")
    
    # Get unique accounts
    accounts = set(t['account'] for t in unique if t['account'])
    print(f"Accounts found: {len(accounts)}")
    for acc in sorted(accounts):
        count = sum(1 for t in unique if t['account'] == acc)
        print(f"  {acc}: {count} transactions")
    
    # Summary by subcategory
    subcats = {}
    for t in unique:
        sc = t['subcategory'] or 'Unknown'
        subcats[sc] = subcats.get(sc, 0) + 1
    print("\nTransaction types:")
    for sc, count in sorted(subcats.items(), key=lambda x: -x[1]):
        print(f"  {sc}: {count}")
    
    # Write output
    output = {
        'source': 'Barclays',
        'generated': __import__('datetime').datetime.now().isoformat(),
        'totalFiles': file_count,
        'totalTransactions': len(unique),
        'dateRange': {'from': earliest if unique else '', 'to': latest if unique else ''},
        'accounts': sorted(list(accounts)),
        'transactions': unique
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Written {len(unique)} transactions to {OUTPUT_FILE}")
    print(f"  File size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")


if __name__ == '__main__':
    main()
