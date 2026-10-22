"""
Script to assemble and verify M2 Task 13 Handoff Package for Milestone M3.
Adheres strictly to M2/Ke_hoach_M2_Phan_cum_co_phieu.md (Nhiệm vụ 13).
"""

import os
import sys
import glob
import json
import hashlib
import shutil
import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    base_dir = os.path.abspath(".")
    handoff_dir = os.path.join(base_dir, "M2", "artifacts", "m2-final-handoff-v1")
    models_dir = os.path.join(base_dir, "M2", "models", "final_selected_model")
    holdout_models_dir = os.path.join(base_dir, "M2", "models", "holdout")
    
    os.makedirs(handoff_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    print("=== Step 1: Copy Holdout Models to final_selected_model ===")
    holdout_model_files = sorted(glob.glob(os.path.join(holdout_models_dir, "*.json")))
    for mf in holdout_model_files:
        dest = os.path.join(models_dir, os.path.basename(mf))
        shutil.copy2(mf, dest)
        print(f"Copied {os.path.basename(mf)} to final_selected_model")
        
    all_models = sorted(glob.glob(os.path.join(models_dir, "*.json")))
    all_model_names = [os.path.basename(m) for m in all_models if os.path.basename(m) != "model_file_manifest.json"]
    print(f"Total model files in final_selected_model: {len(all_model_names)}")
    assert len(all_model_names) == 22, f"Expected 22 models, got {len(all_model_names)}"
    
    # Generate model_file_manifest_22m.json for full 22-snapshot inventory
    # (Preserve model_file_manifest.json intact for freeze_gate in delta_t1)
    model_manifest_22m = {
        "milestone": "M2_FINAL_SELECTED_MODEL_22_SNAPSHOTS",
        "algorithm": "KMeans_Baseline",
        "global_k": 2,
        "n_models": len(all_model_names),
        "files": {
            m: compute_sha256(os.path.join(models_dir, m)) for m in all_model_names
        }
    }
    with open(os.path.join(models_dir, "model_file_manifest_22m.json"), "w", encoding="utf-8") as f:
        json.dump(model_manifest_22m, f, indent=2)
    print("Generated model_file_manifest_22m.json (model_file_manifest.json preserved)")
    
    print("\n=== Step 2: Build m2_cluster_labels_for_m3.csv ===")
    # Dev assignments
    dev_members = pd.read_csv("M2/artifacts/m2-evaluation-kmeans/cluster_profile_members.csv")
    dev_t4 = pd.read_csv("M2/artifacts/m2-task4-kmeans-baseline-v1/assignments.csv")
    # Ticker mapping from dev_t4
    ticker_map = dict(zip(dev_t4['security_id'], dev_t4['ticker']))
    dev_members['ticker'] = dev_members['security_id'].map(ticker_map)
    # Fill any missing from security_id
    dev_members['ticker'] = dev_members['ticker'].fillna(dev_members['security_id'].apply(lambda x: x.split(':')[-1]))
    
    dev_labels = pd.DataFrame({
        'snapshot_date': dev_members['snapshot_date'],
        'security_id': dev_members['security_id'],
        'ticker': dev_members['ticker'],
        'cluster_label': dev_members['aligned_cluster_id'],
        'membership_period': 'development'
    })
    
    # Holdout assignments
    holdout_assign = pd.read_csv("M2/artifacts/m2-final-holdout-v1/assignments.csv")
    holdout_ticker = holdout_assign['security_id'].apply(lambda x: x.split(':')[-1])
    holdout_labels = pd.DataFrame({
        'snapshot_date': holdout_assign['snapshot_date'],
        'security_id': holdout_assign['security_id'],
        'ticker': holdout_ticker,
        'cluster_label': holdout_assign['aligned_cluster_id'],
        'membership_period': 'holdout'
    })
    
    combined_labels = pd.concat([dev_labels, holdout_labels], ignore_index=True)
    # Reorder columns as specified: snapshot_date, ticker, cluster_label, membership_period (keep security_id for PIT tracing)
    cols_order = ['snapshot_date', 'security_id', 'ticker', 'cluster_label', 'membership_period']
    combined_labels = combined_labels[cols_order]
    
    labels_csv = os.path.join(handoff_dir, "m2_cluster_labels_for_m3.csv")
    combined_labels.to_csv(labels_csv, index=False)
    print(f"Exported {labels_csv} with {len(combined_labels)} rows across {combined_labels['snapshot_date'].nunique()} snapshots")
    
    print("\n=== Step 3: Build m2_cluster_profiles_for_m3.csv ===")
    dev_prof = pd.read_csv("M2/artifacts/m2-evaluation-kmeans/cluster_profiles.csv")
    dev_prof['membership_period'] = 'development'
    
    holdout_prof = pd.read_csv("M2/artifacts/m2-final-holdout-v1/cluster_profiles.csv")
    holdout_prof['membership_period'] = 'holdout'
    
    # Standardize column names
    feature_cols = ['mom_21', 'mom_63', 'mom_126', 'mom_252', 'vol_63', 'mdd_126', 'beta_126', 'liquidity_21']
    # Check column names in dev_prof
    prof_dfs = []
    for df, period in [(dev_prof, 'development'), (holdout_prof, 'holdout')]:
        sub = pd.DataFrame()
        sub['snapshot_date'] = df['snapshot_date']
        sub['cluster_label'] = df['aligned_cluster_id']
        sub['size'] = df['size']
        sub['size_ratio'] = df['size_ratio']
        for col in feature_cols:
            if col in df.columns:
                sub[col] = df[col]
            elif f"{col}_mean" in df.columns:
                sub[col] = df[f"{col}_mean"]
            else:
                raise ValueError(f"Missing {col} in profile dataframe")
        sub['membership_period'] = period
        prof_dfs.append(sub)
        
    combined_profiles = pd.concat(prof_dfs, ignore_index=True)
    
    # Also add summary median profiles
    summary_rows = []
    for cluster_id in [0, 1]:
        c_sub_dev = combined_profiles[(combined_profiles['cluster_label'] == cluster_id) & (combined_profiles['membership_period'] == 'development')]
        c_sub_hold = combined_profiles[(combined_profiles['cluster_label'] == cluster_id) & (combined_profiles['membership_period'] == 'holdout')]
        c_sub_all = combined_profiles[combined_profiles['cluster_label'] == cluster_id]
        
        row_dev = {
            'snapshot_date': 'MEDIAN_DEVELOPMENT',
            'cluster_label': cluster_id,
            'size': int(round(c_sub_dev['size'].median())),
            'size_ratio': c_sub_dev['size_ratio'].median(),
            'membership_period': 'development'
        }
        for col in feature_cols:
            row_dev[col] = c_sub_dev[col].median()
        summary_rows.append(row_dev)
        
        row_hold = {
            'snapshot_date': 'MEDIAN_HOLDOUT',
            'cluster_label': cluster_id,
            'size': int(round(c_sub_hold['size'].median())),
            'size_ratio': c_sub_hold['size_ratio'].median(),
            'membership_period': 'holdout'
        }
        for col in feature_cols:
            row_hold[col] = c_sub_hold[col].median()
        summary_rows.append(row_hold)
        
        row_all = {
            'snapshot_date': 'MEDIAN_OVERALL_22M',
            'cluster_label': cluster_id,
            'size': int(round(c_sub_all['size'].median())),
            'size_ratio': c_sub_all['size_ratio'].median(),
            'membership_period': 'overall'
        }
        for col in feature_cols:
            row_all[col] = c_sub_all[col].median()
        summary_rows.append(row_all)
        
    summary_df = pd.DataFrame(summary_rows)
    all_profiles_df = pd.concat([combined_profiles, summary_df], ignore_index=True)
    
    profiles_csv = os.path.join(handoff_dir, "m2_cluster_profiles_for_m3.csv")
    all_profiles_df.to_csv(profiles_csv, index=False)
    print(f"Exported {profiles_csv} with {len(all_profiles_df)} profile rows (44 monthly + 6 summary rows)")
    
    print("\n=== Step 4: Build m2_transition_turnover_reference.csv ===")
    dev_temp = pd.read_csv("M2/artifacts/m2-evaluation-kmeans/temporal_stability.csv")
    dev_temp['membership_period'] = 'development'
    
    holdout_temp = pd.read_csv("M2/artifacts/m2-final-holdout-v1/temporal_stability.csv")
    holdout_temp['membership_period'] = 'holdout'
    
    temp_combined = pd.concat([dev_temp, holdout_temp], ignore_index=True)
    temp_combined['pair_id'] = [f"PAIR_{i+1:02d}" for i in range(len(temp_combined))]
    
    cols_temp = [
        'pair_id', 'from_date', 'to_date', 'membership_period', 'n_common', 
        'ari', 'nmi', 'persistence_probability', 'migration_rate', 
        'entered_count', 'exited_count', 'status'
    ]
    temp_combined = temp_combined[cols_temp]
    
    turnover_csv = os.path.join(handoff_dir, "m2_transition_turnover_reference.csv")
    temp_combined.to_csv(turnover_csv, index=False)
    print(f"Exported {turnover_csv} with {len(temp_combined)} transition pairs (14 dev + 6 holdout)")
    
    print("\n=== Step 5: Build m2_to_m3_handoff_manifest.json ===")
    snapshot_dates = list(combined_labels['snapshot_date'].unique())
    
    handoff_manifest = {
        "manifest_version": "1.0.0",
        "pipeline_milestone": "M2_TO_M3_HANDOFF",
        "timestamp": "2026-10-05T08:35:00+07:00",
        "status": "OFFICIALLY_HANDED_OFF",
        "methodology": {
            "selected_algorithm": "KMeans_Baseline",
            "global_k": 2,
            "features": feature_cols,
            "scaling": "RobustScaler per snapshot (Median, IQR)",
            "selection_rationale": "KMeans_Baseline selected via 5-tier evaluation matrix and Occam's Razor (< 0.03 gap, identical temporal stability to PCA, direct economic interpretability on 8 raw features)"
        },
        "coverage": {
            "n_development_snapshots": 15,
            "development_window": ["2023-11-30", "2025-01-24"],
            "systemic_gap": ["2025-02-03", "2026-01-30"],
            "n_holdout_snapshots": 7,
            "holdout_window": ["2026-02-27", "2026-08-28"],
            "total_snapshots": 22,
            "total_transition_pairs": 20,
            "total_member_observations": len(combined_labels),
            "rebalance_dates": snapshot_dates
        },
        "artifacts_sha256": {
            "m2_cluster_labels_for_m3.csv": compute_sha256(labels_csv),
            "m2_cluster_profiles_for_m3.csv": compute_sha256(profiles_csv),
            "m2_transition_turnover_reference.csv": compute_sha256(turnover_csv),
            "final_selected_models_manifest": compute_sha256(os.path.join(models_dir, "model_file_manifest.json")),
            "all_models_22m_manifest": compute_sha256(os.path.join(models_dir, "model_file_manifest_22m.json"))
        },
        "verification_audit_reference": {
            "audit_report": "M2/reports/Bao_cao_M2_Nhiem_vu_12_Verify.md",
            "audit_verdict": "METHODOLOGY_CLEARED_PASS",
            "frozen_winner": "KMeans_Baseline",
            "preregistration_limitation_accepted": True
        },
        "m3_boundary_rules": [
            "Strict one-way handoff: M3 must not modify clustering parameters or Global K based on backtest return/Sharpe.",
            "Metric segregation: M2 metrics (Silhouette, DB, CH, ARI, NMI, Migration) are completely decoupled from M3 portfolio metrics (CAGR, Sharpe, MDD).",
            "PIT execution: Snapshot t labels are available at decision_at (month-end close); portfolio trades execute at t+1 open."
        ]
    }
    
    manifest_path = os.path.join(handoff_dir, "m2_to_m3_handoff_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(handoff_manifest, f, indent=2)
    print(f"Exported {manifest_path}")
    print("\nTask 13 Handoff Package generated successfully!")

if __name__ == "__main__":
    main()
