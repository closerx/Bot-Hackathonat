import asyncio
import httpx
from pyrogram import Client

# البيانات الأساسية
API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"

# ضع النص المترجم للجلسة (Session String) المستخرج من جهازك هنا بين التنصيص
SESSION_STRING = "ضع_هنا_نص_الـ_session_string_الخاص_بك"

N8N_WEBHOOK_URL = "https://cst-n8n-8ae0ef0c-5bd3b69f.cloud-station.app/webhook/data"
TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]
DESTINATION_GROUP = "hackersksa"
FETCH_INTERVAL = 12 * 60 * 60  # كل 12 ساعة

# إنشاء العميل باستخدام session_string المباشرة
app = Client(
    "railway_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

async def fetch_and_send_to_n8n():
    all_messages_payload = []

    for channel in TARGET_CHANNELS:
        found_photo = False
        try:
            async for message in app.get_chat_history(channel, limit=20):
                if message.photo:
                    caption_text = message.caption or "بدون وصف"

                    extracted_link = None
                    entities = message.caption_entities
                    if entities:
                        for entity in entities:
                            if entity.type.name == "TEXT_LINK":
                                extracted_link = entity.url
                            elif entity.type.name == "URL" and message.caption:
                                extracted_link = message.caption[entity.offset : entity.offset + entity.length]

                    # 1. نسخ الرسالة والصورة وإرسالها للقروب
                    forwarded_msg = await app.copy_message(
                        chat_id=DESTINATION_GROUP,
                        from_chat_id=channel,
                        message_id=message.id
                    )

                    # 2. بناء رابط الرسالة في القروب
                    forwarded_msg_link = f"https://t.me/{DESTINATION_GROUP}/{forwarded_msg.id}"

                    msg_data = {
                        "message_id": message.id,
                        "channel": str(channel),
                        "file_id": message.photo.file_id,
                        "description": caption_text,
                        "link": extracted_link or "",
                        "forwarded_message_id": forwarded_msg.id,
                        "forwarded_message_link": forwarded_msg_link,
                        "has_media": True,
                        "media_type": "photo"
                    }
                    all_messages_payload.append(msg_data)
                    found_photo = True
                    
                    print("==================================================")
                    print(f"📌 القناة الأصلية: @{channel}")
                    print(f"🆔 رقم الرسالة الأصلية: {message.id}")
                    print(f"📤 تم نسخ الصورة وإرسالها لـ @{DESTINATION_GROUP} بنجاح!")
                    print(f"🔗 رابط الرسالة في القروب: {forwarded_msg_link}")
                    print(f"📝 الوصف: {caption_text[:60]}...")
                    print("==================================================\n")
                    
                    break

            if not found_photo:
                print(f"⚠️ لم يتم العثور على أي صورة في أحدث الرسائل بالقناة: @{channel}")

        except Exception as ch_err:
            print(f"❌ خطأ في القناة @{channel}: {ch_err}")
            
        await asyncio.sleep(1)

    count = len(all_messages_payload)
    
    if count > 0:
        print(f"📊 إجمالي الرسائل المنشورة والمجمعة: {count}")
        print("🚀 جاري إرسال البيانات إلى n8n Webhook...")
        
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

        print("⏳ الانتظار لمدة 12 ساعة قبل الدورة القادمة...")
        await asyncio.sleep(FETCH_INTERVAL)

async def main():
    await app.start()
    print("🚀 تم تشغيل البوت بنجاح.. جاري إعادة التوجيه والإرسال:")
    try:
        await worker()
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
