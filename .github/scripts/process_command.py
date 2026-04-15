import os, requests, subprocess

token = os.environ['BOT_TOKEN']
chat_id = os.environ['CHAT_ID']
cmd = os.environ.get('CMD', '')
filename = os.environ.get('FILENAME', '')

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg}
    )

def git_push(commit_msg):
    subprocess.run(["git", "config", "user.email", "bot@getcloudsource.com"])
    subprocess.run(["git", "config", "user.name", "CloudSource Bot"])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", commit_msg])
    subprocess.run(["git", "push"])

if cmd == "onayla":
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
        send(f"Dosya bulunamadi: blog/taslaklar/{filename}.md")

elif cmd == "reddet":
    src = f"blog/taslaklar/{filename}.md"
    if os.path.exists(src):
        os.makedirs("blog/reddedildi", exist_ok=True)
        dst = f"blog/reddedildi/{filename}.md"
        os.rename(src, dst)
        git_push(f"Reddedildi: {filename}")
        send(f"Reddedildi.\n{filename} arsive tasindi.")
    else:
        send(f"Dosya bulunamadi: blog/taslaklar/{filename}.md")

elif cmd == "duzenle":
    send(f"Duzenleme modu: {filename}\nNe degistirilsin?")

else:
    send(f"Bilinmeyen komut: {cmd}")
