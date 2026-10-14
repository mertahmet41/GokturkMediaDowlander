# Göktürk Medya İndirme Merkezi — Kullanım Kılavuzu

Bu kılavuzda Göktürk Medya İndirme Merkezi'nin temel çalışma modları ve pratik kullanım adımları anlatılmaktadır.

---

## 🚀 Başlatma

1. **Doğrudan Başlatma:**
   ```bash
   python main.py
   # veya
   python otuken.py
   ```
2. **Windows Kısayolu:**
   - Kurulum sihirbazını (`kurulum.bat`) çalıştırdıysanız masaüstünüzdeki **"Gokturk Dizi Indirici"** kısayoluna çift tıklayın.

---

## 🎬 1. Dizi Modu (Akıllı Sezon / Bölüm İndirme)

- Dizi izleme sitelerindeki herhangi bir bölüm linkini yapıştırın:
  `Örnek: https://ornekdizi.com/dizi/better-call-saul-1-sezon-1-bolum`
- Program dizinin adını, sezon ve bölümünü otomatik tespit eder.
- Başlangıç ve bitiş sezon/bölüm aralığını girin.
- Playwright botu arka planda sayfayı yükler, video oynatıcısını tetikler ve gizli `.m3u8` medya akışını yakalayarak sırayla indirir.
- İndirilen dosyalar otomatik olarak şu hiyerarşide saklanır:
  `Masaüstü > Indirilen_Mediyalar > [Dizi Adı] > Sezon [X] > Sezon_X_Bolum_Y.mp4`

---

## 🎥 2. Doğrudan Video / Film Modu

- **Desteklenen Platformlar:** YouTube, Instagram Reels, TikTok, Twitter/X ve doğrudan video oynatıcı barındıran film siteleri.
- İstediğiniz kadar linki alt alta yapıştırın. Boş bırakıp `Enter` tuşuna bastığınızda toplu indirme başlar.
- Sosyal medya videoları `Indirilen_Mediyalar/Sosyal Medya Videolari` klasörüne, filmler ise `Indirilen_Mediyalar/Filmler ve Tekli Videolar` klasörüne kaydedilir.

---

## 🎵 3. Müzik İndirme Modu (MP3)

1. **Tekli YouTube Videosu:** Video linkini girin; otomatik olarak en yüksek kalitede 192kbps MP3 olarak dönüştürülüp indirilir.
2. **YouTube Playlist / Mix:** Çalma listesi linkini yapıştırın; listedeki tüm parçalar tek tek sırayla indirilir.
3. **Spotify Şarkı Linki:** `https://open.spotify.com/track/...` linkini yapıştırın; sistem şarkı adını ve sanatçısını otomatik çözer, YouTube müzik kaynaklarından bularak MP3 olarak kaydeder.

---

## ⚙️ 4. Ayarlar (İndirme Dizinini Değiştirme)

- Menüden `4` seçeneğini seçerek medyaların kaydedileceği varsayılan klasör yolunu istediğiniz disk veya klasörle güncelleyebilirsiniz.
- Ayarlar `%APPDATA%\GokturkMediaDownloader\config.json` dosyasına kaydedilir.
