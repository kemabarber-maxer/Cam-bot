import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
from database import *

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MIN_POINTS = int(os.getenv("MIN_POINTS_FOR_PRIZE", "100"))
REF_BONUS = int(os.getenv("REFERRAL_BONUS", "50"))

# === MENYULAR ===
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Kanala abuna bol", callback_data="channels")
    builder.button(text="👤 Profilim", callback_data="profile")
    builder.button(text="🏆 Liderler", callback_data="leaderboard")
    builder.button(text="🎁 Uç alyş", callback_data="prizes")
    builder.button(text="🔗 Referal çagyrmak", callback_data="referral")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Yza", callback_data="main_menu")]
    ])

# === START ===
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandStart):
    user_id = message.from_user.id
    args = command.args
    
    user = get_user(user_id)
    
    if not user:
        referred_by = int(args) if args and args.isdigit() else None
        add_user(
            user_id=user_id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            referred_by=referred_by
        )
        if referred_by and referred_by != user_id:
            try:
                await bot.send_message(
                    referred_by, 
                    f"🎉 {message.from_user.full_name} siziň referalyňyz boldy! +{REF_BONUS} bal!"
                )
            except:
                pass
    
    await message.answer(
        f"🎮 **Uç Gazan Botuna hoş geldiňiz!**\n\n"
        f"📢 Kanallara abuna bolup bal gazanyň\n"
        f"🔗 Referal arkaly dost çagyryp has köp bal\n"
        f"🎁 {MIN_POINTS} bal ýygnap uç alyň!",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# === KANALLAR ===
@router.callback_query(F.data == "channels")
async def show_channels(callback):
    user_id = callback.from_user.id
    channels = get_channels(user_id)
    
    if not channels:
        await callback.message.edit_text(
            "Häzirlikçe tapşyrk ýok. Admin kanal goşar! ⏳",
            reply_markup=back_menu()
        )
        return
    
    builder = InlineKeyboardBuilder()
    
    for channel_id, name, points, completed in channels:
        status = " ✅" if completed else ""
        clean_id = channel_id.replace("@", "")
        
        if not completed:
            builder.button(
                text=f"📢 {name} (+{points} bal)",
                url=f"https://t.me/{clean_id}"
            )
            builder.button(
                text=f"✓ Barla",
                callback_data=f"check_{channel_id}"
            )
        else:
            builder.button(
                text=f"📢 {name} (+{points} bal){status}",
                callback_data="done"
            )
    
    builder.button(text="🔄 Täzele", callback_data="channels")
    builder.button(text="⬅️ Yza", callback_data="main_menu")
    builder.adjust(2, 2, 2, 1)
    
    await callback.message.edit_text(
        "📢 **Kanallara abuna bolup bal gazanyň**\n\n"
        "1. Kanala basyp abuna boluň\n"
        "2. Yza dönüp '✓ Barla' basyň\n"
        "3. Bal gazanyň! 🎉",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# === KANAL BARLAMA ===
@router.callback_query(F.data.startswith("check_"))
async def check_subscription(callback):
    channel_id = callback.data.replace("check_", "")
    user_id = callback.from_user.id
    
    try:
        # ULANYJYNYŇ KANALDAKY STATUSYNY BARLA
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        
        # Abuna bolanmy?
        if member.status in ["member", "administrator", "creator"]:
            import sqlite3
            conn = sqlite3.connect("bot.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT points FROM channels WHERE channel_id = ?", 
                (channel_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                points = result[0]
                if complete_channel_task(user_id, channel_id, points):
                    await callback.answer(
                        f"🎉 Gutlaýarys! +{points} bal gazandyňyz!", 
                        show_alert=True
                    )
                    await show_channels(callback)
                else:
                    await callback.answer(
                        "Bu kanal eýýäm barlanan!", 
                        show_alert=True
                    )
            else:
                await callback.answer("Kanal tapylmady!", show_alert=True)
        else:
            await callback.answer(
                "❌ Siz bu kanala abuna däl!\nKanala abuna bolup täzeden barlaň.", 
                show_alert=True
            )
            
    except TelegramBadRequest as e:
        await callback.answer(
            "Kanal tapylmady ýa-da bot kanala admin däl!", 
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            "Ýalňyşlyk ýüze çykdy. Soňra synanyşyň.", 
            show_alert=True
        )

@router.callback_query(F.data == "done")
async def already_done(callback):
    await callback.answer("Bu kanal eýýäm ýerine ýetirilen!", show_alert=True)

# === PROFIL ===
@router.callback_query(F.data == "profile")
async def show_profile(callback):
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if not user:
        await callback.answer("Ýalňyşlyk!", show_alert=True)
        return
    
    _, username, full_name, points, referrals, referred_by, tasks_completed, created_at = user
    remaining = max(0, MIN_POINTS - points)
    can_claim = "✅ Uç alyp bilersiňiz!" if points >= MIN_POINTS else f"❌ Galarak: {remaining} bal"
    
    await callback.message.edit_text(
        f"👤 **Profilim**\n\n"
        f"📛 Ady: {full_name}\n"
        f"💰 Bal: **{points}**\n"
        f"👥 Referallar: {referrals}\n"
        f"✅ Ýerine ýetirilen: {tasks_completed}\n\n"
        f"🎯 {can_claim}",
        reply_markup=back_menu(),
        parse_mode="Markdown"
    )

# === LIDERLER ===
@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback):
    leaders = get_leaderboard()
    
    text = "🏆 **Top 10 Liderler:**\n\n"
    for i, (name, points, refs) in enumerate(leaders, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        text += f"{medal} {name}: {points} bal ({refs} ref)\n"
    
    await callback.message.edit_text(text, reply_markup=back_menu(), parse_mode="Markdown")

# === REFERRAL ===
@router.callback_query(F.data == "referral")
async def show_referral(callback):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    user = get_user(user_id)
    refs = user[4] if user else 0
    
    await callback.message.edit_text(
        f"🔗 **Referal çagyrmak**\n\n"
        f"Linki kopýalaň:\n`{link}`\n\n"
        f"💰 Her täze ulanyjy: +{REF_BONUS} bal\n"
        f"👥 Siziň referallaryňyz: {refs}",
        reply_markup=back_menu(),
        parse_mode="Markdown"
    )

# === UÇ ALIŞ ===
@router.callback_query(F.data == "prizes")
async def show_prizes(callback):
    user_id = callback.from_user.id
    user = get_user(user_id)
    points = user[3] if user else 0
    
    builder = InlineKeyboardBuilder()
    
    if points >= MIN_POINTS:
        builder.button(text=f"🎁 {MIN_POINTS} bal - Uç", callback_data=f"claim_{MIN_POINTS}")
    if points >= MIN_POINTS * 2:
        builder.button(text=f"🎁 {MIN_POINTS*2} bal - 2x Uç", callback_data=f"claim_{MIN_POINTS*2}")
    
    builder.button(text="⬅️ Yza", callback_data="main_menu")
    builder.adjust(1)
    
    can_claim = "✅ Uç alyp bilersiňiz!" if points >= MIN_POINTS else f"❌ Gerek: {MIN_POINTS - points} bal"
    
    await callback.message.edit_text(
        f"🎁 **Uç alyş**\n\n"
        f"💰 Siziň balyňyz: {points}\n"
        f"📍 Minimum: {MIN_POINTS} bal\n\n"
        f"{can_claim}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("claim_"))
async def claim_prize(callback):
    points = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    if request_prize(user_id, points):
        user = get_user(user_id)
        new_points = user[3] if user else 0
        
        await callback.message.edit_text(
            f"✅ **Uç alyş üstünlikli!**\n\n"
            f"💰 Ulanan bal: {points}\n"
            f"📊 Galan bal: {new_points}\n"
            f"⏳ Admin tassyklamak üçin habar iberildi.",
            reply_markup=back_menu()
        )
        
        await bot.send_message(
            ADMIN_ID,
            f"🎁 **Täze uç alyş!**\n\n"
            f"👤 {callback.from_user.full_name}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 {points} bal\n"
            f"✅ /confirm_{user_id} | ❌ /reject_{user_id}",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("Ýeterlik bal ýok!", show_alert=True)

# === ADMIN ===
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    import sqlite3
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(points), SUM(referrals) FROM users")
    total_users, total_points, total_refs = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM prizes WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    conn.close()
    
    await message.answer(
        f"🔧 **Admin Panel**\n\n"
        f"👥 Ulanyjy: {total_users or 0}\n"
        f"💰 Jemi bal: {total_points or 0}\n"
        f"🔗 Referal: {total_refs or 0}\n"
        f"⏳ Garaşylýan uç: {pending or 0}\n\n"
        f"/addchannel @kanal 'Ady' bal\n"
        f"/pending - Garaşylýanlar\n"
        f"/confirm_ID - Tassykla\n"
        f"/reject_ID - Ret et"
    )

@router.message(Command("addchannel"))
async def add_channel_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 4:
        await message.answer("Ulanylyş: /addchannel @kanal 'Kanal ady' 20")
        return
    
    channel_id = args[1]
    points = int(args[-1])
    name = " ".join(args[2:-1]).strip("'\"")
    
    add_channel(channel_id, name, points)
    await message.answer(f"✅ {channel_id} goşuldy! ({points} bal)")

@router.message(Command("pending"))
async def pending_prizes(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    import sqlite3
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.user_id, u.full_name, p.points_used 
        FROM prizes p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.status = 'pending'
    ''')
    pending = cursor.fetchall()
    conn.close()
    
    if not pending:
        await message.answer("Garaşylýan uç ýok!")
        return
    
    text = "⏳ **Garaşylýan uçlar:**\n\n"
    for user_id, name, points in pending:
        text += f"👤 {name} (ID: {user_id}) - {points} bal\n"
        text += f"✅ /confirm_{user_id} | ❌ /reject_{user_id}\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("confirm"))
async def confirm_prize(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split("_")
    if len(args) < 2:
        await message.answer("Ulanylyş: /confirm_123456")
        return
    
    user_id = int(args[1])
    
    import sqlite3
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE prizes SET status = 'confirmed' WHERE user_id = ? AND status = 'pending'",
        (user_id,)
    )
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Ulanyjy {user_id} üçin uç tassyklandy!")
    
    try:
        await bot.send_message(
            user_id,
            "🎉 **Tebrikler!**\n\nUç alyşyňyz tassyklandy!\nUç gysga wagtda iberiler."
        )
    except:
        pass

@router.message(Command("reject"))
async def reject_prize(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split("_")
    if len(args) < 2:
        await message.answer("Ulanylyş: /reject_123456")
        return
    
    user_id = int(args[1])
    
    import sqlite3
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT points_used FROM prizes WHERE user_id = ? AND status = 'pending'",
        (user_id,)
    )
    result = cursor.fetchone()
    
    if result:
        points = result[0]
        cursor.execute(
            "UPDATE prizes SET status = 'rejected' WHERE user_id = ? AND status = 'pending'",
            (user_id,)
        )
        cursor.execute(
            "UPDATE users SET points = points + ? WHERE user_id = ?",
            (points, user_id)
        )
        conn.commit()
        await message.answer(f"❌ Ret edildi. Bal yzyna gaýtaryldy.")
        
        try:
            await bot.send_message(
                user_id,
                f"❌ Uç alyşyňyz ret edildi.\n💰 {points} bal yzyna gaýtaryldy."
            )
        except:
            pass
    else:
        await message.answer("Garaşylýan uç tapylmady!")
    
    conn.close()

# === YZYA ===
@router.callback_query(F.data == "main_menu")
async def back_to_main(callback):
    await callback.message.edit_text(
        f"🎮 **Uç Gazan Botuna hoş geldiňiz!**\n\n"
        f"📢 Kanallara abuna bolup bal gazanyň\n"
        f"🔗 Referal arkaly has köp bal\n"
        f"🎁 {MIN_POINTS} bal ýygnap uç alyň!",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# === ISLEMEK ===
async def main():
    init_db()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
