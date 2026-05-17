import telebot
from telebot import types
import sqlite3
from datetime import datetime
import anthropic

TOKEN = "8757440726:AAEhGqpaDpNNcKSpvbpH4HWx6UPPKpfi8HE"
ADMIN_ID = 5523040957
GRUP_ID = -3996063718
ANTHROPIC_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
user_state = {}
user_data = {}

DEPARTMANLAR = {
    'Genel Mudur': 'Sen bir şirketin Genel Müdürüsün. Görevleri analiz et, departmanlara yönlendir ve rapor sun.',
    'Grafik Tasarimci': 'Sen bir Grafik Tasarımcısın. Şirket için görsel tasarım önerileri sun.',
    'Sosyal Medya': 'Sen bir Sosyal Medya Uzmanısın. Instagram, Facebook içerikleri üret.',
    'Meta Reklam': 'Sen bir Meta Reklam Uzmanısın. Facebook ve Instagram reklam kampanyaları yönet.',
    'Google SEO': 'Sen bir Google SEO Uzmanısın. Web sitesi SEO ve reklam çalışmaları yap.',
    'Musteri Temsilcisi': 'Sen bir Müşteri Temsilcisisin. Müşterilere profesyonel cevaplar ver.',
    'Mockup Uzmani': 'Sen bir Mockup Uzmanısın. Tasarımları modeller üzerinde görselleştir.',
    'Yazilimci': 'Sen bir Yazılımcısın. Teknik konularda destek ver.',
    'Finans Direktoru': 'Sen bir Finans Direktörüsün. Satış ve karlılık raporları sun.'
}

def db_baglanti():
    conn = sqlite3.connect('tasks.db')
    conn.execute('CREATE TABLE IF NOT EXISTS gorevler (id INTEGER PRIMARY KEY AUTOINCREMENT, departman TEXT, aciklama TEXT, durum TEXT, tarih TEXT, cevap TEXT)')
    conn.commit()
    return conn

def ana_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Gorev Ekle', 'Gorevleri Listele')
    markup.row('Gorevi Tamamla', 'Gorevi Sil')
    markup.row('Durum Raporu')
    return markup

def departman_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Genel Mudur', 'Grafik Tasarimci')
    markup.row('Sosyal Medya', 'Meta Reklam')
    markup.row('Google SEO', 'Musteri Temsilcisi')
    markup.row('Mockup Uzmani', 'Yazilimci')
    markup.row('Finans Direktoru')
    return markup

def claude_cevap_al(departman, gorev):
    sistem = DEPARTMANLAR.get(departman, 'Sen bir şirket çalışanısın.')
    mesaj = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024
    system=sistem,
        messages=[{"role": "user", "content": gorev}]
    )
    return mesaj.content[0].text

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Yetkisiz erisim!")
        return
    bot.send_message(message.chat.id, "Bubuga Sanal Ofis'e Hosgeldiniz!", reply_markup=ana_menu())

@bot.message_handler(func=lambda m: m.text == 'Gorev Ekle')
def gorev_ekle_baslat(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_state[message.from_user.id] = 'departman_seciliyor'
    bot.send_message(message.chat.id, "Departman secin:", reply_markup=departman_menu())

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'departman_seciliyor')
def departman_sec(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text not in DEPARTMANLAR:
        bot.send_message(message.chat.id, "Lutfen listeden secin!")
        return
    user_data[message.from_user.id] = {'departman': message.text}
    user_state[message.from_user.id] = 'aciklama_bekleniyor'
    bot.send_message(message.chat.id, "Gorevi yazin:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'aciklama_bekleniyor')
def aciklama_al(message):
    if message.from_user.id != ADMIN_ID:
        return
    departman = user_data[message.from_user.id]['departman']
    aciklama = message.text
    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
    bot.send_message(message.chat.id, departman + " gorevi aliyor, lutfen bekleyin...")
    cevap = claude_cevap_al(departman, aciklama)
    conn = db_baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gorevler (departman, aciklama, durum, tarih, cevap) VALUES (?, ?, ?, ?, ?)", (departman, aciklama, 'Tamamlandi', tarih, cevap))
    conn.commit()
    gorev_id = cursor.lastrowid
    conn.close()
    user_state.pop(message.from_user.id, None)
    user_data.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "Gorev ID: " + str(gorev_id) + "\nDepartman: " + departman + "\n\nCevap:\n" + cevap, reply_markup=ana_menu())
    bot.send_message(GRUP_ID, "Yeni Gorev Tamamlandi!\nID: " + str(gorev_id) + "\nDepartman: " + departman + "\nGorev: " + aciklama + "\n\nCevap:\n" + cevap)

@bot.message_handler(func=lambda m: m.text == 'Gorevleri Listele')
def gorevleri_listele(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = db_baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT FROM gorevler")
    gorevler = cursor.fetchall()
    conn.close()
    if not gorevler:
        bot.send_message(message.chat.id, "Hic gorev yok!")
        return
    for g in gorevler:
        mesaj = "ID: " + str(g[0]) + "\nDepartman: " + g[1] + "\nGorev: " + g[2] + "\nDurum: " + g[3] + "\nTarih: " + g[4] + "\nCevap: " + str(g[5])
        bot.send_message(message.chat.id, mesaj)
    bot.send_message(message.chat.id, "Liste tamamlandi!", reply_markup=ana_menu())

@bot.message_handler(func=lambda m: m.text == 'Gorevi Tamamla')
def gorevi_tamamla_baslat(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_state[message.from_user.id] = 'tamamla_id_bekleniyor'
    bot.send_message(message.chat.id, "Tamamlanacak gorev ID sini girin:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'tamamla_id_bekleniyor')
def gorevi_tamamla(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        gorev_id = int(message.text)
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute("UPDATE gorevler SET durum='Tamamlandi' WHERE id=?", (gorev_id,))
        conn.commit()
        conn.close()
        user_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "Gorev " + str(gorev_id) + " tamamlandi!", reply_markup=ana_menu())
        bot.send_message(GRUP_ID, "Gorev Tamamlandi! ID: " + str(gorev_id))
    except:
        bot.send_message(message.chat.id, "Gecersiz ID!", reply_markup=ana_menu())

@bot.message_handler(func=lambda m: m.text == 'Gorevi Sil')
def gorevi_sil_baslat(message):
    if message.from_user.id != ADMIN_ID:
        return
    user_state[message.from_user.id] = 'sil_id_bekleniyor'
    bot.send_message(message.chat.id, "Silinecek gorev ID sini girin:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'sil_id_bekleniyor')
def gorevi_sil(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        gorev_id = int(message.text)
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gorevler WHERE id=?", (gorev_id,))
        conn.commit()
        conn.close()
        user_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "Gorev " + str(gorev_id) + " silindi!", reply_markup=ana_menu())
        bot.send_message(GRUP_ID, "Gorev Silindi! ID: " + str(gorev_id))
    except:
        bot.send_message(message.chat.id, "
                         Gecersiz ID!", reply_markup=ana_menu())

@bot.message_handler(func=lambda m: m.text == 'Durum Raporu')
def durum_raporu(message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = db_baglanti()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gorevler")
    toplam = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE durum='Tamamlandi'")
    tamamlandi = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE durum='Bekliyor'")
    bekliyor = cursor.fetchone()[0]
    cursor.execute("SELECT departman, COUNT(*) FROM gorevler GROUP BY departman")
    departmanlar = cursor.fetchall()
    conn.close()
    mesaj = "Durum Raporu\n\nToplam: " + str(toplam) + "\nTamamlandi: " + str(tamamlandi) + "\nBekliyor: " + str(bekliyor) + "\n\nDepartman Bazli:\n"
    for d in departmanlar:
        mesaj += d[0] + ": " + str(d[1]) + " gorev\n"
    bot.send_message(message.chat.id, mesaj, reply_markup=ana_menu())

bot.polling(none_stop=True)
