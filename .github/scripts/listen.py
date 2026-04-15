import os, glob, requests, subprocess

token = os.environ['BOT_TOKEN']
chat_id = os.environ['CHAT_ID']
offset_file = ".github/telegram_offset.txt"

def send(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg}
    )
    print(f"Mesaj gonderildi: {r.status_code}")

def git_commit(msg):
    subprocess.run(["git", "config", "user.email", "bot@getcloudsource.com"])
    subprocess.run(["git", "config", "user.name", "CloudSource Bot"])
    subprocess.run(["git", "add", "-A"])
    r = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if r.returncode != 0:
        subprocess.run(["git", "commit", "-m", msg])
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        print(f"Push: {result.returncode} {result.stderr}")

def get_title(filepath):
    try:
        for line in open(filepath):
            if line.startswith("title:"):
                return line.replace("title:", "").strip().strip('"')
    except:
        pass
    return os.path.basename(filepath).replace(".md", "")

def load_index(folder):
    files = sorted(glob.glob(f"{folder}/*.md"))
    return {str(i+1): f for i, f in enumerate(files)}

# --- OFFSET OKU ---
offset = 0
if os.path.exists(offset_file):
    try:
        val = open(offset_file).read().strip()
        if val:
            offset = int(val)
    except:
        offset = 0
print(f"Baslangic offset: {offset}")

# --- GUNCELLEME AL ---
r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"offset": offset, "limit": 10, "timeout": 3}
)
data = r.json()
updates = data.get("result", [])
print(f"Gelen mesaj sayisi: {len(updates)}")

if not updates:
    print("Yeni mesaj yok, cikiliyor")
    exit(0)

# --- ONCE OFFSET'I KAYDET, SONRA ISLE ---
# Bu sayede tekrar islemez
last_id = updates[-1]["update_id"]
new_offset = last_id + 1
print(f"Yeni offset: {new_offset}")

os.makedirs(".github", exist_ok=True)
open(offset_file, "w").write(str(new_offset))
git_commit(f"Offset guncellendi: {new_offset}")

# --- MESAJLARI ISLE ---
for u in updates:
    msg_obj = u.get("message", {})
    text = msg_obj.get("text", "").strip()
    from_chat = str(msg_obj.get("chat", {}).get("id", ""))

    if from_chat != chat_id:
        print(f"Farkli chat: {from_chat}, atlaniyor")
        continue
    if not text.startswith("/"):
        continue

    print(f"Isleniyor: {text}")
    clean = text.lstrip("/").strip()
    parts = clean.split("_", 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "liste":
        taslaklar = load_index("blog/taslaklar")
        yayinda = load_index("blog/yayinlandi")
        msg_text = ""

        if taslaklar:
            msg_text += "BEKLEYEN TASLAKLAR:\n"
            for num, path in taslaklar.items():
                msg_text += f"{num}. {get_title(path)}\n"
            msg_text += "\n/onayla_1  /reddet_1\n\n"
        else:
            msg_text += "Bekleyen taslak yok.\n\n"

        if yayinda:
            msg_text += "YAYINDA:\n"
            for num, path in yayinda.items():
                msg_text += f"{num}. {get_title(path)}\n"
            msg_text += "\n/gericek_1"
        else:
            msg_text += "Yayinda yazi yok."

        send(msg_text)

    elif cmd == "onayla" and arg:
        taslaklar = load_index("blog/taslaklar")
        src = taslaklar.get(arg) or f"blog/taslaklar/{arg}.md"
        if os.path.exists(src):
            filename = os.path.basename(src).replace(".md", "")
            title = get_title(src)
            os.makedirs("blog/yayinlandi", exist_ok=True)
            content = open(src).read().replace("status: taslak", "status: yayinda")
            open(f"blog/yayinlandi/{filename}.md", "w").write(content)
            os.remove(src)
            git_commit(f"Yayinlandi: {filename}")
            send(f"Yayinlandi!\n{title}\n\n~30 saniye sonra canlida.")
        else:
            send("Bulunamadi. /liste ile kontrol edin.")

    elif cmd == "reddet" and arg:
        taslaklar = load_index("blog/taslaklar")
        src = taslaklar.get(arg) or f"blog/taslaklar/{arg}.md"
        if os.path.exists(src):
            filename = os.path.basename(src).replace(".md", "")
            title = get_title(src)
            os.makedirs("blog/reddedildi", exist_ok=True)
            os.rename(src, f"blog/reddedildi/{filename}.md")
            git_commit(f"Reddedildi: {filename}")
            send(f"Reddedildi.\n{title}")
        else:
            send("Bulunamadi. /liste ile kontrol edin.")

    elif cmd == "gericek" and arg:
        yayinda = load_index("blog/yayinlandi")
        src = yayinda.get(arg) or f"blog/yayinlandi/{arg}.md"
        if os.path.exists(src):
            filename = os.path.basename(src).replace(".md", "")
            title = get_title(src)
            os.makedirs("blog/taslaklar", exist_ok=True)
            content = open(src).read().replace("status: yayinda", "status: taslak")
            open(f"blog/taslaklar/{filename}.md", "w").write(content)
            os.remove(src)
            git_commit(f"Geri cekildi: {filename}")
            send(f"Geri cekildi!\n{title}\nTaslaga alindi.")
        else:
            send("Bulunamadi. /liste ile kontrol edin.")

    elif cmd == "start":
        send(
            "CloudSource Blog Bot\n\n"
            "/liste - Yazilari goster\n"
            "/onayla_1 - Yayinla\n"
            "/reddet_1 - Reddet\n"
            "/gericek_1 - Yayindan geri cek"
        )

    else:
        send(
            "/liste - Yazilari goster\n"
            "/onayla_NUMARA - Yayinla\n"
            "/reddet_NUMARA - Reddet\n"
            "/gericek_NUMARA - Geri cek"
        )

print("Tum komutlar islendi")
