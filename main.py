from flask import Flask, request, jsonify
import pandas as pd
import os
import requests
from datetime import datetime

app = Flask(__name__)

FILE_NAME = "data.xlsx"
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def reply_to_line(reply_token, message_data):
    """
    ส่งข้อความกลับไปยัง LINE
    message_data สามารถเป็น string (text message) หรือ dict (flex message)
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    # ถ้าเป็น string ให้แปลงเป็น text message
    if isinstance(message_data, str):
        messages = [{"type": "text", "text": message_data}]
    else:
        # ถ้าเป็น dict แสดงว่าเป็น flex message หรือ message อื่นๆ
        messages = [message_data]
    
    body = {
        "replyToken": reply_token,
        "messages": messages
    }
    r = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
    return r

def create_product_flex(results):
    """สร้าง Flex Message สำหรับแสดงรายการสินค้า"""
    
    # จำกัดจำนวนผลลัพธ์
    if len(results) > 10:
        results = results[:10]
    
    contents = []
    
    for i, product in enumerate(results):
        item_id = product.get('ไอเท็ม', '')
        plu = product.get('PLU', 'ไม่พบ')
        name = product.get('สินค้า', '')
        price = product.get('ราคา', '')
        stock = product.get('มี Stock อยู่ที่', '')
        on_order = product.get('On Order', '')
        
        # กำหนดสีของ stock
        stock_color = "#FF5551" if float(str(stock).replace("~", "").strip() or "0") <= 0 else "#00C851"
        
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"#{i+1}",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": name[:50] + ("..." if len(name) > 50 else ""),
                        "weight": "bold",
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "ไอเท็ม:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": str(item_id),
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 3
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "PLU:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": str(plu),
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 3
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "ราคา:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{price} บาท",
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 3
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "คงเหลือ:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{stock} ชิ้น",
                                        "wrap": True,
                                        "color": stock_color,
                                        "size": "sm",
                                        "flex": 3,
                                        "weight": "bold"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "On Order:",
                                        "color": "#aaaaaa",
                                        "size": "sm",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{on_order} mu",
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 3
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "spacing": "sm",
                "paddingAll": "13px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "ดูรายละเอียด",
                            "text": f"@@mm{item_id}"
                        }
                    }
                ],
                "flex": 0
            }
        }
        contents.append(bubble)
    
    return {
        "type": "flex",
        "altText": f"พบสินค้า {len(results)} รายการ",
        "contents": {
            "type": "carousel",
            "contents": contents
        }
    }

def create_item_detail_flex(item_data, lines):
    """สร้าง Flex Message สำหรับแสดงรายละเอียดสินค้า (mm command)"""
    
    # แยกข้อมูลหัวเรื่อง
    header_lines = item_data.split('\n\n')[0].split('\n')
    item_info = header_lines[0] if len(header_lines) > 0 else ""
    product_name = header_lines[1] if len(header_lines) > 1 else ""
    
    # สร้างรายการข้อมูลจาก lines
    table_contents = []
    
    for i, line in enumerate(lines[1:]):  # ข้าม header
        if i >= 10:  # จำกัดจำนวนแถว
            break
            
        parts = line.split('|')
        if len(parts) >= 5:
            date = parts[0].strip()
            sales = parts[1].strip()
            rec = parts[2].strip()
            adj = parts[3].strip()
            soh = parts[4].strip()
            
            # สีของยอดขาย
            sales_color = "#FF5551" if sales == "0" else "#00C851"
            
            table_contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": date,
                        "size": "xs",
                        "color": "#666666",
                        "flex": 2
                    },
                    {
                        "type": "text",
                        "text": sales,
                        "size": "xs",
                        "color": sales_color,
                        "flex": 1,
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": rec,
                        "size": "xs",
                        "color": "#666666",
                        "flex": 1,
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": adj,
                        "size": "xs",
                        "color": "#666666",
                        "flex": 1,
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": soh,
                        "size": "xs",
                        "color": "#666666",
                        "flex": 1,
                        "align": "center"
                    }
                ],
                "margin": "sm"
            })
    
    return {
        "type": "flex",
        "altText": f"รายละเอียดสินค้า {item_info}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "รายละเอียดสินค้า",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": item_info,
                        "weight": "bold",
                        "size": "md",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": product_name[:60] + ("..." if len(product_name) > 60 else ""),
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True,
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px",
                "paddingBottom": "16px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "Date",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 2,
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "Sales",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 1,
                                "align": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "Rec",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 1,
                                "align": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "Adj",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 1,
                                "align": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "SOH",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 1,
                                "align": "center",  
                                "weight": "bold"
                            }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "sm"
                    }
                ] + table_contents,
                "spacing": "sm",
                "paddingAll": "13px"
            }
        }
    }

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
    
    # ตรวจสอบคำสั่ง mm สำหรับรายละเอียดสินค้า
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
                sales = row.get("Sales", [])
                dc = row.get("DC", [])
                sales_realtime = row.get("Sales_Realtime", None)
                current_stock = row.get("มี Stock อยู่ที่", None)

                # แก้ None เป็น 0
                receipts = [r if r is not None else 0 for r in receipts]
                dc = [d if d is not None else 0 for d in dc]
                invs = [v if v is not None else 0 for v in invs]
                eoys = [s if s is not None else 0 for s in eoys]
                sales = [s if s is not None else 0 for s in sales]

                # เรียงวันที่ใหม่สุด → เก่าสุด
                sorted_indexes = sorted(
                    range(len(dates)),
                    key=lambda i: datetime.strptime(dates[i], "%Y-%m-%d"),
                    reverse=True
                )

                def short_dayname(dt):
                    day_map = {
                        "Mon": "M", "Tue": "Tu", "Wed": "W", "Thu": "Th", 
                        "Fri": "Fr", "Sat": "Sa", "Sun": "Su",
                    }
                    return day_map.get(dt.strftime("%a"), "?")

                lines = ["Date    | Sales | Rec  | Adj  | SOH"]
                
                # เพิ่มข้อมูลจาก Sales_Realtime เป็นบรรทัดแรก (ถ้ามี)
                if sales_realtime is not None:
                    try:
                        realtime_sales = float(sales_realtime) if sales_realtime is not None else 0
                        realtime_stock = float(current_stock) if current_stock is not None else 0
                        
                        realtime_line = (
                            f"Today    | "
                            f"{str(int(round(realtime_sales))).rjust(5)} | "
                            f"{str(0).rjust(5)} | "
                            f"{str(0).rjust(5)} | "
                            f"{str(int(round(realtime_stock))).rjust(4)}"
                        )
                        lines.append(realtime_line)
                    except Exception as e:
                        print(f"Error processing Sales_Realtime data: {e}")
                
                for i in sorted_indexes:
                    try:
                        d = datetime.strptime(dates[i], "%Y-%m-%d")
                        day = short_dayname(d)
                        short_date = f"{day} {d.day}/{d.month}"
                    except:
                        short_date = dates[i]

                    rec_total = receipts[i] + dc[i]
                    line = (
                        f"{short_date.ljust(8)}| "
                        f"{str(int(round(sales[i]))).rjust(5)} | "
                        f"{str(int(round(rec_total))).rjust(5)} | "
                        f"{str(int(round(invs[i]))).rjust(5)} | "
                        f"{str(int(round(eoys[i]))).rjust(4)}"
                    )
                    lines.append(line)

                header = (
                    f"ไอเท็ม: {item_id} | Dept: {depts[0]} | Class: {classes[0]}\n"
                    f"สินค้า: {row.get('สินค้า', '')}"
                )
                
                # ส่งกลับเป็น Flex Message สำหรับรายละเอียดสินค้า
                return create_item_detail_flex(header, lines)

        return f"❌ ไม่พบข้อมูลไอเท็ม '{item_id}'"

    # ค้นหาสินค้าปกติ
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
    
    # เรียงตาม Stock จากมากไปน้อย
    results = sorted(results, key=lambda r: float(str(r.get("มี Stock อยู่ที่", "0")).replace("~", "").strip()), reverse=True)

    # ส่งกลับเป็น Flex Message สำหรับรายการสินค้า
    return create_product_flex(results)

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
                    # ถ้าไม่ใช่ @@ → ไม่ตอบกลับ
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