from flask import Flask, request, jsonify
import pandas as pd
import os
import requests
from datetime import datetime

app = Flask(__name__)

FILE_NAME = "data.xlsx"
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def reply_to_line(reply_token, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    r = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

@app.route("/api/upload-file", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "fail", "message": "ไม่พบไฟล์ในคำขอ"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "fail", "message": "ชื่อไฟล์ว่าง"}), 400
    try:
        file.save(FILE_NAME)
        return jsonify({"status": "success", "message": f"อัปโหลดไฟล์ {FILE_NAME} สำเร็จ!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def search_product(keyword):
    global json_data
    if not json_data:
        return "❌ ยังไม่มีข้อมูลสินค้า กรุณาอัปโหลดไฟล์ก่อน"

    keyword = keyword.strip().lower().replace(" ", "")
    results = []

    is_plu_search = keyword.startswith("plu")
    search_value = keyword[3:] if is_plu_search else keyword

    if keyword.startswith("mm"):
        item_id = keyword.replace("mm", "").strip()
        for row in json_data:
            if str(row.get("ไอเท็ม", "")) == item_id:
                dates = row.get("date", [])
                depts = row.get("Dept", [])
                classes = row.get("Class", [])
                receipts = row.get("Receipts", [])
                invs = row.get("InvAdjust", [])
                eoys = row.get("EOYSOH", [])
                shrinks = row.get("Shrink", [])
                sales = row.get("Sales", [])

                lines = []
                lines.append("Date     | Sales | Rec  | Adj   | SOH")
                receipts = [r if r is not None else 0 for r in receipts]        
                invs = [v if v is not None else 0 for v in invs]
                eoys = [s if s is not None else 0 for s in eoys]
                shrinks = [s if s is not None else 0 for s in shrinks]
                sales = [s if s is not None else 0 for s in sales]

                sorted_indexes = sorted(
                    range(len(dates)),
                    key=lambda i: datetime.strptime(dates[i], "%Y-%m-%d"),
                    reverse=True
                )

                dates = [dates[i] for i in sorted_indexes]
                classes = [classes[i] for i in sorted_indexes]
                receipts = [receipts[i] for i in sorted_indexes]
                invs = [invs[i] for i in sorted_indexes]
                eoys = [eoys[i] for i in sorted_indexes]
                shrinks = [shrinks[i] for i in sorted_indexes]
                sales = [sales[i] for i in sorted_indexes]
                
                for i in range(len(dates)):
                    try:
                        date_obj = datetime.strptime(dates[i], "%Y-%m-%d")
                        short_date = f"{date_obj.day}/{date_obj.month}/{str(date_obj.year)[-2:]}"
                    except:
                        short_date = dates[i]
                    line = (
                        f"{short_date.ljust(9)}| "
                        f"{str(round(sales[i], 1)).ljust(6)}| "
                        f"{str(round(receipts[i], 1)).ljust(5)}| "
                        f"{str(round(invs[i], 1)).ljust(6)}| "
                        f"{str(round(eoys[i], 1)).ljust(5)}"
                    )
                    lines.append(line)

                header = (
                    f"ไอเท็ม: {item_id} | Dept: {depts[0]} | Class: {classes[0]}\n"
                    f"สินค้า: {row.get('สินค้า', '')}"
                )
                return header + "\n\n" + "\n".join(lines)
            
        return f"❌ ไม่พบข้อมูลไอเท็ม '{item_id}'"
                

    for row in json_data:
        name = row.get("สินค้า", "").lower().replace(" ", "")
        item_id = str(row.get("ไอเท็ม", "")).split(".")[0]
        plu = str(row.get("PLU", "")).strip()
        barcodes = []
        raw_barcode = row.get("Barcode", [])
        if raw_barcode is None:
            barcodes = []
        elif isinstance(raw_barcode, str):
            barcodes = [raw_barcode.strip()]
        else:
            barcodes = raw_barcode
        stock_raw = row.get("มี Stock อยู่ที่", "").replace("~", "").strip()

        try:
            stock = float(stock_raw)
        except ValueError:
            continue

        # if stock == 0:
        #    continue

        if is_plu_search:
            if search_value == plu:
                results.append(row)
        else:
            if (
                search_value in name    
                or search_value == item_id
                or search_value in barcodes
            ):
                results.append(row)
                
    if not results:
        return f"❌ ไม่พบสินค้า '{keyword}' กรุณาลองใหม่อีกครั้ง"
    
    results = sorted(results, key=lambda r: float(str(r.get("มี Stock อยู่ที่", "0")).replace("~", "").strip()), reverse=True)

    MAX_LINE_LENGTH = 4500
    lines = [
        f"- {r.get('ไอเท็ม', '')} | PLU: {r.get('PLU', 'ไม่พบ')} | {r.get('สินค้า', '')} | {r.get('ราคา', '')} บาท | เหลือ {r.get('มี Stock อยู่ที่', '')} ชิ้น | On {r.get('On Order', '')} mu"
        for r in results
    ]

    full_message = "\n\n".join(lines)
    if len(full_message) > MAX_LINE_LENGTH:
        top_results = sorted(
        results,
        key=lambda r: float(str(r.get("มี Stock อยู่ที่", "0")).replace("~", "").strip()),
        reverse=True
        )[:10]

        top_lines = [
        f"- {r['ไอเท็ม']} | PLU: {r['PLU']} | {r['สินค้า']} | {r['ราคา']} บาท | เหลือ {r['มี Stock อยู่ที่']} ชิ้น | On {r['On Order']} mu"
        for r in top_results
    ]

        return "\n\n".join(top_lines)

    return full_message

@app.route("/callback", methods=["POST"])
def callback():
    body = request.json
    try:
        events = body.get("events", [])
        for event in events:
            if event.get("type") == "message" and event["message"]["type"] == "text":
                user_msg = event["message"]["text"]
                reply_token = event["replyToken"]

                if user_msg.startswith("@@"):
                    keyword = user_msg.replace("@@", "").strip()
                    answer = search_product(keyword)
                    reply_to_line(reply_token, answer)
                else:
                    # ❌ ถ้าไม่ใช่ @@ → ไม่ตอบกลับ
                    return "", 200

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

json_data = []  # ตัวแปรสำหรับเก็บ JSON ที่ upload เข้ามา

@app.before_request
def log_uptime_ping():
    user_agent = request.headers.get("User-Agent", "")
    if request.method == "HEAD" and "UptimeRobot" in user_agent:
        from datetime import datetime
        print(f"✅ Ping จาก UptimeRobot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

@app.route("/api/upload-json", methods=["POST"])
def upload_json():
    global json_data
    try:
        json_data = request.get_json()
        print("✅ Upload Json success:", flush=True)
        return jsonify({"status": "success"})
    except Exception as e:
        print("ERROR:", str(e)) 
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/api/upload-log", methods=["POST"])
def upload_log():
    try:
        data = request.get_json()
        msg = data.get("message", "📋 ไม่มีข้อความ")
        timestamp = data.get("time", datetime.now().isoformat())
        print(f"{timestamp} | {msg}", flush=True)
        return jsonify({"status": "received"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "❌ ไม่พบ log"  

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "OK", 200