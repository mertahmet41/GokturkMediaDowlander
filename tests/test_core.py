import os
import sys
import unittest
from pathlib import Path

# Proje ana dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from otuken import (
    dosya_adi_temizle,
    link_sablonu_olustur,
    make_progress_hook,
    spotify_bilgisi_al,
    ayar_yukle,
    ayar_kaydet,
    CONFIG_FILE,
)


class TestGokturkCore(unittest.TestCase):
    def test_dosya_adi_temizle(self):
        # Soru işareti ve Windows geçersiz karakterleri
        self.assertEqual(dosya_adi_temizle("https://example.com/video?token=12345"), "video")
        self.assertEqual(dosya_adi_temizle('te:st*fi/le?"na<me>|'), "testfilename")
        # yt-dlp şablonu korunmalı
        self.assertEqual(dosya_adi_temizle("%(title)s"), "%(title)s")
        # Boş girdide varsayılan
        self.assertEqual(dosya_adi_temizle("", varsayilan="dosya"), "dosya")

    def test_link_sablonu_olustur(self):
        url = "https://dizipal.com/dizi/breaking-bad-1-sezon-2-bolum"
        sablon, s, b, dizi = link_sablonu_olustur(url)
        self.assertEqual(s, 1)
        self.assertEqual(b, 2)
        self.assertEqual(dizi, "Breaking Bad")
        self.assertIn("{sezon}", sablon)
        self.assertIn("{bolum}", sablon)

        url2 = "https://ornek.com/dizi/better-call-saul/sezon-3/bolum-5"
        sablon2, s2, b2, dizi2 = link_sablonu_olustur(url2)
        self.assertEqual(s2, 3)
        self.assertEqual(b2, 5)
        self.assertEqual(dizi2, "Better Call Saul")

    def test_make_progress_hook_no_crash(self):
        # Sahte bir progress nesnesi
        class DummyProgress:
            def __init__(self):
                self.calls = []

            def update(self, task_id, **kwargs):
                self.calls.append((task_id, kwargs))

        p = DummyProgress()
        hook = make_progress_hook(p, "task_1")

        # 1. info_dict olmayan veri (Eski sürümde KeyError verip patlayan durum)
        hook({'status': 'downloading', 'downloaded_bytes': 500, 'total_bytes': 1000})
        self.assertTrue(len(p.calls) > 0)

        # 2. Fragment indirme
        hook({'status': 'downloading', 'fragment_index': 1, 'fragment_count': 10})
        self.assertTrue(len(p.calls) > 1)

        # 3. Finished durumu
        hook({'status': 'finished'})
        self.assertTrue(len(p.calls) > 2)

    def test_spotify_bilgisi_al(self):
        track_url = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
        res = spotify_bilgisi_al(track_url)
        # Never Gonna Give You Up dönmeli
        self.assertIn("Never Gonna Give You Up", res)

    def test_ayar_sistemi(self):
        ayarlar = ayar_yukle()
        self.assertIn("indirme_dizini", ayarlar)


if __name__ == "__main__":
    unittest.main()
