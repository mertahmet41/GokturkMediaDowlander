# Göktürk Medya İndirme Merkezi — Kullanım Kılavuzu

Göktürk Medya İndirme Merkezi hem **Modern Grafik Arayüz (GUI)** hem de **Komut Satırı (CLI)** üzerinden kullanılabilir.

---

## 🚀 1. Başlatma Seçenekleri

### Seçenek A: Taşınabilir `.exe` ile (En Kolay)
- [GitHub Releases](https://github.com/mertahmet41/GokturkMediaDowlander/releases) sayfasından indirilen `GokturkMediaDownloader.exe` dosyasına çift tıklayın.
- Herhangi bir Python veya ek kurulum gerektirmez, doğrudan açılır.

### Seçenek B: Python ile Başlatma
```bash
# Grafik Arayüzü Başlat
python main.py
# veya
python gui.py

# Komut Satırı (Terminal) Modunu Başlat
python main.py --cli
```

---

## 💻 2. Grafik Arayüz (GUI) Kullanımı

### 📺 Dizi İndirme Sekmesi:
1. Dizi izleme sitelerindeki herhangi bir bölüm linkini yapıştırın:
   *(Örn: `https://ornekdizi.com/dizi/better-call-saul-1-sezon-1-bolum`)*
2. Program dizinin adını, sezon ve bölümünü otomatik tespit eder.
3. İndirmek istediğiniz **Başlangıç/Bitiş Sezon ve Bölümlerini** belirleyin.
4. **"🚀 Bölümleri Sırayla İndir"** butonuna basın.
5. Arka plan botu gizli `.m3u8` akışını yakalayıp bölümleri sırayla indirecektir.

### 🎬 Video & Film İndirme Sekmesi:
1. İndirmek istediğiniz linkleri kutuya alt alta yapıştırın:
   *(YouTube, Instagram Reels, TikTok, Twitter/X veya doğrudan film linkleri)*
2. Kalite / Format menüsünden çözünürlüğü seçin (En İyi, 1080p, 720p veya Sadece Ses MP3).
3. **"📥 Seçilen Videoları İndir"** butonuna basın.

### 🎵 Müzik İndirme (MP3) Sekmesi:
1. Tekli YouTube videosu, oynatma listesi (playlist) veya Spotify şarkı linkini yapıştırın.
2. Kalite menüsünden 192kbps veya 320kbps seçin.
3. **"🎵 MP3 Olarak Dönüştür ve İndir"** butonuna basın.

### ⚙️ Ayarlar Sekmesi:
- **İndirme Konumu:** "📂 Gözat" butonuna basarak medyaların indirileceği klasörü değiştirebilirsiniz.
- **Klasörü Aç:** İndirilenlerin bulunduğu klasörü doğrudan Windows Gezgini'nde açar.

---

## 🛑 İndirmeyi İptal Etme
İndirme sırasında pencerenin altındaki kırmızı **"⏹️ İndirmeyi Durdur"** butonuna basarak işlemi güvenle durdurabilirsiniz.
