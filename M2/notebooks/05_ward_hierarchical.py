import subprocess
import sys
import time
import os
import glob

print("==================================================================")
print("BẮT ĐẦU NHIỆM VỤ 5: HUẤN LUYỆN WARD HIERARCHICAL CLUSTERING")
print("==================================================================")
print("-> Tiến trình: Chạy pipeline qua 15 snapshots (Development Window)")
print("-> Cấu hình: configs/experiments/m2_ward_market_only_v1.json\n")

start_time = time.time()
target_model_dir = "M2/artifacts/m2-task5-ward-v1/models"

print("[Tiến trình] Đang khởi động pipeline...")

# Chạy luồng thực thi chạy ngầm
process = subprocess.Popen([
    "python", "scripts/run_research.py",
    "artifacts/cafef_primary/cafef-c8-complete-only-v1",
    "--config", "configs/experiments/m2_ward_market_only_v1.json"
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Thanh tiến trình tự chế (Đếm số file json MỚI đẻ ra trong folder models)
total_snapshots = 15
last_count = 0

while process.poll() is None:
    if os.path.exists(target_model_dir):
        # Chỉ đếm những file được sửa đổi/tạo ra SAU KHI script này bắt đầu chạy
        current_count = sum(1 for f in glob.glob(f"{target_model_dir}/*.json") if os.path.getmtime(f) > start_time)
        if current_count > last_count:
            print(f"👉 Đã xử lý xong: {current_count}/{total_snapshots} snapshots", flush=True)
            last_count = current_count
    time.sleep(0.5)

# Tính toán thời gian đã trôi qua
elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)

print("\n==================================================================")
# Kiểm tra mã lỗi trả về (Exit Code 0 = Thành công, Khác 0 = Lỗi)
if process.returncode == 0:
    print("✅ HUẤN LUYỆN HOÀN TẤT THÀNH CÔNG!")
    print(f"⏱️ Tổng thời gian chạy: {int(minutes)} phút {int(seconds)} giây")
    print(f"Artifacts chuẩn hóa đã tự động được lưu tại: {target_model_dir.replace('/models', '')}")
    print("Sẵn sàng dữ liệu cho Nhiệm vụ 7, 8, 9 và 10.")
else:
    print(f"❌ HUẤN LUYỆN THẤT BẠI (Mã lỗi: {process.returncode})!")
    print(f"⏱️ Thời gian gián đoạn: {int(minutes)} phút {int(seconds)} giây")
    print("Phát hiện có lỗi trong quá trình thực thi:")
    print(process.stderr.read())
    sys.exit(process.returncode)
