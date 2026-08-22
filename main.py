import asyncio
from datetime import datetime, timedelta, timezone
import httpx
from pyrogram import Client

# ==================== الإعدادات الأساسية ====================
API_ID = 14762571
API_HASH = "26d1cacfb046cb168dce4cd7c3d1208f"

SESSION_STRING = "AQDhQksAKUA_ab1RrMW9YzvSOlQvpy3vQmbLHIjzLKKde9nxldLPYmsE38V90MwodeMpOhTQW02b1EpZGBWl1VGiKFA-b4d-ZOLIInnEEsPmPfEdzUmfroHC0DbnDN8x6cd75GcJ80gjXL0EJ-JaM99sBNRMtxcOytduHlTTDyHfL4blHNK-4ePJ5U12EodRP0F6Ft_EXMe3HrMNst0bRJdAJqKp5qtQy7P02GzVYKoNA9UvmjoUr8TS0kgCDcOPu0weCZmO4rdkucZxVdCJGOjbMHG1SeeQU1GE2LABBYDxmGIbFx853fWi-gUuYbiNj42jSt_5ybbNXIrxZaVWapYfTDSSpQAAAABUTfzIAA"
N8N_WEBHOOK_URL = "https://cst-n8n-8ae0ef0c-5bd3b69f.cloud-station.app/webhook/data"

TARGET_CHANNELS = ["Haymant2030", "urpath_uni", "hakathonat", "Sudie2030KSA"]
DESTINATION_GROUP = "hackersksa"
FETCH_INTERVAL = 12 * 60 * 60  # كل 12 ساعة

# قاموس لتتبع آخر ID تم معالجته لكل قناة لمنع التكرار
LAST_PROCESSED_IDS = {channel: 0 for channel in TARGET_CHANNELS}

# إنشاء العميل باستخدام session_string المباشرة
app = Client(
    "railway_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)


async def fetch_and_send_to_n8n():
    all_messages_payload = []
    
    # حد الوقت: فقط الرسائل المنشورة خلال الـ 12 ساعة الأخيرة
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=12)

    for channel in TARGET_CHANNELS:
        new_photos_count = 0
        last_id = LAST_PROCESSED_IDS[channel]
        highest_id_in_this_run = last_id

        try:
            messages = []
            # جلب أحدث 100 رسالة للفحص
            async for message in app.get_chat_history(channel, limit=100):
                # إذا وصلنا لرسالة أقدم من 12 ساعة وفي الدورة الأولى، نتوقف عن الفحص لتوفير الموارد
                if message.date < time_threshold and last_id == 0:
                    break
                messages.append(message)

            # ترتيب الرسائل تصاعدياً (من القديم إلى الجديد) لإرسالها بالترتيب الزمني الصحيح
            messages.reverse()

            for message in messages:
                # الشرط: تحتوي على صورة + أن تكون أحدث من آخر رسالة جرى فحصها + نُشرت خلال الـ 12 ساعة الأخيرة
                if message.photo and message.id > last_id and message.date >= time_threshold:
                    caption_text = message.caption or "بدون وصف"

                    # استخراج الروابط من وصف الرسالة
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
                        "media_type": "photo",
                        "date": str(message.date)
                    }
                    all_messages_payload.append(msg_data)
                    new_photos_count += 1

                    # تحديث أعلى ID تم الوصول إليه في هذه الدورة
                    if message.id > highest_id_in_this_run:
                        highest_id_in_this_run = message.id

                    print("==================================================")
                    print(f"📌 القناة الأصلية: @{channel}")
                    print(f"🆔 رقم الرسالة الأصلية: {message.id}")
                    print(f"📅 تاريخ النشر: {message.date}")
                    print(f"📤 تم نسخ الصورة وإرسالها لـ @{DESTINATION_GROUP} بنجاح!")
                    print(f"🔗 رابط الرسالة في القروب: {forwarded_msg_link}")
                    print(f"📝 الوصف: {caption_text[:60]}...")
                    print("==================================================\n")

            # تحديث السجل برقم أحدث رسالة تم معالجتها بالقناة
            if highest_id_in_this_run > last_id:
                LAST_PROCESSED_IDS[channel] = highest_id_in_this_run

            if new_photos_count == 0:
                print(f"ℹ️ لا توجد صور جديدة خلال الـ 12 ساعة الماضية في القناة: @{channel}")

        except Exception as ch_err:
            print(f"❌ خطأ في القناة @{channel}: {ch_err}")

        await asyncio.sleep(1)

    count = len(all_messages_payload)

    if count > 0:
        print(f"📊 إجمالي الرسائل الجديدة المنشورة والمجمعة: {count}")
        print("🚀 جاري إرسال البيانات إلى n8n Webhook...")

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            try:
                response = await http_client.post(N8N_WEBHOOK_URL, json=all_messages_payload)
                print(f"✅ تم الإرسال بنجاح! رمز استجابة السيرفر: {response.status_code}")
            except Exception as req_err:
                print(f"⚠️ فشل الإرسال لـ n8n: {req_err}")
    else:
        print("⚠️ لم يتم العثور على أي صور جديدة في كل القنوات المحددة.")


async def worker():
    while True:
        print("\n🔄 بدء دورة الفحص والجلب الجديدة...")
        try:
            await fetch_and_send_to_n8n()
        except Exception as e:
            print(f"❌ حدث خطأ غير متوقع: {e}")

        print("⏳ الانتظار لمدة 12 ساعة قبل الدورة القادمة...")
        await asyncio.sleep(FETCH_INTERVAL)


async def main():
    await app.start()
    print("🚀 تم تشغيل البوت بنجاح.. جاري المراقبة والدفع التلقائي:")
    try:
        await worker()
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
