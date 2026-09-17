# M1 Scale — Worker 03

## Phạm vi bất biến

- Collector: `collector-03`
- Scale: `m1-scale-20260917T080125Z-ad8cebe3`
- Assignment: `m1-scale-20260917T080125Z-ad8cebe3-worker-03`
- Số mã: `100`
- Range: `2020-01-01 .. 2026-09-15`
- Eligibility: tối thiểu 3 năm usable history; range chung dài 5–15 năm
- Benchmark owner: `false`
- Assignment SHA-256: `e44e254bc0f535032ebf2457cba1e9ba8d46c82857b3df3b75de6bcd8ee9bf76`

Không sửa config, assignment, ticker, date range hoặc code. Coordinator phải cung cấp đúng real pilot gate tại `data/input/representative_pilot/gate.json`.
Gate SHA-256 bắt buộc: `fac8cfba89be144e0ef8ceae3885c3b183bc18e066d6d69f53f79d18e894955f`.

## Preflight

```powershell
git status --short
git rev-parse HEAD
Get-FileHash configs/data/m1_scale.assignments.v1/worker-03.json -Algorithm SHA256
Get-FileHash data/input/representative_pilot/gate.json -Algorithm SHA256
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

## Zero-network dry-run

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-03.json `
  --dry-run
```

Chỉ chạy lệnh dưới đây sau khi dry-run in `READINESS=PASS network_requests=0`.

## Real execution

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-03.json `
  --execute
```

## Resume

Không đổi code/config/gate/assignment. Dùng run ID đã được lệnh execute in ra:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-03.json `
  --execute --resume <RUN_ID>
```

## 100 mã được giao

| # | Ticker | Exchange | Security ID |
|---:|---|---|---|
| 1 | AME | HNX | KBS:HNX:AME |
| 2 | BAX | HNX | KBS:HNX:BAX |
| 3 | BTW | HNX | KBS:HNX:BTW |
| 4 | CEO | HNX | KBS:HNX:CEO |
| 5 | DC2 | HNX | KBS:HNX:DC2 |
| 6 | FID | HNX | KBS:HNX:FID |
| 7 | HLC | HNX | KBS:HNX:HLC |
| 8 | IDV | HNX | KBS:HNX:IDV |
| 9 | KSD | HNX | KBS:HNX:KSD |
| 10 | MAC | HNX | KBS:HNX:MAC |
| 11 | MKV | HNX | KBS:HNX:MKV |
| 12 | NTP | HNX | KBS:HNX:NTP |
| 13 | PGS | HNX | KBS:HNX:PGS |
| 14 | PPE | HNX | KBS:HNX:PPE |
| 15 | PTD | HNX | KBS:HNX:PTD |
| 16 | S55 | HNX | KBS:HNX:S55 |
| 17 | SED | HNX | KBS:HNX:SED |
| 18 | SVN | HNX | KBS:HNX:SVN |
| 19 | TMX | HNX | KBS:HNX:TMX |
| 20 | V12 | HNX | KBS:HNX:V12 |
| 21 | VE3 | HNX | KBS:HNX:VE3 |
| 22 | VMC | HNX | KBS:HNX:VMC |
| 23 | VTV | HNX | KBS:HNX:VTV |
| 24 | ACC | HOSE | KBS:HOSE:ACC |
| 25 | AST | HOSE | KBS:HOSE:AST |
| 26 | BVH | HOSE | KBS:HOSE:BVH |
| 27 | CLC | HOSE | KBS:HOSE:CLC |
| 28 | CTR | HOSE | KBS:HOSE:CTR |
| 29 | DCL | HOSE | KBS:HOSE:DCL |
| 30 | DTA | HOSE | KBS:HOSE:DTA |
| 31 | EVF | HOSE | KBS:HOSE:EVF |
| 32 | FPT | HOSE | KBS:HOSE:FPT |
| 33 | GHC | HOSE | KBS:HOSE:GHC |
| 34 | HAS | HOSE | KBS:HOSE:HAS |
| 35 | HHV | HOSE | KBS:HOSE:HHV |
| 36 | HTN | HOSE | KBS:HOSE:HTN |
| 37 | ITD | HOSE | KBS:HOSE:ITD |
| 38 | KLB | HOSE | KBS:HOSE:KLB |
| 39 | LDG | HOSE | KBS:HOSE:LDG |
| 40 | LPB | HOSE | KBS:HOSE:LPB |
| 41 | MCP | HOSE | KBS:HOSE:MCP |
| 42 | NNC | HOSE | KBS:HOSE:NNC |
| 43 | PDN | HOSE | KBS:HOSE:PDN |
| 44 | PIT | HOSE | KBS:HOSE:PIT |
| 45 | PVP | HOSE | KBS:HOSE:PVP |
| 46 | SBV | HOSE | KBS:HOSE:SBV |
| 47 | SHP | HOSE | KBS:HOSE:SHP |
| 48 | STK | HOSE | KBS:HOSE:STK |
| 49 | TCL | HOSE | KBS:HOSE:TCL |
| 50 | TMT | HOSE | KBS:HOSE:TMT |
| 51 | TPB | HOSE | KBS:HOSE:TPB |
| 52 | TVT | HOSE | KBS:HOSE:TVT |
| 53 | VFG | HOSE | KBS:HOSE:VFG |
| 54 | VIX | HOSE | KBS:HOSE:VIX |
| 55 | VSI | HOSE | KBS:HOSE:VSI |
| 56 | ABI | UPCOM | KBS:UPCOM:ABI |
| 57 | AGX | UPCOM | KBS:UPCOM:AGX |
| 58 | BIG | UPCOM | KBS:UPCOM:BIG |
| 59 | BRS | UPCOM | KBS:UPCOM:BRS |
| 60 | BTU | UPCOM | KBS:UPCOM:BTU |
| 61 | CBI | UPCOM | KBS:UPCOM:CBI |
| 62 | CI5 | UPCOM | KBS:UPCOM:CI5 |
| 63 | CMD | UPCOM | KBS:UPCOM:CMD |
| 64 | CNT | UPCOM | KBS:UPCOM:CNT |
| 65 | DC1 | UPCOM | KBS:UPCOM:DC1 |
| 66 | DID | UPCOM | KBS:UPCOM:DID |
| 67 | DP1 | UPCOM | KBS:UPCOM:DP1 |
| 68 | DWS | UPCOM | KBS:UPCOM:DWS |
| 69 | FOX | UPCOM | KBS:UPCOM:FOX |
| 70 | HAF | UPCOM | KBS:UPCOM:HAF |
| 71 | HD6 | UPCOM | KBS:UPCOM:HD6 |
| 72 | HHG | UPCOM | KBS:UPCOM:HHG |
| 73 | HNG | UPCOM | KBS:UPCOM:HNG |
| 74 | HWS | UPCOM | KBS:UPCOM:HWS |
| 75 | ILC | UPCOM | KBS:UPCOM:ILC |
| 76 | KIP | UPCOM | KBS:UPCOM:KIP |
| 77 | LIC | UPCOM | KBS:UPCOM:LIC |
| 78 | MEC | UPCOM | KBS:UPCOM:MEC |
| 79 | MSR | UPCOM | KBS:UPCOM:MSR |
| 80 | NOS | UPCOM | KBS:UPCOM:NOS |
| 81 | ODE | UPCOM | KBS:UPCOM:ODE |
| 82 | PFL | UPCOM | KBS:UPCOM:PFL |
| 83 | PVL | UPCOM | KBS:UPCOM:PVL |
| 84 | PXI | UPCOM | KBS:UPCOM:PXI |
| 85 | QHW | UPCOM | KBS:UPCOM:QHW |
| 86 | QSP | UPCOM | KBS:UPCOM:QSP |
| 87 | SCD | UPCOM | KBS:UPCOM:SCD |
| 88 | SDA | UPCOM | KBS:UPCOM:SDA |
| 89 | SID | UPCOM | KBS:UPCOM:SID |
| 90 | SSH | UPCOM | KBS:UPCOM:SSH |
| 91 | TCD | UPCOM | KBS:UPCOM:TCD |
| 92 | THW | UPCOM | KBS:UPCOM:THW |
| 93 | TOW | UPCOM | KBS:UPCOM:TOW |
| 94 | TTS | UPCOM | KBS:UPCOM:TTS |
| 95 | USC | UPCOM | KBS:UPCOM:USC |
| 96 | VEA | UPCOM | KBS:UPCOM:VEA |
| 97 | VIM | UPCOM | KBS:UPCOM:VIM |
| 98 | VLW | UPCOM | KBS:UPCOM:VLW |
| 99 | VSE | UPCOM | KBS:UPCOM:VSE |
| 100 | XMC | UPCOM | KBS:UPCOM:XMC |

## Bàn giao

Bàn giao nguyên trạng control run dưới `data/raw/m1_scale/m1-scale-20260917T080125Z-ad8cebe3/shards/m1-scale-20260917T080125Z-ad8cebe3-worker-03/<RUN_ID>/` và provider raw dưới `data/raw/kbs/<RUN_ID>/`, `data/raw/cafef/<RUN_ID>/`. Không gửi file đã ghép tay, không commit raw và không thay mã lỗi.
