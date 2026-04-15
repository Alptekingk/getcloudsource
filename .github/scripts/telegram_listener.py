import os, requests, subprocess, glob

token = os.environ['BOT_TOKEN']
chat_id = os.environ['CHAT_ID']
gh_token = os.environ['GH_TOKEN']
gh_repo = os.environ['GH_REPO']
offset_file = ".github/telegram_offset.txt"

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg}
    )

def git_push(commit_msg):
    subprocess.run(["git", "config", "user.email", "bot@getcloudsource.com"])
    subprocess.run(["git", "config", "user.name", "CloudSource Bot"])
    subprocess.run(["git", "add", "-A"])
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", commit_msg])
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
    print("Yeni mesaj yok")
    exit(0)

last_id = offset
for u in updates:
    last_id = u["update_id"]
    msg = u.get("message", {})
    text = msg.get("text", "").strip()
    from_chat = str(msg.get("chat", {}).get("id", ""))

    if from_chat != chat_id:
        continue

    print(f"Komut: {text}")

    if not text.startswith("/"):
        continue

    text_clean = text.lstrip("/")
    parts = text_clean.split("_", 1)
    cmd = parts[0]
    filename = parts[1] if len(parts) > 1 else ""

    if cmd == "onayla" and filename:
        src = f"blog/taslaklar/{filename}.md"
        dst = f"blog/yayinlandi/{filename}.md"
        if os.path.exists(src):
            os.makedirs("blog/yayinlandi", exist_ok=True)
            content = open(src).read().replace("status: taslak", "status: yayinda")
            open(dst, "w").write(content)
            os.remove(src)
            git_push(f"Yayinlandi: {filename}")
            send(f"Yayinlandi!\n\n{filename}\n\nVercel deploy basliyor, ~30 saniye sonra canlida.")
        else:
            send(f"Dosya bulunamadi: {src}")

    elif cmd == "reddet" and filename:
        src = f"blog/taslaklar/{filename}.md"
        if os.path.exists(src):
            os.makedirs("blog/reddedildi", exist_ok=True)
            dst = f"blog/reddedildi/{filename}.md"
            os.rename(src, dst)
            git_push(f"Reddedildi: {filename}")
            send(f"Reddedildi.\n{filename} arsive tasindi.")
        else:
            send(f"Dosya bulunamadi: {src}")

    elif cmd == "duzenle" and filename:
        send(f"Duzenleme modu: {filename}\nNe degistirilsin? Lutfen belirtin.")

    elif cmd == "liste":
        files = glob.glob("blog/taslaklar/*.md")
        if files:
            msg_text = "Bekleyen taslaklar:\n\n"
            for f in files:
                name = os.path.basename(f).replace(".md", "")
                msg_text += f"- {name}\n"
            msg_text += "\nOnaylamak icin: /onayla_DOSYAADI"
        else:
            msg_text = "Bekleyen taslak yok."
        send(msg_text)

    elif cmd == "start":
        send(
            "CloudSource Blog Bot aktif!\n\n"
            "Komutlar:\n"
            "/liste - Bekleyen taslaklari goster\n"
            "/onayla_DOSYAADI - Yaziyi yayinla\n"
            "/reddet_DOSYAADI - Yaziyi reddet\n"
            "/duzenle_DOSYAADI - Duzenleme iste"
        )

    else:
        send(
            "Komutlar:\n"
            "/liste - Bekleyen taslaklari goster\n"
            "/onayla_DOSYAADI - Yaziyi yayinla\n"
            "/reddet_DOSYAADI - Yaziyi reddet\n"
            "/duzenle_DOSYAADI - Duzenleme iste"
        )

# Offset kaydet
open(offset_file, "w").write(str(last_id + 1))
git_push("Telegram offset guncellendi")
print("Tamamlandi")
