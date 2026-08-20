import asyncio
import httpx
from pyrogram import Client, errors

API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"
N8N_WEBHOOK_URL = "https://cst-n8n-8ae0ef0c-5bd3b69f.cloud-station.app/webhook/data"
SESSION_STRING = "AQDhQksAvouTovJfShP4wdY-Qu1D6aVq0F1vLZO8MRJRHO6gTw1B1de3c9FqyLpU9KFkUA_cQmwhNaEB80ey2ijty29gmAEk0ELNPjPZr7r8HQIc9ZZ7lwTIzOn--HiGMgQ0qglTf7FKmxjmpCCzgObnsz0QOCkNKpmyUYblMcEm18rmN6M4B7u2sKSUIBJ5f1zVINE_S-1kQBg-bdKPS3m4Yx4DxeiF6iYCknBFdwSw_SFdQbuWQZ8NtdQBHLgUsa92qWe-UmBH7reCImMw7qzsoRgx8XUpGBLeWok3Nnh8j_hDGaA-MLasUA_XmNNC5m4muml_kUQS02xYrxwStoR3GchduAAAAABUTfzIAA"

TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]

# التعديل هنا: 12 ساعة = 43200 ثانية (مرتين في اليوم)
FETCH_INTERVAL = 12 * 60 * 60  

app = Client("my_tele_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

async def fetch_and_send_to_n8n():
    all_messages_payload = []

    for channel in TARGET_CHANNELS:
        found_photo = False
        try:
            # البحث في أحدث 20 رسالة عن صورة
            async for message in app.get_chat_history(channel, limit=2):
                if message.photo:
                    file_id = message.photo.file_id
                    caption_text = message.caption or "بدون وصف"

                    extracted_link = None
                    entities = message.caption_entities
                    if entities:
                        for entity in entities:
                            if entity.type.name == "TEXT_LINK":
                                extracted_link = entity.url
                            elif entity.type.name == "URL" and message.caption:
                                extracted_link = message.caption[entity.offset : entity.offset + entity.length]

                    msg_data = {
                        "message_id": message.id,
                        "channel": str(channel),
                        "file_id": file_id,
                        "description": caption_text,
                        "link": extracted_link or "",
                        "has_media": True,
                        "media_type": "photo",
                    }
                    all_messages_payload.append(msg_data)
                    found_photo = True
                    
                    # طباعة التفاصيل في الشاشة
                    print(f"==================================================")
                    print(f"📌 القناة: @{channel}")
                    print(f"🆔 رقم الرسالة: {message.id}")
                    print(f"🖼️ File ID للصورة: {file_id[:25]}...")
                    print(f"📝 الوصف: {caption_text[:60]}...")
                    print(f"🔗 الرابط المستخرج: {extracted_link or 'لا يوجد'}")
                    print(f"==================================================\n")
                    
                    break

            if not found_photo:
                print(f"⚠️ لم يتم العثور على أي صورة في أحدث 20 رسالة بالقناة: @{channel}")

        except Exception as ch_err:
            print(f"❌ خطأ في القناة @{channel}: {ch_err}")
            
        await asyncio.sleep(1)

    count = len(all_messages_payload)
    
    if count > 0:
        print(f"📊 إجمالي الصور المجلوبة: {count} من أصل 4 قنوات.")
        print("🚀 جاري الإرسال إلى n8n Webhook...")
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            try:
                response = await http_client.post(N8N_WEBHOOK_URL, json=all_messages_payload)
                print(f"✅ تم الإرسال بنجاح! رمز استجابة السيرفر: {response.status_code}")
            except Exception as req_err:
                print(f"⚠️ فشل الإرسال لـ n8n: {req_err}")
    else:
        print("⚠️ لم يتم العثور على أي صور في كل القنوات المحددة.")

async def worker():
    while True:
        print("\n🔄 بدء دورة الفحص والجلب جديدة...")
        try:
            await fetch_and_send_to_n8n()
        except Exception as e:
            print(f"❌ حدث خطأ غير متوقع: {e}")

        print(f"⏳ الانتظار لمدة 12 ساعة (43200 ثانية) قبل الدورة القادمة...")
        await asyncio.sleep(FETCH_INTERVAL)

async def main():
    await app.start()
    print("🚀 تم تشغيل البوت بنجاح.. جاري جلب البيانات الآن:")
    try:
        await worker()
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
