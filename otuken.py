import os
import re
import time
import sys
import json
import yt_dlp
from pathlib import Path
from playwright.sync_api import sync_playwright

# Gelişmiş arayüz için Rich kütüphanesi
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.text import Text
from rich.table import Table
from rich import print as rprint

# --- AYAR SİSTEMİ ---
APP_NAME = "GokturkMediaDownloader"
CONFIG_DIR = Path(os.getenv('APPDATA')) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

def ayar_yukle():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        default_path = str(Path.home() / "Desktop" / "Indirilen_Mediyalar")
        ayarlar = {"indirme_dizini": default_path}
        with open(CONFIG_FILE, "w") as f: 
            json.dump(ayarlar, f)
        return ayarlar
    with open(CONFIG_FILE, "r") as f: 
        return json.load(f)

def ayar_kaydet(yeni_yol):
    ayarlar = {"indirme_dizini": yeni_yol}
    with open(CONFIG_FILE, "w") as f: 
        json.dump(ayarlar, f)
    rprint("[bold green]✓ Ayarlar başarıyla kaydedildi![/bold green]")

console = Console()

ayarlar = ayar_yukle()
INDIRME_KLASORU = ayarlar["indirme_dizini"]
if not os.path.exists(INDIRME_KLASORU):
    os.makedirs(INDIRME_KLASORU)

OPERASYON_RAPORU = []

def klasor_hazirla(ana_klasor, alt_klasor=""):
    """Dizi adı ve sezona göre klasör mimarisi oluşturur."""
    temiz_ana = re.sub(r'[\\/*?:"<>|]', "", ana_klasor).strip()
    yol = os.path.join(INDIRME_KLASORU, temiz_ana)
    if alt_klasor:
        temiz_alt = re.sub(r'[\\/*?:"<>|]', "", alt_klasor).strip()
        yol = os.path.join(yol, temiz_alt)
    if not os.path.exists(yol):
        os.makedirs(yol)
    return yol

def animasyonlu_baslik(metin):
    panel = Panel(
        Text(metin, justify="center", style="bold gold1"),
        border_style="cyan",
        title="[ GOKTURK MEDYA INDIRME MERKEZI V5.0 ]",
        subtitle="Siber Otomatik Otomasyon Istasyonu"
    )
    console.print(panel)

def ytdlp_ilerleme_cubugu(d):
    """yt-dlp çıktısını yakalayıp Rich çubuğuna pürüzsüz aktaran fonksiyon."""
    if d['status'] == 'downloading':
        toplam = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        indirilen = d.get('downloaded_bytes', 0)
        
        frag_idx = d.get('fragment_index')
        frag_cnt = d.get('fragment_count')
        
        if 'rich_progress' in d['info_dict']:
            progress = d['info_dict']['rich_progress']
            task = d['info_dict']['rich_task_id']
            
            if frag_idx and frag_cnt:
                desc = f"[bold cyan][>] Parça indiriliyor: {frag_idx}/{frag_cnt}[/bold cyan]"
            else:
                desc = "[bold blue][>] Video indiriliyor...[/bold blue]"
                
            progress.update(task, completed=indirilen, total=toplam or None, description=desc)
            
    elif d['status'] == 'finished':
        if 'rich_progress' in d['info_dict']:
            progress = d['info_dict']['rich_progress']
            task = d['info_dict']['rich_task_id']
            progress.update(task, description="[bold gold1][⚡] Parçalar birleştiriliyor (MP4)...[/bold gold1]")

def videoyu_indir_gelismis(url, klasor_yolu, dosya_adi, sadece_ses=False, playlist_mi=False):
    """Gelişmiş, ham çıktıları gizleyen ve zaman aşımı korumalı indirme motoru."""
    cikis_sablonu = os.path.join(klasor_yolu, f"{dosya_adi}.%(ext)s")
    tipe_gore = "MP3" if sadece_ses else "MP4"
    
    ydl_opts = {
        'outtmpl': cikis_sablonu,
        'quiet': True,          
        'noprogress': True,     
        'no_warnings': True,
        'progress_hooks': [ytdlp_ilerleme_cubugu],
        'retries': 3,
        'fragment_retries': 5,
        'ignoreerrors': False,
        
        # ZAMAN AŞIMI GÜNCELLEMESİ: 15 saniye internet/sunucu donarsa indirmeyi durdur ve hata fırlat
        'timeout': 15,          
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'null',
        }
    }
    
    if playlist_mi:
        ydl_opts.update({'noplaylist': False, 'extract_flat': False})
    else:
        ydl_opts.update({'noplaylist': True, 'extract_flat': False})
    
    if sadece_ses:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'remux_video': 'mp4',
        })

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold cyan"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task_id = progress.add_task("[bold yellow][..] Bağlantı kuruluyor...[/bold yellow]", total=100)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                if playlist_mi and info and 'entries' in info:
                    entries = list(info['entries'])
                    progress.update(task_id, description=f"[+] {len(entries)} Şarkı Listelendi")
                    
                    for idx, entry in enumerate(entries):
                        if not entry: continue
                        v_title = entry.get('title', f"Sarki_{idx+1}")
                        entry['rich_progress'] = progress
                        entry['rich_task_id'] = task_id
                        try:
                            ydl.process_info(entry)
                            OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "BASARILI", "green"))
                        except:
                            OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "HATA", "red"))
                else:
                    v_title = info.get('title', dosya_adi) if info else dosya_adi
                    if info:
                        info['rich_progress'] = progress
                        info['rich_task_id'] = task_id
                        ydl.process_info(info)
                    OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "BASARILI", "green"))
                
                progress.update(task_id, description="[bold green][✓] Tamamlandı![/bold green]")
                return True # Başarılı bitti sinyali
            except Exception as e:
                progress.update(task_id, description="[bold red][-] Bağlantı Koptu / Zaman Aşımı![/bold red]")
                return False # Hata oluştu sinyali (Ana döngü bunu yakalayıp taze link alacak)

def m3u8_linki_yakala(url):
    yakalanan_link = None
    with console.status("[bold yellow]Gokturk Botu calisiyor, gizli kaynaklar araniyor...[/bold yellow]", spinner="bouncingBar"):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            
            def istek_kontrol(request):
                nonlocal yakalanan_link
                if ".m3u8" in request.url and "playlist" not in request.url:
                    if not yakalanan_link: 
                        yakalanan_link = request.url

            page.on("request", istek_kontrol)
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)
                
                tıklanacaklar = [
                    "div.play-button", ".play-btn", "[class*='play']", 
                    ".vjs-big-play-button", "button.jw-display-icon-container",
                    "video", "iframe", "#player", ".player"
                ]
                
                for secici in tıklanacaklar:
                    if yakalanan_link: break
                    try:
                        el = page.locator(secici).first
                        if el.is_visible():
                            el.click(force=True)
                            time.sleep(1.5)
                    except:
                        continue
                        
                if not yakalanan_link:
                    page.mouse.click(640, 360)
                    time.sleep(2)
                    if not yakalanan_link:
                        page.mouse.click(640, 360)
                        time.sleep(2)
                        
            except Exception as e:
                pass
            finally:
                browser.close()
                
    return yakalanan_link

def link_sablonu_olustur(ornek_link):
    sayilar = re.findall(r'\d+', ornek_link)
    if len(sayilar) < 2: return None, None, None, "Dizi"
    
    parcalar = [p for p in ornek_link.split('/') if p]
    dizi_adi = "Bilinmeyen Dizi"
    
    if "dizi" in parcalar:
        idx = parcalar.index("dizi")
        if idx + 1 < len(parcalar):
            dizi_adi = parcalar[idx + 1]
    else:
        for p in parcalar:
            if len(p) > 4 and ("-" in p or "_" in p) and "sezon" not in p and "bolum" not in p:
                dizi_adi = p
                break
                
    dizi_adi = dizi_adi.replace("-izle", "").replace("izle", "")
    dizi_adi = dizi_adi.replace("-", " ").replace("_", " ").strip().title()
            
    ornek_sezon, ornek_bolum = int(sayilar[-2]), int(sayilar[-1])
    
    sablon_link = ornek_link
    r_matches = list(re.finditer(r'\d+', ornek_link))
    if len(r_matches) >= 2:
        b_start, b_end = r_matches[-1].span()
        sablon_link = sablon_link[:b_start] + "{bolum}" + sablon_link[b_end:]
        
        r_matches2 = list(re.finditer(r'\d+', sablon_link))
        s_start, s_end = r_matches2[-1].span()
        sablon_link = sablon_link[:s_start] + "{sezon}" + sablon_link[s_end:]
        
    return sablon_link, ornek_sezon, ornek_bolum, dizi_adi

def final_raporu_yazdir():
    if not OPERASYON_RAPORU: return
    table = Table(title="RAPOR: GOKTURK MEDYA OPERASYONU", title_style="bold magenta")
    table.add_column("Medya Adi", style="cyan")
    table.add_column("Tur", style="yellow")
    table.add_column("Durum", style="bold")
    for idx, (isim, tur, durum, renk) in enumerate(OPERASYON_RAPORU):
        if idx > 25: 
            table.add_row("... ve digerleri ...", "-", "-", "white")
            break
        table.add_row(isim, tur, f"[{renk}]{durum}[/{renk}]")
    console.print("\n")
    console.print(table)

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    animasyonlu_baslik(" GOKTURK MEDYA ISTASYONUNA HOS GELDINIZ ")
    
    rprint("\n[bold magenta]-> Lutfen Yapmak Istediginiz Modu Secin:[/bold magenta]")
    rprint("[bold green][1][/bold green] Dizi Modu (Ornek Linkten Akilli Sezon/Bolum Araligi Indir)")
    rprint("[bold green][2][/bold green] Dogrudan Video/Film Indir (Tek Link veya Liste)")
    rprint("[bold green][3][/bold green] Muzik Indirme Modu (MP3 - YouTube & Spotify)")
    rprint("[bold cyan][4][/bold cyan] Ayarlar (Dizin Degistir)")
    
    secim = console.input("\n[bold cyan]Seciminiz (1/2/3/4): [/bold cyan]").strip()
    
    if secim == "4":
        yeni = console.input("\n[bold yellow]Yeni tam dizin yolunu girin: [/bold yellow]").strip()
        if os.path.exists(os.path.dirname(yeni)):
            ayar_kaydet(yeni)
        else:
            rprint("[bold red]Hata: Klasör yolu geçersiz![/bold red]")
        sys.exit()

    elif secim == "1":
        ornek_link = console.input("\n[bold yellow]✍ Ornek bir bolum linki yapistirin: [/bold yellow]").strip()
        sablon, o_sezon, o_bolum, dizi_adi = link_sablonu_olustur(ornek_link)
        if not sablon:
            rprint("[bold red]❌ Link yapisi cozulemedi![/bold red]"); exit()
            
        rprint(f"[bold green]✓ Algilanan Dizi:[/bold green] {dizi_adi} | [bold green]Sezon:[/bold green] {o_sezon} | [bold green]Bolum:[/bold green] {o_bolum}")
        s_bas = int(console.input("[bold cyan]> Baslangic Sezonu: [/bold cyan]"))
        b_bas = int(console.input("[bold cyan]> Baslangic Bolumu: [/bold cyan]"))
        s_bit = int(console.input("[bold red]■ Bitis Sezonu: [/bold red]"))
        b_bit = int(console.input("[bold red]■ Bitis Bölümü: [/bold red]"))
        
        current_s, current_b = s_bas, b_bas
        while True:
            url = sablon.format(sezon=current_s, bolum=current_b)
            dosya_adi = f"Sezon_{current_s}_Bolum_{current_b}"
            kayit_klasoru = klasor_hazirla(dizi_adi, f"Sezon {current_s}")
            
            # --- GELİŞMİŞ AKILLI RETRY DÖNGÜSÜ MİMARİSİ ---
            max_deneme = 3
            deneme = 0
            basarili = False
            
            while deneme < max_deneme:
                if deneme > 0:
                    rprint(f"[bold yellow][!] İndirme takıldı veya koptu. Taze link alınıp tekrar deneniyor... (Deneme {deneme+1}/{max_deneme})[/bold yellow]")
                
                m3u8_url = m3u8_linki_yakala(url)
                if m3u8_url:
                    # İndirmeyi başlat, başarısız olursa timeout mekanizması False dönecek
                    basarili = videoyu_indir_gelismis(m3u8_url, kayit_klasoru, dosya_adi, sadece_ses=False)
                    if basarili:
                        break # Eğer pürüzsüz bittiyse deneme döngüsünden çık
                else:
                    rprint(f"[bold red]❌ Siteden video kaynağı sökülemedi, {5 * (deneme+1)} sn bekleniyor...[/bold red]")
                    time.sleep(5 * (deneme+1))
                deneme += 1
                
            if not basarili:
                rprint(f"[bold red]❌ Kaynak bulunamadi veya zaman asimi kırılamadı: Sezon {current_s} Bolum {current_b}[/bold red]")
                OPERASYON_RAPORU.append((dosya_adi, "MP4", "BULUNAMADI", "red"))
            
            if current_s == s_bit and current_b == b_bit: break
            current_b += 1
            if current_b > 30 and current_s < s_bit: 
                current_s += 1
                current_b = 1

    elif secim == "2":
        rprint("\n[bold yellow]✍ Indirmek istediginiz video linklerini girin.[/bold yellow]")
        rprint("[bold dim]Baslatmak icin bos birakip Enter'a basin.[/bold dim]")
        linkler = []
        while True:
            l = console.input(f"[bold cyan]-> {len(linkler)+1}. Link: [/bold cyan]").strip()
            if not l: break
            linkler.append(l)
            
        for i, link in enumerate(linkler):
            if "youtube.com" in link or "youtu.be" in link or "instagram.com" in link or "tiktok.com" in link:
                kayit_klasoru = klasor_hazirla("Sosyal Medya Videolari")
                videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=False, playlist_mi=False)
            else:
                kayit_klasoru = klasor_hazirla("Filmler ve Tekli Videolar")
                m3u8_url = m3u8_linki_yakala(link)
                if m3u8_url:
                    dosya = link.split("/")[-2] if link.endswith('/') else link.split("/")[-1]
                    videoyu_indir_gelismis(m3u8_url, kayit_klasoru, dosya[:20], sadece_ses=False)
                else:
                    rprint("[bold red]❌ Siteden video kaynagi sokulemedi.[/bold red]")

    elif secim == "3":
        rprint("\n[bold magenta]--- 🎵 MP3 MUZIK INDIRME KANALI ---[/bold magenta]")
        rprint("[bold green][1][/bold green] Tekli YouTube Videosu (Sadece o videoyu MP3 yapar)")
        rprint("[bold green][2][/bold green] YouTube Playlist / Mix Linki (Tüm listeyi sırayla MP3 yapar)")
        rprint("[bold green][3][/bold green] Spotify Sarki / Playlist Linki (Otomatik MP3 indirir)")
        
        m_secim = console.input("\n[bold cyan]Müzik Modu Seçiniz (1/2/3): [/bold cyan]").strip()
        kayit_klasoru = klasor_hazirla("Indirilen_Muzikler")
        
        if m_secim == "1":
            link = console.input("[bold yellow]✍ Tekli YouTube Video Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)
        elif m_secim == "2":
            link = console.input("[bold yellow]✍ YouTube Playlist / Mix Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=True)
        elif m_secim == "3":
            link = console.input("[bold yellow]✍ Spotify Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(f"ytsearch:{link}", kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)

    final_raporu_yazdir()
    rprint("\n[bold green]=========================================[/bold green]")
    rprint("[bold gold1]       GOKTURK OPERASYONU BASARIYLA BITTI       [/bold gold1]")
    rprint("[bold green]=========================================[/bold green]")
    console.input("\n[bold white]Kapatmak icin Enter'a basin...[/bold white]")
