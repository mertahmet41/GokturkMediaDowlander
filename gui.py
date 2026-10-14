import os
import sys
import re
import time
import json
import shutil
import threading
import queue
import urllib.request
import urllib.parse
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

# Windows ANSI ve UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    os.system("")

# Çekirdek yardımcı fonksiyonları içe aktar
from otuken import (
    APP_NAME,
    CONFIG_DIR,
    CONFIG_FILE,
    ayar_yukle,
    ayar_kaydet,
    dosya_adi_temizle,
    link_sablonu_olustur,
    spotify_bilgisi_al,
    m3u8_linki_yakala,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class GokturkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Göktürk Medya İndirme Merkezi v6.0")
        self.geometry("960x700")
        self.minsize(850, 600)

        # Ayarları yükle
        self.ayarlar = ayar_yukle()
        self.indirme_dizini = self.ayarlar.get("indirme_dizini", str(Path.home() / "Desktop" / "Indirilen_Mediyalar"))
        if not os.path.exists(self.indirme_dizini):
            os.makedirs(self.indirme_dizini, exist_ok=True)

        self.is_downloading = False
        self.cancel_requested = False
        self.log_queue = queue.Queue()

        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        # 1. Üst Başlık ve Logo Alanı
        self.header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#1f2937", "#111827"))
        self.header_frame.pack(fill="x", padx=16, pady=(14, 8))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ GÖKTÜRK MEDYA İNDİRME MERKEZİ",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#38bdf8"
        )
        self.title_label.pack(side="left", padx=16, pady=10)

        self.badge_label = ctk.CTkLabel(
            self.header_frame,
            text="v6.0 Portable",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7",
            text_color="white",
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.badge_label.pack(side="left", padx=6, pady=10)

        self.btn_open_folder_header = ctk.CTkButton(
            self.header_frame,
            text="📁 İndirilenler Klasörü",
            width=150,
            command=self.open_download_folder,
            fg_color="#334155",
            hover_color="#475569"
        )
        self.btn_open_folder_header.pack(side="right", padx=16, pady=10)

        # 2. Ana Sekmeli Panel (Tabview)
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=6)

        self.tab_dizi = self.tabview.add("📺 Dizi İndir")
        self.tab_video = self.tabview.add("🎬 Video & Film")
        self.tab_muzik = self.tabview.add("🎵 Müzik (MP3)")
        self.tab_ayarlar = self.tabview.add("⚙️ Ayarlar")

        self.build_dizi_tab()
        self.build_video_tab()
        self.build_muzik_tab()
        self.build_ayarlar_tab()

        # 3. Alt İlerleme ve Durum Paneli
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=10)
        self.bottom_frame.pack(fill="x", padx=16, pady=(6, 14))

        self.status_label = ctk.CTkLabel(
            self.bottom_frame,
            text="Hazır. İndirmek istediğiniz modu ve linki seçin.",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=14, pady=(8, 4))

        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame, height=12)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=14, pady=4)

        # Log Görünüm Çubuğu ve Butonlar
        self.controls_subframe = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.controls_subframe.pack(fill="x", padx=14, pady=(4, 6))

        self.btn_toggle_log = ctk.CTkButton(
            self.controls_subframe,
            text="📜 Konsol Loglarını Göster / Gizle",
            width=200,
            height=28,
            command=self.toggle_log_box,
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_toggle_log.pack(side="left")

        self.btn_cancel = ctk.CTkButton(
            self.controls_subframe,
            text="⏹️ İndirmeyi Durdur",
            width=140,
            height=28,
            command=self.cancel_download,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            state="disabled"
        )
        self.btn_cancel.pack(side="right")

        # Katlanabilir Log Alanı
        self.log_box = ctk.CTkTextbox(self.bottom_frame, height=110, font=ctk.CTkFont(family="Consolas", size=11))
        # Başlangıçta gizli tutuyoruz

    # --- SEKME OLUŞTURUCULARI ---

    def build_dizi_tab(self):
        container = ctk.CTkFrame(self.tab_dizi, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        info_lbl = ctk.CTkLabel(
            container,
            text="Örnek bir bölüm linki yapıştırın; dizi adı, sezon ve bölüm otomatik ayrıştırılacaktır:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        info_lbl.pack(fill="x", pady=(0, 6))

        url_row = ctk.CTkFrame(container, fg_color="transparent")
        url_row.pack(fill="x", pady=4)

        self.entry_dizi_url = ctk.CTkEntry(
            url_row,
            placeholder_text="https://ornekdizi.com/dizi/better-call-saul-1-sezon-1-bolum",
            height=38
        )
        self.entry_dizi_url.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_dizi_url.bind("<KeyRelease>", self.on_dizi_url_changed)
        self.entry_dizi_url.bind("<FocusOut>", self.on_dizi_url_changed)

        self.btn_parse_dizi = ctk.CTkButton(
            url_row,
            text="🔍 Çözümle",
            width=100,
            height=38,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.on_dizi_url_changed
        )
        self.btn_parse_dizi.pack(side="right")

        # Algılanan Dizi Kartı
        self.detected_frame = ctk.CTkFrame(container, fg_color=("#1e293b", "#0f172a"), corner_radius=8)
        self.detected_frame.pack(fill="x", pady=10)

        dizi_name_row = ctk.CTkFrame(self.detected_frame, fg_color="transparent")
        dizi_name_row.pack(fill="x", padx=14, pady=(8, 4))
        ctk.CTkLabel(dizi_name_row, text="Dizi Adı (Klasör Adı):", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        self.entry_dizi_adi = ctk.CTkEntry(dizi_name_row, height=30, placeholder_text="Dizi Adı")
        self.entry_dizi_adi.pack(side="left", fill="x", expand=True)

        self.lbl_detected = ctk.CTkLabel(
            self.detected_frame,
            text="Algılanan Durum: Henüz link girilmedi",
            font=ctk.CTkFont(size=12),
            text_color="#38bdf8",
            anchor="w"
        )
        self.lbl_detected.pack(padx=14, pady=(2, 8), fill="x")

        # Sezon ve Bölüm Aralığı Grid
        range_frame = ctk.CTkFrame(container, fg_color="transparent")
        range_frame.pack(fill="x", pady=6)

        ctk.CTkLabel(range_frame, text="Başlangıç Sezonu:").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.entry_s_bas = ctk.CTkEntry(range_frame, width=70, height=32)
        self.entry_s_bas.insert(0, "1")
        self.entry_s_bas.grid(row=0, column=1, padx=6, pady=4)

        ctk.CTkLabel(range_frame, text="Başlangıç Bölümü:").grid(row=0, column=2, padx=6, pady=4, sticky="w")
        self.entry_b_bas = ctk.CTkEntry(range_frame, width=70, height=32)
        self.entry_b_bas.insert(0, "1")
        self.entry_b_bas.grid(row=0, column=3, padx=6, pady=4)

        ctk.CTkLabel(range_frame, text="Bitiş Sezonu:").grid(row=0, column=4, padx=6, pady=4, sticky="w")
        self.entry_s_bit = ctk.CTkEntry(range_frame, width=70, height=32)
        self.entry_s_bit.insert(0, "1")
        self.entry_s_bit.grid(row=0, column=5, padx=6, pady=4)

        ctk.CTkLabel(range_frame, text="Bitiş Bölümü:").grid(row=0, column=6, padx=6, pady=4, sticky="w")
        self.entry_b_bit = ctk.CTkEntry(range_frame, width=70, height=32)
        self.entry_b_bit.insert(0, "10")
        self.entry_b_bit.grid(row=0, column=7, padx=6, pady=4)

        self.btn_start_dizi = ctk.CTkButton(
            container,
            text="🚀 Bölümleri Sırayla İndir",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            command=self.start_dizi_download
        )
        self.btn_start_dizi.pack(fill="x", pady=(16, 0))

    def build_video_tab(self):
        container = ctk.CTkFrame(self.tab_video, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        lbl = ctk.CTkLabel(
            container,
            text="İndirmek istediğiniz video linklerini alt alta yapıştırın (YouTube, Instagram, TikTok, Film Siteleri):",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        lbl.pack(fill="x", pady=(0, 6))

        self.txt_video_links = ctk.CTkTextbox(container, height=130, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_video_links.pack(fill="x", pady=4)

        opt_frame = ctk.CTkFrame(container, fg_color="transparent")
        opt_frame.pack(fill="x", pady=8)

        ctk.CTkLabel(opt_frame, text="Kalite / Format:").pack(side="left", padx=(0, 8))
        self.combo_video_quality = ctk.CTkComboBox(
            opt_frame,
            values=["En İyi Kalite (Best MP4)", "1080p Full HD", "720p HD", "480p SD", "Sadece Ses (MP3)"],
            width=220
        )
        self.combo_video_quality.set("En İyi Kalite (Best MP4)")
        self.combo_video_quality.pack(side="left", padx=4)

        self.btn_start_video = ctk.CTkButton(
            container,
            text="📥 Seçilen Videoları İndir",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.start_video_download
        )
        self.btn_start_video.pack(fill="x", pady=(14, 0))

    def build_muzik_tab(self):
        container = ctk.CTkFrame(self.tab_muzik, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        lbl = ctk.CTkLabel(
            container,
            text="YouTube video linki, YouTube Playlist linki veya Spotify şarkı/playlist linki yapıştırın:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        lbl.pack(fill="x", pady=(0, 6))

        self.entry_music_url = ctk.CTkEntry(
            container,
            placeholder_text="https://open.spotify.com/track/... veya https://www.youtube.com/watch?v=...",
            height=38
        )
        self.entry_music_url.pack(fill="x", pady=4)

        opt_frame = ctk.CTkFrame(container, fg_color="transparent")
        opt_frame.pack(fill="x", pady=8)

        ctk.CTkLabel(opt_frame, text="Ses Kalitesi (Bitrate):").pack(side="left", padx=(0, 8))
        self.combo_audio_bitrate = ctk.CTkComboBox(
            opt_frame,
            values=["320 kbps (Yüksek Kalite)", "192 kbps (Önerilen)", "128 kbps (Hızlı İndirme)"],
            width=220
        )
        self.combo_audio_bitrate.set("192 kbps (Önerilen)")
        self.combo_audio_bitrate.pack(side="left", padx=4)

        self.btn_start_music = ctk.CTkButton(
            container,
            text="🎵 MP3 Olarak Dönüştür ve İndir",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=self.start_music_download
        )
        self.btn_start_music.pack(fill="x", pady=(14, 0))

    def build_ayarlar_tab(self):
        container = ctk.CTkFrame(self.tab_ayarlar, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            container,
            text="İndirme Konumu:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(4, 4))

        path_frame = ctk.CTkFrame(container, fg_color="transparent")
        path_frame.pack(fill="x", pady=4)

        self.entry_save_path = ctk.CTkEntry(path_frame, height=36)
        self.entry_save_path.insert(0, self.indirme_dizini)
        self.entry_save_path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_browse = ctk.CTkButton(
            path_frame,
            text="📂 Gözat",
            width=100,
            command=self.browse_folder
        )
        self.btn_browse.pack(side="right")

        self.switch_subfolders = ctk.CTkSwitch(
            container,
            text="Medyaları kategorilerine göre alt klasörlere ayır (Diziler, Filmler, Müzikler)"
        )
        self.switch_subfolders.select()
        self.switch_subfolders.pack(anchor="w", pady=(16, 8))

        self.btn_save_settings = ctk.CTkButton(
            container,
            text="💾 Ayarları Kaydet",
            width=160,
            height=36,
            command=self.save_settings,
            fg_color="#059669",
            hover_color="#047857"
        )
        self.btn_save_settings.pack(anchor="w", pady=10)

    # --- YARDIMCI VE OLAY YÖNETİCİLERİ ---

    def log(self, message):
        """Thread-safe log ekleme."""
        self.log_queue.put(message)

    def check_queue(self):
        """Kuyruktaki log ve durum mesajlarını arayüze aktarır."""
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            if isinstance(msg, dict):
                if "status" in msg:
                    self.status_label.configure(text=msg["status"])
                if "progress" in msg:
                    self.progress_bar.set(msg["progress"])
            else:
                self.log_box.insert("end", f"{msg}\n")
                self.log_box.see("end")
        self.after(100, self.check_queue)

    def toggle_log_box(self):
        if self.log_box.winfo_ismapped():
            self.log_box.pack_forget()
        else:
            self.log_box.pack(fill="x", padx=14, pady=(0, 8))

    def browse_folder(self):
        secilen = filedialog.askdirectory(initialdir=self.indirme_dizini)
        if secilen:
            self.entry_save_path.delete(0, "end")
            self.entry_save_path.insert(0, secilen)

    def save_settings(self):
        yeni = self.entry_save_path.get().strip()
        if yeni and os.path.exists(yeni):
            self.indirme_dizini = yeni
            ayar_kaydet(yeni)
            messagebox.showinfo("Başarılı", "İndirme klasörü başarıyla güncellendi!")
        else:
            messagebox.showerror("Hata", "Lütfen geçerli bir klasör yolu belirtin.")

    def open_download_folder(self):
        if os.path.exists(self.indirme_dizini):
            os.startfile(self.indirme_dizini)
        else:
            messagebox.showwarning("Uyarı", "İndirme klasörü henüz mevcut değil.")

    def on_dizi_url_changed(self, event=None):
        url = self.entry_dizi_url.get().strip()
        if len(url) > 10:
            sablon, s, b, dizi_adi = link_sablonu_olustur(url)
            if sablon and b is not None:
                self.entry_dizi_adi.delete(0, "end")
                self.entry_dizi_adi.insert(0, dizi_adi)
                s_val = s if s is not None else 1
                self.lbl_detected.configure(text=f"✓ Çözümlendi: Dizi: {dizi_adi} | Sezon: {s_val} | Bölüm: {b}")
                self.entry_s_bas.delete(0, "end")
                self.entry_s_bas.insert(0, str(s_val))
                self.entry_b_bas.delete(0, "end")
                self.entry_b_bas.insert(0, str(b))
                self.entry_s_bit.delete(0, "end")
                self.entry_s_bit.insert(0, str(s_val))
                self.entry_b_bit.delete(0, "end")
                self.entry_b_bit.insert(0, str(b + 5))
            else:
                self.lbl_detected.configure(text="[!] Link formatından bölüm algılanamadı, lütfen geçerli bir link girin.")

    def set_download_state(self, downloading=True):
        self.is_downloading = downloading
        self.cancel_requested = False
        if downloading:
            self.btn_cancel.configure(state="normal")
            self.btn_start_dizi.configure(state="disabled")
            self.btn_start_video.configure(state="disabled")
            self.btn_start_music.configure(state="disabled")
        else:
            self.btn_cancel.configure(state="disabled")
            self.btn_start_dizi.configure(state="normal")
            self.btn_start_video.configure(state="normal")
            self.btn_start_music.configure(state="normal")

    def cancel_download(self):
        if self.is_downloading:
            self.cancel_requested = True
            self.log("[!] İndirme iptali istendi. Mevcut işlem bitince durdurulacak...")
            self.status_label.configure(text="İndirme iptal ediliyor...")

    # --- İNDİRME MOTORLARI (ARKA PLAN THREAD) ---

    def run_in_thread(self, target_func, *args):
        self.set_download_state(True)
        t = threading.Thread(target=target_func, args=args, daemon=True)
        t.start()

    def start_dizi_download(self):
        url = self.entry_dizi_url.get().strip()
        if not url:
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir bölüm linki girin.")
            return

        sablon, o_s, o_b, oto_dizi_adi = link_sablonu_olustur(url)
        if not sablon:
            messagebox.showerror("Hata", "Link formatından sezon ve bölüm çıkarılamadı!")
            return

        dizi_adi = self.entry_dizi_adi.get().strip() or oto_dizi_adi

        try:
            s_bas = int(self.entry_s_bas.get().strip())
            b_bas = int(self.entry_b_bas.get().strip())
            s_bit = int(self.entry_s_bit.get().strip())
            b_bit = int(self.entry_b_bit.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Lütfen sezon ve bölüm için geçerli sayılar girin.")
            return

        self.run_in_thread(self._worker_dizi, sablon, dizi_adi, s_bas, b_bas, s_bit, b_bit)

    def _worker_dizi(self, sablon, dizi_adi, s_bas, b_bas, s_bit, b_bit):
        self.log(f"[BAŞLATILDI] Dizi İndirme Operasyonu: {dizi_adi}")
        curr_s, curr_b = s_bas, b_bas
        ardisik_hata = 0

        while not self.cancel_requested:
            try:
                url = sablon.format(sezon=curr_s, bolum=curr_b)
            except Exception:
                url = sablon.replace("{sezon}", str(curr_s)).replace("{bolum}", str(curr_b))

            dosya_adi = f"Sezon_{curr_s}_Bolum_{curr_b}"
            klasor = os.path.join(self.indirme_dizini, dosya_adi_temizle(dizi_adi), f"Sezon {curr_s}")
            os.makedirs(klasor, exist_ok=True)

            self.log_queue.put({"status": f"Bağlantı taranıyor: Sezon {curr_s} Bölüm {curr_b}..."})
            self.log(f"[>] Kaynak taranıyor: Sezon {curr_s} Bölüm {curr_b}...")

            m3u8_url = m3u8_linki_yakala(url)
            if m3u8_url:
                self.log(f"[✓] Medya akışı yakalandı. İndiriliyor...")
                basarili = self._indir_ytdlp(m3u8_url, klasor, dosya_adi, sadece_ses=False)
                if basarili:
                    self.log(f"[TAMAMLANDI] Sezon {curr_s} Bölüm {curr_b} başarıyla indirildi.")
                    ardisik_hata = 0
                else:
                    self.log(f"[-] İndirme başarısız: Sezon {curr_s} Bölüm {curr_b}")
                    ardisik_hata += 1
            else:
                self.log(f"[..] Doğrudan bağlantı ile deneniyor...")
                basarili = self._indir_ytdlp(url, klasor, dosya_adi, sadece_ses=False)
                if basarili:
                    self.log(f"[TAMAMLANDI] Sezon {curr_s} Bölüm {curr_b} başarıyla indirildi.")
                    ardisik_hata = 0
                else:
                    self.log(f"[!] Kaynak bulunamadı: Sezon {curr_s} Bölüm {curr_b}")
                    ardisik_hata += 1

            if curr_s >= s_bit and curr_b >= b_bit:
                break

            curr_b += 1
            if ardisik_hata >= 3 and curr_s < s_bit:
                self.log(f"[ℹ️] 3 ardışık bölüm bulunamadı, Sezon {curr_s + 1}'e geçiliyor.")
                curr_s += 1
                curr_b = 1
                ardisik_hata = 0

        self.log_queue.put({"status": "Dizi indirme operasyonu tamamlandı!", "progress": 1.0})
        self.log("[BİTTİ] Operasyon sonlandı.")
        self.set_download_state(False)

    def start_video_download(self):
        metin = self.txt_video_links.get("1.0", "end").strip()
        if not metin:
            messagebox.showwarning("Eksik Bilgi", "Lütfen en az bir video linki girin.")
            return
        linkler = [l.strip() for l in metin.splitlines() if l.strip()]
        sadece_ses = "Sadece Ses" in self.combo_video_quality.get()
        self.run_in_thread(self._worker_video, linkler, sadece_ses)

    def _worker_video(self, linkler, sadece_ses):
        toplam = len(linkler)
        self.log(f"[BAŞLATILDI] Toplu Video İndirme: {toplam} link işlenecek.")
        kalite_secim = self.combo_video_quality.get()

        for i, link in enumerate(linkler):
            if self.cancel_requested:
                break

            self.log_queue.put({"status": f"İşleniyor ({i+1}/{toplam}): {link[:50]}..."})
            self.log(f"[>] Link {i+1}/{toplam} indiriliyor: {link}")

            # Sosyal medya veya tekil video
            if any(dom in link for dom in ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", "x.com"]):
                klasor = os.path.join(self.indirme_dizini, "Sosyal Medya Videolari")
                os.makedirs(klasor, exist_ok=True)
                basarili = self._indir_ytdlp(link, klasor, "%(title)s", sadece_ses=sadece_ses, format_secim=kalite_secim)
                if basarili:
                    self.log(f"[✓] Başarıyla tamamlandı: Link {i+1}")
            else:
                klasor = os.path.join(self.indirme_dizini, "Filmler ve Videolar")
                os.makedirs(klasor, exist_ok=True)
                ham_isim = link.rstrip("/").split("/")[-1]
                temiz = dosya_adi_temizle(ham_isim, varsayilan=f"Video_{i+1}")
                basarili = self._indir_ytdlp(link, klasor, temiz[:35], sadece_ses=sadece_ses, format_secim=kalite_secim)
                if not basarili:
                    m3u8_url = m3u8_linki_yakala(link)
                    if m3u8_url:
                        basarili = self._indir_ytdlp(m3u8_url, klasor, temiz[:35], sadece_ses=sadece_ses, format_secim=kalite_secim)
                    else:
                        self.log("[!] Siteden video akışı yakalanamadı.")
                if basarili:
                    self.log(f"[✓] Başarıyla tamamlandı: Link {i+1}")

        self.log_queue.put({"status": "Tüm videolar indirildi!", "progress": 1.0})
        self.log("[BİTTİ] Toplu video indirme tamamlandı.")
        self.set_download_state(False)

    def start_music_download(self):
        url = self.entry_music_url.get().strip()
        if not url:
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir YouTube veya Spotify linki girin.")
            return

        bitrate_secim = self.combo_audio_bitrate.get()
        bitrate = "192"
        if "320" in bitrate_secim:
            bitrate = "320"
        elif "128" in bitrate_secim:
            bitrate = "128"

        self.run_in_thread(self._worker_music, url, bitrate)

    def _worker_music(self, url, bitrate):
        self.log(f"[BAŞLATILDI] Müzik İndirme: {url}")
        klasor = os.path.join(self.indirme_dizini, "Indirilen_Muzikler")
        os.makedirs(klasor, exist_ok=True)

        hedef_arama = url
        is_playlist = "playlist" in url or "list=" in url

        if "spotify.com" in url:
            self.log_queue.put({"status": "Spotify parça bilgisi çözümleniyor..."})
            cozulen = spotify_bilgisi_al(url)
            self.log(f"[✓] Spotify Parçası: {cozulen}")
            hedef_arama = f"ytsearch1:{cozulen}"

        self.log_queue.put({"status": "Müzik indiriliyor ve MP3 formatına dönüştürülüyor..."})
        basarili = self._indir_ytdlp(hedef_arama, klasor, "%(title)s", sadece_ses=True, bitrate=bitrate, playlist_mi=is_playlist)

        if basarili:
            self.log_queue.put({"status": "Müzik başarıyla indirildi!", "progress": 1.0})
            self.log("[TAMAMLANDI] MP3 dosyası hazır.")
        else:
            self.log_queue.put({"status": "Müzik indirme başarısız oldu.", "progress": 0.0})

        self.set_download_state(False)

    def _indir_ytdlp(self, url, klasor, dosya_adi, sadece_ses=False, bitrate="192", playlist_mi=False, format_secim="En İyi Kalite (Best MP4)"):
        cikis = os.path.join(klasor, f"{dosya_adi}.%(ext)s")

        def progress_hook(d):
            if self.cancel_requested:
                raise Exception("Kullanıcı tarafından iptal edildi.")

            status = d.get('status')
            if status == 'downloading':
                toplam = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                indirilen = d.get('downloaded_bytes', 0)
                hiz = d.get('speed') or 0
                hiz_str = f"{hiz / 1024 / 1024:.1f} MB/s" if hiz else "--"

                if toplam > 0:
                    yuzde = indirilen / toplam
                    yuzde_str = f"%{yuzde * 100:.1f}"
                    self.log_queue.put({
                        "progress": yuzde,
                        "status": f"İndiriliyor: {yuzde_str} ({hiz_str})"
                    })
                else:
                    self.log_queue.put({
                        "progress": 0.5,
                        "status": f"İndiriliyor: {indirilen / 1024 / 1024:.1f} MB ({hiz_str})"
                    })
            elif status == 'finished':
                self.log_queue.put({
                    "progress": 1.0,
                    "status": "Dönüştürülüyor / Birleştiriliyor..."
                })

        js_runtimes = {}
        if shutil.which("node"):
            js_runtimes["node"] = {}
        if shutil.which("deno"):
            js_runtimes["deno"] = {}

        ydl_opts = {
            'outtmpl': cikis,
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'retries': 3,
            'fragment_retries': 5,
            'timeout': 30,
            'progress_hooks': [progress_hook],
            'extractor_args': {
                'youtube': {
                    'player_client': ['web_creator', 'ios', 'android', 'web', 'mweb']
                }
            }
        }
        if js_runtimes:
            ydl_opts['js_runtimes'] = js_runtimes

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
                    'preferredquality': bitrate,
                }],
            })
        else:
            if "1080p" in format_secim:
                fmt = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
            elif "720p" in format_secim:
                fmt = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
            elif "480p" in format_secim:
                fmt = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            else:
                fmt = 'bestvideo+bestaudio/best'

            ydl_opts.update({
                'format': fmt,
                'merge_output_format': 'mp4',
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            return True
        except Exception as e:
            self.log(f"[HATA] {e}")
            return False


def main():
    app = GokturkApp()
    app.mainloop()


if __name__ == "__main__":
    main()
