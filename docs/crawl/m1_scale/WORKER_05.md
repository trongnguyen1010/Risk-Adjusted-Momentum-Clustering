# M1 Scale — Worker 05

## Phạm vi bất biến

- Collector: `collector-05`
- Scale: `m1-scale-20260917T080125Z-ad8cebe3`
- Assignment: `m1-scale-20260917T080125Z-ad8cebe3-worker-05`
- Số mã: `100`
- Range: `2020-01-01 .. 2026-09-15`
- Eligibility: tối thiểu 3 năm usable history; range chung dài 5–15 năm
- Benchmark owner: `false`
- Assignment SHA-256: `4c2ce32b37aeab6ad38dc0692a992a7b1a1945f1181f119e8c061b9d60c5093d`

Không sửa config, assignment, ticker, date range hoặc code. Coordinator phải cung cấp đúng real pilot gate tại `data/input/representative_pilot/gate.json`.
Gate SHA-256 bắt buộc: `fac8cfba89be144e0ef8ceae3885c3b183bc18e066d6d69f53f79d18e894955f`.

## Preflight

```powershell
git status --short
git rev-parse HEAD
Get-FileHash configs/data/m1_scale.assignments.v1/worker-05.json -Algorithm SHA256
Get-FileHash data/input/representative_pilot/gate.json -Algorithm SHA256
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

## Zero-network dry-run

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-05.json `
  --dry-run
```

Chỉ chạy lệnh dưới đây sau khi dry-run in `READINESS=PASS network_requests=0`.

## Real execution

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-05.json `
  --execute
```

## Resume

Không đổi code/config/gate/assignment. Dùng run ID đã được lệnh execute in ra:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-05.json `
  --execute --resume <RUN_ID>
```

## 100 mã được giao

| # | Ticker | Exchange | Security ID |
|---:|---|---|---|
| 1 | APS | HNX | KBS:HNX:APS |
| 2 | BCF | HNX | KBS:HNX:BCF |
| 3 | CAP | HNX | KBS:HNX:CAP |
| 4 | CLH | HNX | KBS:HNX:CLH |
| 5 | DS3 | HNX | KBS:HNX:DS3 |
| 6 | HAD | HNX | KBS:HNX:HAD |
| 7 | HMH | HNX | KBS:HNX:HMH |
| 8 | IPA | HNX | KBS:HNX:IPA |
| 9 | KTS | HNX | KBS:HNX:KTS |
| 10 | MCO | HNX | KBS:HNX:MCO |
| 11 | NSH | HNX | KBS:HNX:NSH |
| 12 | PBP | HNX | KBS:HNX:PBP |
| 13 | PIA | HNX | KBS:HNX:PIA |
| 14 | PRC | HNX | KBS:HNX:PRC |
| 15 | PVB | HNX | KBS:HNX:PVB |
| 16 | SAF | HNX | KBS:HNX:SAF |
| 17 | SJE | HNX | KBS:HNX:SJE |
| 18 | THT | HNX | KBS:HNX:THT |
| 19 | TTT | HNX | KBS:HNX:TTT |
| 20 | VC7 | HNX | KBS:HNX:VC7 |
| 21 | VGP | HNX | KBS:HNX:VGP |
| 22 | VSA | HNX | KBS:HNX:VSA |
| 23 | WSS | HNX | KBS:HNX:WSS |
| 24 | ADS | HOSE | KBS:HOSE:ADS |
| 25 | BCM | HOSE | KBS:HOSE:BCM |
| 26 | CHP | HOSE | KBS:HOSE:CHP |
| 27 | CMX | HOSE | KBS:HOSE:CMX |
| 28 | DAH | HOSE | KBS:HOSE:DAH |
| 29 | DGC | HOSE | KBS:HOSE:DGC |
| 30 | DVP | HOSE | KBS:HOSE:DVP |
| 31 | FIR | HOSE | KBS:HOSE:FIR |
| 32 | GAS | HOSE | KBS:HOSE:GAS |
| 33 | GMH | HOSE | KBS:HOSE:GMH |
| 34 | HCM | HOSE | KBS:HOSE:HCM |
| 35 | HQC | HOSE | KBS:HOSE:HQC |
| 36 | HU1 | HOSE | KBS:HOSE:HU1 |
| 37 | KBC | HOSE | KBS:HOSE:KBC |
| 38 | KSB | HOSE | KBS:HOSE:KSB |
| 39 | LHG | HOSE | KBS:HOSE:LHG |
| 40 | MBB | HOSE | KBS:HOSE:MBB |
| 41 | MWG | HOSE | KBS:HOSE:MWG |
| 42 | NTC | HOSE | KBS:HOSE:NTC |
| 43 | PGI | HOSE | KBS:HOSE:PGI |
| 44 | PLX | HOSE | KBS:HOSE:PLX |
| 45 | S4A | HOSE | KBS:HOSE:S4A |
| 46 | SCS | HOSE | KBS:HOSE:SCS |
| 47 | SRC | HOSE | KBS:HOSE:SRC |
| 48 | SVT | HOSE | KBS:HOSE:SVT |
| 49 | TDP | HOSE | KBS:HOSE:TDP |
| 50 | TNH | HOSE | KBS:HOSE:TNH |
| 51 | TV2 | HOSE | KBS:HOSE:TV2 |
| 52 | VAB | HOSE | KBS:HOSE:VAB |
| 53 | VHC | HOSE | KBS:HOSE:VHC |
| 54 | VMD | HOSE | KBS:HOSE:VMD |
| 55 | A32 | UPCOM | KBS:UPCOM:A32 |
| 56 | ACS | UPCOM | KBS:UPCOM:ACS |
| 57 | ALV | UPCOM | KBS:UPCOM:ALV |
| 58 | BLN | UPCOM | KBS:UPCOM:BLN |
| 59 | BSL | UPCOM | KBS:UPCOM:BSL |
| 60 | C4G | UPCOM | KBS:UPCOM:C4G |
| 61 | CC1 | UPCOM | KBS:UPCOM:CC1 |
| 62 | CKA | UPCOM | KBS:UPCOM:CKA |
| 63 | CMI | UPCOM | KBS:UPCOM:CMI |
| 64 | CQT | UPCOM | KBS:UPCOM:CQT |
| 65 | DDH | UPCOM | KBS:UPCOM:DDH |
| 66 | DNH | UPCOM | KBS:UPCOM:DNH |
| 67 | DRI | UPCOM | KBS:UPCOM:DRI |
| 68 | EIC | UPCOM | KBS:UPCOM:EIC |
| 69 | GPC | UPCOM | KBS:UPCOM:GPC |
| 70 | HAN | UPCOM | KBS:UPCOM:HAN |
| 71 | HEJ | UPCOM | KBS:UPCOM:HEJ |
| 72 | HLS | UPCOM | KBS:UPCOM:HLS |
| 73 | HPH | UPCOM | KBS:UPCOM:HPH |
| 74 | ICN | UPCOM | KBS:UPCOM:ICN |
| 75 | IST | UPCOM | KBS:UPCOM:IST |
| 76 | L62 | UPCOM | KBS:UPCOM:L62 |
| 77 | LMI | UPCOM | KBS:UPCOM:LMI |
| 78 | MGC | UPCOM | KBS:UPCOM:MGC |
| 79 | NAU | UPCOM | KBS:UPCOM:NAU |
| 80 | NTT | UPCOM | KBS:UPCOM:NTT |
| 81 | PCC | UPCOM | KBS:UPCOM:PCC |
| 82 | PHS | UPCOM | KBS:UPCOM:PHS |
| 83 | PWA | UPCOM | KBS:UPCOM:PWA |
| 84 | PXS | UPCOM | KBS:UPCOM:PXS |
| 85 | QNS | UPCOM | KBS:UPCOM:QNS |
| 86 | S74 | UPCOM | KBS:UPCOM:S74 |
| 87 | SCL | UPCOM | KBS:UPCOM:SCL |
| 88 | SEA | UPCOM | KBS:UPCOM:SEA |
| 89 | SKV | UPCOM | KBS:UPCOM:SKV |
| 90 | SWC | UPCOM | KBS:UPCOM:SWC |
| 91 | TDS | UPCOM | KBS:UPCOM:TDS |
| 92 | TLP | UPCOM | KBS:UPCOM:TLP |
| 93 | TST | UPCOM | KBS:UPCOM:TST |
| 94 | TV1 | UPCOM | KBS:UPCOM:TV1 |
| 95 | VCP | UPCOM | KBS:UPCOM:VCP |
| 96 | VGI | UPCOM | KBS:UPCOM:VGI |
| 97 | VIW | UPCOM | KBS:UPCOM:VIW |
| 98 | VNI | UPCOM | KBS:UPCOM:VNI |
| 99 | VTK | UPCOM | KBS:UPCOM:VTK |
| 100 | XMP | UPCOM | KBS:UPCOM:XMP |

## Bàn giao

Bàn giao nguyên trạng control run dưới `data/raw/m1_scale/m1-scale-20260917T080125Z-ad8cebe3/shards/m1-scale-20260917T080125Z-ad8cebe3-worker-05/<RUN_ID>/` và provider raw dưới `data/raw/kbs/<RUN_ID>/`, `data/raw/cafef/<RUN_ID>/`. Không gửi file đã ghép tay, không commit raw và không thay mã lỗi.
