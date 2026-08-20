import asyncio
import httpx
from pyrogram import Client, filters

API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"
N8N_WEBHOOK_URL = "https://cst-n8n-8ae0ef0c-5bd3b69f.cloud-station.app/webhook/data"
SESSION_STRING = "AQDhQksAvouTovJfShP4wdY-Qu1D6aVq0F1vLZO8MRJRHO6gTw1B1de3c9FqyLpU9KFkUA_cQmwhNaEB80ey2ijty29gmAEk0ELNPjPZr7r8HQIc9ZZ7lwTIzOn--HiGMgQ0qglTf7FKmxjmpCCzgObnsz0QOCkNKpmyUYblMcEm18rmN6M4B7u2sKSUIBJ5f1zVINE_S-1kQBg-bdKPS3m4Yx4DxeiF6iYCknBFdwSw_SFdQbuWQZ8NtdQBHLgUsa92qWe-UmBH7reCImMw7qzsoRgx8XUpGBLeWok3Nnh8j_hDGaA-MLasUA_XmNNC5m4muml_kUQS02xYrxwStoR3GchduAAAAABUTfzIAA"

TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]

app = Client("my_tele_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 1. المستمع: يعمل فوراً عند وصول أي رسالة
@app.on_message(filters.chat(TARGET_CHANNELS))
async def handle_new_message(client, message):
    text_content = message.text or message.caption or ""
    if not text_content: return

    msg_data = {
        "message_id": message.id,
        "channel": str(message.chat.username or message.chat.title),
        "description": text_content,
    }

    async with httpx.AsyncClient(timeout=15.0) as http_client:
        try:
            await http_client.post(N8N_WEBHOOK_URL, json=[msg_data])
            print(f"📩 تم إرسال رسالة فورية من {msg_data['channel']}")
        except Exception as e:
            print(f"⚠️ خطأ أثناء الإرسال الفوري: {e}")

# 2. مهمة النبض (Heartbeat): تعمل كل ساعة لمنع n8n من النوم
async def keep_alive_task():
    while True:
        await asyncio.sleep(3600)  # انتظار ساعة واحدة
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                # نرسل إشارة "Ping" بسيطة لـ n8n
                await http_client.post(N8N_WEBHOOK_URL, json={"type": "ping"})
                print("💓 نبض النشاط (Heartbeat) تم إرساله لـ n8n لمنع الخمول.")
        except Exception as e:
            print(f"⚠️ خطأ في إرسال نبض النشاط: {e}")

async def main():
    await app.start()
    # تشغيل مهمة النبض في الخلفية بالتوازي مع البوت
    asyncio.create_task(keep_alive_task())
    print("🚀 البوت يعمل الآن (استماع فوري + نبض نشاط كل ساعة)...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
