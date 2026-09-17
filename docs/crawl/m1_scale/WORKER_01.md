# M1 Scale — Worker 01

## Phạm vi bất biến

- Collector: `collector-01`
- Scale: `m1-scale-20260917T080125Z-ad8cebe3`
- Assignment: `m1-scale-20260917T080125Z-ad8cebe3-worker-01`
- Số mã: `100`
- Range: `2020-01-01 .. 2026-09-15`
- Eligibility: tối thiểu 3 năm usable history; range chung dài 5–15 năm
- Benchmark owner: `true`
- Assignment SHA-256: `8f5f521fb4e49dcff1eed4b9ba58700b0ac580447ae42da058d39e78eeb7068e`

Không sửa config, assignment, ticker, date range hoặc code. Coordinator phải cung cấp đúng real pilot gate tại `data/input/representative_pilot/gate.json`.
Gate SHA-256 bắt buộc: `fac8cfba89be144e0ef8ceae3885c3b183bc18e066d6d69f53f79d18e894955f`.

## Preflight

```powershell
git status --short
git rev-parse HEAD
Get-FileHash configs/data/m1_scale.assignments.v1/worker-01.json -Algorithm SHA256
Get-FileHash data/input/representative_pilot/gate.json -Algorithm SHA256
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

## Zero-network dry-run

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-01.json `
  --dry-run
```

Chỉ chạy lệnh dưới đây sau khi dry-run in `READINESS=PASS network_requests=0`.

## Real execution

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-01.json `
  --execute
```

## Resume

Không đổi code/config/gate/assignment. Dùng run ID đã được lệnh execute in ra:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-01.json `
  --execute --resume <RUN_ID>
```

## 100 mã được giao

| # | Ticker | Exchange | Security ID |
|---:|---|---|---|
| 1 | ADC | HNX | KBS:HNX:ADC |
| 2 | ATS | HNX | KBS:HNX:ATS |
| 3 | BPC | HNX | KBS:HNX:BPC |
| 4 | CAR | HNX | KBS:HNX:CAR |
| 5 | CMC | HNX | KBS:HNX:CMC |
| 6 | EBS | HNX | KBS:HNX:EBS |
| 7 | HDA | HNX | KBS:HNX:HDA |
| 8 | HMR | HNX | KBS:HNX:HMR |
| 9 | KHS | HNX | KBS:HNX:KHS |
| 10 | L18 | HNX | KBS:HNX:L18 |
| 11 | MDC | HNX | KBS:HNX:MDC |
| 12 | NST | HNX | KBS:HNX:NST |
| 13 | PCE | HNX | KBS:HNX:PCE |
| 14 | PIC | HNX | KBS:HNX:PIC |
| 15 | PSD | HNX | KBS:HNX:PSD |
| 16 | PVG | HNX | KBS:HNX:PVG |
| 17 | SD5 | HNX | KBS:HNX:SD5 |
| 18 | SLS | HNX | KBS:HNX:SLS |
| 19 | TIG | HNX | KBS:HNX:TIG |
| 20 | TV3 | HNX | KBS:HNX:TV3 |
| 21 | VC9 | HNX | KBS:HNX:VC9 |
| 22 | VHE | HNX | KBS:HNX:VHE |
| 23 | VTC | HNX | KBS:HNX:VTC |
| 24 | X20 | HNX | KBS:HNX:X20 |
| 25 | AGR | HOSE | KBS:HOSE:AGR |
| 26 | BFC | HOSE | KBS:HOSE:BFC |
| 27 | CII | HOSE | KBS:HOSE:CII |
| 28 | CRE | HOSE | KBS:HOSE:CRE |
| 29 | DBC | HOSE | KBS:HOSE:DBC |
| 30 | DGW | HOSE | KBS:HOSE:DGW |
| 31 | ELC | HOSE | KBS:HOSE:ELC |
| 32 | FIT | HOSE | KBS:HOSE:FIT |
| 33 | GDT | HOSE | KBS:HOSE:GDT |
| 34 | GTA | HOSE | KBS:HOSE:GTA |
| 35 | HDC | HOSE | KBS:HOSE:HDC |
| 36 | HRC | HOSE | KBS:HOSE:HRC |
| 37 | HUB | HOSE | KBS:HOSE:HUB |
| 38 | KDH | HOSE | KBS:HOSE:KDH |
| 39 | L10 | HOSE | KBS:HOSE:L10 |
| 40 | LIX | HOSE | KBS:HOSE:LIX |
| 41 | MCH | HOSE | KBS:HOSE:MCH |
| 42 | NAF | HOSE | KBS:HOSE:NAF |
| 43 | OCB | HOSE | KBS:HOSE:OCB |
| 44 | PGV | HOSE | KBS:HOSE:PGV |
| 45 | PNJ | HOSE | KBS:HOSE:PNJ |
| 46 | SAB | HOSE | KBS:HOSE:SAB |
| 47 | SHB | HOSE | KBS:HOSE:SHB |
| 48 | SSB | HOSE | KBS:HOSE:SSB |
| 49 | SZC | HOSE | KBS:HOSE:SZC |
| 50 | THG | HOSE | KBS:HOSE:THG |
| 51 | TNI | HOSE | KBS:HOSE:TNI |
| 52 | TVB | HOSE | KBS:HOSE:TVB |
| 53 | VCG | HOSE | KBS:HOSE:VCG |
| 54 | VHM | HOSE | KBS:HOSE:VHM |
| 55 | VND | HOSE | KBS:HOSE:VND |
| 56 | AAS | UPCOM | KBS:UPCOM:AAS |
| 57 | ACV | UPCOM | KBS:UPCOM:ACV |
| 58 | ATG | UPCOM | KBS:UPCOM:ATG |
| 59 | BMF | UPCOM | KBS:UPCOM:BMF |
| 60 | BSP | UPCOM | KBS:UPCOM:BSP |
| 61 | C92 | UPCOM | KBS:UPCOM:C92 |
| 62 | CDR | UPCOM | KBS:UPCOM:CDR |
| 63 | CKD | UPCOM | KBS:UPCOM:CKD |
| 64 | CNC | UPCOM | KBS:UPCOM:CNC |
| 65 | CTW | UPCOM | KBS:UPCOM:CTW |
| 66 | DDV | UPCOM | KBS:UPCOM:DDV |
| 67 | DNL | UPCOM | KBS:UPCOM:DNL |
| 68 | DTC | UPCOM | KBS:UPCOM:DTC |
| 69 | FIC | UPCOM | KBS:UPCOM:FIC |
| 70 | GSM | UPCOM | KBS:UPCOM:GSM |
| 71 | HBD | UPCOM | KBS:UPCOM:HBD |
| 72 | HEP | UPCOM | KBS:UPCOM:HEP |
| 73 | HND | UPCOM | KBS:UPCOM:HND |
| 74 | HPT | UPCOM | KBS:UPCOM:HPT |
| 75 | IFS | UPCOM | KBS:UPCOM:IFS |
| 76 | JOS | UPCOM | KBS:UPCOM:JOS |
| 77 | L63 | UPCOM | KBS:UPCOM:L63 |
| 78 | LTC | UPCOM | KBS:UPCOM:LTC |
| 79 | MGG | UPCOM | KBS:UPCOM:MGG |
| 80 | NBT | UPCOM | KBS:UPCOM:NBT |
| 81 | NTW | UPCOM | KBS:UPCOM:NTW |
| 82 | PCF | UPCOM | KBS:UPCOM:PCF |
| 83 | POM | UPCOM | KBS:UPCOM:POM |
| 84 | PWS | UPCOM | KBS:UPCOM:PWS |
| 85 | QBS | UPCOM | KBS:UPCOM:QBS |
| 86 | QNW | UPCOM | KBS:UPCOM:QNW |
| 87 | SBD | UPCOM | KBS:UPCOM:SBD |
| 88 | SD2 | UPCOM | KBS:UPCOM:SD2 |
| 89 | SGB | UPCOM | KBS:UPCOM:SGB |
| 90 | SRB | UPCOM | KBS:UPCOM:SRB |
| 91 | SZG | UPCOM | KBS:UPCOM:SZG |
| 92 | TED | UPCOM | KBS:UPCOM:TED |
| 93 | TNW | UPCOM | KBS:UPCOM:TNW |
| 94 | TTD | UPCOM | KBS:UPCOM:TTD |
| 95 | TVN | UPCOM | KBS:UPCOM:TVN |
| 96 | VCR | UPCOM | KBS:UPCOM:VCR |
| 97 | VGT | UPCOM | KBS:UPCOM:VGT |
| 98 | VKC | UPCOM | KBS:UPCOM:VKC |
| 99 | VNZ | UPCOM | KBS:UPCOM:VNZ |
| 100 | VW3 | UPCOM | KBS:UPCOM:VW3 |

## Bàn giao

Bàn giao nguyên trạng control run dưới `data/raw/m1_scale/m1-scale-20260917T080125Z-ad8cebe3/shards/m1-scale-20260917T080125Z-ad8cebe3-worker-01/<RUN_ID>/` và provider raw dưới `data/raw/kbs/<RUN_ID>/`, `data/raw/cafef/<RUN_ID>/`. Không gửi file đã ghép tay, không commit raw và không thay mã lỗi.
