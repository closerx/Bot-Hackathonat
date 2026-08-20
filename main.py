import asyncio
import httpx
from pyrogram import Client, errors

API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"
N8N_WEBHOOK_URL = "https://cst-n8n-8ae0ef0c-5bd3b69f.cloud-station.app/webhook/data"
SESSION_STRING = "AQDhQksAvouTovJfShP4wdY-Qu1D6aVq0F1vLZO8MRJRHO6gTw1B1de3c9FqyLpU9KFkUA_cQmwhNaEB80ey2ijty29gmAEk0ELNPjPZr7r8HQIc9ZZ7lwTIzOn--HiGMgQ0qglTf7FKmxjmpCCzgObnsz0QOCkNKpmyUYblMcEm18rmN6M4B7u2sKSUIBJ5f1zVINE_S-1kQBg-bdKPS3m4Yx4DxeiF6iYCknBFdwSw_SFdQbuWQZ8NtdQBHLgUsa92qWe-UmBH7reCImMw7qzsoRgx8XUpGBLeWok3Nnh8j_hDGaA-MLasUA_XmNNC5m4muml_kUQS02xYrxwStoR3GchduAAAAABUTfzIAA"

TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]
FETCH_INTERVAL = 3600 # ساعة واحدة

app = Client("my_tele_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

async def fetch_and_send_to_n8n():
    all_messages_payload = []

    for channel in TARGET_CHANNELS:
        try:
            async for message in app.get_chat_history(channel, limit=1):
                text_content = message.text or message.caption or ""
                
                # إضافة شرط: إذا كان الوصف فارغاً تماماً لا نعتبره رسالة مهمة
                # يمكنك حذف هذا الشرط if text_content: إذا كنت تريد جلب الرسائل حتى لو بدون نص
                if text_content: 
                    extracted_link = None
                    entities = message.entities or message.caption_entities
                    if entities:
                        for entity in entities:
                            if entity.type.name == "TEXT_LINK":
                                extracted_link = entity.url
                            elif entity.type.name == "URL":
                                extracted_link = text_content[entity.offset : entity.offset + entity.length]

                    msg_data = {
                        "message_id": message.id,
                        "channel": str(channel),
                        "description": text_content,
                        "link": extracted_link or "",
                        "has_media": message.media is not None,
                        "media_type": str(message.media) if message.media else None,
                    }
                    all_messages_payload.append(msg_data)

        except Exception as ch_err:
            print(f"❌ خطأ في القناة {channel}: {ch_err}")
        await asyncio.sleep(1)

    # هنا قمنا بحساب العدد
    count = len(all_messages_payload)
    
    if count > 0:
        print(f"📊 تم العثور على {count} رسالة تحتوي على وصف. جاري الإرسال لـ n8n...")
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            try:
                response = await http_client.post(N8N_WEBHOOK_URL, json=all_messages_payload)
                print(f"✅ تم الإرسال بنجاح! رمز الاستجابة: {response.status_code}")
            except Exception as req_err:
                print(f"⚠️ فشل الاتصال بـ n8n: {req_err}")
    else:
        print("⚠️ لم يتم العثور على رسائل جديدة تحتوي على نصوص في القنوات.")

async def worker():
    while True:
        print("\n🔄 بدء دورة جلب البيانات الجديدة...")
        try:
            await fetch_and_send_to_n8n()
        except Exception as e:
            print(f"❌ حدث خطأ غير متوقع أثناء الدورة: {e}")

        print(f"⏳ سيكرر الكود الفحص بعد ساعة واحدة...")
        await asyncio.sleep(FETCH_INTERVAL)

async def main():
    await app.start()
    print("🚀 البوت يعمل الآن..")
    try:
        await worker()
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
