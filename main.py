import asyncio
import httpx
from pyrogram import Client

API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"

 #ضع رابط الـ Webhook الفعلي من n8n هنا
N8N_WEBHOOK_URL = "https://9e925693.kube-ops.com/webhook/data"

TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]

# مدة الانتظار بالثواني (3600 ثانية = 1 ساعة)
FETCH_INTERVAL = 3600

app = Client("my_tele_session", api_id=API_ID, api_hash=API_HASH)


async def fetch_and_send_to_n8n():
    all_messages_payload = []

    for channel in TARGET_CHANNELS:
        try:
            # جلب آخر رسالة من كل قناة
            async for message in app.get_chat_history(channel, limit=1):
                text_content = message.text or message.caption or ""

                extracted_link = None
                entities = message.entities or message.caption_entities
                if entities:
                    for entity in entities:
                        if entity.type.name == "TEXT_LINK":
                            extracted_link = entity.url
                        elif entity.type.name == "URL":
                            extracted_link = text_content[
                                entity.offset : entity.offset + entity.length
                            ]

                msg_data = {
                    "message_id": message.id,
                    "channel": str(channel),
                    "description": text_content,
                    "link": extracted_link or "",
                    "has_media": message.media is not None,
                    "media_type": (
                        message.media.value if message.media else None
                    ),
                }

                all_messages_payload.append(msg_data)

        except Exception as ch_err:
            print(f"❌ خطأ في القناة {channel}: {ch_err}")

    # إرسال البيانات
    if all_messages_payload:
        print(
            f"📦 تم تجميع {len(all_messages_payload)} رسالة. جاري الإرسال لـ n8n..."
        )
        print(all_messages_payload)

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            try:
                response = await http_client.post(
                    N8N_WEBHOOK_URL, json=all_messages_payload
                )
                print(
                    f"✅ تم الإرسال بنجاح! رمز الاستجابة: {response.status_code}"
                )
            except Exception as req_err:
                
                print(f" فشل الاتصال بي n8n  {req_err} ⚠️ ")
    else:
        print("⚠️ لم يتم جلب أي رسائل.")


async def worker():
    """حلقة تكرار تعمل باستمرار كل ساعة"""
    while True:
        print("\n🔄 بدء دورة جلب البيانات الجديدة...")
        try:
            await fetch_and_send_to_n8n()
        except Exception as e:
            print(f"❌ حدث خطأ غير متوقع أثناء الدورة: {e}")

        print(f"⏳ سيكرر الكود الفحص بعد {FETCH_INTERVAL // 60} دقيقة...")
        await asyncio.sleep(FETCH_INTERVAL)


async def main():
    # تشغيل العميل والتأكد من استمرارية الجلسة بدون إعادة فتح وإغلاق
    await app.start()
    try:
        await worker()
    finally:
        await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())




#----------------
