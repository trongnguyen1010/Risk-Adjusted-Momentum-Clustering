"use strict";
const $=id=>document.getElementById(id);
const number=v=>v==null?"—":new Intl.NumberFormat("vi-VN",{maximumFractionDigits:1}).format(v);
const phase={RUNNING_SYMBOL_QA:"Đang kiểm tra từng mã",CONSOLIDATING_OUTPUTS:"Đang tổng hợp báo cáo",COMPLETE_OFFLINE_INVENTORY_QA_DIAGNOSTICS:"QA offline đã hoàn tất",HELD_REVIEW_REQUIRED:"Đã dừng · cần kiểm tra",UNKNOWN:"Chưa có trạng thái"};
const labels={report:"Report tổng hợp",summary:"Summary",symbols:"Danh sách mã",coverage:"Coverage",missing:"Kỳ thiếu",queue:"Hàng đợi PDF"};
let busy=false;
function text(id,value){$(id).textContent=value??"—";}
function date(value,zone){if(!value)return"—";return new Intl.DateTimeFormat("vi-VN",{timeZone:zone,dateStyle:"short",timeStyle:"medium"}).format(new Date(value))+" (UTC+7)";}
function render(data){
 const q=data.qa,a=data.acquisition,held=q.stage.includes("HELD"),current=phase[q.stage]||q.stage;
 text("acq-percent",a.percent==null?"—":number(a.percent)+"%");text("acq-count",`${number(a.completed)} / ${number(a.total)} mã`);$("acq-bar").style.width=(a.percent??0)+"%";text("acq-badge",a.complete?"HOÀN TẤT":"CHƯA CHỐT");
 text("qa-percent",q.percent==null?"—":number(q.percent)+"%");text("qa-count",`${number(q.completed)} / ${number(q.total)} mã đã xử lý`);$("qa-bar").style.width=(q.percent??0)+"%";text("qa-stage",current);text("qa-badge",held?"CẦN REVIEW":q.complete?"HOÀN TẤT":"ĐANG XỬ LÝ");$("qa-badge").classList.toggle("warning",!q.complete);
 text("current-stage",current);text("current-symbol",`Mã gần nhất: ${q.last_symbol??"—"}`);text("activity-time",date(q.at,data.timezone));text("fetch-time",date(data.served_at,data.timezone));
 $("step-acq").className=a.complete?"done":"";$("step-qa").className=q.complete?"done":"active";
 const totals=data.summary?.totals;text("failures",number(totals?.failed_requests));text("conflicts",number(totals?.provider_value_conflicts));text("shifts",number(totals?.possible_row_displacements));text("queue-count",number(totals?.document_queue_periods));
 text("summary-note",totals?"Các dấu hiệu cần review; không đồng nghĩa mọi chênh lệch là lỗi dữ liệu.":"Các số liệu này xuất hiện sau khi QA và tổng hợp hoàn tất.");
 $("downloads").replaceChildren(...Object.entries(data.downloads).map(([name,href])=>{const a=document.createElement("a");a.href=href;a.textContent=labels[name]||name;return a;}));
 $("recent").replaceChildren(...data.recent.map(row=>{const tr=document.createElement("tr");[row.last_symbol,`${number(row.completed)} / ${number(row.total)}`,number(row.completed*100/row.total)+"%"].forEach(value=>{const td=document.createElement("td");td.textContent=value;tr.append(td);});return tr;}));
 text("log",[...data.log,...(data.errors.length?["\n--- STDERR ---",...data.errors]:[])].join("\n")||"Chưa có log.");$("log").scrollTop=$("log").scrollHeight;
 const notices=[];if(q.reason)notices.push(q.reason);if(q.activity_stale)notices.push(`Chưa có cập nhật hoạt động trong ${number(Math.round(q.last_activity_age_seconds/60))} phút. Trạng thái này chưa xác nhận tiến trình đã dừng.`);if(data.warnings.length)notices.push("Một số file trạng thái chưa đọc được; giữ dữ liệu gần nhất nếu có.");$("notice").hidden=!notices.length;text("notice",notices.join(" "));
 text("connection","● Đã đồng bộ · chỉ đọc");$("connection").classList.remove("offline");
}
async function refresh(){if(busy)return;busy=true;$("refresh").disabled=true;try{const response=await fetch("/api/v1/monitor",{cache:"no-store",signal:AbortSignal.timeout(10000)});if(!response.ok)throw new Error("HTTP "+response.status);render(await response.json());}catch(error){text("connection","● Mất kết nối dashboard");$("connection").classList.add("offline");$("notice").hidden=false;text("notice","Không lấy được trạng thái mới. Dữ liệu đang hiển thị có thể đã cũ; flow nền hoạt động độc lập với dashboard.");}finally{busy=false;$("refresh").disabled=false;}}
$("refresh").addEventListener("click",refresh);refresh();setInterval(refresh,5000);
