from flask import Flask, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

# 🔒 ใส่ LINE ACCESS TOKEN ของคุณตรงนี้
LINE_ACCESS_TOKEN = "Txryzcs+6W5ID6/HZmn1aCYIvaFgIuwGpFWD1yxomBZ8/CDColHRA+3gmLu9vBE+96lLEtwj4sLd5Qg/Z+gq/qhcaGRSMXWoIFULicrDdhOCCGw/cqH76whKHwYaE4vIyhscibFPEVvCn5Imk20tSwdB04t89/1O/w1cDnyilFU="

json_data_mm = []

# ✅ ฟังก์ชันส่งข้อความกลับ LINE
def reply_to_line(reply_token, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

# ✅ Webhook จาก LINE
@app.route("/callback", methods=["POST"])
def callback():
    global json_data_mm
    try:
        payload = request.get_json()
        events = payload.get("events", [])
        for event in events:
            reply_token = event["replyToken"]
            user_msg = event["message"]["text"]

            # ถ้าพิมพ์ว่า @mm ตามด้วยเลข Item
            if user_msg.startswith("@mm"):
                keyword = user_msg.replace("@mm", "").strip()
                answer = search_mm(keyword)
                reply_to_line(reply_token, answer)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ อัปโหลด JSON
@app.route("/api/upload-mm", methods=["POST"])
def upload_mm():
    global json_data_mm
    try:
        json_data_mm = request.get_json()
        print(f"✅ ได้รับข้อมูล MM จำนวน {len(json_data_mm)} records")
        return jsonify({"status": "success", "records": len(json_data_mm)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ ค้นหาข้อมูลตาม Item Number
def search_mm(keyword):
    global json_data_mm
    if not json_data_mm:
        return "❌ ยังไม่มีข้อมูล MM กรุณาอัปโหลดก่อน"

    keyword = keyword.strip()
    df = pd.DataFrame(json_data_mm)
    df = df[df["Item Number"].astype(str).str.strip() == keyword]

    if df.empty:
        return f"❌ ไม่พบข้อมูลสำหรับ Item Number: {keyword}"

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values("Date", ascending=False).head(7)

    lines = []
    for _, row in df.iterrows():
        line = f"- {row['Date'].date()} | {row['Item']} | QTY: {row['EOY SOH Qty']}"
        lines.append(line)

    return "\n".join(lines)

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running."

# ✅ สำหรับ Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
