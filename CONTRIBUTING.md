# Katkı Rehberi / Contributing

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)**

---

## Türkçe

MediaGrab tek kişilik, gönüllü bakım altında bir proje. PR'lar memnuniyetle karşılanır; büyük bir değişikliğe başlamadan önce bir issue açıp yaklaşımı konuşmak, boşa emek harcamanızı önler.

### Geliştirme ortamı

Kurulum ve test komutları için [README → Elle Kurulum](README.md#yöntem-b-elle-kurulum-kaynak-koddan-her-platform) ve [README → Testler](README.md#testler) bölümlerine bakın. Özetle: sanal ortam, `pip install -r requirements-dev.txt`, `pytest`.

### Mimari kurallar (PR'lar bunlara uymalı)

Bunlar tercih değil, projenin şu anki tasarımının dayandığı temeller — bir PR bunlardan birini bozarsa muhtemelen geri çevrilir veya değişiklik istenir:

- **yt-dlp kullanımı yalnızca `mediagrab/downloader.py` içinde kalır.** Başka hiçbir dosya `yt_dlp`'yi import etmez. Bu sınırı `mediagrab/deps.py` içindeki not da açıklıyor.
- **Veritabanı yok, hesap sistemi yok.** Durum düz JSON dosyalarında tutulur (`channels.json`, `settings.json`). Yeni bir kalıcı veri türü gerekiyorsa aynı deseni izleyin (bkz. `mediagrab/store.py`), yeni bir bağımlılık eklemeyin.
- **Her kullanıcıya görünen metin iki dilde de bulunmalı.** `mediagrab/i18n.py`'deki `tr` ve `en` sözlükleri aynı anahtar kümesine sahip olmalı. `test_i18n.py` bunu zaten doğruluyor; yeni bir arayüz metni eklerken ikisini birden yazın.
- **Kullanıcı verisine (indirilenler klasörü, channels.json, settings.json) dokunan her değişiklik önce yedeklenebilir/geri alınabilir olmalı.** Bkz. `_stash_user_data`/`_restore_backups` desenleri.
- **Yeni bir bağımlılık eklemeden önce bir kez daha düşünün.** Bu proje standart kütüphaneye ve mevcut bağımlılıklara (`yt-dlp`, `ffmpeg`, `fastapi`, `mutagen`) kasıtlı olarak sadık kalıyor.

### Testler

Yeni bir davranış eklerken bir test de ekleyin. "Çalıştığını gördüm" yeterli değil — testin gerçekten o hatayı yakaladığını görmek için, düzeltmeyi geçici olarak geri alıp testin kırmızıya döndüğünü doğrulamanızı öneririz (mutasyon testi). Bu depodaki testlerin çoğu bu yöntemle yazıldı.

### Commit mesajları

Kısa, "ne" değil "neden" odaklı. Geçmiş commit'lere bakıp üslubu görebilirsiniz.

---

## English

MediaGrab is a one-person, volunteer-maintained project. PRs are welcome; for anything non-trivial, opening an issue first to discuss the approach saves you wasted effort.

### Development setup

See [README → Manual Install](README.md#method-b-manual-install-from-source-any-platform) and [README → Tests](README.md#tests) for setup and test commands. In short: a virtualenv, `pip install -r requirements-dev.txt`, `pytest`.

### Architectural rules (PRs need to follow these)

These aren't preferences — they're what the current design rests on. A PR that breaks one of these will likely be sent back for changes:

- **yt-dlp usage stays inside `mediagrab/downloader.py` only.** No other file imports `yt_dlp`. The note in `mediagrab/deps.py` documents this boundary too.
- **No database, no account system.** State lives in plain JSON files (`channels.json`, `settings.json`). If you need a new kind of persisted data, follow that same pattern (see `mediagrab/store.py`) rather than adding a new dependency.
- **Every user-facing string exists in both languages.** The `tr` and `en` dicts in `mediagrab/i18n.py` must have the same key set. `test_i18n.py` already checks this — add both when you add UI text.
- **Anything touching user data (the downloads folder, channels.json, settings.json) must be backup/restorable first.** See the `_stash_user_data`/`_restore_backups` patterns.
- **Think twice before adding a new dependency.** This project deliberately stays close to the standard library and its existing dependencies (`yt-dlp`, `ffmpeg`, `fastapi`, `mutagen`).

### Tests

Add a test with any new behavior. "I saw it work" isn't enough — we recommend temporarily reverting your fix and confirming the test goes red, to actually prove it catches the bug (mutation testing). Most tests in this repo were written this way.

### Commit messages

Short, focused on *why* rather than *what*. Check past commits for the style.
