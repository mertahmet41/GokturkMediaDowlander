# Değişiklik Günlüğü (Changelog) — Göktürk Medya İndirme Merkezi

Bu dokümanda projenin tüm sürüm geçmişi, yapılan hata düzeltmeleri ve geliştirmeler kayıt altına alınmıştır.

---

## [5.0.0] - 2026-10-14 (Güncel Sürüm)

### 🐛 Düzeltilen Kritik Hatalar:
1. **İlerleme Çubuğu `KeyError: 'info_dict'` Çökmesi Düzeltildi:**
   - `yt-dlp` indirme kancasında (`progress_hooks`), m3u8 parçaları veya belirli akışlar indirilirken `info_dict` anahtarının bulunmaması durumunda programın çökmesine yol açan hata giderildi. Güvenli kanca mimarisine (`make_progress_hook`) geçildi.
2. **Windows Geçersiz Dosya Adı (`[Errno 22]`) Hatası Çözüldü:**
   - Video linklerinde veya başlıklarında yer alan Windows'un yasaklı karakterleri (`\ / : * ? " < > |`) ve URL sorgu parametreleri (`?token=...`) filtrelenerek `[Errno 22] Invalid argument` hatası engellendi (`dosya_adi_temizle`).
3. **M3U8 Akış Yakalayıcı Playlist Filtreleme Hatası Düzeltildi:**
   - `m3u8_linki_yakala` fonksiyonunda yer alan `"playlist" not in request.url` koşulu, CDN'lerin standart olarak kullandığı `playlist.m3u8` akışlarının yakalanmasını engelliyordu. Bu kısıtlama kaldırıldı, reklam/analitik filtreleri eklendi ve HTTP Content-Type kontrolü entegre edildi.
4. **Spotify İndirme Altyapısı Yenilendi:**
   - Önceden Spotify URL'si doğrudan YouTube aramasına gönderildiğinde arama sonuçsuz kalıyor ya da alakasız videolar indiriliyordu. Resmi Spotify oEmbed API entegre edilerek şarkı ve sanatçı adı otomatik çözümlenir hale getirildi.
5. **Windows Türkçe Karakter Kodlaması (`UnicodeEncodeError: 'charmap'`) Çözüldü:**
   - Windows CP1254 terminallerinde zengin metin karakterlerinin (`✓`, `⚡`, `🚀`) sebep olduğu `charmap can't encode character` çökmesi, `sys.stdout.reconfigure(encoding='utf-8')` ile kalıcı olarak giderildi.
6. **Dizi İsmi Ayrıştırma Hatası Düzeltildi:**
   - Örnek bölüm linklerinden dizi adı çıkarılırken sezon ve bölüm numaralarının dizi klasör ismine yapışması (`Breaking Bad 1 Sezon 2 Bolum` gibi) regex temizliğiyle düzeltildi.
7. **Sonsuz Hata Döngüsü ve 30 Bölüm Sınırı İyileştirildi:**
   - Dizi modunda art arda 3 bölüm bulunamadığında sonraki sezona akıllı geçiş yapan mekanizma eklendi.
8. **Türkçe Karakterli `Kaldır.bat` Dosya İsmi Düzenlendi:**
   - Windows konsollarında kodlama karmaşasını önlemek adına `kaldir.bat` olarak standartlaştırıldı.

### ✨ Yeni Özellikler & İyileştirmeler:
- `main.py` standart giriş noktası eklendi.
- `archive/v4.5-legacy/` klasörü oluşturularak önceki v4.5 sürümünün kaynak kodları arşivlendi.
- `tests/test_core.py` ile otomatik birim testleri (unit tests) eklendi.
- `.gitignore` dosyası oluşturuldu.

---

## [4.5.0] - 2026-05-31 (Önceki Sürüm / Legacy)
- İlk kamuya açık sürüm.
- Playwright tabanlı arka plan Chromium tarayıcı koklama mimarisi.
- Rich kütüphanesiyle terminal panelleri ve ilerleme çubuğu.
- Temel dizi, tekli video ve YouTube MP3 indirme modları.
- Kurulum ve kaldırma betikleri (`kurulum.bat`, `calistir.bat`, `Kaldır.bat`).
- Kodlar `archive/v4.5-legacy/` dizininde incelenebilir.
