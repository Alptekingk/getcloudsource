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

# Offset oku
offset = 0
if os.path.exists(offset_file):
    try:
        offset = int(open(offset_file).read().strip())
    except:
        offset = 0

# Guncelleme al
r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"offset": offset, "timeout": 5}
)
updates = r.json().get("result", [])

if not updates:
    print("Mesaj yok")
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
    clean = text.lstrip("/")
    parts = clean.split("_", 1)
    cmd = parts[0].lower()
    filename = parts[1] if len(parts) > 1 else ""

    if cmd == "onayla" and filename:
        src = f"blog/taslaklar/{filename}.md"
        dst = f"blog/yayinlandi/{filename}.md"
        if os.path.exists(src):
            os.makedirs("blog/yayinlandi", exist_ok=True)
            content = open(src).read().replace("status: taslak", "status: yayinda")
            open(dst, "w").write(content)
            os.remove(src)
            git_commit(f"Yayinlandi: {filename}")
            send(f"Yayinlandi!\n{filename}\n\nVercel deploy basliyor.")
        else:
            send(f"Dosya bulunamadi: {src}\n\nMevcut taslaklar icin /liste yazin.")

    elif cmd == "reddet" and filename:
        src = f"blog/taslaklar/{filename}.md"
        if os.path.exists(src):
            os.makedirs("blog/reddedildi", exist_ok=True)
            os.rename(src, f"blog/reddedildi/{filename}.md")
            git_commit(f"Reddedildi: {filename}")
            send(f"Reddedildi. {filename} arsive tasindi.")
        else:
            send(f"Dosya bulunamadi: {src}")

    elif cmd == "liste":
        files = glob.glob("blog/taslaklar/*.md")
        if files:
            msg_text = "Bekleyen taslaklar:\n\n"
            for f in sorted(files):
                name = os.path.basename(f).replace(".md", "")
                msg_text += f"{name}\n"
            msg_text += "\nOnaylamak: /onayla_DOSYAADI\nReddetmek: /reddet_DOSYAADI"
        else:
            msg_text = "Bekleyen taslak yok."
        send(msg_text)

    elif cmd == "start":
        send(
            "CloudSource Blog Bot\n\n"
            "/liste - Bekleyen yazilari goster\n"
            "/onayla_DOSYAADI - Yayinla\n"
            "/reddet_DOSYAADI - Reddet"
        )
    else:
        send(
            "Komutlar:\n"
            "/liste - Bekleyen yazilari goster\n"
            "/onayla_DOSYAADI - Yayinla\n"
            "/reddet_DOSYAADI - Reddet"
        )

# Offset kaydet
open(offset_file, "w").write(str(last_id + 1))
git_commit("Offset guncellendi")
print("Tamamlandi")
