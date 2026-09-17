# M1 Scale — Worker 04

## Phạm vi bất biến

- Collector: `collector-04`
- Scale: `m1-scale-20260917T080125Z-ad8cebe3`
- Assignment: `m1-scale-20260917T080125Z-ad8cebe3-worker-04`
- Số mã: `100`
- Range: `2020-01-01 .. 2026-09-15`
- Eligibility: tối thiểu 3 năm usable history; range chung dài 5–15 năm
- Benchmark owner: `false`
- Assignment SHA-256: `440fcbc822629fac5254db0df9c757adb3d92b05d9d0f5f56d30fdf5738e2e57`

Không sửa config, assignment, ticker, date range hoặc code. Coordinator phải cung cấp đúng real pilot gate tại `data/input/representative_pilot/gate.json`.
Gate SHA-256 bắt buộc: `fac8cfba89be144e0ef8ceae3885c3b183bc18e066d6d69f53f79d18e894955f`.

## Preflight

```powershell
git status --short
git rev-parse HEAD
Get-FileHash configs/data/m1_scale.assignments.v1/worker-04.json -Algorithm SHA256
Get-FileHash data/input/representative_pilot/gate.json -Algorithm SHA256
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

## Zero-network dry-run

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-04.json `
  --dry-run
```

Chỉ chạy lệnh dưới đây sau khi dry-run in `READINESS=PASS network_requests=0`.

## Real execution

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-04.json `
  --execute
```

## Resume

Không đổi code/config/gate/assignment. Dùng run ID đã được lệnh execute in ra:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-04.json `
  --execute --resume <RUN_ID>
```

## 100 mã được giao

| # | Ticker | Exchange | Security ID |
|---:|---|---|---|
| 1 | AMV | HNX | KBS:HNX:AMV |
| 2 | BBS | HNX | KBS:HNX:BBS |
| 3 | CAG | HNX | KBS:HNX:CAG |
| 4 | CET | HNX | KBS:HNX:CET |
| 5 | DNC | HNX | KBS:HNX:DNC |
| 6 | GDW | HNX | KBS:HNX:GDW |
| 7 | HLD | HNX | KBS:HNX:HLD |
| 8 | INN | HNX | KBS:HNX:INN |
| 9 | KST | HNX | KBS:HNX:KST |
| 10 | MAS | HNX | KBS:HNX:MAS |
| 11 | MVB | HNX | KBS:HNX:MVB |
| 12 | ONE | HNX | KBS:HNX:ONE |
| 13 | PHN | HNX | KBS:HNX:PHN |
| 14 | PPP | HNX | KBS:HNX:PPP |
| 15 | PV2 | HNX | KBS:HNX:PV2 |
| 16 | S99 | HNX | KBS:HNX:S99 |
| 17 | SGD | HNX | KBS:HNX:SGD |
| 18 | TDT | HNX | KBS:HNX:TDT |
| 19 | TTH | HNX | KBS:HNX:TTH |
| 20 | V21 | HNX | KBS:HNX:V21 |
| 21 | VFS | HNX | KBS:HNX:VFS |
| 22 | VNT | HNX | KBS:HNX:VNT |
| 23 | VTZ | HNX | KBS:HNX:VTZ |
| 24 | ACL | HOSE | KBS:HOSE:ACL |
| 25 | BCE | HOSE | KBS:HOSE:BCE |
| 26 | CCL | HOSE | KBS:HOSE:CCL |
| 27 | CLW | HOSE | KBS:HOSE:CLW |
| 28 | CTS | HOSE | KBS:HOSE:CTS |
| 29 | DCM | HOSE | KBS:HOSE:DCM |
| 30 | DTT | HOSE | KBS:HOSE:DTT |
| 31 | FDC | HOSE | KBS:HOSE:FDC |
| 32 | FRT | HOSE | KBS:HOSE:FRT |
| 33 | GMD | HOSE | KBS:HOSE:GMD |
| 34 | HAX | HOSE | KBS:HOSE:HAX |
| 35 | HID | HOSE | KBS:HOSE:HID |
| 36 | HTV | HOSE | KBS:HOSE:HTV |
| 37 | JVC | HOSE | KBS:HOSE:JVC |
| 38 | KMR | HOSE | KBS:HOSE:KMR |
| 39 | LGL | HOSE | KBS:HOSE:LGL |
| 40 | LSS | HOSE | KBS:HOSE:LSS |
| 41 | MSH | HOSE | KBS:HOSE:MSH |
| 42 | NO1 | HOSE | KBS:HOSE:NO1 |
| 43 | PDV | HOSE | KBS:HOSE:PDV |
| 44 | PLP | HOSE | KBS:HOSE:PLP |
| 45 | QCG | HOSE | KBS:HOSE:QCG |
| 46 | SC5 | HOSE | KBS:HOSE:SC5 |
| 47 | SIP | HOSE | KBS:HOSE:SIP |
| 48 | SVC | HOSE | KBS:HOSE:SVC |
| 49 | TCR | HOSE | KBS:HOSE:TCR |
| 50 | TN1 | HOSE | KBS:HOSE:TN1 |
| 51 | TRC | HOSE | KBS:HOSE:TRC |
| 52 | UIC | HOSE | KBS:HOSE:UIC |
| 53 | VGC | HOSE | KBS:HOSE:VGC |
| 54 | VJC | HOSE | KBS:HOSE:VJC |
| 55 | VVS | HOSE | KBS:HOSE:VVS |
| 56 | ABW | UPCOM | KBS:UPCOM:ABW |
| 57 | AIC | UPCOM | KBS:UPCOM:AIC |
| 58 | BIO | UPCOM | KBS:UPCOM:BIO |
| 59 | BSH | UPCOM | KBS:UPCOM:BSH |
| 60 | BVG | UPCOM | KBS:UPCOM:BVG |
| 61 | CBS | UPCOM | KBS:UPCOM:CBS |
| 62 | CID | UPCOM | KBS:UPCOM:CID |
| 63 | CMF | UPCOM | KBS:UPCOM:CMF |
| 64 | CPI | UPCOM | KBS:UPCOM:CPI |
| 65 | DCT | UPCOM | KBS:UPCOM:DCT |
| 66 | DNA | UPCOM | KBS:UPCOM:DNA |
| 67 | DPC | UPCOM | KBS:UPCOM:DPC |
| 68 | E12 | UPCOM | KBS:UPCOM:E12 |
| 69 | GGG | UPCOM | KBS:UPCOM:GGG |
| 70 | HAM | UPCOM | KBS:UPCOM:HAM |
| 71 | HDW | UPCOM | KBS:UPCOM:HDW |
| 72 | HLB | UPCOM | KBS:UPCOM:HLB |
| 73 | HNM | UPCOM | KBS:UPCOM:HNM |
| 74 | ICI | UPCOM | KBS:UPCOM:ICI |
| 75 | ILS | UPCOM | KBS:UPCOM:ILS |
| 76 | L43 | UPCOM | KBS:UPCOM:L43 |
| 77 | LLM | UPCOM | KBS:UPCOM:LLM |
| 78 | MFS | UPCOM | KBS:UPCOM:MFS |
| 79 | MVN | UPCOM | KBS:UPCOM:MVN |
| 80 | NQN | UPCOM | KBS:UPCOM:NQN |
| 81 | OIL | UPCOM | KBS:UPCOM:OIL |
| 82 | PHP | UPCOM | KBS:UPCOM:PHP |
| 83 | PVX | UPCOM | KBS:UPCOM:PVX |
| 84 | PXM | UPCOM | KBS:UPCOM:PXM |
| 85 | QNC | UPCOM | KBS:UPCOM:QNC |
| 86 | RIC | UPCOM | KBS:UPCOM:RIC |
| 87 | SCJ | UPCOM | KBS:UPCOM:SCJ |
| 88 | SDP | UPCOM | KBS:UPCOM:SDP |
| 89 | SJG | UPCOM | KBS:UPCOM:SJG |
| 90 | STT | UPCOM | KBS:UPCOM:STT |
| 91 | TDB | UPCOM | KBS:UPCOM:TDB |
| 92 | TIS | UPCOM | KBS:UPCOM:TIS |
| 93 | TSD | UPCOM | KBS:UPCOM:TSD |
| 94 | TUG | UPCOM | KBS:UPCOM:TUG |
| 95 | VAV | UPCOM | KBS:UPCOM:VAV |
| 96 | VGG | UPCOM | KBS:UPCOM:VGG |
| 97 | VIN | UPCOM | KBS:UPCOM:VIN |
| 98 | VNB | UPCOM | KBS:UPCOM:VNB |
| 99 | VST | UPCOM | KBS:UPCOM:VST |
| 100 | XMD | UPCOM | KBS:UPCOM:XMD |

## Bàn giao

Bàn giao nguyên trạng control run dưới `data/raw/m1_scale/m1-scale-20260917T080125Z-ad8cebe3/shards/m1-scale-20260917T080125Z-ad8cebe3-worker-04/<RUN_ID>/` và provider raw dưới `data/raw/kbs/<RUN_ID>/`, `data/raw/cafef/<RUN_ID>/`. Không gửi file đã ghép tay, không commit raw và không thay mã lỗi.
