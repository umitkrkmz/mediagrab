# Katkı Rehberi / Contributing

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)**

---

## Türkçe

MediaGrab tek kişilik, gönüllü bakım altında bir proje. PR'lar memnuniyetle karşılanır; büyük bir değişikliğe başlamadan önce bir issue açıp yaklaşımı konuşmak, boşa emek harcamanızı önler.

### Geliştirme ortamı

Kurulum ve test komutları için [Kılavuz → Elle Kurulum](docs/README.tr.md#yöntem-b-elle-kurulum-kaynak-koddan-her-platform) ve [Kılavuz → Testler](docs/README.tr.md#testler) bölümlerine bakın. Özetle: sanal ortam, `pip install -r requirements-dev.txt`, `pytest`.

### Mimari kurallar (PR'lar bunlara uymalı)

Bunlar tercih değil, projenin şu anki tasarımının dayandığı temeller — bir PR bunlardan birini bozarsa muhtemelen geri çevrilir veya değişiklik istenir:

- **yt-dlp kullanımı yalnızca `mediagrab/downloader.py` içinde kalır.** Başka hiçbir dosya `yt_dlp`'yi import etmez. Bu sınırı `mediagrab/deps.py` içindeki not da açıklıyor.
- **Veritabanı yok, hesap sistemi yok.** Durum düz JSON dosyalarında tutulur (`channels.json`, `settings.json`). Yeni bir kalıcı veri türü gerekiyorsa aynı deseni izleyin (bkz. `mediagrab/store.py`), yeni bir bağımlılık eklemeyin.
- **Her kullanıcıya görünen metin iki dilde de bulunmalı.** `mediagrab/i18n.py`'deki `tr` ve `en` sözlükleri aynı anahtar kümesine sahip olmalı. `test_i18n.py` bunu zaten doğruluyor; yeni bir arayüz metni eklerken ikisini birden yazın.
- **Kullanıcı verisine (indirilenler klasörü, channels.json, settings.json) dokunan her değişiklik önce yedeklenebilir/geri alınabilir olmalı.** Bkz. `mediagrab/downloader.py`'deki `_backup_existing_outputs`/`_restore_backups` deseni.
- **Yeni bir bağımlılık eklemeden önce bir kez daha düşünün.** Bu proje standart kütüphaneye ve mevcut bağımlılıklara (`yt-dlp`, `ffmpeg`, `fastapi`, `mutagen`) kasıtlı olarak sadık kalıyor.

### Testler

Yeni bir davranış eklerken bir test de ekleyin. "Çalıştığını gördüm" yeterli değil — testin gerçekten o hatayı yakaladığını görmek için, düzeltmeyi geçici olarak geri alıp testin kırmızıya döndüğünü doğrulamanızı öneririz (mutasyon testi). Bu depodaki testlerin çoğu bu yöntemle yazıldı.

### Commit mesajları

Kısa, "ne" değil "neden" odaklı. Geçmiş commit'lere bakıp üslubu görebilirsiniz.

### Yayın yaparken (bakımcı notu)

Proje düzenli yayın almıyor; adımlar uzun bir aradan sonra hatırlanmak zorunda kalınmasın diye burada.

1. **Sürümü artırın.** `mediagrab/__init__.py` içindeki `__version__` ile `CHANGELOG.md`'nin en üstteki girdisi (TR ve EN) aynı olmalı; uyuşmazsa `tests/test_version.py` kırmızıya döner. CHANGELOG'daki tarihi yayın gününe çekin.
2. **README rozetini güncelleyin.** `README.md`'nin en üstündeki "Latest Release" bağlantısı.
3. **Etiketlemeden önce iki iş akışını elle çalıştırın.** GitHub → Actions → "Release" ve "Docker" → *Run workflow*, `master` dalı seçili. Bu deneme yayın yapmaz: Release testleri koşup exe'yi derler (çalıştırmanın sayfasından indirip elle deneyebilirsiniz), Docker imajı derleyip container'ı ayağa kaldırır.
4. **Çalıştırmaların uyarılarına bakın.** Özet sayfasındaki sarı uyarılar (kullanımdan kalkan bir Node sürümü, değişecek bir runner görüntüsü vb.) bir sonraki yayında hataya dönüşebilir; şimdi düzeltin. Runner'lar (`ubuntu-24.04`, `windows-2025`) ve PyInstaller sürümü bilerek sabitli. Yükseltmek gerekirse bilinçli yapın, PyInstaller'ı yükselttiyseniz exe'yi elle deneyin.
5. **Etiketleyin.** `git tag vX.Y.Z` ve `git push origin vX.Y.Z`. Release exe'yi GitHub Release'e, Docker imajı `ghcr.io/umitkrkmz/mediagrab`'a (`latest` ve sürüm etiketiyle) yayımlar.

**Docker taban imajı:** Her yayın `python:3.12-slim`'in o günkü güncel hâliyle derlenir, ayrıca bir şey yapmak gerekmez. Yayınlar arası uzun süre geçer ve taban imajda ciddi bir güvenlik açığı duyulursa: Actions → "Docker" → *Run workflow* → "Use workflow from" kısmında son sürüm etiketini (`vX.Y.Z`) seçin. İmaj taze tabanla yeniden derlenip aynı etiketlerle yeniden yayımlanır. Bu bilerek otomatikleştirilmedi: kimsenin izlemediği otomatik bir derleme bozuk bir `latest` yayımlayabilir.

---

## English

MediaGrab is a one-person, volunteer-maintained project. PRs are welcome; for anything non-trivial, opening an issue first to discuss the approach saves you wasted effort.

### Development setup

See [Guide → Manual Install](docs/README.en.md#method-b-manual-install-from-source-any-platform) and [Guide → Tests](docs/README.en.md#tests) for setup and test commands. In short: a virtualenv, `pip install -r requirements-dev.txt`, `pytest`.

### Architectural rules (PRs need to follow these)

These aren't preferences — they're what the current design rests on. A PR that breaks one of these will likely be sent back for changes:

- **yt-dlp usage stays inside `mediagrab/downloader.py` only.** No other file imports `yt_dlp`. The note in `mediagrab/deps.py` documents this boundary too.
- **No database, no account system.** State lives in plain JSON files (`channels.json`, `settings.json`). If you need a new kind of persisted data, follow that same pattern (see `mediagrab/store.py`) rather than adding a new dependency.
- **Every user-facing string exists in both languages.** The `tr` and `en` dicts in `mediagrab/i18n.py` must have the same key set. `test_i18n.py` already checks this — add both when you add UI text.
- **Anything touching user data (the downloads folder, channels.json, settings.json) must be backup/restorable first.** See the `_backup_existing_outputs`/`_restore_backups` pattern in `mediagrab/downloader.py`.
- **Think twice before adding a new dependency.** This project deliberately stays close to the standard library and its existing dependencies (`yt-dlp`, `ffmpeg`, `fastapi`, `mutagen`).

### Tests

Add a test with any new behavior. "I saw it work" isn't enough — we recommend temporarily reverting your fix and confirming the test goes red, to actually prove it catches the bug (mutation testing). Most tests in this repo were written this way.

### Commit messages

Short, focused on *why* rather than *what*. Check past commits for the style.

### Cutting a release (maintainer note)

The project doesn't release on a schedule, so the steps live here rather than in anyone's memory.

1. **Bump the version.** `__version__` in `mediagrab/__init__.py` must match the newest `CHANGELOG.md` entry (both TR and EN); `tests/test_version.py` goes red if they disagree. Set the CHANGELOG date to release day.
2. **Update the README badge.** The "Latest Release" link at the top of `README.md`.
3. **Run both workflows by hand before tagging.** GitHub → Actions → "Release" and "Docker" → *Run workflow*, with the `master` branch selected. This dry run publishes nothing: Release runs the tests and builds the exe (downloadable from the run page to try by hand), Docker builds the image and starts a container.
4. **Read the runs' warnings.** Yellow annotations on the summary page (a Node version being retired, a runner image about to change, etc.) can become failures by the next release; fix them now. The runners (`ubuntu-24.04`, `windows-2025`) and the PyInstaller version are pinned on purpose. Bump them deliberately, and try the exe by hand after a PyInstaller bump.
5. **Tag it.** `git tag vX.Y.Z` and `git push origin vX.Y.Z`. Release publishes the exe to a GitHub Release, Docker publishes the image to `ghcr.io/umitkrkmz/mediagrab` (as `latest` and the version tag).

**Docker base image:** every release is built on that day's `python:3.12-slim`, so nothing else is needed. If a long time passes between releases and a serious base-image vulnerability comes up: Actions → "Docker" → *Run workflow* → pick the latest version tag (`vX.Y.Z`) under "Use workflow from". The image is rebuilt on a fresh base and re-published under the same tags. Deliberately not automated: an unattended automatic build can publish a broken `latest` with nobody watching.
