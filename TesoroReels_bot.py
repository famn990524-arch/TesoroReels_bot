import asyncio
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import json
from typing import List, Dict, Optional
import re
import os
import shutil
import time

# ======================
# CONFIGURAZIONE
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ No se encontró la variable de entorno BOT_TOKEN. Configúrala en Railway.")

ADMIN_USERS = [7097140504, 6094647471, 5363312268]
ADMIN_USERNAMES = {7097140504: "famn25", 6094647471: "ccgonzalezb13", 5363312268: "Drose1493"}

DATA_FOLDER = "reels_bot_data"
REELS_FOLDER = os.path.join(DATA_FOLDER, "reels")
REELS_DB_FILE = os.path.join(DATA_FOLDER, "reels_db.json")
POSTERS_DB_FILE = os.path.join(DATA_FOLDER, "posters_db.json")
USERS_DB_FILE = os.path.join(DATA_FOLDER, "users_db.json")

THRESHOLD_REELS = 3

waiting_for_reel_upload = {}
waiting_for_poster_input = {}
waiting_for_account_input = {}
waiting_for_country_input = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

reels_data = {}
reels_files = {}
user_posters = {}

# ======================
# FUNCIONES DE PERSISTENCIA
# ======================

def init_folders():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(REELS_FOLDER, exist_ok=True)

def load_data():
    global reels_data, reels_files, user_posters
    
    if os.path.exists(POSTERS_DB_FILE):
        with open(POSTERS_DB_FILE, 'r', encoding='utf-8') as f:
            reels_data = json.load(f)
    else:
        reels_data = {
            "spain": {
                "name": "🇪🇸 España",
                "posters": {
                    "camila": {"name": "CamilaG", "accounts": ["mxmiluxi", "mllwxxu", "mixwula", "milixwwo"]},
                    "giselle": {"name": "Giselle", "accounts": ["milwxuxo", "wulmixw", "milxwlu", "wximul"]},
                    "anna": {"name": "Anna", "accounts": ["wumlaxwm", "xmilwux", "wixlmu", "miluwlx"]},
                    "maya": {"name": "Maya", "accounts": ["wxmill1", "wumlixo", "xmuwali"]},
                    "ismerda": {"name": "Ismerda", "accounts": ["mulawxi", "woxmilu", "ilxwuma", "milxwulm"]},
                    "javiera": {"name": "Javiera", "accounts": ["milxawu77", "wmilau6xa", "mizuxw7", "wmilxwu"]}
                }
            },
            "usa": {
                "name": "🇺🇸 USA",
                "posters": {
                    "oluwatoyosi": {"name": "Oluwatoyosi", "accounts": ["chloewatanabesora", "scarlettodayuki"]},
                    "truong": {"name": "Truong", "accounts": ["mlwxmux", "ariamoriharu"]}
                }
            },
            "brazil": {
                "name": "🇧🇷 Brasil",
                "posters": {
                    "sarah": {"name": "Sarah", "accounts": ["milaxwu_1", "woxliam", "lumawxi", "xwmilau", "wilamxu", "milxuwuu", "milxwuoa1", "milawu9x"]},
                    "victor": {"name": "Victor", "accounts": ["wumilaxx", "xwmilauu", "milwuxa", "wmilaox"]}
                }
            },
            "germany": {
                "name": "🇩🇪 Alemania",
                "posters": {
                    "maya": {"name": "Maya", "accounts": ["wangmilinae", "wangixmilii", "milawangxi"]},
                    "camila": {"name": "CamilaG", "accounts": ["milawaaangz", "milawangya"]},
                    "gf": {"name": "GFR", "accounts": ["milawangri"]}
                }
            },
            "italy": {
                "name": "🇮🇹 Italia",
                "posters": {
                    "gf": {"name": "GFR", "accounts": ["micaxwox", "wumiclxc", "milazhcx", "micaelawu7x", "zhangmilaa", "milaaazxo", "wuxmicx77", "wuxmicalex"]},
                    "dianne": {"name": "DianneR", "accounts": ["elirasantara", "eliraasant", "laelirasant", "aauroraleonetti", "auroraaleonetti", "auroraleonetti_", "naomiiwang_", "milbloomx", "justmilix", "milenadamanti"]},
                    "alberto": {"name": "Alberto", "accounts": ["bellaamorenox", "labelamoregram", "bellalaspagnolaa"]},
                    "laura": {"name": "Laura", "accounts": ["bellamorenooo__", "bellamorenoo_", "bellalaspagnola"]},
                    "sara": {"name": "Sara", "accounts": ["isabellaaurent", "laura_laugram"]},
                    "thuany": {"name": "Thuany", "accounts": ["damantmilena", "sweet_milexo", "milenadaman", "walimxu", "wamilux"]},
                    "valentina": {"name": "Valentina", "accounts": ["lamorenobellaax", "bellasimoren", "morenabellaai", "lalauretaxx", "lalaauretta", "lauraeey_", "elirabellisima69", "elirasanreal", "elirabellisima", "muxilaw"]}
                }
            }
        }
        save_posters_data()
    
    if os.path.exists(REELS_DB_FILE):
        with open(REELS_DB_FILE, 'r', encoding='utf-8') as f:
            reels_files = json.load(f)
    else:
        reels_files = {}
        for country, country_data in reels_data.items():
            for poster, poster_data in country_data["posters"].items():
                for account in poster_data["accounts"]:
                    if account not in reels_files:
                        reels_files[account] = {"total": 0, "disponibili": [], "usate": [], "metadata": {}}
        save_reels_data()
    
    if os.path.exists(USERS_DB_FILE):
        with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            user_posters = user_data.get("posters", {})
    else:
        user_posters = {}
        save_users_data()

def save_posters_data():
    with open(POSTERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(reels_data, f, ensure_ascii=False, indent=2)

def save_reels_data():
    with open(REELS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(reels_files, f, ensure_ascii=False, indent=2)

def save_users_data():
    with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump({"posters": user_posters}, f, ensure_ascii=False, indent=2)

def get_poster_countries(poster_name: str):
    countries = []
    for country_key, country_data in reels_data.items():
        for poster_key, poster_data in country_data["posters"].items():
            if poster_data["name"].lower() == poster_name.lower():
                countries.append({
                    "country_key": country_key,
                    "country_name": country_data["name"],
                    "poster_key": poster_key,
                    "poster_name": poster_data["name"]
                })
    return countries

def aggiungere_reel_per_account(account: str, reel_path: str):
    if account not in reels_files:
        reels_files[account] = {"total": 0, "disponibili": [], "usate": [], "metadata": {}}
    
    nuovo_id = reels_files[account]["total"] + 1
    ext = os.path.splitext(reel_path)[1]
    nuovo_nome = f"{account}_reel_{nuovo_id}{ext}"
    nuovo_path = os.path.join(REELS_FOLDER, nuovo_nome)
    
    shutil.copy2(reel_path, nuovo_path)
    
    reels_files[account]["metadata"][str(nuovo_id)] = {"path": nuovo_path, "original_name": os.path.basename(reel_path), "used": False}
    reels_files[account]["total"] += 1
    reels_files[account]["disponibili"].append(nuovo_id)
    
    save_reels_data()
    return nuovo_id

def ottenere_reel_disponibile_per_account(account: str) -> Optional[int]:
    if account not in reels_files:
        return None
    disponibili = reels_files[account]["disponibili"]
    if not disponibili:
        return None
    random.shuffle(disponibili)
    return disponibili[0]

def marcare_reel_come_usato(account: str, reel_id: int):
    if account not in reels_files:
        return
    reel_id_str = str(reel_id)
    if reel_id_str in reels_files[account]["metadata"]:
        reels_files[account]["metadata"][reel_id_str]["used"] = True
        if reel_id in reels_files[account]["disponibili"]:
            reels_files[account]["disponibili"].remove(reel_id)
        reels_files[account]["usate"].append(reel_id)
    save_reels_data()

def get_stato_account(account: str) -> tuple:
    if account not in reels_files:
        return 0, 0, 0
    usate = len(reels_files[account]["usate"])
    disponibili = len(reels_files[account]["disponibili"])
    total = reels_files[account]["total"]
    return usate, disponibili, total

def reset_reels_per_account(account: str):
    if account in reels_files:
        for reel_id, meta in reels_files[account]["metadata"].items():
            path = meta.get("path")
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass
    reels_files[account] = {"total": 0, "disponibili": [], "usate": [], "metadata": {}}
    save_reels_data()

def delete_account(country_key: str, poster_key: str, account: str):
    if country_key in reels_data and poster_key in reels_data[country_key]["posters"]:
        if account in reels_data[country_key]["posters"][poster_key]["accounts"]:
            reels_data[country_key]["posters"][poster_key]["accounts"].remove(account)
            save_posters_data()
            if account in reels_files:
                for reel_id, meta in reels_files[account]["metadata"].items():
                    path = meta.get("path")
                    if path and os.path.exists(path):
                        try:
                            os.unlink(path)
                        except:
                            pass
                del reels_files[account]
                save_reels_data()
            return True
    return False

def delete_poster(country_key: str, poster_key: str):
    if country_key in reels_data and poster_key in reels_data[country_key]["posters"]:
        for account in reels_data[country_key]["posters"][poster_key]["accounts"]:
            if account in reels_files:
                for reel_id, meta in reels_files[account]["metadata"].items():
                    path = meta.get("path")
                    if path and os.path.exists(path):
                        try:
                            os.unlink(path)
                        except:
                            pass
                del reels_files[account]
        del reels_data[country_key]["posters"][poster_key]
        save_posters_data()
        save_reels_data()
        return True
    return False

def aggiungere_nuovo_poster(country_key: str, poster_key: str, poster_name: str, accounts: List[str]):
    if country_key not in reels_data or poster_key in reels_data[country_key]["posters"]:
        return False
    reels_data[country_key]["posters"][poster_key] = {"name": poster_name, "accounts": accounts}
    save_posters_data()
    for account in accounts:
        if account not in reels_files:
            reels_files[account] = {"total": 0, "disponibili": [], "usate": [], "metadata": {}}
    save_reels_data()
    return True

def aggiungere_nuova_account(country_key: str, poster_key: str, account: str):
    if country_key not in reels_data or poster_key not in reels_data[country_key]["posters"]:
        return False
    if account in reels_data[country_key]["posters"][poster_key]["accounts"]:
        return False
    reels_data[country_key]["posters"][poster_key]["accounts"].append(account)
    save_posters_data()
    if account not in reels_files:
        reels_files[account] = {"total": 0, "disponibili": [], "usate": [], "metadata": {}}
    save_reels_data()
    return True

def aggiungere_nuovo_paese(country_key: str, country_name: str):
    if country_key in reels_data:
        return False
    reels_data[country_key] = {"name": country_name, "posters": {}}
    save_posters_data()
    return True

# ======================
# NOTIFICHE ADMIN
# ======================

async def notificare_admin(context: ContextTypes.DEFAULT_TYPE, messaggio: str, is_admin_action: bool = False):
    for admin_id in ADMIN_USERS:
        try:
            if is_admin_action:
                await context.bot.send_message(chat_id=admin_id, text=f"👑 <b>ADMIN:</b>\n{messaggio}", parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=admin_id, text=messaggio, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error sending admin notification to {admin_id}: {e}")

# ======================
# MENU USUARIO
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name
    
    if user.id not in ADMIN_USERS:
        await notificare_admin(context, f"👤 New user: @{username} (ID: {user.id})")
    
    await update.message.reply_text(
        f"Hello @{username}! 👋\n\n"
        f"🎬 <b>Welcome to the Reels Bot!</b>\n\n"
        f"Use <code>/menu</code> to start receiving reels.\n"
        f"Type your poster name (e.g., <code>CamilaG</code>, <code>DianneR</code>, <code>GFR</code>)\n\n"
        f"💡 <b>Commands:</b>\n"
        f"• <code>/menu</code> - Start receiving reels\n"
        f"• <code>/admin</code> - Admin panel\n"
        f"• <code>/start</code> - This message",
        parse_mode="HTML"
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if str(user_id) in user_posters:
        keyboard = [
            [InlineKeyboardButton("✅ Usar mi poster actual", callback_data="use_current_poster")],
            [InlineKeyboardButton("🆕 Cambiar de poster", callback_data="change_poster")]
        ]
        if user_id in ADMIN_USERS:
            keyboard.append([InlineKeyboardButton("👑 Ir a Admin", callback_data="go_to_admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_poster = user_posters[str(user_id)]["name"]
        await update.message.reply_text(
            f"👋 Hola de nuevo, <b>{current_poster}</b>!\n\n"
            f"¿Qué deseas hacer?",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "🎬 <b>Please type your poster name:</b>\n\n"
            "Ejemplos: <code>CamilaG</code>, <code>DianneR</code>, <code>GFR</code>\n\n"
            "If you appear in multiple countries, you'll be asked to choose one.",
            parse_mode="HTML"
        )
        context.user_data["waiting_for_poster"] = True

async def handle_poster_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    poster_name = update.message.text.strip()
    
    countries = get_poster_countries(poster_name)
    
    if not countries:
        await update.message.reply_text(
            f"❌ Poster '{poster_name}' not found.\n\n"
            f"Please check the name and try again.\n"
            f"Use <code>/menu</code> to try again.\n\n"
            f"📋 Available posters: CamilaG, Giselle, Anna, Maya, Ismerda, Javiera, Oluwatoyosi, Truong, Sarah, Victor, DianneR, Alberto, Laura, Sara, Thuany, Valentina, GFR",
            parse_mode="HTML"
        )
        return
    
    if len(countries) == 1:
        country = countries[0]
        user_posters[str(user_id)] = {
            "name": country["poster_name"],
            "poster_key": country["poster_key"],
            "country_key": country["country_key"],
            "country_name": country["country_name"]
        }
        save_users_data()
        await show_accounts_menu(update, context, country["country_key"], country["poster_key"])
    else:
        context.user_data["pending_poster"] = {"name": poster_name, "countries": countries}
        
        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(country["country_name"], callback_data=f"select_country_{country['country_key']}_{country['poster_key']}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🌍 <b>Poster '{poster_name}' found in multiple countries.</b>\n\n"
            f"Please select which country you want reels from:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def show_accounts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str):
    poster_data = reels_data.get(country_key, {}).get("posters", {}).get(poster_key, {})
    accounts = poster_data.get("accounts", [])
    
    keyboard = []
    for account in accounts:
        _, disponibili, _ = get_stato_account(account)
        status_icon = "🟢" if disponibili > 0 else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status_icon} {account}", callback_data=f"get_reel_{account}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"🎬 <b>Select an account for {poster_data['name']} in {reels_data[country_key]['name']}:</b>\n\n"
            f"🟢 = Reels available | 🔴 = No reels available\n\n"
            f"Use /menu to go back to the main menu.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"🎬 <b>Select an account for {poster_data['name']} in {reels_data[country_key]['name']}:</b>\n\n"
            f"🟢 = Reels available | 🔴 = No reels available\n\n"
            f"Use /menu to go back to the main menu.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def send_reel_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, account: str):
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    await query.answer()
    
    if account not in reels_files:
        await query.edit_message_text(f"❌ No reels available for account @{account}.")
        return
    
    used, available, total = get_stato_account(account)
    
    if available <= THRESHOLD_REELS and available > 0:
        await notificare_admin(
            context,
            f"⚠️ <b>LOW REELS WARNING!</b>\n"
            f"🎬 Account: @{account}\n"
            f"📸 Reels available: {available}\n"
            f"📌 Upload more reels!",
            is_admin_action=True
        )
    
    if available == 0:
        await query.edit_message_text(f"❌ No reels available for account @{account}. All reels have been used!")
        return
    
    reel_id = ottenere_reel_disponibile_per_account(account)
    if not reel_id:
        await query.edit_message_text(f"❌ No reels available for account @{account}. Please try again later.")
        return
    
    metadata = reels_files[account]["metadata"].get(str(reel_id), {})
    reel_path = metadata.get("path")
    
    if reel_path and os.path.exists(reel_path):
        try:
            await query.edit_message_text(f"🎬 Sending reel from @{account}...")
            with open(reel_path, 'rb') as f:
                await context.bot.send_video(chat_id=user_id, video=f, caption=f"🎬 Reel from @{account}")
            
            marcare_reel_come_usato(account, reel_id)
            await notificare_admin(context, f"🎬 @{username} received a reel from @{account}")
            
            _, remaining, _ = get_stato_account(account)
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ <b>Reel sent!</b>\n\n📨 Sent: 1 reel from @{account}\n📊 Remaining for this account: {remaining}\n\nUse <code>/menu</code> to get another reel.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error sending reel for {account}: {e}")
            await context.bot.send_message(chat_id=user_id, text="❌ Error sending the reel. Please try again.")
    else:
        await query.edit_message_text("❌ Reel file not found. Please try again.")

# ======================
# ADMIN MENU PRINCIPAL
# ======================

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_USERS:
        await update.message.reply_text("❌ Only admins can use this command.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🎬 Upload Reels", callback_data="admin_upload")],
        [InlineKeyboardButton("➕ Add New Poster", callback_data="admin_add_poster")],
        [InlineKeyboardButton("➕ Add New Account", callback_data="admin_add_account")],
        [InlineKeyboardButton("🌍 Add New Country", callback_data="admin_add_country")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="admin_delete_account_start")],
        [InlineKeyboardButton("🗑️ Delete Poster", callback_data="admin_delete_poster_start")],
        [InlineKeyboardButton("📊 Account Status", callback_data="admin_status")],
        [InlineKeyboardButton("🔄 Reset Account", callback_data="admin_reset")],
        [InlineKeyboardButton("🎬 Recibir reels (como usuario)", callback_data="use_as_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "👑 <b>Admin Menu</b>\n\nSelect an option:",
            reply_markup=reply_markup, 
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "👑 <b>Admin Menu</b>\n\nSelect an option:",
            reply_markup=reply_markup, 
            parse_mode="HTML"
        )

# ======================
# ADMIN - UPLOAD REELS
# ======================

async def admin_upload_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(country_data["name"], callback_data=f"upload_country_{country_key}")] 
                for country_key, country_data in reels_data.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🌍 <b>Select country to upload reels:</b>", reply_markup=reply_markup, parse_mode="HTML")

async def admin_upload_poster_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str):
    query = update.callback_query
    await query.answer()
    
    posters = reels_data.get(country_key, {}).get("posters", {})
    keyboard = [[InlineKeyboardButton(poster_data["name"], callback_data=f"upload_poster_{country_key}_{poster_key}")] 
                for poster_key, poster_data in posters.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="admin_upload")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📸 <b>Select poster for {reels_data[country_key]['name']}:</b>", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_upload_account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str):
    query = update.callback_query
    await query.answer()
    
    accounts = reels_data.get(country_key, {}).get("posters", {}).get(poster_key, {}).get("accounts", [])
    keyboard = [[InlineKeyboardButton(account, callback_data=f"upload_account_{country_key}_{poster_key}_{account}")] for account in accounts]
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data=f"upload_back_{country_key}_{poster_key}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🎬 <b>Select account for {reels_data[country_key]['posters'][poster_key]['name']}:</b>", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE, account: str):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    waiting_for_reel_upload[user_id] = {"account": account, "files": []}
    await query.edit_message_text(f"🎬 <b>Uploading reels for @{account}</b>\n\nSend video files (.mp4, .mov) one or more at a time.\nWhen done, type <code>/done</code>\n\n⏳ Files received so far: 0", parse_mode="HTML")

# ======================
# ADMIN - DELETE ACCOUNT (CON PAÍSES Y POSTERS)
# ======================

async def admin_delete_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 1: Seleccionar país para eliminar cuenta"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(country_data["name"], callback_data=f"del_acc_country_{country_key}")] 
                for country_key, country_data in reels_data.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🌍 <b>Delete Account - Select Country:</b>\n\nChoose the country of the account you want to delete:", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_account_poster(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str):
    """Paso 2: Seleccionar poster para eliminar cuenta"""
    query = update.callback_query
    await query.answer()
    
    posters = reels_data.get(country_key, {}).get("posters", {})
    keyboard = [[InlineKeyboardButton(poster_data["name"], callback_data=f"del_acc_poster_{country_key}_{poster_key}")] 
                for poster_key, poster_data in posters.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="admin_delete_account_start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📸 <b>Delete Account - Select Poster in {reels_data[country_key]['name']}:</b>\n\nChoose the poster:", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_account_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str):
    """Paso 3: Seleccionar cuenta específica para eliminar"""
    query = update.callback_query
    await query.answer()
    
    accounts = reels_data.get(country_key, {}).get("posters", {}).get(poster_key, {}).get("accounts", [])
    keyboard = []
    for account in accounts:
        used, available, total = get_stato_account(account)
        keyboard.append([InlineKeyboardButton(f"{account} ({used}/{total} used)", callback_data=f"del_acc_confirm_{country_key}_{poster_key}_{account}")])
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data=f"del_acc_back_poster_{country_key}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🗑️ <b>Delete Account - Select Account</b>\n\nCountry: {reels_data[country_key]['name']}\nPoster: {reels_data[country_key]['posters'][poster_key]['name']}\n\nSelect the account to delete:", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_account_execute(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str, account: str):
    """Paso 4: Confirmar y eliminar la cuenta"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✅ YES, Delete", callback_data=f"del_acc_final_{country_key}_{poster_key}_{account}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_delete_account_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"⚠️ <b>Confirm Delete Account</b>\n\nAccount: @{account}\nCountry: {reels_data[country_key]['name']}\nPoster: {reels_data[country_key]['posters'][poster_key]['name']}\n\n<b>All reels for this account will be deleted!</b>\n\nAre you sure?", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_account_final(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str, account: str):
    """Ejecutar eliminación de la cuenta"""
    query = update.callback_query
    await query.answer()
    
    if delete_account(country_key, poster_key, account):
        await query.edit_message_text(f"✅ <b>Account @{account} has been deleted!</b>\n\nAll reels and data for this account have been removed.", parse_mode="HTML")
        await notificare_admin(context, f"🗑️ Admin deleted account @{account}", is_admin_action=True)
    else:
        await query.edit_message_text(f"❌ Error deleting account @{account}.", parse_mode="HTML")

# ======================
# ADMIN - DELETE POSTER
# ======================

async def admin_delete_poster_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 1: Seleccionar país para eliminar poster"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(country_data["name"], callback_data=f"del_post_country_{country_key}")] 
                for country_key, country_data in reels_data.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🌍 <b>Delete Poster - Select Country:</b>\n\nChoose the country of the poster you want to delete:", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_poster_select(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str):
    """Paso 2: Seleccionar poster para eliminar"""
    query = update.callback_query
    await query.answer()
    
    posters = reels_data.get(country_key, {}).get("posters", {})
    keyboard = []
    for poster_key, poster_data in posters.items():
        accounts_count = len(poster_data["accounts"])
        keyboard.append([InlineKeyboardButton(f"{poster_data['name']} ({accounts_count} accounts)", callback_data=f"del_post_confirm_{country_key}_{poster_key}")])
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="admin_delete_poster_start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🗑️ <b>Delete Poster - Select Poster in {reels_data[country_key]['name']}:</b>\n\n⚠️ Warning: This will delete ALL accounts under this poster!", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_poster_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str):
    """Paso 3: Confirmar eliminación del poster"""
    query = update.callback_query
    await query.answer()
    
    poster_name = reels_data[country_key]["posters"][poster_key]["name"]
    accounts_count = len(reels_data[country_key]["posters"][poster_key]["accounts"])
    
    keyboard = [
        [InlineKeyboardButton("✅ YES, Delete", callback_data=f"del_post_final_{country_key}_{poster_key}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_delete_poster_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"⚠️ <b>Confirm Delete Poster</b>\n\nPoster: {poster_name}\nCountry: {reels_data[country_key]['name']}\nAccounts: {accounts_count}\n\n<b>All accounts and reels will be deleted!</b>\n\nAre you sure?", 
                                  reply_markup=reply_markup, parse_mode="HTML")

async def admin_delete_poster_final(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str):
    """Ejecutar eliminación del poster"""
    query = update.callback_query
    await query.answer()
    
    poster_name = reels_data[country_key]["posters"][poster_key]["name"]
    if delete_poster(country_key, poster_key):
        await query.edit_message_text(f"✅ <b>Poster '{poster_name}' has been deleted!</b>\n\nAll accounts and reels for this poster have been removed.", parse_mode="HTML")
        await notificare_admin(context, f"🗑️ Admin deleted poster '{poster_name}'", is_admin_action=True)
    else:
        await query.edit_message_text(f"❌ Error deleting poster '{poster_name}'.", parse_mode="HTML")

# ======================
# ADMIN - OTRAS FUNCIONES
# ======================

async def admin_add_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(country_data["name"], callback_data=f"add_poster_country_{country_key}")] 
                for country_key, country_data in reels_data.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("➕ <b>Add New Poster</b>\n\nSelect the country for the new poster:", reply_markup=reply_markup, parse_mode="HTML")

async def admin_add_poster_country(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    waiting_for_poster_input[user_id] = {"country": country_key, "step": "name"}
    await query.edit_message_text(f"➕ <b>Add New Poster to {reels_data[country_key]['name']}</b>\n\nPlease type the name of the new poster.\n\nAfter that, you will be asked to add accounts.", parse_mode="HTML")

async def admin_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(country_data["name"], callback_data=f"add_account_country_{country_key}")] 
                for country_key, country_data in reels_data.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("➕ <b>Add New Account</b>\n\nSelect the country:", reply_markup=reply_markup, parse_mode="HTML")

async def admin_add_account_poster(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str):
    query = update.callback_query
    await query.answer()
    
    posters = reels_data.get(country_key, {}).get("posters", {})
    keyboard = [[InlineKeyboardButton(poster_data["name"], callback_data=f"add_account_poster_{country_key}_{poster_key}")] 
                for poster_key, poster_data in posters.items()]
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="admin_add_account")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"➕ <b>Add New Account to {reels_data[country_key]['name']}</b>\n\nSelect the poster:", reply_markup=reply_markup, parse_mode="HTML")

async def admin_add_account_input(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, poster_key: str):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    waiting_for_account_input[user_id] = {"country": country_key, "poster": poster_key}
    await query.edit_message_text(f"➕ <b>Add New Account</b>\n\nCountry: {reels_data[country_key]['name']}\nPoster: {reels_data[country_key]['posters'][poster_key]['name']}\n\nPlease type the Instagram account name:", parse_mode="HTML")

async def admin_add_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    waiting_for_country_input[user_id] = True
    await query.edit_message_text("🌍 <b>Add New Country</b>\n\nPlease type the country name with emoji.\nExample: <code>🇫🇷 France</code>\n\nThe country key will be generated automatically.", parse_mode="HTML")

async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    status_text = "<b>📊 Account Status:</b>\n\n"
    for country_key, country_data in reels_data.items():
        status_text += f"\n<b>{country_data['name']}</b>\n"
        for poster_key, poster_data in country_data["posters"].items():
            status_text += f"  📸 <b>{poster_data['name']}</b>\n"
            for account in poster_data["accounts"]:
                used, available, total = get_stato_account(account)
                status_text += f"    • @{account}: {used}/{total} used, {available} available\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(status_text) > 4000:
        status_text = status_text[:4000] + "\n\n... (truncated)"
    
    await query.edit_message_text(status_text, reply_markup=reply_markup, parse_mode="HTML")

async def admin_reset_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for country_key, country_data in reels_data.items():
        for poster_key, poster_data in country_data["posters"].items():
            for account in poster_data["accounts"]:
                used, available, total = get_stato_account(account)
                keyboard.append([InlineKeyboardButton(f"{account} ({used}/{total} used)", callback_data=f"admin_reset_account_{account}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🔄 <b>Reset Account Reels</b>\n\nSelect an account to reset all its reels:\n⚠️ <b>WARNING:</b> This will delete all reels and free up space.", reply_markup=reply_markup, parse_mode="HTML")

async def admin_reset_account(update: Update, context: ContextTypes.DEFAULT_TYPE, account: str):
    query = update.callback_query
    await query.answer()
    
    if account not in reels_files:
        await query.edit_message_text(f"❌ Account @{account} not found.")
        return
    
    used, available, total = get_stato_account(account)
    keyboard = [
        [InlineKeyboardButton("✅ YES, Reset", callback_data=f"admin_confirm_reset_{account}")],
        [InlineKeyboardButton("❌ NO, Cancel", callback_data="admin_reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"⚠️ <b>Confirm Reset for @{account}</b>\n\nCurrent status:\n• Total reels: {total}\n• Used: {used}\n• Available: {available}\n\n<b>All reels will be permanently deleted!</b>\n\nAre you sure?", reply_markup=reply_markup, parse_mode="HTML")

async def admin_confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE, account: str):
    query = update.callback_query
    await query.answer()
    reset_reels_per_account(account)
    await query.edit_message_text(f"✅ <b>Account @{account} has been reset!</b>\n\nAll reels have been deleted.\nYou can now upload new reels.", parse_mode="HTML")

# ======================
# HANDLER DE TEXTO PARA ADMIN
# ======================

async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_USERS:
        return
    
    text = update.message.text.strip()
    
    if user_id in waiting_for_country_input:
        country_name = text
        country_key = re.sub(r'[^\w\s]', '', country_name).lower().strip().replace(" ", "_")
        
        if country_key in reels_data:
            await update.message.reply_text(f"❌ Country '{country_name}' already exists (key: {country_key}).")
        else:
            aggiungere_nuovo_paese(country_key, country_name)
            await update.message.reply_text(f"✅ <b>New country added successfully!</b>\n\n🌍 Country: {country_name}\n🔑 Key: {country_key}\n\nNow you can add posters and accounts to this country using the Admin Menu.", parse_mode="HTML")
        
        del waiting_for_country_input[user_id]
        return
    
    if user_id in waiting_for_account_input:
        account_name = text
        country_key = waiting_for_account_input[user_id]["country"]
        poster_key = waiting_for_account_input[user_id]["poster"]
        
        if account_name in reels_data[country_key]["posters"][poster_key]["accounts"]:
            await update.message.reply_text(f"❌ Account '{account_name}' already exists in this poster.")
        else:
            aggiungere_nuova_account(country_key, poster_key, account_name)
            await update.message.reply_text(f"✅ <b>New account added successfully!</b>\n\n🌍 Country: {reels_data[country_key]['name']}\n👤 Poster: {reels_data[country_key]['posters'][poster_key]['name']}\n📱 New account: {account_name}\n\nNow you can upload reels for this account using the Admin Menu.", parse_mode="HTML")
        
        del waiting_for_account_input[user_id]
        return
    
    if user_id in waiting_for_poster_input and waiting_for_poster_input[user_id]["step"] == "name":
        poster_name = text
        country_key = waiting_for_poster_input[user_id]["country"]
        poster_key = poster_name.lower().replace(" ", "_")
        
        if poster_key in reels_data[country_key]["posters"]:
            await update.message.reply_text(f"❌ Poster '{poster_name}' already exists in {reels_data[country_key]['name']}.")
            del waiting_for_poster_input[user_id]
            return
        
        waiting_for_poster_input[user_id]["poster_key"] = poster_key
        waiting_for_poster_input[user_id]["poster_name"] = poster_name
        waiting_for_poster_input[user_id]["step"] = "accounts"
        
        await update.message.reply_text(f"✅ Poster '{poster_name}' will be added to {reels_data[country_key]['name']}.\n\nNow please type the Instagram accounts for this poster.\nSeparate multiple accounts with commas.\nExample: <code>account1, account2, account3</code>", parse_mode="HTML")
        return
    
    if user_id in waiting_for_poster_input and waiting_for_poster_input[user_id]["step"] == "accounts":
        accounts_text = text
        accounts = [acc.strip() for acc in accounts_text.split(",") if acc.strip()]
        
        if not accounts:
            await update.message.reply_text("❌ Please type at least one account.")
            return
        
        country_key = waiting_for_poster_input[user_id]["country"]
        poster_key = waiting_for_poster_input[user_id]["poster_key"]
        poster_name = waiting_for_poster_input[user_id]["poster_name"]
        
        aggiungere_nuovo_poster(country_key, poster_key, poster_name, accounts)
        del waiting_for_poster_input[user_id]
        
        await update.message.reply_text(f"✅ <b>New poster added successfully!</b>\n\n🌍 Country: {reels_data[country_key]['name']}\n👤 Poster: {poster_name}\n📱 Accounts: {', '.join(accounts)}\n\nNow you can upload reels for these accounts using the Admin Menu.", parse_mode="HTML")
        return

# ======================
# RECEIVE REEL UPLOAD
# ======================

async def receive_reel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_USERS or user_id not in waiting_for_reel_upload:
        return
    
    account = waiting_for_reel_upload[user_id]["account"]
    temp_path = None
    
    if update.message.video:
        video = update.message.video
        file = await context.bot.get_file(video.file_id)
        ext = ".mp4" if not video.file_name else os.path.splitext(video.file_name)[1]
        temp_path = f"reel_temp_{int(time.time())}_{random.randint(1000,9999)}{ext}"
        await file.download_to_drive(temp_path)
    
    elif update.message.document:
        doc = update.message.document
        file_ext = os.path.splitext(doc.file_name or "")[1].lower()
        if file_ext in ['.mov', '.mp4', '.avi', '.mkv']:
            file = await context.bot.get_file(doc.file_id)
            temp_path = f"reel_temp_{int(time.time())}_{random.randint(1000,9999)}{file_ext}"
            await file.download_to_drive(temp_path)
        else:
            await update.message.reply_text(f"❌ Unsupported file type: {file_ext}\nPlease send .mp4 or .mov files.")
            return
    
    if temp_path:
        waiting_for_reel_upload[user_id]["files"].append(temp_path)
        total = len(waiting_for_reel_upload[user_id]["files"])
        await update.message.reply_text(f"📦 Received 1 reel for @{account}\n📊 Total so far: {total}\n\nSend more or type <code>/done</code>", parse_mode="HTML")

async def done_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_USERS or user_id not in waiting_for_reel_upload:
        await update.message.reply_text("❌ No active upload session.")
        return
    
    account = waiting_for_reel_upload[user_id]["account"]
    files = waiting_for_reel_upload[user_id]["files"]
    total_files = len(files)
    
    if total_files == 0:
        await update.message.reply_text("❌ No files to process.")
        return
    
    status_msg = await update.message.reply_text(f"📥 Processing {total_files} reels for @{account}...")
    
    success_count = 0
    for path in files:
        try:
            aggiungere_reel_per_account(account, path)
            success_count += 1
        except Exception as e:
            logger.error(f"Error processing reel {path}: {e}")
        finally:
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass
    
    del waiting_for_reel_upload[user_id]
    used, available, total = get_stato_account(account)
    
    await status_msg.edit_text(f"✅ <b>Reels loaded successfully for @{account}!</b>\n\n🎬 Added: {success_count}/{total_files}\n📊 Total in pool: {total}\n⏳ Available: {available}\n✅ Used: {used}", parse_mode="HTML")
    await notificare_admin(context, f"🎬 You loaded {success_count} reels for @{account}", is_admin_action=True)

# ======================
# CALLBACK HANDLER
# ======================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # BACK BUTTONS - Admin menu returns
    if data == "admin_back":
        await admin_menu(update, context)
        return
    elif data == "go_to_admin":
        await admin_menu(update, context)
        return
    elif data == "use_as_user":
        await query.edit_message_text(
            "🎬 Use /menu to receive reels as a regular user.\n\n"
            "You can also type your poster name directly.",
            parse_mode="HTML"
        )
        return
    elif data == "use_current_poster":
        if str(user_id) in user_posters:
            await show_accounts_menu(
                update, context, 
                user_posters[str(user_id)]["country_key"], 
                user_posters[str(user_id)]["poster_key"]
            )
        else:
            await query.edit_message_text("❌ No poster found. Use /menu to start over.")
        return
    elif data == "change_poster":
        if str(user_id) in user_posters:
            del user_posters[str(user_id)]
            save_users_data()
        await query.edit_message_text(
            "🎬 <b>Please type your new poster name:</b>\n\n"
            "Ejemplos: <code>CamilaG</code>, <code>DianneR</code>, <code>GFR</code>",
            parse_mode="HTML"
        )
        context.user_data["waiting_for_poster"] = True
        return
    
    # Admin menu options
    elif data == "admin_upload":
        await admin_upload_menu(update, context)
        return
    elif data == "admin_add_poster":
        await admin_add_poster(update, context)
        return
    elif data == "admin_add_account":
        await admin_add_account(update, context)
        return
    elif data == "admin_add_country":
        await admin_add_country(update, context)
        return
    elif data == "admin_delete_account_start":
        await admin_delete_account_start(update, context)
        return
    elif data == "admin_delete_poster_start":
        await admin_delete_poster_start(update, context)
        return
    elif data == "admin_status":
        await admin_status(update, context)
        return
    elif data == "admin_reset":
        await admin_reset_menu(update, context)
        return
    
    # Upload reels navigation
    elif data.startswith("upload_country_"):
        country_key = data.replace("upload_country_", "")
        await admin_upload_poster_menu(update, context, country_key)
        return
    elif data.startswith("upload_poster_"):
        parts = data.split("_")
        if len(parts) >= 3:
            country_key = parts[2]
            poster_key = parts[3] if len(parts) > 3 else parts[2]
            if len(parts) > 3:
                await admin_upload_account_menu(update, context, parts[2], parts[3])
            else:
                await admin_upload_account_menu(update, context, parts[2], parts[2])
        return
    elif data.startswith("upload_account_"):
        parts = data.split("_")
        if len(parts) >= 4:
            await admin_start_upload(update, context, parts[3])
        return
    elif data.startswith("upload_back_"):
        parts = data.split("_")
        if len(parts) >= 3:
            await admin_upload_poster_menu(update, context, parts[2])
        return
    
    # Add poster
    elif data.startswith("add_poster_country_"):
        country_key = data.replace("add_poster_country_", "")
        await admin_add_poster_country(update, context, country_key)
        return
    elif data.startswith("add_account_country_"):
        country_key = data.replace("add_account_country_", "")
        await admin_add_account_poster(update, context, country_key)
        return
    elif data.startswith("add_account_poster_"):
        parts = data.split("_")
        if len(parts) >= 4:
            await admin_add_account_input(update, context, parts[3], parts[4])
        return
    
    # Delete account
    elif data.startswith("del_acc_country_"):
        country_key = data.replace("del_acc_country_", "")
        await admin_delete_account_poster(update, context, country_key)
        return
    elif data.startswith("del_acc_poster_"):
        parts = data.split("_")
        if len(parts) >= 4:
            await admin_delete_account_confirm(update, context, parts[3], parts[4])
        return
    elif data.startswith("del_acc_confirm_"):
        parts = data.split("_")
        if len(parts) >= 5:
            await admin_delete_account_execute(update, context, parts[3], parts[4], parts[5])
        return
    elif data.startswith("del_acc_final_"):
        parts = data.split("_")
        if len(parts) >= 5:
            await admin_delete_account_final(update, context, parts[3], parts[4], parts[5])
        return
    elif data.startswith("del_acc_back_poster_"):
        country_key = data.replace("del_acc_back_poster_", "")
        await admin_delete_account_poster(update, context, country_key)
        return
    
    # Delete poster
    elif data.startswith("del_post_country_"):
        country_key = data.replace("del_post_country_", "")
        await admin_delete_poster_select(update, context, country_key)
        return
    elif data.startswith("del_post_confirm_"):
        parts = data.split("_")
        if len(parts) >= 4:
            await admin_delete_poster_confirm(update, context, parts[3], parts[4])
        return
    elif data.startswith("del_post_final_"):
        parts = data.split("_")
        if len(parts) >= 4:
            await admin_delete_poster_final(update, context, parts[3], parts[4])
        return
    
    # Reset account
    elif data.startswith("admin_reset_account_"):
        account = data.replace("admin_reset_account_", "")
        await admin_reset_account(update, context, account)
        return
    elif data.startswith("admin_confirm_reset_"):
        account = data.replace("admin_confirm_reset_", "")
        await admin_confirm_reset(update, context, account)
        return
    
    # Selección de país para poster con múltiples países
    elif data.startswith("select_country_"):
        parts = data.split("_")
        if len(parts) >= 4:
            country_key = parts[2]
            poster_key = parts[3]
            pending = context.user_data.get("pending_poster", {})
            poster_name = pending.get("name", "")
            
            user_posters[str(user_id)] = {
                "name": poster_name,
                "poster_key": poster_key,
                "country_key": country_key,
                "country_name": reels_data[country_key]["name"]
            }
            save_users_data()
            
            if "pending_poster" in context.user_data:
                del context.user_data["pending_poster"]
            
            await show_accounts_menu(update, context, country_key, poster_key)
        return
    
    # Menú de usuario - obtener reel
    elif data.startswith("get_reel_"):
        account = data.replace("get_reel_", "")
        await send_reel_to_user(update, context, account)
        return

# ======================
# MAIN
# ======================

def main():
    init_folders()
    load_data()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CommandHandler("done", done_upload))
    
    application.add_handler(MessageHandler(filters.VIDEO & filters.User(ADMIN_USERS), receive_reel_upload))
    application.add_handler(MessageHandler(filters.Document.VIDEO & filters.User(ADMIN_USERS), receive_reel_upload))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_USERS), handle_admin_text))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_USERS), handle_poster_name))
    
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    print("✅ Bot iniciado. Presiona Ctrl+C para detener.")
    print(f"👑 Admins: {', '.join(ADMIN_USERNAMES.values())}")
    application.run_polling()

if __name__ == "__main__":
    main()