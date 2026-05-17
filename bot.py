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
    'Genel Mudur': 'Sen bir sirketin Genel Mudurusun. Gorevleri analiz et, departmanlara yonlendir ve rapor sun.',
    'Grafik Tasarimci': 'Sen bir Grafik Tasarimcisin. Sirket icin gorsel tasarim onerileri sun.',
    'Sosyal Medya': 'Sen bir Sosyal Medya Uzmanisın. Instagram, Facebook icerikleri uret.',
    'Meta Reklam': 'Sen bir Meta Reklam Uzmanisın. Facebook ve Instagram reklam kampanyalari yonet.',
    'Google SEO': 'Sen bir Google SEO Uzmanisın. Web sitesi SEO ve reklam calismalari yap.',
    'Musteri Temsilcisi': 'Sen bir Musteri Temsilcisisin. Musterilere profesyonel cevaplar ver.',
    'Mockup Uzmani': 'Sen bir Mockup Uzmanisın. Tasarimlari modeller uzerinde gorsellestir.',
    'Yazilimci': 'Sen bir Yazilimcisin. Teknik konularda destek ver.',
    'Finans Direktoru': 'Sen bir Finans Direktorusun. Satis ve karlilik raporlari sun.'
}

def db_baglanti():
    conn = sqlite3.connect('tasks.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS gorevler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        departman TEXT,
        aciklama TEXT,
        durum TEXT,
        tarih TEXT,
        cevap TEXT
    )''')
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
    sistem = DEPARTMANLAR.get(departman, 'Sen bir sirket calisanisin.')
    mesaj = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
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
    conn = db_
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
    cursor.execute("SELECT * FROM gorevler")
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
        bot.send_message(message.chat.id, "Gecersiz ID!", reply_markup=ana_menu())

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
    mesaj = "Durum Raporu\n\nToplam: " + str
