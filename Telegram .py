import json
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8659981637:AAGfciCvnp25nz2WChvZ2BC-njhru70-g3g"
ADMIN_ID = 8241829833
USDT_ADDRESS = "0x98472057c7E396f86B2526D0A4bC0ce51aE47e91"

DB_FILE = "USDTbebot"

# ================= DATABASE =================
def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

users = load_users()

# ================= KEYBOARD =================
menu = ReplyKeyboardMarkup(
    [
        ["💰 Balance", "📥 Deposit"],
        ["📈 Invest", "🎁 Claim"],
        ["👥 Referral", "📤 Withdraw"]
    ],
    resize_keyboard=True
)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id not in users:
        ref = None
        if context.args:
            ref = context.args[0]

        users[user_id] = {
            "balance": 0,
            "investments": [],
            "ref": ref,
            "total_earned": 0
        }

        # referral reward
        if ref and ref in users:
            users[ref]["balance"] += 1  # small signup bonus

    save_users(users)

    await update.message.reply_text(
        "🚀 Welcome to USDT Investment Bot",
        reply_markup=menu
    )

# ================= BALANCE =================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.message.from_user.id)]

    await update.message.reply_text(
        f"💰 Balance: ${user['balance']}\n"
        f"📊 Total Earned: ${user['total_earned']}"
    )

# ================= DEPOSIT =================
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📥 Send USDT (BEP-20) to:\n{USDT_ADDRESS}\n\n"
        "After sending, contact admin to confirm."
    )

# ================= INVEST =================
async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user = users[user_id]

    if user["balance"] < 2:
        await update.message.reply_text("❌ Minimum investment is $2")
        return

    amount = user["balance"]
    user["balance"] = 0

    investment = {
        "amount": amount,
        "start": time.time(),
        "claimed": 0
    }

    user["investments"].append(investment)

    # referral bonus
    if user["ref"] and user["ref"] in users:
        users[user["ref"]]["balance"] += amount * 0.2

    save_users(users)

    await update.message.reply_text(f"✅ Invested ${amount}")

# ================= CLAIM =================
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.message.from_user.id)]
    total = 0

    for inv in user["investments"]:
        days = int((time.time() - inv["start"]) / 86400)

        if days > 4:
            days = 4

        profit = inv["amount"] * 0.2 * days

        claimable = profit - inv["claimed"]

        if claimable > 0:
            total += claimable
            inv["claimed"] += claimable

    user["balance"] += total
    user["total_earned"] += total

    save_users(users)

    await update.message.reply_text(f"🎁 Claimed: ${total}")

# ================= REFERRAL =================
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"

    await update.message.reply_text(
        f"👥 Your referral link:\n{link}\n\n"
        "Earn 20% of referrals investment!"
    )

# ================= WITHDRAW =================
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.message.from_user.id)]

    if user["balance"] < 5:
        await update.message.reply_text("❌ Minimum withdraw is $5")
        return

    amount = user["balance"]
    user["balance"] = 0

    save_users(users)

    await update.message.reply_text(
        f"📤 Withdrawal request: ${amount}\nWaiting for admin approval..."
    )

# ================= MESSAGE HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💰 Balance":
        await balance(update, context)

    elif text == "📥 Deposit":
        await deposit(update, context)

    elif text == "📈 Invest":
        await invest(update, context)

    elif text == "🎁 Claim":
        await claim(update, context)

    elif text == "👥 Referral":
        await referral(update, context)

    elif text == "📤 Withdraw":
        await withdraw(update, context)

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

print("🤖 Bot Running...")
app.run_polling()
