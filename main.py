import asyncio
import httpx
from pyrogram import Client, errors

# البيانات مباشرة بدون os.getenv
API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"
N8N_WEBHOOK_URL = "https://9e925693.kube-ops.com/webhook/data/"
SESSION_STRING = "AQDhQksAvouTovJfShP4wdY-Qu1D6aVq0F1vLZO8MRJRHO6gTw1B1de3c9FqyLpU9KFkUA_cQmwhNaEB80ey2ijty29gmAEk0ELNPjPZr7r8HQIc9ZZ7lwTIzOn--HiGMgQ0qglTf7FKmxjmpCCzgObnsz0QOCkNKpmyUYblMcEm18rmN6M4B7u2sKSUIBJ5f1zVINE_S-1kQBg-bdKPS3m4Yx4DxeiF6iYCknBFdwSw_SFdQbuWQZ8NtdQBHLgUsa92qWe-UmBH7reCImMw7qzsoRgx8XUpGBLeWok3Nnh8j_hDGaA-MLasUA_XmNNC5m4muml_kUQS02xYrxwStoR3GchduAAAAABUTfzIAA"

TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]

# تحديد وقت الانتظار: 3 دقائق (3 * 60 = 180 ثانية)
FETCH_INTERVAL = 3 * 60

app = Client("my_tele_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)


async def fetch_and_send_to_n8n():
    all_messages_payload = []

    for channel in TARGET_CHANNELS:
        try:
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
                        str(message.media) if message.media else None
                    ),
                }

                all_messages_payload.append(msg_data)

        except errors.FloodWait as f_err:
            print(f"⚠️ ضغط طلبات من تليجرام، انتظار {f_err.value} ثانية...")
            await asyncio.sleep(f_err.value)
        except Exception as ch_err:
            print(f"❌ خطأ في القناة {channel}: {ch_err}")

        await asyncio.sleep(1)

    if all_messages_payload:
        print(f"📦 تم تجميع {len(all_messages_payload)} رسالة. جاري الإرسال لـ n8n...")

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            try:
                response = await http_client.post(
                    N8N_WEBHOOK_URL, json=all_messages_payload
                )
                print(f"✅ تم الإرسال بنجاح! كود الاستجابة: {response.status_code}")
            except Exception as req_err:
                print(f"⚠️ فشل الاتصال بـ n8n: {req_err}")
    else:
        print("⚠️ لم يتم جلب أي رسائل.")


async def worker():
    """حلقة تكرار مضمونة لا تتوقف"""
    while True:
        print("\n🔄 بدء دورة جلب البيانات الجديدة...")
        try:
            await fetch_and_send_to_n8n()
        except Exception as e:
            print(f"❌ حدث خطأ غير متوقع: {e}")

        print(f"⏳ سيكرر الكود الفحص بعد {FETCH_INTERVAL // 60} دقائق...")
        await asyncio.sleep(FETCH_INTERVAL)


async def main():
    await app.start()
    print("🚀 تم الاتصال بـ Telegram بنجاح! البوت يعمل الآن كل 3 دقائق...")
    try:
        await worker()
    finally:
        await app.stop()


if __name__ == "__main__":
    # تشغيل مستمر متوافق مع البيئات السحابية مثل Railway
    asyncio.run(main())
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
        await asyncio.sleep(mytime)


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
