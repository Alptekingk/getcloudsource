import os, subprocess, requests

token = os.environ['BOT_TOKEN']
chat_id = os.environ['CHAT_ID']

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg}
    )

result = subprocess.run(
    ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
    capture_output=True, text=True
)
files = [f for f in result.stdout.strip().split("\n") if "blog/taslaklar/" in f and f.endswith(".md")]

for filepath in files:
    if not os.path.exists(filepath):
        continue
    filename = os.path.basename(filepath).replace(".md", "")
    title, date, category = "", "", ""
    for line in open(filepath):
        if line.startswith("title:"):
            title = line.replace("title:", "").strip().strip('"')
        elif line.startswith("date:"):
            date = line.replace("date:", "").strip()
        elif line.startswith("category:"):
            category = line.replace("category:", "").strip()

    msg = (
        f"YENİ YAZI TASLAĞI\n\n"
        f"Baslik: {title}\n"
        f"Tarih: {date}\n"
        f"Kategori: {category}\n\n"
        f"Onaylamak: /onayla_{filename}\n"
        f"Reddetmek: /reddet_{filename}"
    )
    send(msg)
    print(f"Bildirim gonderildi: {filename}")
