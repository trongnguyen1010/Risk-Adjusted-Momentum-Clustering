"""
delta_t1.experiments.investment_assessment_v1

Bộ điều phối tính toán Offline Đánh giá đầu tư (Investment Assessment Orchestrator - Stage S3: Task R1-17, R1-19).
Triển khai bộ quy tắc D-ASS-01:
  - 4 trạng thái verdict:
      1. WORTH_CONSIDERING ("Đáng cân nhắc đầu tư")
      2. MONITOR ("Cần theo dõi")
      3. LOW_PRIORITY ("Chưa nên ưu tiên đầu tư")
      4. INSUFFICIENT_EVIDENCE ("Không đủ cơ sở")
  - Tích hợp 18 đặc trưng (9 thị trường A v4 + 9 tài chính B-PIT Enriched).
  - So sánh Peers theo chính sách mục 6.3.
  - Xuất các artifact payload: assessments.jsonl, peer_benchmarks.csv, coverage.csv, feature_history.jsonl, manifest.json.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import csv
import hashlib
from datetime import datetime, timezone

from .assessment.inputs import (
    AssessmentInputResolver,
    AssessmentInputRecord,
    FINANCIAL_FEATURES,
    MARKET_FEATURES,
    DEFAULT_AS_OF,
    sha256_file,
)
from .assessment.peers import PeerBenchmarkBuilder, MetricPeerStats
from .assessment.history import AssessmentHistoryBuilder

VERDICT_WORTH_CONSIDERING = "WORTH_CONSIDERING"
VERDICT_MONITOR = "MONITOR"
VERDICT_LOW_PRIORITY = "LOW_PRIORITY"
VERDICT_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

VERDICT_LABELS_VI = {
    VERDICT_WORTH_CONSIDERING: "Đáng cân nhắc đầu tư",
    VERDICT_MONITOR: "Cần theo dõi",
    VERDICT_LOW_PRIORITY: "Chưa nên ưu tiên đầu tư",
    VERDICT_INSUFFICIENT_EVIDENCE: "Không đủ cơ sở đánh giá",
}

@dataclass
class SingleAssessmentPayload:
    ticker: str
    as_of: str
    verdict: str
    verdict_label_vi: str
    rationale: str
    cluster_a: Optional[int]
    cluster_b: Optional[int]
    latest_fy: Optional[int]
    usable_from_date: Optional[str]
    favorable_signals: List[str]
    caution_signals: List[str]
    financial_features: Dict[str, Optional[float]]
    market_features: Dict[str, Optional[float]]
    peer_comparisons: Dict[str, Dict[str, Any]]

class InvestmentAssessmentEngine:
    """Engine đánh giá đầu tư dựa trên quy tắc D-ASS-01."""
    def evaluate(
        self,
        record: AssessmentInputRecord,
        peer_stats: Dict[str, MetricPeerStats],
    ) -> SingleAssessmentPayload:
        if not record.is_eligible:
            return SingleAssessmentPayload(
                ticker=record.ticker,
                as_of=record.as_of,
                verdict=VERDICT_INSUFFICIENT_EVIDENCE,
                verdict_label_vi=VERDICT_LABELS_VI[VERDICT_INSUFFICIENT_EVIDENCE],
                rationale=f"Không đủ điều kiện đánh giá: {record.eligibility_reason}.",
                cluster_a=record.cluster_a,
                cluster_b=record.cluster_b,
                latest_fy=record.latest_fy,
                usable_from_date=record.usable_from_date,
                favorable_signals=[],
                caution_signals=[record.eligibility_reason],
                financial_features=record.financial_features,
                market_features=record.market_features,
                peer_comparisons={},
            )

        favorable = []
        caution = []

        # Đánh giá chỉ số tài chính so với Peers
        roe = record.financial_features.get("roe")
        roe_peer = peer_stats.get("roe")
        if roe is not None and roe_peer and roe_peer.median is not None:
            if roe > roe_peer.median:
                favorable.append(f"ROE ({roe*100:.1f}%) cao hơn trung vị nhóm ({roe_peer.median*100:.1f}%)")
            else:
                caution.append(f"ROE ({roe*100:.1f}%) thấp hơn trung vị nhóm ({roe_peer.median*100:.1f}%)")

        de = record.financial_features.get("debt_to_equity")
        de_peer = peer_stats.get("debt_to_equity")
        if de is not None and de_peer and de_peer.median is not None:
            if de < de_peer.median:
                favorable.append(f"Tỷ lệ nợ/Vốn chủ sở hữu ({de:.2f}) an toàn hơn trung vị nhóm ({de_peer.median:.2f})")
            elif de > 2.0:
                caution.append(f"Đòn bẩy nợ cao ({de:.2f})")

        # Đánh giá phân cụm
        # Cụm B=0 là cụm tài chính tốt nhất (xếp theo ROE giảm dần)
        is_strong_fin = (record.cluster_b == 0)
        is_weak_fin = (record.cluster_b is not None and record.cluster_b >= 2)

        # Cụm A=0 là cụm thị trường dẫn dắt/thanh khoản tốt
        is_strong_mkt = (record.cluster_a == 0)
        is_weak_mkt = (record.cluster_a is not None and record.cluster_a >= 2)

        if is_strong_fin and is_strong_mkt and len(caution) == 0:
            verdict = VERDICT_WORTH_CONSIDERING
            rationale = "Doanh nghiệp có nền tảng tài chính vững chắc và động lượng thị trường tích cực."
        elif is_weak_fin and is_weak_mkt:
            verdict = VERDICT_LOW_PRIORITY
            rationale = "Cả chỉ số tài chính và động lượng thị trường đều yếu, rủi ro tương đối cao."
        else:
            verdict = VERDICT_MONITOR
            rationale = "Tín hiệu phân hóa giữa tài chính và diễn biến thị trường, nên theo dõi thêm các phiên tiếp theo."

        peer_comps = {}
        for m, ps in peer_stats.items():
            peer_comps[m] = {
                "peer_basis": ps.peer_basis,
                "peer_count": ps.peer_count,
                "peer_median": ps.median,
                "p25": ps.p25,
                "p75": ps.p75,
            }

        return SingleAssessmentPayload(
            ticker=record.ticker,
            as_of=record.as_of,
            verdict=verdict,
            verdict_label_vi=VERDICT_LABELS_VI[verdict],
            rationale=rationale,
            cluster_a=record.cluster_a,
            cluster_b=record.cluster_b,
            latest_fy=record.latest_fy,
            usable_from_date=record.usable_from_date,
            favorable_signals=favorable,
            caution_signals=caution,
            financial_features=record.financial_features,
            market_features=record.market_features,
            peer_comparisons=peer_comps,
        )

class OfflineAssessmentBuilder:
    """Bộ điều phối toàn bộ pipeline xây dựng dữ liệu Investment Assessment."""
    def __init__(
        self,
        indicators_db_path: Path,
        availability_csv_path: Path,
        bpit_labels_path: Path,
        as_of: str = DEFAULT_AS_OF,
    ):
        self.resolver = AssessmentInputResolver(indicators_db_path, availability_csv_path, bpit_labels_path)
        self.history_builder = AssessmentHistoryBuilder(indicators_db_path, availability_csv_path)
        self.engine = InvestmentAssessmentEngine()
        self.as_of = as_of

    def build_all(self, tickers: List[str]) -> List[SingleAssessmentPayload]:
        # 1. Resolve records
        records = {t: self.resolver.resolve_ticker(t, as_of=self.as_of) for t in tickers}

        # 2. Build peers
        peer_builder = PeerBenchmarkBuilder(records)

        # 3. Evaluate each ticker
        payloads = []
        for t in tickers:
            rec = records[t]
            p_stats = peer_builder.build_peer_stats_for_ticker(t)
            res = self.engine.evaluate(rec, p_stats)
            payloads.append(res)

        return payloads

    def export_artifacts(
        self,
        payloads: List[SingleAssessmentPayload],
        output_dir: Path,
    ) -> Dict[str, Any]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        assessments_jsonl = output_dir / "assessments.jsonl"
        with open(assessments_jsonl, "w", encoding="utf-8") as f:
            for p in payloads:
                f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")

        manifest = {
            "version": "investment_assessment_v1",
            "as_of": self.as_of,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_tickers": len(payloads),
            "verdict_summary": {
                v: sum(1 for p in payloads if p.verdict == v)
                for v in [VERDICT_WORTH_CONSIDERING, VERDICT_MONITOR, VERDICT_LOW_PRIORITY, VERDICT_INSUFFICIENT_EVIDENCE]
            },
            "outputs": {
                "assessments_jsonl_sha256": sha256_file(assessments_jsonl),
            },
        }
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        return manifest
