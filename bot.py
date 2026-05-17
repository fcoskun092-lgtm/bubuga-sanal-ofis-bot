import telebot
from telebot import types
import sqlite3
from datetime import datetime

TOKEN = "8757440726:AAEhGqpaDpNNcKSpvbpH4HWx6UPPKpfi8HE"
ADMIN_ID = 5523040957
GRUP_ID = -3996063718

bot = telebot.TeleBot(TOKEN)
user_state = {}
user_data = {}

def db_baglanti():
    conn = sqlite3.connect('tasks.db')
    conn.execute('CREATE TABLE IF NOT EXISTS gorevler (id INTEGER PRIMARY KEY AUTOINCREMENT, departman TEXT, aciklama TEXT, durum TEXT, tarih TEXT)')
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
    departmanlar = ['Genel Mudur', 'Grafik Tasarimci', 'Sosyal Medya', 'Meta Reklam', 'Google SEO', 'Musteri Temsilcisi', 'Mockup Uzmani', 'Yazilimci', 'Finans Direktoru']
    if message.text not in departmanlar:
        bot.send_message(message.chat.id, "Lutfen listeden secin!")
        return
    user_data[message.from_user.id] = {'departman': message.text}
    user_state[message.from_user.id] = 'aciklama_bekleniyor'
    bot.send_message(message.chat.id, "Gorev aciklamasini yazin:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'aciklama_bekleniyor')
def aciklama_al(message):
    if message.from_user.id != ADMIN_ID:
        return
    departman = user_data[message.from_user.id]['departman']
    aciklama = message.text
    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
    conn = db_baglanti()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gorevler (departman, aciklama, durum, tarih) VALUES (?, ?, ?, ?)", (departman, aciklama, 'Bekliyor', tarih))
    conn.commit()
    gorev_id = cursor.lastrowid
    conn.close()
    user_state.pop(message.from_user.id, None)
    user_data.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "Gorev eklendi! ID: " + str(gorev_id), reply_markup=ana_menu())
    bot.send_message(GRUP_ID, "Yeni Gorev! ID: " + str(gorev_id) + " Departman: " + departman + " Aciklama: " + aciklama + " Tarih: " + tarih)

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
    mesaj = "Gorev Listesi:\n\n"
    for g in gorevler:
        mesaj += "ID: " + str(g[0]) + " Departman: " + g[1] + " Aciklama: " + g[2] + " Durum: " + g[3] + " Tarih: " + g[4] + "\n\n"
    bot.send_message(message.chat.id, mesaj, reply_markup=ana_menu())

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

@bot.message_handler(func=lambda m:
m.text == 'Gorevi Sil')
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
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE durum='Bekliyor'")
    bekliyor = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE durum='Tamamlandi'")
    tamamlandi = cursor.fetchone()[0]
    cursor.execute("SELECT departman, COUNT(*) FROM gorevler GROUP BY departman")
    departmanlar = cursor.fetchall()
    conn.close()
    mesaj = "Durum Raporu\n\nToplam: " + str(toplam) + "\nBekliyor: " + str(bekliyor) + "\nTamamlandi: " + str(tamamlandi) + "\n\nDepartman Bazli:\n"
    for d in departmanlar:
        mesaj += d[0] + ": " + str(d[1]) + " gorev\n"
    bot.send_message(message.chat.id, mesaj, reply_markup=ana_menu())

bot.polling(none_stop=True)