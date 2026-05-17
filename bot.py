import telebot
from telebot import types
import sqlite3
import threading
from datetime import datetime
import anthropic

TOKEN = "8757440726:AAEhGqpaDpNNcKSpvbpH4HWx6UPPKpfi8HE"
ADMIN_ID = 5523040957
GRUP_ID = -3996063718
ANTHROPIC_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

user_state = {}
user_data = {}

DEPARTMANLAR = {
    'Genel Mudur': {
        'etiket': '@Genel',
        'kisaltma': 'genel',
        'emoji': '👔',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Genel Mudurusun. Gorevleri analiz et, departmanlara yonlendir ve rapor sun. Profesyonel ve net cevaplar ver.'
    },
    'Grafik Tasarimci': {
        'etiket': '@Grafik',
        'kisaltma': 'grafik',
        'emoji': '🎨',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Grafik Tasarimcisisin. Jobka Kids ve Tshirtal markalari icin gorsel tasarim onerileri sun. Yaratici ve detayli cevaplar ver.'
    },
    'Sosyal Medya': {
        'etiket': '@Sosyal',
        'kisaltma': 'sosyal',
        'emoji': '📱',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Sosyal Medya Uzmanisisin. Jobka Kids ve Tshirtal markalari icin Instagram Reels, Stories, gonderi ve Facebook icerikleri uret.'
    },
    'Meta Reklam': {
        'etiket': '@Reklam',
        'kisaltma': 'reklam',
        'emoji': '📢',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Meta Reklam Uzmanisisin. Facebook ve Instagram reklam kampanyalarini yonet ve optimize et.'
    },
    'Google SEO': {
        'etiket': '@SEO',
        'kisaltma': 'seo',
        'emoji': '🔍',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Google SEO Uzmanisisin. Web sitesi SEO ve Google reklam calismalarini yonet.'
    },
    'Musteri Temsilcisi': {
        'etiket': '@Musteri',
        'kisaltma': 'musteri',
        'emoji': '💬',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Musteri Temsilcisisin. Musterilere WhatsApp, Facebook, Instagram ve web sitesinde profesyonel cevaplar ver.'
    },
    'Mockup Uzmani': {
        'etiket': '@Mockup',
        'kisaltma': 'mockup',
        'emoji': '🖼️',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Mockup Uzmanisisin. Tasarimlari modeller uzerinde 3 farkli pozda gorsellestir ve detayli acikla.'
    },
    'Yazilimci': {
        'etiket': '@Yazilim',
        'kisaltma': 'yazilim',
        'emoji': '💻',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Yazilimcisisin. Web gelistirme, mobil uygulama, e-ticaret API entegrasyonlari ve otomasyon scriptleri konularinda teknik destek ver.'
    },
    'Finans Direktoru': {
        'etiket': '@Finans',
        'kisaltma': 'finans',
        'emoji': '💰',
        'sistem': 'Sen Bubuga Perakende Giyim sirketinin Finans Direktorusun. Satis ve odemeleri takip et, karlilik raporlari sun.'
    }
}

KISALTMA_MAP = {v['kisaltma']: k for k, v in DEPARTMANLAR.items()}


def db_baglanti():
    conn = sqlite3.connect('tasks.db')
    conn.execute("""CREATE TABLE IF NOT EXISTS gorevler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        departman TEXT,
        aciklama TEXT,
        durum TEXT,
        tarih TEXT,
        cevap TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS grup_mesajlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici TEXT,
        departman TEXT,
        mesaj TEXT,
        cevap TEXT,
        tarih TEXT
    )""")
    conn.commit()
    return conn


def gorevi_kaydet(departman, aciklama, tarih, cevap):
    conn = None
    try:
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO gorevler (departman, aciklama, durum, tarih, cevap) VALUES (?, ?, ?, ?, ?)",
            (departman, aciklama, 'Tamamlandi', tarih, cevap)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Veritabani hatasi: {e}")
        return None
    finally:
        if conn:
            conn.close()


def grup_mesaj_kaydet(kullanici, departman, mesaj, cevap, tarih):
    conn = None
    try:
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO grup_mesajlar (kullanici, departman, mesaj, cevap, tarih) VALUES (?, ?, ?, ?, ?)",
            (kullanici, departman, mesaj, cevap, tarih)
        )
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Grup mesaj kayit hatasi: {e}")
    finally:
        if conn:
            conn.close()



def gorev_baslat(departman, aciklama, tarih):
    conn = None
    try:
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO gorevler (departman, aciklama, durum, tarih, cevap) VALUES (?, ?, ?, ?, ?)",
            (departman, aciklama, 'Devam Ediyor', tarih, '')
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Gorev baslatma hatasi: {e}")
        return None
    finally:
        if conn:
            conn.close()


def gorev_cevap_guncelle(gorev_id, cevap, durum='Tamamlandi'):
    conn = None
    try:
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE gorevler SET cevap=?, durum=? WHERE id=?",
            (cevap, durum, gorev_id)
        )
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Gorev guncelleme hatasi: {e}")
    finally:
        if conn:
            conn.close()


def telegrama_uzun_mesaj_gonder(chat_id, metin, reply_markup=None):
    limit = 3900
    if metin is None:
        metin = ""

    metin = str(metin)

    if len(metin) <= limit:
        bot.send_message(chat_id, metin, reply_markup=reply_markup)
        return

    parcalar = [metin[i:i + limit] for i in range(0, len(metin), limit)]
    for index, parca in enumerate(parcalar):
        if index == len(parcalar) - 1:
            bot.send_message(chat_id, parca, reply_markup=reply_markup)
        else:
            bot.send_message(chat_id, parca)


def arka_planda_gorev_calistir(gorev_id, departman, aciklama, kullanici_chat_id, grup_id=None):
    try:
        cevap = claude_cevap_al(departman, aciklama)
        gorev_cevap_guncelle(gorev_id, cevap, 'Tamamlandi')

        sonuc_mesaji = (
            f"Gorev ID: {gorev_id}\n"
            f"Departman: {DEPARTMANLAR[departman]['emoji']} {departman}\n"
            f"Durum: Tamamlandi\n\n"
            f"Cevap:\n{cevap}"
        )

        telegrama_uzun_mesaj_gonder(kullanici_chat_id, sonuc_mesaji, reply_markup=ana_menu())

        if grup_id:
            grup_mesaji = (
                f"🆕 Yeni Gorev Tamamlandi!\n"
                f"ID: {gorev_id}\n"
                f"Departman: {DEPARTMANLAR[departman]['emoji']} {departman}\n"
                f"Gorev: {aciklama}\n\n"
                f"Cevap:\n{cevap}"
            )
            telegrama_uzun_mesaj_gonder(grup_id, grup_mesaji)

    except Exception as e:
        hata = f"Hata olustu: {e}"
        gorev_cevap_guncelle(gorev_id, hata, 'Hata')
        telegrama_uzun_mesaj_gonder(
            kullanici_chat_id,
            f"Gorev ID: {gorev_id}\nDepartman: {departman}\nDurum: Hata\n\n{hata}",
            reply_markup=ana_menu()
        )


def arka_planda_grup_mesaji_calistir(chat_id, kullanici, hedef_departman, metin, tarih):
    try:
        cevap = claude_cevap_al(hedef_departman, metin)
        bot.send_message(
            chat_id,
            f"{DEPARTMANLAR[hedef_departman]['emoji']} *{hedef_departman}*\n\n{cevap}",
            parse_mode='Markdown'
        )
        grup_mesaj_kaydet(kullanici, hedef_departman, metin, cevap, tarih)
    except Exception as e:
        bot.send_message(chat_id, f"{DEPARTMANLAR[hedef_departman]['emoji']} {hedef_departman} cevap veremedi: {e}")


def arka_planda_ekip_calistir(chat_id, kullanici, soru, tarih):
    for departman_adi, departman_bilgi in DEPARTMANLAR.items():
        try:
            cevap = claude_cevap_al(departman_adi, soru)
            bot.send_message(
                chat_id,
                f"{departman_bilgi['emoji']} *{departman_adi}*\n\n{cevap}",
                parse_mode='Markdown'
            )
            grup_mesaj_kaydet(kullanici, departman_adi, soru, cevap, tarih)
        except Exception as e:
            bot.send_message(chat_id, f"{departman_bilgi['emoji']} {departman_adi} cevap veremedi: {e}")


def claude_cevap_al(departman, gorev):
    try:
        sistem = DEPARTMANLAR[departman]['sistem']
        mesaj = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=sistem,
            messages=[{"role": "user", "content": gorev}]
        )
        return mesaj.content[0].text
    except Exception as e:
        return f"Hata olustu: {e}"


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
    if message.chat.type in ['group', 'supergroup']:
        bot.send_message(
            message.chat.id,
            "Bubuga Sanal Ofis Grubu'na hosgeldiniz!\n\n"
            "Departmanlarla konusmak icin:\n"
            "👔 @Genel - Genel Mudur\n"
            "🎨 @Grafik - Grafik Tasarimci\n"
            "📱 @Sosyal - Sosyal Medya\n"
            "📢 @Reklam - Meta Reklam\n"
            "🔍 @SEO - Google SEO\n"
            "💬 @Musteri - Musteri Temsilcisi\n"
            "🖼️ @Mockup - Mockup Uzmani\n"
            "💻 @Yazilim - Yazilimci\n"
            "💰 @Finans - Finans Direktoru\n\n"
            "/ekip - Tum ekip ayni soruya cevap verir"
        )
        return

    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Yetkisiz erisim!")
        return

    bot.send_message(message.chat.id, "Bubuga Sanal Ofis'e Hosgeldiniz!", reply_markup=ana_menu())


@bot.message_handler(commands=['ekip'])
def ekip_cevap(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.send_message(message.chat.id, "Bu komut sadece grupta kullanilabilir!")
        return

    soru = message.text.replace('/ekip', '').strip()
    if not soru:
        bot.send_message(message.chat.id, "Lutfen bir soru yazin. Ornek: /ekip Yeni sezon icin ne yapmaliyiz?")
        return

    bot.send_message(message.chat.id, "Tum ekip sorunuzu degerlendiriyor. Cevaplar hazir oldukca buradan gelecek.")
    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
    kullanici = message.from_user.first_name or "Kullanici"

    threading.Thread(
        target=arka_planda_ekip_calistir,
        args=(message.chat.id, kullanici, soru, tarih),
        daemon=True
    ).start()

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def grup_mesaj_isle(message):
    if not message.text:
        return

    metin = message.text.strip()
    hedef_departman = None

    for departman_adi, departman_bilgi in DEPARTMANLAR.items():
        etiket = departman_bilgi['etiket'].lower()
        if metin.lower().startswith(etiket):
            hedef_departman = departman_adi
            metin = metin[len(etiket):].strip()
            break

    if not hedef_departman:
        return

    if not metin:
        bot.send_message(message.chat.id, f"{DEPARTMANLAR[hedef_departman]['emoji']} Lutfen bir mesaj yazin!")
        return

    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
    kullanici = message.from_user.first_name or "Kullanici"

    bot.send_message(
        message.chat.id,
        f"{DEPARTMANLAR[hedef_departman]['emoji']} *{hedef_departman}* gorevi aldi. Cevap hazir olunca buradan gelecek.",
        parse_mode='Markdown'
    )

    threading.Thread(
        target=arka_planda_grup_mesaji_calistir,
        args=(message.chat.id, kullanici, hedef_departman, metin, tarih),
        daemon=True
    ).start()

@bot.message_handler(func=lambda m: m.text == 'Gorev Ekle' and m.chat.type == 'private')
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

    gorev_id = gorev_baslat(departman, aciklama, tarih)

    user_state.pop(message.from_user.id, None)
    user_data.pop(message.from_user.id, None)

    bot.send_message(
        message.chat.id,
        f"{DEPARTMANLAR[departman]['emoji']} {departman} gorevi aldi.\n"
        f"Gorev ID: {gorev_id}\n"
        f"Durum: Arka planda calisiyor. Sonuc hazir olunca buradan gelecek.",
        reply_markup=ana_menu()
    )

    threading.Thread(
        target=arka_planda_gorev_calistir,
        args=(gorev_id, departman, aciklama, message.chat.id, GRUP_ID),
        daemon=True
    ).start()

@bot.message_handler(func=lambda m: m.text == 'Gorevleri Listele' and m.chat.type == 'private')
def gorevleri_listele(message):
    if message.from_user.id != ADMIN_ID:
        return

    conn = None
    try:
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gorevler ORDER BY id DESC")
        gorevler = cursor.fetchall()

        if not gorevler:
            bot.send_message(message.chat.id, "Hic gorev yok!")
            return

        for g in gorevler:
            emoji = DEPARTMANLAR.get(g[1], {}).get('emoji', '📋')
            mesaj = (
                f"ID: {g[0]}\n"
                f"{emoji} Departman: {g[1]}\n"
                f"Gorev: {g[2]}\n"
                f"Durum: {g[3]}\n"
                f"Tarih: {g[4]}\n"
                f"Cevap: {g[5]}"
            )
            bot.send_message(message.chat.id, mesaj)

        bot.send_message(message.chat.id, "Liste tamamlandi!", reply_markup=ana_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"Hata: {e}")
    finally:
        if conn:
            conn.close()


@bot.message_handler(func=lambda m: m.text == 'Gorevi Tamamla' and m.chat.type == 'private')
def gorevi_tamamla_baslat(message):
    if message.from_user.id != ADMIN_ID:
        return

    user_state[message.from_user.id] = 'tamamla_id_bekleniyor'
    bot.send_message(message.chat.id, "Tamamlanacak gorev ID sini girin:", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'tamamla_id_bekleniyor')
def gorevi_tamamla(message):
    if message.from_user.id != ADMIN_ID:
        return

    conn = None
    try:
        gorev_id = int(message.text)
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute("UPDATE gorevler SET durum='Tamamlandi' WHERE id=?", (gorev_id,))
        conn.commit()

        user_state.pop(message.from_user.id, None)

        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, f"{gorev_id} ID numarali gorev bulunamadi.", reply_markup=ana_menu())
            return

        bot.send_message(message.chat.id, f"Gorev {gorev_id} tamamlandi!", reply_markup=ana_menu())
        bot.send_message(GRUP_ID, f"✅ Gorev Tamamlandi! ID: {gorev_id}")
    except ValueError:
        user_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "Gecersiz ID, lutfen sayi girin!", reply_markup=ana_menu())
    except Exception as e:
        user_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, f"Hata: {e}", reply_markup=ana_menu())
    finally:
        if conn:
            conn.close()


@bot.message_handler(func=lambda m: m.text == 'Gorevi Sil' and m.chat.type == 'private')
def gorevi_sil_baslat(message):
    if message.from_user.id != ADMIN_ID:
        return

    user_state[message.from_user.id] = 'sil_id_bekleniyor'
    bot.send_message(message.chat.id, "Silinecek gorev ID sini girin:", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'sil_id_bekleniyor')
def gorevi_sil(message):
    if message.from_user.id != ADMIN_ID:
        return

    conn = None
    try:
        gorev_id = int(message.text)
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gorevler WHERE id=?", (gorev_id,))
        conn.commit()

        user_state.pop(message.from_user.id, None)

        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, f"{gorev_id} ID numarali gorev bulunamadi.", reply_markup=ana_menu())
            return

        bot.send_message(message.chat.id, f"Gorev {gorev_id} silindi!", reply_markup=ana_menu())
        bot.send_message(GRUP_ID, f"🗑️ Gorev Silindi! ID: {gorev_id}")
    except ValueError:
        user_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "Gecersiz ID, lutfen sayi girin!", reply_markup=ana_menu())
    except Exception as e:
        user_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, f"Hata: {e}", reply_markup=ana_menu())
    finally:
        if conn:
            conn.close()


@bot.message_handler(func=lambda m: m.text == 'Durum Raporu' and m.chat.type == 'private')
def durum_raporu(message):
    if message.from_user.id != ADMIN_ID:
        return

    conn = None
    try:
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

        cursor.execute("SELECT COUNT(*) FROM grup_mesajlar")
        grup_toplam = cursor.fetchone()[0]

        rapor = "📊 Durum Raporu\n\n"
        rapor += f"📋 Toplam Gorev: {toplam}\n"
        rapor += f"✅ Tamamlandi: {tamamlandi}\n"
        rapor += f"⏳ Bekliyor: {bekliyor}\n"
        rapor += f"💬 Grup Mesaj Sayisi: {grup_toplam}\n\n"
        rapor += "📁 Departman Bazli Gorevler:\n"

        for dep in departmanlar:
            emoji = DEPARTMANLAR.get(dep[0], {}).get('emoji', '📋')
            rapor += f"{emoji} {dep[0]}: {dep[1]} gorev\n"

        bot.send_message(message.chat.id, rapor, reply_markup=ana_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"Hata: {e}", reply_markup=ana_menu())
    finally:
        if conn:
            conn.close()


@bot.message_handler(commands=['gecmis'])
def grup_gecmis(message):
    if message.chat.type not in ['group', 'supergroup']:
        return

    conn = None
    try:
        conn = db_baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT kullanici, departman, mesaj, cevap, tarih FROM grup_mesajlar ORDER BY id DESC LIMIT 5"
        )
        mesajlar = cursor.fetchall()

        if not mesajlar:
            bot.send_message(message.chat.id, "Hic grup mesaji yok!")
            return

        for m in mesajlar:
            emoji = DEPARTMANLAR.get(m[1], {}).get('emoji', '📋')
            bot.send_message(
                message.chat.id,
                f"👤 {m[0]} - {m[4]}\n{emoji} {m[1]}\n❓ {m[2]}\n💡 {m[3]}"
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"Hata: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Bubuga Sanal Ofis Botu baslatiliyor...")
    print("Ozel mesajlar ve grup sohbeti aktif!")
    print("Grup etiketleri: @Genel @Grafik @Sosyal @Reklam @SEO @Musteri @Mockup @Yazilim @Finans")
    print("/ekip komutu ile tum ekibe soru sorabilirsiniz.")
    print("/gecmis komutu ile son 5 grup mesajini gorebilirsiniz.")
    bot.polling(none_stop=True, interval=0, timeout=20)
