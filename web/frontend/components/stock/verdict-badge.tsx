import type { AssessmentStatus as AssessmentVerdict } from "@/lib/types";

const VERDICT_PRESENTATION: Record<
  AssessmentVerdict,
  { label: string; tone: string }
> = {
  RESEARCH_FAVORABLE: { label: "Tích cực để nghiên cứu", tone: "teal" },
  WATCH: { label: "Theo dõi", tone: "purple" },
  CAUTION: { label: "Cần thận trọng", tone: "amber" },
  INSUFFICIENT_EVIDENCE: {
    label: "Chưa đủ bằng chứng",
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
