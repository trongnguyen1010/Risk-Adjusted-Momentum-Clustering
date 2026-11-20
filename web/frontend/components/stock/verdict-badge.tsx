import type { AssessmentStatus as AssessmentVerdict } from "@/lib/types";

const VERDICT_PRESENTATION: Record<
  AssessmentVerdict,
  { label: string; tone: string }
> = {
  RESEARCH_FAVORABLE: { label: "Đáng cân nhắc đầu tư", tone: "teal" },
  WATCH: { label: "Cần theo dõi", tone: "purple" },
  CAUTION: { label: "Chưa nên ưu tiên đầu tư", tone: "amber" },
  INSUFFICIENT_EVIDENCE: {
    label: "Chưa đủ bằng chứng đánh giá",
    tone: "subtle",
  },
};

export function VerdictBadge({ status }: { status: AssessmentVerdict }) {
  const presentation = VERDICT_PRESENTATION[status];

  return (
    <span
      aria-label={`Kết luận Assessment: ${presentation.label}`}
      className={`badge ${presentation.tone}`}
    >
      {presentation.label}
    </span>
  );
}
