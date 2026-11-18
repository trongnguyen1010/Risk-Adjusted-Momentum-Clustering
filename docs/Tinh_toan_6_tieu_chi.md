# HƯỚNG DẪN CHI TIẾT TÍNH TOÁN 6 TIÊU CHÍ VÀ CHUẨN HÓA PHÂN VỊ (PERCENTILE)

> **Tài liệu tham chiếu:** [`docs/KE_HOACH_M3_SCHEMA_GITHUB.md`](file:///c:/Users/HP/Downloads/Phân cụm động lượng TTCK/docs/KE_HOACH_M3_SCHEMA_GITHUB.md) (Mục 3.5, Q7, Q8, Q9)  
> **Mã nguồn thực thi:** [`src/delta_t1/m3/ranking.py`](file:///c:/Users/HP/Downloads/Phân cụm động lượng TTCK/src/delta_t1/m3/ranking.py)

---

## 1. CÔNG THỨC TOÁN HỌC CHUẨN HÓA PHÂN VỊ (PERCENTILE)

Để kết hợp các chỉ số có đơn vị đo lường khác nhau (% tăng giá, tỷ đồng thanh khoản, thang điểm số), hệ thống chuẩn hóa từng tiêu chí về thang đo phân vị trung bình (average-rank percentile) trong đoạn $[0.0, 1.0]$:

$$\text{percentile}(v) = \frac{\text{below} + \frac{\text{equal} - 1}{2}}{N_{\text{present}} - 1}$$

### Giải thích các thành phần:
* **$v$**: Giá trị của chỉ số đang xét của mã cổ phiếu.
* **$N_{\text{present}}$**: Tổng số mã có dữ liệu hợp lệ trong kỳ đánh giá.
* **Mẫu số ($N_{\text{present}} - 1$)**: Số khoảng cách giữa các mã khi xếp thành hàng từ nhỏ nhất đến lớn nhất. Chia cho $N_{\text{present}} - 1$ đảm bảo mã thấp nhất luôn nhận điểm tuyệt đối `0.00` và mã cao nhất luôn nhận điểm tuyệt đối `1.00`.
* **`below`**: Số lượng mã có giá trị **nhỏ hơn** $v$.
* **`equal`**: Số lượng mã có giá trị **bằng** $v$ (luôn tính cả chính nó, nên $\text{equal} \ge 1$).
* **Phần bù $\frac{\text{equal} - 1}{2}$**: Khoảng cách từ đầu nhóm đến tâm (vị trí chính giữa) của nhóm các mã hòa điểm, đảm bảo các mã bằng điểm nhau đều nhận chung một mức điểm trung bình hoàn toàn công bằng.
  - Khi mã đứng một mình không hòa ai ($\text{equal} = 1$): $\frac{1 - 1}{2} = 0 \implies \text{Tử số} = \text{below}$.
  - Khi có 2 mã hòa nhau ($\text{equal} = 2$): $\frac{2 - 1}{2} = 0.5 \implies \text{Tử số} = \text{below} + 0.5$.
  - Khi có 3 mã hòa nhau ($\text{equal} = 3$): $\frac{3 - 1}{2} = 1.0 \implies \text{Tử số} = \text{below} + 1.0$.

### Quy tắc đảo dấu cho tiêu chí nghịch đảo (Lower is better):
Đối với tiêu chí **MC2 (`downside_vol_63`)**, do tính chất **càng thấp càng tốt**, hệ thống sẽ **đảo dấu âm ($-v$)** trước khi xếp hạng. Mã có biến động giảm thấp nhất sẽ có giá trị đại số sau đảo dấu lớn nhất, qua đó nhận điểm phân vị cao nhất (tiến gần về `1.00`).

---

## 2. BẢNG DỮ LIỆU THÔ BAN ĐẦU (VÍ DỤ 5 MÃ $\times$ 6 TIÊU CHÍ)

Xét vũ trụ ứng viên gồm $N = 5$ mã cổ phiếu: **A, B, C, D, E**.  
Mẫu số chuẩn hóa cố định là:
$$N - 1 = 5 - 1 = \mathbf{4}$$

| Mã | MC1: Tăng giá 6T (`mom_126`) | MC2: Biến động giảm (`downside_vol_63`) | MC3: Thanh khoản (`liquidity_21`) | FC1: ROE (`roe`) | FC2: F-score (`f_score`) | FC3: Z-score (`z_score`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Chiều ưu tiên** | *Càng cao càng tốt* | *Càng thấp càng tốt* | *Càng cao càng tốt* | *Càng cao càng tốt* | *Càng cao càng tốt* | *Càng cao càng tốt* |
| **A** | $+5\%$ | $30\%$ | $50\text{ tỷ}$ | $8\%$ | $4$ | $1.6$ |
| **B** | $+10\%$ | $22\%$ | $120\text{ tỷ}$ | $12\%$ | **$6$** | $2.1$ |
| **C** | **$+20\%$** | $16\%$ | $180\text{ tỷ}$ | $15\%$ | **$6$** | $2.5$ |
| **D** | **$+20\%$** | $12\%$ | $250\text{ tỷ}$ | $18\%$ | $7$ | $2.9$ |
| **E** | $+35\%$ | $8\%$ | $400\text{ tỷ}$ | $25\%$ | $8$ | $3.6$ |

*(Trong dữ liệu mẫu: C và D hòa nhau ở MC1 với $+20\%$; B và C hòa nhau ở FC2 với $6\text{ điểm}$)*.

---

## 3. TÍNH PERCENTILE CHI TIẾT CHO TỪNG TIÊU CHÍ

---

### Tiêu chí 1: MC1 — Động lượng giá 6 tháng (`mom_126`)
*Chiều đánh giá:* Càng cao càng tốt.  
Dãy số: A ($+5\%$), B ($+10\%$), C ($+20\%$), D ($+20\%$), E ($+35\%$).

| Mã | Giá trị thô | `below` (nhỏ hơn) | `equal` (bằng) | Phép tính chi tiết: $\frac{\text{below} + \frac{\text{equal}-1}{2}}{4}$ | Điểm Percentile |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $+5\%$ | $0$ | $1$ | $\frac{0 + \frac{1-1}{2}}{4} = \frac{0}{4}$ | **`0.000`** |
| **B** | $+10\%$ | $1$ *(A)* | $1$ | $\frac{1 + \frac{1-1}{2}}{4} = \frac{1}{4}$ | **`0.250`** |
| **C** | $+20\%$ | $2$ *(A, B)* | $2$ *(C, D)* | $\frac{2 + \frac{2-1}{2}}{4} = \frac{2 + 0.5}{4} = \frac{2.5}{4}$ | **`0.625`** |
| **D** | $+20\%$ | $2$ *(A, B)* | $2$ *(C, D)* | $\frac{2 + \frac{2-1}{2}}{4} = \frac{2 + 0.5}{4} = \frac{2.5}{4}$ | **`0.625`** |
| **E** | $+35\%$ | $4$ *(A, B, C, D)* | $1$ | $\frac{4 + \frac{1-1}{2}}{4} = \frac{4}{4}$ | **`1.000`** |

---

### Tiêu chí 2: MC2 — Biến động giảm 63 phiên (`downside_vol_63`)
*Chiều đánh giá:* Càng thấp càng tốt $\rightarrow$ Đảo dấu âm ($-v$) trước khi xếp hạng.  
Dãy sau đảo dấu: A ($-30\%$) < B ($-22\%$) < C ($-16\%$) < D ($-12\%$) < E ($-8\%$).

| Mã | Biến động thô | Giá trị sau đảo dấu | `below` | `equal` | Phép tính chi tiết: $\frac{\text{below} + \frac{\text{equal}-1}{2}}{4}$ | Điểm Percentile |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $30\%$ *(xấu nhất)* | $-30\%$ | $0$ | $1$ | $\frac{0 + 0}{4} = \frac{0}{4}$ | **`0.000`** |
| **B** | $22\%$ | $-22\%$ | $1$ *(A)* | $1$ | $\frac{1 + 0}{4} = \frac{1}{4}$ | **`0.250`** |
| **C** | $16\%$ | $-16\%$ | $2$ *(A, B)* | $1$ | $\frac{2 + 0}{4} = \frac{2}{4}$ | **`0.500`** |
| **D** | $12\%$ | $-12\%$ | $3$ *(A, B, C)* | $1$ | $\frac{3 + 0}{4} = \frac{3}{4}$ | **`0.750`** |
| **E** | $8\%$ *(tốt nhất)* | $-8\%$ | $4$ *(A, B, C, D)* | $1$ | $\frac{4 + 0}{4} = \frac{4}{4}$ | **`1.000`** |

---

### Tiêu chí 3: MC3 — Thanh khoản 21 phiên (`liquidity_21`)
*Chiều đánh giá:* Càng cao càng tốt.  
Dãy số: A ($50$), B ($120$), C ($180$), D ($250$), E ($400$).

| Mã | Giá trị thô | `below` | `equal` | Phép tính chi tiết: $\frac{\text{below} + \frac{\text{equal}-1}{2}}{4}$ | Điểm Percentile |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $50\text{ tỷ}$ | $0$ | $1$ | $\frac{0 + 0}{4} = \frac{0}{4}$ | **`0.000`** |
| **B** | $120\text{ tỷ}$ | $1$ *(A)* | $1$ | $\frac{1 + 0}{4} = \frac{1}{4}$ | **`0.250`** |
| **C** | $180\text{ tỷ}$ | $2$ *(A, B)* | $1$ | $\frac{2 + 0}{4} = \frac{2}{4}$ | **`0.500`** |
| **D** | $250\text{ tỷ}$ | $3$ *(A, B, C)* | $1$ | $\frac{3 + 0}{4} = \frac{3}{4}$ | **`0.750`** |
| **E** | $400\text{ tỷ}$ | $4$ *(A, B, C, D)* | $1$ | $\frac{4 + 0}{4} = \frac{4}{4}$ | **`1.000`** |

---

### Tiêu chí 4: FC1 — Tỷ suất sinh lời trên vốn (`roe`)
*Chiều đánh giá:* Càng cao càng tốt.  
Dãy số: A ($8\%$), B ($12\%$), C ($15\%$), D ($18\%$), E ($25\%$).

| Mã | Giá trị thô | `below` | `equal` | Phép tính chi tiết: $\frac{\text{below} + \frac{\text{equal}-1}{2}}{4}$ | Điểm Percentile |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $8\%$ | $0$ | $1$ | $\frac{0 + 0}{4} = \frac{0}{4}$ | **`0.000`** |
| **B** | $12\%$ | $1$ *(A)* | $1$ | $\frac{1 + 0}{4} = \frac{1}{4}$ | **`0.250`** |
| **C** | $15\%$ | $2$ *(A, B)* | $1$ | $\frac{2 + 0}{4} = \frac{2}{4}$ | **`0.500`** |
| **D** | $18\%$ | $3$ *(A, B, C)* | $1$ | $\frac{3 + 0}{4} = \frac{3}{4}$ | **`0.750`** |
| **E** | $25\%$ | $4$ *(A, B, C, D)* | $1$ | $\frac{4 + 0}{4} = \frac{4}{4}$ | **`1.000`** |

---

### Tiêu chí 5: FC2 — Sức khỏe tài chính Piotroski (`f_score`)
*Chiều đánh giá:* Càng cao càng tốt.  
Dãy số: A ($4$), B ($6$), C ($6$), D ($7$), E ($8$).

| Mã | Giá trị thô | `below` | `equal` | Phép tính chi tiết: $\frac{\text{below} + \frac{\text{equal}-1}{2}}{4}$ | Điểm Percentile |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $4$ | $0$ | $1$ | $\frac{0 + 0}{4} = \frac{0}{4}$ | **`0.000`** |
| **B** | $6$ | $1$ *(A)* | $2$ *(B, C)* | $\frac{1 + \frac{2-1}{2}}{4} = \frac{1 + 0.5}{4} = \frac{1.5}{4}$ | **`0.375`** |
| **C** | $6$ | $1$ *(A)* | $2$ *(B, C)* | $\frac{1 + \frac{2-1}{2}}{4} = \frac{1 + 0.5}{4} = \frac{1.5}{4}$ | **`0.375`** |
| **D** | $7$ | $3$ *(A, B, C)* | $1$ | $\frac{3 + 0}{4} = \frac{3}{4}$ | **`0.750`** |
| **E** | $8$ | $4$ *(A, B, C, D)* | $1$ | $\frac{4 + 0}{4} = \frac{4}{4}$ | **`1.000`** |

---

### Tiêu chí 6: FC3 — An toàn nợ Altman (`z_score`)
*Chiều đánh giá:* Càng cao càng tốt.  
Dãy số: A ($1.6$), B ($2.1$), C ($2.5$), D ($2.9$), E ($3.6$).

| Mã | Giá trị thô | `below` | `equal` | Phép tính chi tiết: $\frac{\text{below} + \frac{\text{equal}-1}{2}}{4}$ | Điểm Percentile |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $1.6$ | $0$ | $1$ | $\frac{0 + 0}{4} = \frac{0}{4}$ | **`0.000`** |
| **B** | $2.1$ | $1$ *(A)* | $1$ | $\frac{1 + 0}{4} = \frac{1}{4}$ | **`0.250`** |
| **C** | $2.5$ | $2$ *(A, B)* | $1$ | $\frac{2 + 0}{4} = \frac{2}{4}$ | **`0.500`** |
| **D** | $2.9$ | $3$ *(A, B, C)* | $1$ | $\frac{3 + 0}{4} = \frac{3}{4}$ | **`0.750`** |
| **E** | $3.6$ | $4$ *(A, B, C, D)* | $1$ | $\frac{4 + 0}{4} = \frac{4}{4}$ | **`1.000`** |

---

## 4. BẢNG TỔNG HỢP 6 CỘT ĐIỂM PERCENTILE

Sau khi tính độc lập từng cột, ta có bảng ma trận phân vị chuẩn hóa hoàn chỉnh:

| Mã | MC1 (Tăng giá) | MC2 (Biến động) | MC3 (Thanh khoản) | FC1 (ROE) | FC2 (F-score) | FC3 (Z-score) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $0.000$ | $0.000$ | $0.000$ | $0.000$ | $0.000$ | $0.000$ |
| **B** | $0.250$ | $0.250$ | $0.250$ | $0.250$ | $0.375$ | $0.250$ |
| **C** | $0.625$ | $0.500$ | $0.500$ | $0.500$ | $0.375$ | $0.500$ |
| **D** | $0.625$ | $0.750$ | $0.750$ | $0.750$ | $0.750$ | $0.750$ |
| **E** | $1.000$ | $1.000$ | $1.000$ | $1.000$ | $1.000$ | $1.000$ |

---

## 5. TÍNH ĐIỂM TỔNG HỢP ($S_{\text{market}}$, $S_{\text{fin}}$, $\text{Combined Score}$) VÀ XẾP HẠNG

### 1. Điểm Thị trường ($S_{\text{market}}$) = Trung bình cộng 3 cột MC1, MC2, MC3:
* **Mã A:** $\frac{0.000 + 0.000 + 0.000}{3} = \mathbf{0.000}$
* **Mã B:** $\frac{0.250 + 0.250 + 0.250}{3} = \frac{0.750}{3} = \mathbf{0.250}$
* **Mã C:** $\frac{0.625 + 0.500 + 0.500}{3} = \frac{1.625}{3} \approx \mathbf{0.542}$
* **Mã D:** $\frac{0.625 + 0.750 + 0.750}{3} = \frac{2.125}{3} \approx \mathbf{0.708}$
* **Mã E:** $\frac{1.000 + 1.000 + 1.000}{3} = \frac{3.000}{3} = \mathbf{1.000}$

### 2. Điểm Tài chính ($S_{\text{fin}}$) = Trung bình cộng 3 cột FC1, FC2, FC3:
* **Mã A:** $\frac{0.000 + 0.000 + 0.000}{3} = \mathbf{0.000}$
* **Mã B:** $\frac{0.250 + 0.375 + 0.250}{3} = \frac{0.875}{3} \approx \mathbf{0.292}$
* **Mã C:** $\frac{0.500 + 0.375 + 0.500}{3} = \frac{1.375}{3} \approx \mathbf{0.458}$
* **Mã D:** $\frac{0.750 + 0.750 + 0.750}{3} = \frac{2.250}{3} = \mathbf{0.750}$
* **Mã E:** $\frac{1.000 + 1.000 + 1.000}{3} = \frac{3.000}{3} = \mathbf{1.000}$

### 3. Điểm kết hợp $\text{Combined Score} = 0.5 \times S_{\text{market}} + 0.5 \times S_{\text{fin}}$:

| Mã | Điểm Thị trường ($S_{\text{market}}$) | Điểm Tài chính ($S_{\text{fin}}$) | Phép tính Combined Score | Điểm chung cuộc | Thứ hạng (Rank) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **E** | $1.000$ | $1.000$ | $0.5 \times 1.000 + 0.5 \times 1.000$ | **`1.000`** | **Hạng 1** |
| **D** | $0.708$ | $0.750$ | $0.5 \times 0.708 + 0.5 \times 0.750 = 0.354 + 0.375$ | **`0.729`** | **Hạng 2** |
| **C** | $0.542$ | $0.458$ | $0.5 \times 0.542 + 0.5 \times 0.458 = 0.271 + 0.229$ | **`0.500`** | **Hạng 3** |
| **B** | $0.250$ | $0.292$ | $0.5 \times 0.250 + 0.5 \times 0.292 = 0.125 + 0.146$ | **`0.271`** | **Hạng 4** |
| **A** | $0.000$ | $0.000$ | $0.5 \times 0.000 + 0.5 \times 0.000$ | **`0.000`** | **Hạng 5** |

---

## 6. LỰA CHỌN DANH MỤC ĐẦU TƯ (TOP 30%)

* Quy mô chọn lựa: 
  $$n_{\text{select}} = \lceil 0.30 \times N_{\text{candidates}} \rceil = \lceil 0.30 \times 5 \rceil = \lceil 1.5 \rceil = \mathbf{2}\text{ mã}$$
* Hai mã có thứ hạng cao nhất được chọn: **Mã E** và **Mã D**.
* Tỷ trọng phân bổ danh mục (Equal-weight):
  $$w = \frac{1}{n_{\text{select}}} = \frac{1}{2} = \mathbf{50\%}\text{ mỗi mã}$$
* Danh mục mục tiêu (`Target Portfolio`): `{'E': 0.50, 'D': 0.50}`.

