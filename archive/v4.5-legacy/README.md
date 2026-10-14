🛰️ Göktürk Medya İndirme Merkezi V4.5
Göktürk Medya İndirme Merkezi; dizi, film, sosyal medya videoları ve müzikleri yüksek hızda, otomatik ve toplu bir şekilde indirmek için geliştirilmiş gelişmiş bir Siber İndirme İstasyonudur.

Gelişmiş web kazıma (web scraping) ve ağ trafiği koklama (network sniffing) yetenekleri sayesinde gizli kaynak .m3u8 linklerini otomatik olarak yakalar, çözer ve yüksek kalitede bilgisayarınıza indirir.

Developer: Developed with ❤️ by Wumpus

🚀 Öne Çıkan Özellikler
🎬 Akıllı Dizi Modu: Örnek bir bölüm linkinden dizinin adını, sezonunu ve bölümünü otomatik analiz eder. Belirttiğiniz başlangıç-bitiş aralığındaki tüm bölümleri arka planda tarayıcı simüle ederek (Playwright) tek tek yakalar ve indirir.

🎥 Doğrudan Video/Film Modu: YouTube, Instagram, TikTok gibi popüler platformların yanı sıra gizli video oynatıcı kullanan film sitelerindeki videoları otomatik olarak tespit eder ve MP4 formatında birleştirir.

🎵 Gelişmiş Müzik Modu: Tekli YouTube videolarını, devasa YouTube oynatma listelerini (Playlist/Mix) veya Spotify şarkı/playlist linklerini doğrudan 192kbps MP3 formatına dönüştürerek indirir.

🎨 Gelişmiş Terminal Arayüzü: Rich motoru kullanılarak hazırlanmış dinamik ilerleme çubukları, operasyon rapor tabloları ve animasyonlu paneller ile tamamen görselleştirilmiş modern bir CLI deneyimi sunar.

⚙️ Taşınabilir Ayar Altyapısı: İndirme dizinini dinamik olarak değiştirebilirsiniz. Varsayılan olarak tüm medyaları masaüstünüzde derli toplu bir şekilde depolar.

📂 Proje Yapısı
Proje dosyaları çalıştırıldığında sistem mimarisine uygun olarak otomatik olarak C:\DiziIndirici dizinine taşınır ve sisteminizde çöp dosya bırakmaz:

otuken.py -> Programın tüm indirme mekanizmasını ve motorunu barındıran ana Python kodu.

kurulum.bat -> Programı C:\ diskine taşıyan, kütüphaneleri, Playwright Chromium mimarisini ve FFmpeg video birleştirme motorunu kurup masaüstüne kısayol bırakan sihirbaz.

calistir.bat -> By: Wumpus özel ASCII açılış ekranıyla programı güvenli modda başlatan tetikleyici.

kaldir.bat -> Programı, kayıtlı ayarları ve masaüstü kısayolunu sistemden tek tıkla pırıl pırıl temizleyen kaldırıcı (Uninstaller).

requirements.txt -> Gerekli Python kütüphanelerinin listesi (yt-dlp, playwright, rich vb.).

🛠️ Kurulum ve Kullanım
1. Kurulum
Proje klasörünü bilgisayarınıza indirdikten sonra klasörün içerisindeki kurulum.bat dosyasına sağ tıklayıp Yönetici Olarak Çalıştır demeniz yeterlidir.

Sihirbaz otomatik olarak:

Tüm dosyaları C:\DiziIndirici klasörüne kopyalayacak,

Gerekli Python bağımlılıklarını yükleyecek,

Gizli linkleri yakalamak için Chromium motorunu kuracak,

Videoları birleştirmek için FFmpeg motorunu sisteme entegre edecek,

Masaüstünüze Gokturk Dizi Indirici adında şık bir kısayol bırakacaktır.

(Kurulum bittikten sonra internetten indirdiğiniz o ilk klasörü tamamen silebilirsiniz, projeniz artık C diskindedir).

2. Çalıştırma
Masaüstünüze gelen Gokturk Dizi Indirici kısayoluna çift tıklayarak Wumpus özel açılış ekranıyla siber indirme istasyonunu başlatabilirsiniz.

3. Sistemden Kaldırma
Eğer programı sisteminizden tamamen kaldırmak isterseniz, C:\DiziIndirici klasörü içerisindeki kaldir.bat dosyasına sağ tıklayıp Yönetici Olarak Çalıştır demeniz yeterlidir. Program, kayıtlı ayarlarınız ve masaüstü kısayolunuz arkada hiçbir çöp bırakılmadan kökten silinecektir.

📋 Gereksinimler
Kurulum sihirbazı bunları otomatik yükler ancak manuel kurmak isteyenler için:

Python 3.7 veya üzeri

FFmpeg (Sistem ortam değişkenlerine eklenmiş olmalıdır)

Playwright bağımlılıkları

⚖️ Yasal Uyarı
Bu araç tamamen eğitim ve kişisel kullanım amacıyla açık kaynak kodlu olarak geliştirilmiştir. İndirilen içeriklerin telif hakları tamamen içerik üreticilerine aittir. Kullanıcıların yaptığı indirmelerden ve kullanım şekillerinden geliştirici (Wumpus) sorumlu tutulamaz.


Geliştiriciden Not: Merhaba! Medya indirme aracımı indirdiğiniz için teşekkürler Aİ ile yaptığım çok mu belli oluyor :) Her neyse Sonuç olarak güzel çalışıyor ve gerçek anlamda işe yarıyor bazen hata verebilir ama kaldığı yerden devame debiliyor 
sonuç olarak bu programı dolaylı yoldan geçilştirdim hepsini tamamen ben yazmadım o yüzden siber indirme istasyonu falan diyor ai işte. Ekleme ve geliştirme yaparsanız bana da gönderin çünkü akitf olarak kullanıyorum bu programı. İyi Eğlenceler
