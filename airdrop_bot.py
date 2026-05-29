import os
import requests
import sqlite3
import logging
import time
from datetime import datetime

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

REQUIRED_CHANNELS = [
    "@Testing13333bot",
    "https://t.me/usdtupdate144"
    "@Testing13333bot"
]

JOINING_BONUS = 10.0
REFERRAL_BONUS = 10.0
MIN_WITHDRAWAL = 25.0

BOT_USERNAME = "USDT UPDATE"

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

log = logging.getLogger(__name__)

# ================= TELEGRAM API =================

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
            [{"text": "💰 Balance"}, {"text": "👥 Referral"}],
            [{"text": "📤 Withdraw"}]
        ],
        "resize_keyboard": True
    }

def join_kb():
    buttons = []

    for c in REQUIRED_CHANNELS:
        buttons.append([
            {
                "text": "➕ Join " + c,
                "url": "https://t.me/" + c.lstrip("@")
            }
        ])

    buttons.append([
        {
            "text": "✅ I've Joined — Continue",
            "callback_data": "check_join"
        }
    ])

    return {"inline_keyboard": buttons}

# ================= MEMBERSHIP CHECK =================

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

def markb(uid):
    c = db()

    c.execute(
        "UPDATE users SET joined_bonus=1 WHERE user_id=?",
        (uid,)
    )

    c.commit()
    c.close()

def setwallet(uid, w):
    c = db()

    c.execute(
        "UPDATE users SET wallet=? WHERE user_id=?",
        (w, uid)
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

pref = {}

# ================= BOT FUNCTIONS =================

def do_start(cid, uid, fn, un, arg):
    nj = check_mem(uid)

    if nj:
        if arg:
            pref[uid] = arg

        send(
            cid,
            "👋 *USDT Airdrop Bot*\n\n"
            "⚠️ Join first:\n\n" +
            "".join("• " + c + "\n" for c in nj) +
            "\nThen tap *I've Joined*.",
            join_kb()
        )

        return

    do_reg(cid, uid, fn, un, arg)

def do_reg(cid, uid, fn, un, arg=None):
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

    u = getu(uid)

    if u and not u["joined_bonus"]:
        addb(uid, JOINING_BONUS)
        markb(uid)

        if ref:
            ru = getu(ref)

            if ru:
                addb(ref, REFERRAL_BONUS)

                send(
                    ref,
                    f"🎉 *Referral Bonus!*\n\n"
                    f"*{fn}* joined!\n"
                    f"You earned *{REFERRAL_BONUS} USDT*! 🚀"
                )

    send(
        cid,
        f"🎉 *USDT Airdrop Bot*\n\n"
        f"Welcome, *{fn}*!\n\n"
        f"🎁 Joining: {JOINING_BONUS} USDT\n"
        f"👥 Per Refer: {REFERRAL_BONUS} USDT\n"
        f"💸 Min Withdraw: {MIN_WITHDRAWAL} USDT",
        main_kb()
    )

def do_bal(cid, uid, fn):
    nj = check_mem(uid)

    if nj:
        send(cid, "⚠️ Join channels first.", join_kb())
        return

    u = getu(uid)

    if not u:
        send(cid, "Send /start first.")
        return

    send(
        cid,
        f"👑 *User:* {fn}\n\n"
        f"💰 *Balance:* {round(u['balance'], 2)} USDT",
        main_kb()
    )

def do_ref(cid, uid):
    nj = check_mem(uid)

    if nj:
        send(cid, "⚠️ Join channels first.", join_kb())
        return

    n = refcount(uid)

    link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    send(
        cid,
        f"🔥 *Airdrop Live!*\n\n"
        f"🎁 Join Bonus: {JOINING_BONUS} USDT\n"
        f"👥 Per Refer: {REFERRAL_BONUS} USDT\n\n"
        f"🔗 *Your Link:*\n`{link}`\n\n"
        f"📊 Referrals: {n}\n"
        f"💵 Earned: {round(n * REFERRAL_BONUS, 2)} USDT",
        main_kb()
    )

def do_with(cid, uid):
    nj = check_mem(uid)

    if nj:
        send(cid, "⚠️ Join channels first.", join_kb())
        return

    u = getu(uid)

    if not u:
        send(cid, "Send /start first.")
        return

    b = u["balance"]

    if b < MIN_WITHDRAWAL:
        send(
            cid,
            f"⚠️ Min withdrawal: {MIN_WITHDRAWAL} USDT\n"
            f"Your balance: {round(b, 2)} USDT",
            main_kb()
        )

        return

    setst(uid, "wallet")

    send(
        cid,
        f"📤 *Withdraw*\n\n"
        f"Balance: *{round(b, 2)} USDT*\n\n"
        f"Send your TRC20 wallet address:"
    )

def do_wallet(cid, uid, w):
    if len(w) < 20:
        send(cid, "❌ Invalid address. Try again.")
        return

    u = getu(uid)

    amt = u["balance"]

    setwallet(uid, w)

    savewith(uid, amt, w)

    clrst(uid)

    send(
        cid,
        f"✅ *Submitted!*\n\n"
        f"💰 Amount: *{round(amt, 2)} USDT*\n"
        f"📬 Wallet: `{w}`\n\n"
        f"⏳ Processing in 24-48hrs.",
        main_kb()
    )

# ================= MAIN LOOP =================

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN environment variable missing")
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

                # CALLBACKS
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
                                "❌ Still not joined:\n\n" +
                                "".join("• " + c + "\n" for c in nj) +
                                "\nTry again.",
                                join_kb()
                            )

                        else:
                            edit(cid, mid, "✅ Verified! Setting up...")
                            do_reg(cid, uid, fn, un)

                    continue

                # MESSAGES
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

                elif txt == "💰 Balance":
                    do_bal(cid, uid, fn)

                elif txt == "👥 Referral":
                    do_ref(cid, uid)

                elif txt == "📤 Withdraw":
                    do_with(cid, uid)

        except KeyboardInterrupt:
            break

        except Exception as e:
            log.error(str(e))
            time.sleep(3)

if __name__ == "__main__":
    main()