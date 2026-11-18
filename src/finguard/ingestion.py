"""SAML-D loader. Labels are retained separately and never enter model prompts."""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = {'Time','Date','Sender_account','Receiver_account','Amount','Payment_currency','Received_currency','Sender_bank_location','Receiver_bank_location','Payment_type'}

def load_transactions(path, limit=None):
    transactions, labels, errors = [], {}, []
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')
        for row_num, row in enumerate(reader, start=2):
            if limit is not None and len(transactions) >= limit:
                break
            try:
                amount = Decimal(row['Amount'].strip())
                if not amount.is_finite() or amount <= 0:
                    raise ValueError('Amount must be finite and positive')
                dt = datetime.strptime(row['Date'].strip()+' '+row['Time'].strip(), '%Y-%m-%d %H:%M:%S')
                if not row['Sender_account'].strip() or not row['Receiver_account'].strip():
                    raise ValueError('Account identifiers are required')
                tid = f'row-{row_num}'
                transactions.append({'transaction_id':tid, 'timestamp':dt.isoformat(), 'source_account':row['Sender_account'].strip(), 'destination_account':row['Receiver_account'].strip(), 'amount':str(amount), 'payment_currency':row['Payment_currency'].strip(), 'received_currency':row['Received_currency'].strip(), 'origin_country':row['Sender_bank_location'].strip(), 'destination_country':row['Receiver_bank_location'].strip(), 'payment_type':row['Payment_type'].strip()})
                if 'Is_laundering' in row:
                    labels[tid] = {'is_laundering':row['Is_laundering'].strip(), 'laundering_type':row.get('Laundering_type','').strip()}
            except (ValueError, InvalidOperation, KeyError) as exc:
                errors.append({'source_row':row_num,'reason':str(exc)})
    return transactions, labels, errors
