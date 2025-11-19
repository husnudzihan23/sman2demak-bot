from flask import Flask, request, jsonify
import requests, json, datetime, re
import os

# ====== Konfigurasi Wablas ======
API_KEY = "jVO7uSyToHXirMbWPBKB21ASGRQS7MdaVPFps4FI0Yr7lHvSMjeSDdV"
SECRET_KEY = "8TaRCCoj"
WABLAS_URL = "https://tegal.wablas.com/api/send-message"

# ====== Load Jadwal & Alias ======
with open("jadwal.json", encoding="utf-8") as f:
    JADWAL = json.load(f)

with open("alias.json", encoding="utf-8") as f:
    ALIAS = json.load(f)

# ====== Load Data Wali & BK ======
with open("wali_bk.json", encoding="utf-8") as f:
    WALI_BK = json.load(f)

app = Flask(__name__)

# ====== Kirim Pesan ke Wablas ======
def kirim_pesan(nomor, pesan):
    data = {"phone": nomor, "message": pesan}
    if SECRET_KEY:
        data["secret"] = SECRET_KEY

    r = requests.post(WABLAS_URL, headers={"Authorization": API_KEY}, data=data)
    print("Respon Wablas:", r.text)

# ====== Hari Indonesia ======
def hari_ini_indo():
    hari = datetime.datetime.now().strftime("%A")
    mapping = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }
    return mapping.get(hari, hari)

# ====== Bersihkan nama ======
def bersihkan_nama(nama):
    return nama.split(",")[0].strip().lower()

# ====== Cek Wali Kelas & Guru BK ======
def cek_wali_bk(pesan):
    pesan = pesan.lower()

    # Wali kelas
    if "wali" in pesan and "kelas" in pesan:
        for data in WALI_BK:
            if data["kelas"].lower() in pesan:
                return f"👩‍🏫 Wali Kelas {data['kelas']} adalah *{data['wali_kelas']}*."
        return "Maaf, saya tidak menemukan data wali kelas tersebut."

    # Guru BK
    if ("guru bk" in pesan) or ("bk" in pesan and "kelas" in pesan):
        for data in WALI_BK:
            if data["kelas"].lower() in pesan:
                return f"🧠 Guru BK {data['kelas']} adalah *{data['guru_bk']}*."
        return "Maaf, saya tidak menemukan data guru BK kelas tersebut."

    return None

# ====== Cari Jadwal Guru ======
def cari_jadwal(pesan):
    pesan = pesan.lower().strip()
    hasil = []

    # === Cek wali kelas / guru BK ===
    wali_bk_jawaban = cek_wali_bk(pesan)
    if wali_bk_jawaban:
        return wali_bk_jawaban

    # === Cek sapaan (case insensitive) ===
    sapaan = [
        "halo", "hai", "assalamualaikum", "hallo",
        "selamat pagi", "selamat siang", "selamat sore", "malam"
    ]

    for s in sapaan:
        if s in pesan:
            return (
                "👋 Halo, terima kasih sudah menghubungi *Chatbot SMAN 2 Demak*.\n"
                "Saya bisa bantu cek:\n"
                "- Jadwal guru (contoh: Jadwal Bu Muslikah)\n"
                "- Jadwal hari tertentu (contoh: Jadwal hari Senin)\n"
                "- Mapel (contoh: Jadwal Biologi)\n"
                "- Kelas (contoh: Jadwal XI-2)\n"
                "- Wali kelas (contoh: Wali kelas XI-1)\n"
                "- Guru BK (contoh: Guru BK X-2)\n"
                "Silakan ketik permintaan Anda 😊"
            )

    # === Jadwal saya ===
    if "jadwal saya" in pesan:
        return "🙏 Silakan sebutkan nama Anda (contoh: Jadwal Bu Siti)"

    # === Alias (nama panggilan) ===
    for alias, nama_lengkap in ALIAS.items():
        if re.search(rf"\b{alias}\b", pesan):
            hasil = [e for e in JADWAL if e["guru"].lower() == nama_lengkap.lower()]
            break

    # === Nama guru tanpa gelar ===
    if not hasil:
        for entri in JADWAL:
            nama_bersih = bersihkan_nama(entri["guru"])
            if re.search(rf"\b{nama_bersih}\b", pesan):
                hasil.append(entri)

    # === Mapel (semua guru) ===
    mapel_hasil = []
    for e in JADWAL:
        if e["mapel"].lower() in pesan:
            mapel_hasil.append(e)
    if mapel_hasil:
        jawaban = f"📚 Jadwal Mapel {mapel_hasil[0]['mapel']}:\n\n"
        for e in mapel_hasil:
            jawaban += f"• {e['guru']} → {e['kelas']} | {e['hari']} | {e['mulai']} - {e['selesai']}\n"
        return jawaban

    # === Jadwal hari ini ===
    if "hari ini" in pesan:
        hari = hari_ini_indo().lower()
        hasil = [e for e in JADWAL if e["hari"].lower() == hari]

    # === Cek hari tertentu ===
    if not hasil:
        for e in JADWAL:
            if e["hari"].lower() in pesan:
                hasil.append(e)

    # === Cek kelas ===
    if not hasil:
        for e in JADWAL:
            if e["kelas"].lower() in pesan:
                hasil.append(e)

    # === Cek jam ===
    if not hasil:
        for e in JADWAL:
            if e["mulai"] in pesan:
                hasil.append(e)

    # === Jika tetap tidak ada ===
    if not hasil:
        return (
            "🙏 Maaf, saya tidak menemukan data yang dimaksud.\n"
            "Contoh perintah:\n"
            "- Jadwal Bu Siti\n"
            "- Jadwal hari Senin\n"
            "- Jadwal Biologi\n"
            "- Wali kelas XI-1\n"
            "- Guru BK X-2"
        )

    # === Format jawaban ===
    hari_list = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu", "hari ini"]

    if any(h in pesan for h in hari_list):
        jawaban = f"📚 Jadwal hari {hasil[0]['hari']}:\n\n"
        for e in hasil:
            jawaban += f"• {e['guru']} → {e['kelas']} | {e['mapel']} | {e['mulai']} - {e['selesai']}\n"
        return jawaban

    # Berdasarkan guru
    guru = hasil[0]["guru"]
    jawaban = f"📚 Jadwal {guru}:\n\n"
    for e in hasil:
        jawaban += f"• {e['hari']} → {e['kelas']} | {e['mapel']} | {e['mulai']} - {e['selesai']}\n"
    return jawaban

# ====== Webhook ======
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook diterima:", data)

    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    nomor = data.get("phone")
    pesan = data.get("message", "")

    jawaban = cari_jadwal(pesan)
    kirim_pesan(nomor, jawaban)

    return jsonify({"status": "ok"}), 200

@app.route("/")
def home():
    return "✅ Bot WA SMAN 2 Demak aktif!"

# ====== Run di Railway ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
