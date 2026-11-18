param(
    [ValidateSet('setup','process','verify')][string]$Action = 'verify',
    [switch]$Network,
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) { $Python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    if ($Action -eq 'setup') {
        $setupArgs=@('scripts/setup_financial_ocr.py')
        if ($Network) { $setupArgs+='--network' }
        & $Python @setupArgs
        if ($LASTEXITCODE) { throw 'OCR setup failed closed' }
        return
    }
    $documentConfigs=@(
        'configs/data/financial_history_documents_v2.json',
        'configs/data/financial_history_documents_gmd2014_v1.json',
        'configs/data/financial_history_documents_mwg2015_v1.json',
        'configs/data/financial_history_documents_brc2015_v1.json',
        'configs/data/financial_history_documents_audit_gmd_v1.json',
        'configs/data/financial_history_documents_audit_brc_v1.json',
        'configs/data/financial_history_documents_audit_fpt2015q3_v1.json',
        'configs/data/financial_history_documents_audit_vcs2015_v1.json',
        'configs/data/financial_history_documents_audit_fox_v1.json',
        'configs/data/financial_history_documents_audit_dbc2022_v1.json',
        'configs/data/financial_history_documents_critical_gas_shs2025_v1.json',
        'configs/data/financial_history_documents_critical_shs2025_en_v1.json'
    )
    foreach ($config in $documentConfigs) {
        if ($Action -eq 'process') {
            $docArgs=@('scripts/financial_history_documents.py','run','--config',$config)
            if ($Network) { $docArgs+='--network' }
            & $Python @docArgs
            if ($LASTEXITCODE) { throw "Document acquisition failed closed: $config" }
            & $Python scripts/financial_history_documents.py extract --config $config
        } else {
            & $Python scripts/financial_history_documents.py verify --config $config
        }
        if ($LASTEXITCODE) { throw "Document processing failed closed: $config" }
    }
    $replayAction=if ($Action -eq 'process') { 'run' } else { 'verify' }
    & $Python scripts/financial_ocr_campaign.py $replayAction --config configs/data/financial_ocr_campaign_v10.json
    if ($LASTEXITCODE) { throw 'Campaign OCR budgets/replay failed closed' }
    & $Python scripts/financial_candidate_units.py $replayAction
    if ($LASTEXITCODE) { throw 'Provider unit evidence replay failed closed' }
    & $Python scripts/financial_history_review.py $replayAction
    if ($LASTEXITCODE) { throw 'Original review replay failed closed' }
    & $Python scripts/financial_reviewed_batch.py $replayAction --config configs/data/financial_reviewed_batch_v8.json
    if ($LASTEXITCODE) { throw 'Reviewed history bundle failed closed' }
    & $Python scripts/financial_history_audit_plan.py $replayAction
    if ($LASTEXITCODE) { throw 'Seeded independent audit plan failed closed' }
    & $Python scripts/financial_history_audit_review.py $replayAction
    if ($LASTEXITCODE) { throw 'Independent document field audit failed closed' }
    # These stages replay offline here. Network work uses its dedicated bounded CLI.
    & $Python scripts/financial_history_stage_gate.py verify
    if ($LASTEXITCODE) { throw 'F2 engineering gate verification failed closed' }
    & $Python scripts/financial_history20_metadata.py verify
    if ($LASTEXITCODE) { throw 'Total20 profile acquisition verification failed closed' }
    & $Python scripts/financial_history20_profiles.py verify
    if ($LASTEXITCODE) { throw 'Current profile metadata verification failed closed' }
    & $Python scripts/financial_history20_probes.py verify
    if ($LASTEXITCODE) { throw 'Financial template probes verification failed closed' }
    & $Python scripts/financial_template_candidates.py $replayAction
    if ($LASTEXITCODE) { throw 'Ambiguous financial template quarantine replay failed closed' }
    & $Python scripts/financial_reference_cohorts.py $replayAction
    if ($LASTEXITCODE) { throw 'Reviewed report-vintage cohort reference replay failed closed' }
    & $Python scripts/financial_history_batch.py verify
    if ($LASTEXITCODE) { throw 'Completed F3 history acquisition verification failed closed' }
    & $Python scripts/financial_history_batch_qa.py $replayAction
    if ($LASTEXITCODE) { throw 'Sealed F3 history candidate QA failed closed' }
    & $Python scripts/financial_history_catalogues.py verify
    if ($LASTEXITCODE) { throw 'F3 public catalogue acquisition verification failed closed' }
    & $Python scripts/financial_catalogue_rows.py $replayAction
    if ($LASTEXITCODE) { throw 'F3 catalogue row parsing failed closed' }
    & $Python scripts/financial_history_batch_audit.py $replayAction
    if ($LASTEXITCODE) { throw 'F3 seeded independent audit selection failed closed' }
    & $Python scripts/financial_candidate_units.py $replayAction --config configs/data/financial_candidate_units_batch20_v1.json
    if ($LASTEXITCODE) { throw 'F3 provider monetary unit overlay failed closed' }
    & $Python data/financial/history20_public_discovery_v1/acquire-fox-catalogues-v2.py
    if ($LASTEXITCODE) { throw 'FOX issuer catalogue evidence replay failed closed' }
    & $Python scripts/financial_history_audit_review.py $replayAction --config configs/data/financial_history_batch20_audit_review_v3.json
    if ($LASTEXITCODE) { throw 'F3 independent document field audit replay failed closed' }
    foreach ($observationScript in @(
        'data/financial/history20_public_discovery_v1/acquire-bmsc-catalogue-v1.py',
        'data/financial/history20_public_discovery_v1/acquire-critical-catalogues-v1.py',
        'data/financial/history20_public_discovery_v1/acquire-vdsc-catalogues-v1.py'
    )) {
        & $Python $observationScript
        if ($LASTEXITCODE) { throw "Public source observation replay failed closed: $observationScript" }
    }
    & $Python scripts/financial_critical_review.py $replayAction
    if ($LASTEXITCODE) { throw 'Critical source partition quarantine replay failed closed' }
    & $Python scripts/financial_reference_cohorts.py $replayAction --config configs/data/financial_reference_cohorts_gas_v1.json
    if ($LASTEXITCODE) { throw 'GAS PDF report-vintage reference replay failed closed' }
} finally { Pop-Location }
