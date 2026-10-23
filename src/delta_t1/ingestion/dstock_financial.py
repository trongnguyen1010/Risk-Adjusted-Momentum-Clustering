"""Pinned public DStock schema; complete vectors, no value/sign inference."""
import json
from collections import defaultdict
from decimal import Decimal
from urllib.parse import urlencode

HOST='api-finfo.vndirect.com.vn'
SCHEMA={
 11000:('current_assets','Tài sản ngắn hạn'),12000:('noncurrent_assets','Tài sản dài hạn'),
 12700:('total_assets','TỔNG CỘNG TÀI SẢN'),13000:('total_liabilities','Nợ phải trả'),
 13100:('current_liabilities','Nợ ngắn hạn'),13300:('noncurrent_liabilities','Nợ dài hạn'),
 14000:('total_equity','Vốn chủ sở hữu'),14400:('total_capital','TỔNG CỘNG NGUỒN VỐN'),
 12210:('net_tangible_ppe','Tài sản cố định hữu hình'),12220:('owned_tangible_ppe_cost','Nguyên giá TSCĐHH'),
 12230:('owned_tangible_ppe_accumulated_depreciation','Hao mòn TSCĐHH'),
 21000:('gross_revenue','Tổng doanh thu hoạt động kinh doanh'),21090:('revenue_deductions','Các khoản giảm trừ doanh thu'),
 21001:('net_revenue','Doanh thu thuần'),22100:('cost_of_goods_sold','Giá vốn hàng bán'),
 23100:('gross_profit','Lợi nhuận gộp'),21500:('finance_income','Doanh thu hoạt động tài chính'),
 22500:('finance_expense','Chi phí tài chính'),22510:('interest_expense','Trong đó: Chi phí lãi vay'),
 23300:('associate_profit','Lợi nhuận hoặc lỗ trong công ty liên kết'),22110:('selling_expense','Chi phí bán hàng'),
 22200:('administrative_expense','Chi phí quản lý doanh nghiệp'),23110:('reported_operating_profit','Lợi nhuận thuần từ hoạt động kinh doanh'),
 21900:('other_income','Thu nhập khác'),22900:('other_expense','Chi phí khác'),23900:('other_profit','Lợi nhuận khác'),
 23800:('profit_before_tax','Lợi nhuận kế toán trước thuế'),22051:('current_tax_expense','Chi phí thuế TNDN hiện hành'),
 22052:('deferred_tax_expense','Chi phí thuế TNDN hoãn lại'),23003:('net_profit','Lợi nhuận sau thuế thu nhập doanh nghiệp'),
 23000:('parent_net_profit','Lợi nhuận sau thuế của Công ty mẹ'),23500:('noncontrolling_profit','Lợi ích của cổ đông thiểu số'),
 32000:('operating_cash_flow','Lưu chuyển tiền thuần từ hoạt động kinh doanh')}
CFO_CODES=[31120,31130,31140,31150,31160,31170,31180,31190,31200]

def norm(s):return ' '.join(s.split()).casefold()

def model_index(payload):
 if payload.get('totalPages')!=1 or len(payload.get('data',[]))!=payload.get('totalElements'):raise ValueError('MODEL_PAGINATION_INCOMPLETE')
 result=defaultdict(list)
 for r in payload['data']:
  code=int(r['itemCode'])
  if code not in SCHEMA:continue
  field,label=SCHEMA[code]
  # Labels are pinned schema evidence, not row offsets; no fuzzy aliases.
  if norm(r['itemVnName'])!=norm(label):raise ValueError('MODEL_LABEL_CHANGED:'+str(code)+':'+r['itemVnName'])
  if r['companyForm']!='NON_FINANCE' or r['modelType'] not in [1,2,3]:raise ValueError('MODEL_FAMILY_CHANGED')
  result[code].append(r)
 if set(result)!=set(SCHEMA):raise ValueError('MODEL_SCHEMA_INCOMPLETE')
 return result

def url(symbols,year,page=1,size=2000):
 if not 1<=len(symbols)<=5 or len(set(symbols))!=len(symbols):raise ValueError('BOUNDED_UNIQUE_GROUP_REQUIRED')
 if any(not s.isalnum() or not s.isascii() for s in symbols) or not 2016<=year<=2025:raise ValueError('INVALID_TARGET')
 return 'https://'+HOST+'/v4/financial_statements?'+urlencode(dict(q='code:'+','.join(symbols)+'~reportType:ANNUAL~fiscalDate:'+str(year)+'-12-31',sort='fiscalDate',size=size,page=page))

def parse_page(raw, symbols, year, page):
 d=json.loads(raw,parse_float=Decimal)
 if not isinstance(d,dict) or not isinstance(d.get('data'),list):raise ValueError('INVALID_ENVELOPE')
 if d.get('currentPage')!=page or type(d.get('totalPages')) is not int or not 0<=d['totalPages']<=5:raise ValueError('PAGINATION_REVIEW_REQUIRED')
 if len(d['data'])>2000 or d.get('size')!=2000 or type(d.get('totalElements')) is not int:raise ValueError('INVALID_PAGE_LIMIT')
 for r in d['data']:
  if r.get('code') not in symbols or r.get('reportType')!='ANNUAL' or r.get('fiscalDate')!=f'{year}-12-31':raise ValueError('UNEXPECTED_ENTITY_PERIOD')
 return d

def vector(rows, symbol, year, models):
 values={};observations=[];reasons=[];codes={};seen=set()
 for r in rows:
  if r['code']!=symbol:continue
  code=int(r['itemCode']);key=(r['code'],r['fiscalDate'],r['reportType'],r['modelType'],code)
  if key in seen:reasons.append('DUPLICATE_PROVIDER_KEY')
  seen.add(key)
  if r['fiscalDate']!=f'{year}-12-31' or r['reportType']!='ANNUAL':reasons.append('ENTITY_PERIOD_MISMATCH');continue
  value=r.get('numericValue')
  if type(value) is bool or value is None:continue
  try:number=Decimal(str(value))
  except (ArithmeticError,ValueError):reasons.append('INVALID_NUMBER');continue
  if not number.is_finite():reasons.append('NONFINITE');continue
  if code in codes:reasons.append('DUPLICATE_ITEM_CODE')
  codes[code]=number
  if code not in SCHEMA:continue
  meta=[m for m in models[code] if symbol in m['codeList'].split(',') and m['modelType']==r['modelType']]
  if len(meta)!=1:reasons.append('MODEL_MEMBERSHIP_OR_SCOPE_AMBIGUOUS');continue
  field=SCHEMA[code][0];values[field]=str(number)
  observations.append(dict(field=field,item_code=code,model_type=int(r['modelType']),numeric_value=str(number),created_at=r.get('createdDate'),modified_at=r.get('modifiedDate'),model_note=meta[0]['note']))
 if not rows:reasons.append('NO_OBSERVATIONS')
 cfo=None
 if all(c in codes for c in CFO_CODES+[32000]):
  cfo=str(sum(codes[c] for c in CFO_CODES)-codes[32000])
  # Direct and indirect component schemes must not be combined or inferred.
 return dict(values=values,observations=observations,reasons=sorted(set(reasons)),cfo_component_residual=cfo,
             cfo_component_completeness='UNVERIFIED_PROVIDER_DECOMPOSITION_DIAGNOSTIC_ONLY')
