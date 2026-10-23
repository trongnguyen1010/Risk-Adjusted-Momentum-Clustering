"""Additional conservative CF totals gate for new DStock rows only; never repairs."""
from decimal import Decimal
from .financial_precision_review import residual_decision

CHECKS=[('CASHFLOW_TOTAL',[32000,33000,34000],[35000]),
 ('CASH_ROLL_FORWARD',[36000,35000,36100],[37000]),
 ('CASH_TO_BALANCE_SHEET',[37000],[11100])]

def cash_checks(values):
 rows=[]
 for name,positive,negative in CHECKS:
  keys=positive+negative;missing=sorted(set(keys)-values.keys())
  if missing:rows.append(dict(check=name,difference=None,status='HELD_MISSING_OR_INVALID',missing=missing));continue
  if any(type(values[k]) is bool or values[k] is None for k in keys):
   rows.append(dict(check=name,difference=None,status='HELD_MISSING_OR_INVALID',missing=[]));continue
  try:terms=[Decimal(str(values[k])) for k in keys]
  except (ArithmeticError,ValueError):rows.append(dict(check=name,difference=None,status='HELD_MISSING_OR_INVALID',missing=[]));continue
  if any(not n.is_finite() for n in terms):rows.append(dict(check=name,difference=None,status='HELD_MISSING_OR_INVALID',missing=[]));continue
  difference=sum(Decimal(str(values[k])) for k in positive)-sum(Decimal(str(values[k])) for k in negative)
  rows.append(dict(check=name,difference=str(difference),status=residual_decision(str(difference),terms),missing=[]))
 return dict(quality_gate=all(not r['status'].startswith('HELD') for r in rows),checks=rows)
