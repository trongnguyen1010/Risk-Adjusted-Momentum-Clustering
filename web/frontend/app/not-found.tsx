import Link from "next/link";
export default function NotFound() {
  return (
    <div className="state-box">
      <h1>Ngoài bản đồ nghiên cứu.</h1>
      <p>Không tìm thấy trang này.</p>
      <Link className="button primary" href="/">
        Về trang Tổng quan
      </Link>
    </div>
  );
}
