# AGENTS.md

**[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)**

Bu dosya, bu depoda çalışan yapay zeka kodlama araçları (Claude Code, Codex, Cursor, Copilot vb.) içindir. `README.md` kullanıcılar için, `CONTRIBUTING.md` insan katkıcılar için — bu dosya sizin için.
This file is for AI coding tools working in this repo (Claude Code, Codex, Cursor, Copilot, etc.). `README.md` is for users, `CONTRIBUTING.md` is for human contributors — this one is for you.

---

## Türkçe

### Bu projede yapay zekanın rolü

MediaGrab büyük ölçüde bir yapay zeka ile (Claude) birlikte, gerçek zamanlı diyalog hâlinde geliştirildi — kod öneri olarak değil, adım adım uygulanan ve test edilen değişiklikler olarak. Bunu gizlemiyoruz; tam tersi, bu dosyanın kendisi o sürecin bir ürünü.

Bu, şu anlama gelmiyor: "yapay zeka ne yaparsa kabul." Bu depoda geçerli olan sınır şu:

- **Hiçbir commit veya push, o an açık bir onay olmadan yapılmaz.** Daha önce onaylanmış olması bir sonraki sefer için onay sayılmaz.
- **"Düzeltildi" iddiası gerçek bir testle desteklenmeden kabul edilmez.** Tercih edilen yöntem: düzeltmeyi geçici olarak geri alıp testin kırmızıya döndüğünü görmek (mutasyon testi) — testin gerçekten o hatayı yakaladığını kanıtlamak için.
- **Yıkıcı veya geri alınamaz işlemler** (`git push --force`, `rm -rf`, kullanıcı verisini silme) **önce açıkça sorulur.**
- Bir yapay zeka aracının önerdiği her değişiklik, birleştirilmeden önce bir insan tarafından gözden geçirilir.

Bir PR'da yapay zeka aracı kullandıysanız bunu gizlemenize gerek yok — ama commit'in kalitesinden ve doğruluğundan siz sorumlusunuz, aracın "çalışıyor" demesi yeterli değil.

### Derleme / test komutları

```bash
pip install -r requirements-dev.txt
pytest
```

Node.js kuruluysa JS testleri de çalışır; değilse otomatik atlanır. Ayrıntı için [README → Testler](README.md#testler).

### Bu depoya özgü kısıtlar

Bunlar üslup tercihi değil — kodun şu anki tasarımı bunlara dayanıyor. Bir değişiklik bunlardan birini bozuyorsa, testler geçse bile muhtemelen yanlıştır:

- **`yt_dlp` yalnızca `mediagrab/downloader.py` içinde import edilir.** Başka hiçbir dosyada değil. Doğrulama: `grep -rn "^import yt_dlp\|^from yt_dlp" mediagrab/*.py` tek dosya döndürmeli.
- **Veritabanı yok.** Kalıcı durum düz JSON dosyalarında (`channels.json`, `settings.json`) tutulur, `mediagrab/store.py` üzerinden. Yeni bir bağımlılık (SQLite dahil) önermeden önce bunun neden yetmediğini açıklayın.
- **`mediagrab/i18n.py`'deki `tr` ve `en` sözlükleri her zaman aynı anahtar kümesine sahip olmalı.** Yeni bir arayüz metni eklerken ikisini birden yazın; `test_i18n.py` bunu doğruluyor, atlamayın.
- **Kullanıcı verisine dokunan hiçbir işlem (indirilenler klasörü, `channels.json`, `settings.json`) geri alınamaz şekilde yazılmaz.** Önce yedekleyip sonra üzerine yazma deseni için `mediagrab/downloader.py`'deki `_backup_existing_outputs`/`_restore_backups` işlevlerine bakın.
- **`setup_mediagrab.py` (kurulum aracı), `mediagrab` paketi diskte var olmadan ÖNCE çalışır** — bu yüzden `mediagrab`'i import etmez, kendi küçük kopyalarını tutar. Bunu "kod tekrarı" diye birleştirmeyin.

### Genel ilke

Küçük, doğrulanmış adımlarla ilerleyin. Bir şeyin çalıştığını iddia etmeden önce çalıştığını gösterin — sunucuyu başlatıp gerçek bir istek atmak, gerçek bir indirme denemek veya hedefli bir mutasyon testiyle. Belirsiz bir mimari karar karşısında (yeni bağımlılık, yeni saklama biçimi, `downloader.py` dışında yt-dlp kullanımı) durup kullanıcıya sorun; varsayımla ilerlemeyin.

---

## English

### The role of AI in this project

MediaGrab was largely built together with an AI (Claude), in real-time dialogue — not as code suggestions, but as changes implemented and tested step by step. This isn't hidden; this file itself is a product of that process.

That doesn't mean "whatever the AI does is fine." The boundary that applies in this repo:

- **No commit or push happens without explicit approval in that moment.** A prior approval doesn't carry over to the next one.
- **A claim of "fixed" isn't accepted without a real test backing it.** Preferred method: temporarily revert the fix and confirm the test goes red (mutation testing) — to actually prove the test catches that bug.
- **Destructive or irreversible operations** (`git push --force`, `rm -rf`, deleting user data) **are asked about explicitly first.**
- Every change an AI tool proposes is reviewed by a human before it's merged.

If you used an AI tool on a PR, you don't need to hide it — but you're responsible for the commit's quality and correctness; the tool saying "it works" isn't enough.

### Build / test commands

```bash
pip install -r requirements-dev.txt
pytest
```

JS tests run if Node.js is installed; otherwise they're skipped automatically. See [README → Tests](README.md#tests) for details.

### Constraints specific to this repo

These aren't style preferences — the code's current design depends on them. If a change breaks one of these, it's probably wrong even if the tests pass:

- **`yt_dlp` is imported only inside `mediagrab/downloader.py`.** Nowhere else. Verify with: `grep -rn "^import yt_dlp\|^from yt_dlp" mediagrab/*.py` should return exactly one file.
- **No database.** Persistent state lives in plain JSON files (`channels.json`, `settings.json`) via `mediagrab/store.py`. Before proposing a new dependency (SQLite included), explain why this isn't enough.
- **The `tr` and `en` dicts in `mediagrab/i18n.py` must always share the same key set.** Add both when adding a new UI string; `test_i18n.py` enforces this — don't skip it.
- **Nothing touching user data (the downloads folder, `channels.json`, `settings.json`) writes destructively.** See the `_backup_existing_outputs`/`_restore_backups` pattern in `mediagrab/downloader.py` for backup-then-overwrite.
- **`setup_mediagrab.py` (the installer) runs BEFORE the `mediagrab` package exists on disk** — so it doesn't import `mediagrab` and keeps small duplicates of its own. Don't "deduplicate" this away.

### General principle

Work in small, verified steps. Show something works before claiming it does — start the server and make a real request, attempt a real download, or run a targeted mutation test. When an architectural decision is ambiguous (a new dependency, a new storage format, yt-dlp usage outside `downloader.py`), stop and ask the user rather than assuming.
