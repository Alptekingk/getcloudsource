import os, glob, requests, subprocess

token = os.environ['BOT_TOKEN']
chat_id = os.environ['CHAT_ID']
offset_file = ".github/telegram_offset.txt"

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg}
    )

def git_commit(msg):
    subprocess.run(["git", "config", "user.email", "bot@getcloudsource.com"])
    subprocess.run(["git", "config", "user.name", "CloudSource Bot"])
    subprocess.run(["git", "add", "-A"])
    r = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if r.returncode != 0:
        subprocess.run(["git", "commit", "-m", msg])
        subprocess.run(["git", "push"])

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

# Offset oku
offset = 0
if os.path.exists(offset_file):
    try:
        offset = int(open(offset_file).read().strip())
    except:
        offset = 0

r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"offset": offset, "timeout": 5}
)
updates = r.json().get("result", [])

if not updates:
    print("Mesaj yok")
    open(offset_file, "w").write(str(offset))
    exit(0)

last_id = offset
for u in updates:
    last_id = u["update_id"]
    msg_obj = u.get("message", {})
    text = msg_obj.get("text", "").strip()
    from_chat = str(msg_obj.get("chat", {}).get("id", ""))

    if from_chat != chat_id:
        continue
    if not text.startswith("/"):
        continue

    print(f"Komut: {text}")
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
                title = get_title(path)
                msg_text += f"{num}. {title}\n"
            msg_text += "\nOnayla: /onayla_1\nReddet: /reddet_1\n\n"
        else:
            msg_text += "Bekleyen taslak yok.\n\n"

        if yayinda:
            msg_text += "YAYINDA:\n"
            for num, path in yayinda.items():
                title = get_title(path)
                msg_text += f"{num}. {title}\n"
            msg_text += "\nGeri cek: /gericek_1"
        else:
            msg_text += "Yayinda yazi yok."

        send(msg_text)

    elif cmd == "onayla" and arg:
        # Numara veya dosya adi destekle
        taslaklar = load_index("blog/taslaklar")
        if arg in taslaklar:
            src = taslaklar[arg]
        else:
            src = f"blog/taslaklar/{arg}.md"

        if os.path.exists(src):
            filename = os.path.basename(src).replace(".md", "")
            title = get_title(src)
            os.makedirs("blog/yayinlandi", exist_ok=True)
            content = open(src).read().replace("status: taslak", "status: yayinda")
            open(f"blog/yayinlandi/{filename}.md", "w").write(content)
            os.remove(src)
            git_commit(f"Yayinlandi: {filename}")
            send(f"Yayinlandi!\n\n{title}\n\nVercel deploy basliyor, ~30 saniye sonra canlida.")
        else:
            send(f"Bulunamadi. Mevcut taslaklar icin /liste yazin.")

    elif cmd == "reddet" and arg:
        taslaklar = load_index("blog/taslaklar")
        if arg in taslaklar:
            src = taslaklar[arg]
        else:
            src = f"blog/taslaklar/{arg}.md"

        if os.path.exists(src):
            filename = os.path.basename(src).replace(".md", "")
            title = get_title(src)
            os.makedirs("blog/reddedildi", exist_ok=True)
            os.rename(src, f"blog/reddedildi/{filename}.md")
            git_commit(f"Reddedildi: {filename}")
            send(f"Reddedildi.\n\n{title}\nArsive tasindi.")
        else:
            send("Bulunamadi. Mevcut taslaklar icin /liste yazin.")

    elif cmd == "gericek" and arg:
        yayinda = load_index("blog/yayinlandi")
        if arg in yayinda:
            src = yayinda[arg]
        else:
            src = f"blog/yayinlandi/{arg}.md"

        if os.path.exists(src):
            filename = os.path.basename(src).replace(".md", "")
            title = get_title(src)
            os.makedirs("blog/taslaklar", exist_ok=True)
            content = open(src).read().replace("status: yayinda", "status: taslak")
            open(f"blog/taslaklar/{filename}.md", "w").write(content)
            os.remove(src)
            git_commit(f"Geri cekildi: {filename}")
            send(f"Geri cekildi!\n\n{title}\nTaslaklar klasorune geri alindi.")
        else:
            send("Bulunamadi. Mevcut yayinlar icin /liste yazin.")

    elif cmd == "start":
        send(
            "CloudSource Blog Bot aktif!\n\n"
            "/liste - Tum yazilari goster\n"
            "/onayla_1 - 1 numarali taslagi yayinla\n"
            "/reddet_1 - 1 numarali taslagi reddet\n"
            "/gericek_1 - 1 numarali yayini geri cek"
        )

    else:
        send(
            "Komutlar:\n"
            "/liste - Tum yazilari goster\n"
            "/onayla_NUMARA - Taslagi yayinla\n"
            "/reddet_NUMARA - Taslagi reddet\n"
            "/gericek_NUMARA - Yayini geri cek"
        )

# Offset kaydet
open(offset_file, "w").write(str(last_id + 1))
git_commit("Offset guncellendi")
print("Tamamlandi")
