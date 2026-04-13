import asyncio
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8767067142:AAGCiNgLT0o8ItLfK03aiBZYGwn4-QgMpC8"
MAX_QUESTIONS = 50

# 📁 Fayldan savollarni yuklash
def load_questions(file_path):
    questions = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line and line[0].isdigit():
            q_text = line

            opts = []
            answer = "A"

            for j in range(1, 5):
                opt = lines[i + j].strip()

                if "#" in opt:
                    answer = opt[0]
                    opt = opt.replace("#", "")

                opts.append(opt[2:].strip())

            questions.append({
                "q": q_text,
                "options": opts,
                "answer": answer
            })

            i += 5
        else:
            i += 1

    return questions

# 🔥 Savollarni yuklash
questions = load_questions("falsafa.txt")

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Boshlash uchun /start_falsafa ni bosing")

async def start_falsafa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_data[user_id] = {"score": 0, "index": 0, "active": True}

    # ⏳ countdown
    for i in range(5, 0, -1):
        await update.message.reply_text(f"Boshlanadi: {i}")
        await asyncio.sleep(1)

    await send_question(update, context)

async def send_question(update, context):
    user_id = update.effective_chat.id
    idx = user_data[user_id]["index"]

    # 🎯 50 ta savoldan keyin natija
    if idx > 0 and idx % MAX_QUESTIONS == 0:
        score = user_data[user_id]["score"]

        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 50 ta savol tugadi!\nNatija: {score}/50"
        )

        user_data[user_id]["score"] = 0

    if idx >= len(questions):
        await context.bot.send_message(
            chat_id=user_id,
            text="🏁 Barcha savollar tugadi!"
        )
        user_data[user_id]["active"] = False
        return

    q = questions[idx]

    # 🔥 VARIANTLARNI ARALASHTIRAMIZ
    options = q["options"].copy()
    correct_text = q["options"][ord(q["answer"]) - 65]

    random.shuffle(options)

    # yangi to‘g‘ri javobni topamiz
    new_correct = options.index(correct_text)

    # user_data ga saqlaymiz
    user_data[user_id]["current_correct"] = options[new_correct]

    keyboard = [[opt] for opt in options]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await context.bot.send_message(
        chat_id=user_id,
        text=q["q"],
        reply_markup=reply_markup
    )

    context.application.create_task(timer(context, user_id, idx))

async def timer(context, user_id, idx):
    msg = await context.bot.send_message(
        chat_id=user_id,
        text="⏳ Vaqt: 30"
    )

    for t in range(30, 0, -1):
        await asyncio.sleep(1)

        # agar user javob berib yuborgan bo‘lsa
        if user_data[user_id]["index"] != idx:
            return

        try:
            await msg.edit_text(f"⏳ Vaqt: {t}")
        except:
            pass

    # vaqt tugadi
    if user_data[user_id]["index"] == idx:
        await context.bot.send_message(chat_id=user_id, text="⏰ Vaqt tugadi!")
        user_data[user_id]["index"] += 1
        await send_question_fake(context, user_id)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if user_id not in user_data or not user_data[user_id]["active"]:
        return

    user_answer = update.message.text
    correct_answer = user_data[user_id]["current_correct"]

    if user_answer == correct_answer:
        user_data[user_id]["score"] += 1
        await update.message.reply_text("✅ To‘g‘ri")
    else:
        await update.message.reply_text("❌ Noto‘g‘ri")

    user_data[user_id]["index"] += 1
    await send_question(update, context)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_falsafa", start_falsafa))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
