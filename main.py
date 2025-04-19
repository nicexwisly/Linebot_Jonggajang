from flask import Flask, request, jsonify
import pandas as pd
import os
import requests
import traceback

app = Flask(__name__)

# เก็บ JSON ที่ upload เข้ามา
json_data_mm = []

# ใส่ LINE Access Token ของคุณตรงนี้
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or "Txryzcs+6W5ID6/HZmn1aCYIvaFgIuwGpFWD1yxomBZ8/CDColHRA+3gmLu9vBE+96lLEtwj4sLd5Qg/Z+gq/qhcaGRSMXWoIFULicrDdhOCCGw/cqH76whKHwYaE4vIyhscibFPEVvCn5Imk20tSwdB04t89/1O/w1cDnyilFU="

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

@app.route("/api/upload-mm", methods=["POST"])
def upload_mm():
    global json_data_mm
    try:
        json_data_mm = request.get_json()
        print(f"✅ อัปโหลดสำเร็จ: {len(json_data_mm)} records")
        return jsonify({"status": "success", "records": len(json_data_mm)}), 200
    except Exception as e:
        print(f"❌ ERROR in upload_mm(): {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def search_mm(keyword):
    global json_data_mm
    if not json_data_mm:
        return "❌ ยังไม่มีข้อมูล MM กรุณาอัปโหลดก่อน"

    keyword = keyword.strip()
    df = pd.DataFrame(json_data_mm)
    df = df[df["Item Number"].astype(str).str.strip() == keyword]

    if df.empty:
        return f"❌ ไม่พบข้อมูลสำหรับ Item Number: {keyword}"

    df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")
    df = df.sort_values("วันที่", ascending=False).head(7)

    lines = [
        f"- {row['Item Number']} | {row['Date'].strftime('%Y-%m-%d')} | รับเข้า {row['Receipts Qty']} | ปรับสต็อก {row['Inv Adjust Qty']} | คงเหลือ {row['EOY SOH Qty']} | ขาดหาย {row['Shrinkage Qty']} | ยอดขาย {row['Net Sales Qty']}"
        for _, row in df.iterrows()
    ]
    return "\n".join(lines)

@app.route("/", methods=["GET"])
def home():
    return "MM Bot Ready!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
