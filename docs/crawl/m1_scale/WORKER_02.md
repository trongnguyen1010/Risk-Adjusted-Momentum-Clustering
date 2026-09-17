# M1 Scale — Worker 02

## Phạm vi bất biến

- Collector: `collector-02`
- Scale: `m1-scale-20260917T080125Z-ad8cebe3`
- Assignment: `m1-scale-20260917T080125Z-ad8cebe3-worker-02`
- Số mã: `100`
- Range: `2020-01-01 .. 2026-09-15`
- Eligibility: tối thiểu 3 năm usable history; range chung dài 5–15 năm
- Benchmark owner: `false`
- Assignment SHA-256: `de1d463371b9349f2c4805807c428c62cf6ecdd2414c3c4a6f06d4b2ba627ef8`

Không sửa config, assignment, ticker, date range hoặc code. Coordinator phải cung cấp đúng real pilot gate tại `data/input/representative_pilot/gate.json`.
Gate SHA-256 bắt buộc: `fac8cfba89be144e0ef8ceae3885c3b183bc18e066d6d69f53f79d18e894955f`.

## Preflight

```powershell
git status --short
git rev-parse HEAD
Get-FileHash configs/data/m1_scale.assignments.v1/worker-02.json -Algorithm SHA256
Get-FileHash data/input/representative_pilot/gate.json -Algorithm SHA256
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m compileall -q src tests scripts run.py
```

## Zero-network dry-run

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-02.json `
  --dry-run
```

Chỉ chạy lệnh dưới đây sau khi dry-run in `READINESS=PASS network_requests=0`.

## Real execution

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-02.json `
  --execute
```

## Resume

Không đổi code/config/gate/assignment. Dùng run ID đã được lệnh execute in ra:

```powershell
.venv\Scripts\python.exe scripts/run_m1_scale_shard.py `
  --config configs/data/m1_scale.v1.json `
  --pilot-gate data/input/representative_pilot/gate.json `
  --assignment configs/data/m1_scale.assignments.v1/worker-02.json `
  --execute --resume <RUN_ID>
```

## 100 mã được giao

| # | Ticker | Exchange | Security ID |
|---:|---|---|---|
| 1 | AMC | HNX | KBS:HNX:AMC |
| 2 | BAB | HNX | KBS:HNX:BAB |
| 3 | BTS | HNX | KBS:HNX:BTS |
| 4 | CDN | HNX | KBS:HNX:CDN |
| 5 | CTT | HNX | KBS:HNX:CTT |
| 6 | EVS | HNX | KBS:HNX:EVS |
| 7 | HJS | HNX | KBS:HNX:HJS |
| 8 | IDC | HNX | KBS:HNX:IDC |
| 9 | KKC | HNX | KBS:HNX:KKC |
| 10 | LDP | HNX | KBS:HNX:LDP |
| 11 | MIC | HNX | KBS:HNX:MIC |
| 12 | NTH | HNX | KBS:HNX:NTH |
| 13 | PCH | HNX | KBS:HNX:PCH |
| 14 | PMB | HNX | KBS:HNX:PMB |
| 15 | PSI | HNX | KBS:HNX:PSI |
| 16 | PVI | HNX | KBS:HNX:PVI |
| 17 | SEB | HNX | KBS:HNX:SEB |
| 18 | STP | HNX | KBS:HNX:STP |
| 19 | TKU | HNX | KBS:HNX:TKU |
| 20 | UNI | HNX | KBS:HNX:UNI |
| 21 | VCS | HNX | KBS:HNX:VCS |
| 22 | VIG | HNX | KBS:HNX:VIG |
| 23 | VTH | HNX | KBS:HNX:VTH |
| 24 | AAM | HOSE | KBS:HOSE:AAM |
| 25 | ANV | HOSE | KBS:HOSE:ANV |
| 26 | BKG | HOSE | KBS:HOSE:BKG |
| 27 | CKG | HOSE | KBS:HOSE:CKG |
| 28 | CTD | HOSE | KBS:HOSE:CTD |
| 29 | DC4 | HOSE | KBS:HOSE:DC4 |
| 30 | DMC | HOSE | KBS:HOSE:DMC |
| 31 | EVE | HOSE | KBS:HOSE:EVE |
| 32 | FMC | HOSE | KBS:HOSE:FMC |
| 33 | GEG | HOSE | KBS:HOSE:GEG |
| 34 | HAR | HOSE | KBS:HOSE:HAR |
| 35 | HHP | HOSE | KBS:HOSE:HHP |
| 36 | HTG | HOSE | KBS:HOSE:HTG |
| 37 | ITC | HOSE | KBS:HOSE:ITC |
| 38 | KHP | HOSE | KBS:HOSE:KHP |
| 39 | LAF | HOSE | KBS:HOSE:LAF |
| 40 | LM8 | HOSE | KBS:HOSE:LM8 |
| 41 | MCM | HOSE | KBS:HOSE:MCM |
| 42 | NAV | HOSE | KBS:HOSE:NAV |
| 43 | PAC | HOSE | KBS:HOSE:PAC |
| 44 | PHR | HOSE | KBS:HOSE:PHR |
| 45 | PTL | HOSE | KBS:HOSE:PTL |
| 46 | SAV | HOSE | KBS:HOSE:SAV |
| 47 | SHI | HOSE | KBS:HOSE:SHI |
| 48 | SSC | HOSE | KBS:HOSE:SSC |
| 49 | TCB | HOSE | KBS:HOSE:TCB |
| 50 | TIX | HOSE | KBS:HOSE:TIX |
| 51 | TNT | HOSE | KBS:HOSE:TNT |
| 52 | TVS | HOSE | KBS:HOSE:TVS |
| 53 | VDS | HOSE | KBS:HOSE:VDS |
| 54 | VID | HOSE | KBS:HOSE:VID |
| 55 | VPG | HOSE | KBS:HOSE:VPG |
| 56 | AAV | UPCOM | KBS:UPCOM:AAV |
| 57 | AG1 | UPCOM | KBS:UPCOM:AG1 |
| 58 | BHP | UPCOM | KBS:UPCOM:BHP |
| 59 | BMV | UPCOM | KBS:UPCOM:BMV |
| 60 | BSQ | UPCOM | KBS:UPCOM:BSQ |
| 61 | CAT | UPCOM | KBS:UPCOM:CAT |
| 62 | CHS | UPCOM | KBS:UPCOM:CHS |
| 63 | CLX | UPCOM | KBS:UPCOM:CLX |
| 64 | CNN | UPCOM | KBS:UPCOM:CNN |
| 65 | CVN | UPCOM | KBS:UPCOM:CVN |
| 66 | DHB | UPCOM | KBS:UPCOM:DHB |
| 67 | DNW | UPCOM | KBS:UPCOM:DNW |
| 68 | DTI | UPCOM | KBS:UPCOM:DTI |
| 69 | FOC | UPCOM | KBS:UPCOM:FOC |
| 70 | H11 | UPCOM | KBS:UPCOM:H11 |
| 71 | HBH | UPCOM | KBS:UPCOM:HBH |
| 72 | HES | UPCOM | KBS:UPCOM:HES |
| 73 | HNF | UPCOM | KBS:UPCOM:HNF |
| 74 | HTM | UPCOM | KBS:UPCOM:HTM |
| 75 | ILA | UPCOM | KBS:UPCOM:ILA |
| 76 | KHW | UPCOM | KBS:UPCOM:KHW |
| 77 | LAI | UPCOM | KBS:UPCOM:LAI |
| 78 | MDF | UPCOM | KBS:UPCOM:MDF |
| 79 | MPC | UPCOM | KBS:UPCOM:MPC |
| 80 | ND2 | UPCOM | KBS:UPCOM:ND2 |
| 81 | NUE | UPCOM | KBS:UPCOM:NUE |
| 82 | PCG | UPCOM | KBS:UPCOM:PCG |
| 83 | PVE | UPCOM | KBS:UPCOM:PVE |
| 84 | PXA | UPCOM | KBS:UPCOM:PXA |
| 85 | QCC | UPCOM | KBS:UPCOM:QCC |
| 86 | QPH | UPCOM | KBS:UPCOM:QPH |
| 87 | SBM | UPCOM | KBS:UPCOM:SBM |
| 88 | SD7 | UPCOM | KBS:UPCOM:SD7 |
| 89 | SGS | UPCOM | KBS:UPCOM:SGS |
| 90 | SSG | UPCOM | KBS:UPCOM:SSG |
| 91 | TAR | UPCOM | KBS:UPCOM:TAR |
| 92 | TGP | UPCOM | KBS:UPCOM:TGP |
| 93 | TOS | UPCOM | KBS:UPCOM:TOS |
| 94 | TTG | UPCOM | KBS:UPCOM:TTG |
| 95 | UDC | UPCOM | KBS:UPCOM:UDC |
| 96 | VDN | UPCOM | KBS:UPCOM:VDN |
| 97 | VHG | UPCOM | KBS:UPCOM:VHG |
| 98 | VLG | UPCOM | KBS:UPCOM:VLG |
| 99 | VPR | UPCOM | KBS:UPCOM:VPR |
| 100 | WSB | UPCOM | KBS:UPCOM:WSB |

## Bàn giao

Bàn giao nguyên trạng control run dưới `data/raw/m1_scale/m1-scale-20260917T080125Z-ad8cebe3/shards/m1-scale-20260917T080125Z-ad8cebe3-worker-02/<RUN_ID>/` và provider raw dưới `data/raw/kbs/<RUN_ID>/`, `data/raw/cafef/<RUN_ID>/`. Không gửi file đã ghép tay, không commit raw và không thay mã lỗi.
