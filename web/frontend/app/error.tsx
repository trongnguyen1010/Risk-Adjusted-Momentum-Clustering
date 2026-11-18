"use client";
import { ErrorState } from "@/components/ui";
export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorState
      message="Không thể hiển thị trang này. Dữ liệu nghiên cứu của bạn không bị thay đổi."
      retry={reset}
    />
  );
}
