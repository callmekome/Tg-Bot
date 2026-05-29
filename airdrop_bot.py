import os
import requests
import sqlite3
import logging
import time
from datetime import datetime

# ================= SETTINGS =================

BOT_NAME = "USDT NEW UPDATE"

BOT_TOKEN = os.getenv("BOT_TOKEN")

BOT_USERNAME = "Testing13333bot"

ADMIN_ID = 8862894177

REQUIRED_CHANNELS = [
    "@usdtupdate144",
    "@discussionnewupdate",
    "@AYOBOLAJI1"
]

GROUP_LINK = "https://t.me/discussionnewupdate"

JOINING_BONUS = 10.0
REFERRAL_BONUS = 10.0
MIN_WITHDRAWAL = 40.0

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= LOGGING =================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

log = logging.getLogger(__name__)

# ================= API =================

def api(method, **p):

    try:

        r = requests.post(
            BASE + "/" + method,
            json=p,
            timeout=20
        )

        return r.json()

    except Exception as e:

        log.error(str(e))

        return {}

def send(cid, text, rm=None):

    p = {
        "chat_id": cid,
        "text": text,
        "parse_mode": "Markdown"
    }

    if rm:
        p["reply_markup"] = rm

    return api("sendMessage", **p)

def edit(cid, mid, text, rm=None):

    p = {
        "chat_id": cid,
        "message_id": mid,
        "text": text,
        "parse_mode": "Markdown"
    }

    if rm:
        p["reply_markup"] = rm

    return api("editMessageText", **p)

# ================= KEYBOARDS =================

def main_kb():

    return {
        "keyboard": [
            [{"text": "💳 Balance"}, {"text": "👥 Referral"}],
            [{"text": "📤 Withdraw"}],
            [{"text": "📢 Updates"}, {"text": "👨‍👩‍👧 Community"}]
        ],
        "resize_keyboard": True
    }

def join_kb():

    buttons = []

    for c in REQUIRED_CHANNELS:

        buttons.append([
            {
                "text": f"🚀 Join {c}",
                "url": "https://t.me/" + c.lstrip("@")
            }
        ])

    buttons.append([
        {
            "text": "✅ I've Joined",
            "callback_data": "check_join"
        }
    ])

    return {"inline_keyboard": buttons}

# ================= DATABASE =================

DB = "airdrop.db"

def db():

    c = sqlite3.connect(DB)

    c.row_factory = sqlite3.Row

    return c

def init():

    c = db()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        balance REAL DEFAULT 0,
        referred_by INTEGER,
        joined_at TEXT,
        wallet TEXT,
        joined_bonus INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS withdrawals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        wallet TEXT,
        status TEXT DEFAULT 'pending',
        requested_at TEXT
    );

    CREATE TABLE IF NOT EXISTS state(
        user_id INTEGER PRIMARY KEY,
        step TEXT
    );
    """)

    c.commit()

    c.close()

def getu(uid):

    c = db()

    r = c.execute(
        "SELECT * FROM users WHERE user_id=?",
        (uid,)
    ).fetchone()

    c.close()

    return r

def mkuser(uid, un, fn, ref=None):

    c = db()

    c.execute(
        """
        INSERT OR IGNORE INTO users(
            user_id,
            username,
            full_name,
            referred_by,
            joined_at
        ) VALUES(?,?,?,?,?)
        """,
        (
            uid,
            un or "",
            fn,
            ref,
            datetime.now().isoformat()
        )
    )

    c.commit()

    c.close()

def addb(uid, amt):

    c = db()

    c.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amt, uid)
    )

    c.commit()

    c.close()

def removeb(uid, amt):

    c = db()

    c.execute(
        "UPDATE users SET balance=balance-? WHERE user_id=?",
        (amt, uid)
    )

    c.commit()

    c.close()

def markb(uid):

    c = db()

    c.execute(
        "UPDATE users SET joined_bonus=1 WHERE user_id=?",
        (uid,)
    )

    c.commit()

    c.close()

def refcount(uid):

    c = db()

    r = c.execute(
        "SELECT COUNT(*) as n FROM users WHERE referred_by=?",
        (uid,)
    ).fetchone()

    c.close()

    return r["n"] if r else 0

def setwallet(uid, w):

    c = db()

    c.execute(
        "UPDATE users SET wallet=? WHERE user_id=?",
        (w, uid)
    )

    c.commit()

    c.close()

def savewith(uid, amt, w):

    c = db()

    c.execute(
        """
        INSERT INTO withdrawals(
            user_id,
            amount,
            wallet,
            requested_at
        ) VALUES(?,?,?,?)
        """,
        (
            uid,
            amt,
            w,
            datetime.now().isoformat()
        )
    )

    c.execute(
        "UPDATE users SET balance=balance-? WHERE user_id=?",
        (amt, uid)
    )

    c.commit()

    c.close()

def setst(uid, s):

    c = db()

    c.execute(
        """
        INSERT OR REPLACE INTO state(
            user_id,
            step
        ) VALUES(?,?)
        """,
        (uid, s)
    )

    c.commit()

    c.close()

def getst(uid):

    c = db()

    r = c.execute(
        "SELECT step FROM state WHERE user_id=?",
        (uid,)
    ).fetchone()

    c.close()

    return r["step"] if r else None

def clrst(uid):

    c = db()

    c.execute(
        "DELETE FROM state WHERE user_id=?",
        (uid,)
    )

    c.commit()

    c.close()

# ================= MEMBERSHIP =================

def check_mem(uid):

    out = []

    for c in REQUIRED_CHANNELS:

        try:

            s = api(
                "getChatMember",
                chat_id=c,
                user_id=uid
            ).get("result", {}).get("status", "left")

            if s in ("left", "kicked", "banned"):
                out.append(c)

        except:
            out.append(c)

    return out

pref = {}

# ================= START =================

def do_start(cid, uid, fn, un, arg):

    welcome = (
        "🚀 *WELCOME TO USDT NEW UPDATE* 🚀\n\n"
        "💎 Premium USDT Reward Bot\n"
        "🔥 Earn Free USDT Daily\n"
        "👥 Invite Friends & Earn More\n"
        "⚡ Instant Reward System\n"
        "🔒 Trusted Crypto Community\n\n"
        f"🎁 Welcome Bonus: *{JOINING_BONUS} USDT*\n"
        f"👥 Referral Reward: *{REFERRAL_BONUS} USDT*\n"
        f"💸 Minimum Withdrawal: *{MIN_WITHDRAWAL} USDT*\n\n"
        "📢 Join all required channels below."
    )

    nj = check_mem(uid)

    if nj:

        if arg:
            pref[uid] = arg

        send(
            cid,
            welcome,
            join_kb()
        )

        return

    do_reg(cid, uid, fn, un, arg)

# ================= REGISTER =================

def do_reg(cid, uid, fn, un, arg=None):

    old_user = getu(uid)

    if old_user:
        return

    ref = None

    ra = arg or pref.pop(uid, None)

    if ra:

        try:

            r = int(ra)

            if r != uid:
                ref = r

        except:
            pass

    mkuser(uid, un, fn, ref)

    addb(uid, JOINING_BONUS)

    markb(uid)

    if ref:

        ru = getu(ref)

        if ru:

            addb(ref, REFERRAL_BONUS)

            send(
                ref,
                f"🎉 *New Referral Joined*\n\n"
                f"👤 {fn} joined using your link.\n"
                f"💰 Bonus Earned: *{REFERRAL_BONUS} USDT*"
            )

    send(
        cid,
        f"✅ *Account Activated Successfully*\n\n"
        f"🎁 Bonus Added: *{JOINING_BONUS} USDT*\n\n"
        f"Use the menu below to continue.",
        main_kb()
    )

# ================= BALANCE =================

def do_bal(cid, uid, fn):

    u = getu(uid)

    if not u:
        return

    send(
        cid,
        f"💳 *ACCOUNT BALANCE*\n\n"
        f"👤 User: *{fn}*\n"
        f"💰 Balance: *{round(u['balance'],2)} USDT*\n"
        f"👥 Referrals: *{refcount(uid)}*",
        main_kb()
    )

# ================= REFERRAL =================

def do_ref(cid, uid):

    n = refcount(uid)

    link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    send(
        cid,
        f"👥 *REFERRAL PROGRAM*\n\n"
        f"🔗 Your Referral Link:\n`{link}`\n\n"
        f"👨‍👩‍👧 Total Referrals: *{n}*\n"
        f"💰 Total Earned: *{round(n * REFERRAL_BONUS,2)} USDT*",
        main_kb()
    )

# ================= WITHDRAW =================

def do_with(cid, uid):

    u = getu(uid)

    if not u:
        return

    b = u["balance"]

    if b < MIN_WITHDRAWAL:

        send(
            cid,
            f"❌ Minimum withdrawal is *{MIN_WITHDRAWAL} USDT*\n\n"
            f"💰 Your Balance: *{round(b,2)} USDT*",
            main_kb()
        )

        return

    setst(uid, "wallet")

    send(
        cid,
        f"📤 *Withdrawal Request*\n\n"
        f"💰 Amount: *{round(b,2)} USDT*\n\n"
        f"Send your wallet address."
    )

def do_wallet(cid, uid, w):

    if len(w) < 20:

        send(cid, "❌ Invalid wallet address.")

        return

    u = getu(uid)

    amt = u["balance"]

    setwallet(uid, w)

    savewith(uid, amt, w)

    clrst(uid)

    send(
        ADMIN_ID,
        f"🚨 *New Withdrawal Request*\n\n"
        f"👤 User ID: `{uid}`\n"
        f"💰 Amount: *{amt} USDT*\n"
        f"💳 Wallet:\n`{w}`"
    )

    send(
        cid,
        f"✅ *Withdrawal Submitted Successfully*\n\n"
        f"💰 Amount: *{round(amt,2)} USDT*\n"
        f"⏳ Processing Time: 24 Hours",
        main_kb()
    )

# ================= MAIN =================

def main():

    if not BOT_TOKEN:

        print("BOT_TOKEN missing")

        return

    init()

    log.info("Bot started!")

    offset = None

    while True:

        try:

            res = api(
                "getUpdates",
                timeout=30,
                offset=offset,
                allowed_updates=["message", "callback_query"]
            )

            for u in res.get("result", []):

                offset = u["update_id"] + 1

                if "callback_query" in u:

                    cq = u["callback_query"]

                    uid = cq["from"]["id"]

                    cid = cq["message"]["chat"]["id"]

                    mid = cq["message"]["message_id"]

                    fn = (
                        cq["from"].get("first_name", "") +
                        (" " + cq["from"].get("last_name", ""))
                    ).strip()

                    un = cq["from"].get("username", "")

                    api(
                        "answerCallbackQuery",
                        callback_query_id=cq["id"]
                    )

                    if cq.get("data") == "check_join":

                        nj = check_mem(uid)

                        if nj:

                            edit(
                                cid,
                                mid,
                                "❌ You must join all required channels first.",
                                join_kb()
                            )

                        else:

                            edit(
                                cid,
                                mid,
                                "✅ Verification successful..."
                            )

                            do_reg(cid, uid, fn, un)

                    continue

                if "message" not in u:
                    continue

                if "text" not in u["message"]:
                    continue

                m = u["message"]

                txt = m["text"]

                cid = m["chat"]["id"]

                uid = m["from"]["id"]

                fn = (
                    m["from"].get("first_name", "") +
                    (" " + m["from"].get("last_name", ""))
                ).strip()

                un = m["from"].get("username", "")

                st = getst(uid)

                if st == "wallet" and not txt.startswith("/"):

                    do_wallet(cid, uid, txt)

                    continue

                if txt.startswith("/start"):

                    p = txt.split()

                    do_start(
                        cid,
                        uid,
                        fn,
                        un,
                        p[1] if len(p) > 1 else None
                    )

                elif txt == "💳 Balance":

                    do_bal(cid, uid, fn)

                elif txt == "👥 Referral":

                    do_ref(cid, uid)

                elif txt == "📤 Withdraw":

                    do_with(cid, uid)

                elif txt == "📢 Updates":

                    send(
                        cid,
                        "📢 Official Updates:\nhttps://t.me/usdtupdate144"
                    )

                elif txt == "👨‍👩‍👧 Community":

                    send(
                        cid,
                        "👥 Official Community:\nhttps://t.me/discussionnewupdate"
                    )

                elif txt.startswith("/addbalance"):

                    if uid != ADMIN_ID:
                        continue

                    try:

                        p = txt.split()

                        target = int(p[1])

                        amount = float(p[2])

                        addb(target, amount)

                        send(
                            cid,
                            f"✅ Added {amount} USDT to {target}"
                        )

                        send(
                            target,
                            f"🎉 Admin added {amount} USDT to your balance."
                        )

                    except:

                        send(
                            cid,
                            "Usage:\n/addbalance userid amount"
                        )

                elif txt.startswith("/removebalance"):

                    if uid != ADMIN_ID:
                        continue

                    try:

                        p = txt.split()

                        target = int(p[1])

                        amount = float(p[2])

                        removeb(target, amount)

                        send(
                            cid,
                            f"✅ Removed {amount} USDT from {target}"
                        )

                    except:

                        send(
                            cid,
                            "Usage:\n/removebalance userid amount"
                        )

        except KeyboardInterrupt:

            break

        except Exception as e:

            log.error(str(e))

            time.sleep(3)

if __name__ == "__main__":
    main()