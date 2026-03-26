# Med-Rehber

Tibbi sonuclarinizi herkesin anlayacagi dile ceviren AI rehberiniz. [MedGemma](https://huggingface.co/google/medgemma-1.5-4b-it) destekli. **Zed**, **Cursor** ve **Claude Code** ile calisir.

> **English:** Your AI guide for understanding medical results in plain language. Powered by MedGemma. Works with Zed, Cursor, and Claude Code. [Jump to English setup](#english-setup)

---

## Ne Yapiyor?

Bu repo'yu bir AI editorde actiginizda, AI asistaniniz:
1. Sizden **hasta bilgisi** alir (yas, cinsiyet, sikayet)
2. Goruntuleri **MedGemma** ile analiz eder
3. Sonuclari **herkesin anlayacagi sade Turkce** ile raporlar
4. Raporlari `reports/` klasorune kaydeder

## Proje Yapisi

```
med-rehber/
├── CLAUDE.md                         ← Claude Code + Zed talimatlari
├── AGENTS.md                         ← Universal talimatlar (Cursor, Zed, Copilot)
├── .cursor/rules/medgemma.mdc        ← Cursor talimatlari
├── .agents/skills/                   ← Universal Skills (tum editorler)
│   ├── medgemma-radiology/SKILL.md   ← Goruntu analizi skill'i
│   └── medgemma-assistant/SKILL.md   ← Lab/ilac/semptom skill'i
├── skills/                           ← Okunabilir skill dosyalari
│   ├── radiology-skill.md
│   └── medical-assistant-skill.md
├── scripts/
│   └── medgemma_api.py               ← MedGemma API client
├── setup.sh                          ← Kurulum scripti (macOS/Linux)
├── setup.bat                         ← Kurulum scripti (Windows)
├── .zed/settings.json.example        ← Zed + OpenRouter config ornegi
├── .env.example                      ← Environment variable ornegi
├── images/                           ← Gorsellerinizi buraya atin
├── reports/                          ← Raporlar buraya kaydedilir
└── test/sample-xrays/                ← Test gorselleri
    ├── normal/                       ← 3 normal X-ray
    ├── pneumonia/                    ← 2 pnomoni X-ray
    └── temporal/                     ← 3 zamansal seri
```

---

## Hizli Kurulum (Tek Komut)

Hicbir teknik bilgiye ihtiyaciniz yok. Script sizi adim adim yonlendirir:

**macOS / Linux:**
```bash
git clone https://github.com/burakcanpolat/med-rehber.git
cd med-rehber
./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/burakcanpolat/med-rehber.git
cd med-rehber
setup.bat
```

**AI Editor ile (en kolayi):**
Repo'yu Zed, Cursor veya Claude Code ile acin ve AI asistana yazin:

> **"kurulumu baslat"**

AI sizi adim adim yonlendirecek: Python kontrolu, ayar dosyasi olusturma, baglanti testi, ilk analiz.

---

## Detayli Kurulum

### Zed (Onerilen)

Zed + OpenRouter ile **istediginiz modeli** kullanabilirsiniz (Claude, Gemini, GPT, Llama...).

**1. Zed'i yukleyin**
- [zed.dev/download](https://zed.dev/download) (macOS, Linux, Windows)

**2. OpenRouter API key alin**
- [openrouter.ai/keys](https://openrouter.ai/keys) adresinden ucretsiz hesap + API key

**3. API key'i Zed'e ekleyin**
- Zed'i acin → Command Palette → `agent: open settings`
- OpenRouter bolumune API key'inizi yapistirinzed
- Veya: `OPENROUTER_API_KEY` environment variable ayarlayin

**4. Repo'yu acin**
```bash
git clone https://github.com/burakcanpolat/med-rehber.git
cd med-rehber
```
Zed ile klasoru acin. `CLAUDE.md` otomatik olarak AI talimatlariniza yuklenir.

**5. (Opsiyonel) Model ayari**
```bash
cp .zed/settings.json.example .zed/settings.json
```
Varsayilan model: Claude Sonnet 4. Degistirmek icin `settings.json` duzenleyin.

**6. Kullanmaya baslayin**
Agent Panel'i acin ve sorun:
> "test klasorundeki X-ray'leri analiz et"

---

### Cursor

**1.** [cursor.com](https://cursor.com) adresinden Cursor'u yukleyin

**2.** Repo'yu klonlayin ve Cursor ile acin:
```bash
git clone https://github.com/burakcanpolat/med-rehber.git
```

**3.** Hazir! `.cursor/rules/medgemma.mdc` otomatik yuklenir (`alwaysApply: true`).

**Not:** Cursor'da OpenRouter modelleri sadece Chat modunda calisir. Agent mode icin Cursor Pro abonelik gerekir.

---

### Claude Code

```bash
npm install -g @anthropic-ai/claude-code
git clone https://github.com/burakcanpolat/med-rehber.git
cd med-rehber
claude
```

Hazir! `CLAUDE.md` otomatik okunur.

---

## Kullanim

### AI Asistan ile (Onerilen)

Editorde AI asistana sorun:

> "test klasorundeki X-ray'leri analiz et"

> "WBC: 12.500, Hb: 9.2, Ferritin: 8 — yorumla"

> "Aspirin ve Warfarin birlikte kullanilir mi?"

### Terminal ile

```bash
python scripts/medgemma_api.py images/xray.jpeg              # Tek goruntu
python scripts/medgemma_api.py img1.jpg img2.jpg img3.jpg     # Coklu goruntu
python scripts/medgemma_api.py arsiv.zip                      # ZIP arsiv
```

### Pipeline

```
Hasta bilgisi → Goruntu → scripts/medgemma_api.py → Modal (MedGemma)
  ├── Seri ≤85 → tek istek
  └── Seri >85 → 85'lik batch
        ↓
AI Asistan → Turkce rapor → reports/
```

## Konfigurasyon

| Degisken | Aciklama | Varsayilan |
|----------|----------|------------|
| `MEDGEMMA_ENDPOINT` | MedGemma API URL | Modal hosted endpoint |
| `MEDGEMMA_MODEL` | Model adi | `google/medgemma-1.5-4b-it` |
| `OPENROUTER_API_KEY` | OpenRouter API key (Zed icin) | — |

Ornekler icin `.env.example` dosyasina bakin.

## Editor Uyumluluk Matrisi

| Dosya | Claude Code | Zed | Cursor | GitHub Copilot |
|-------|:-----------:|:---:|:------:|:--------------:|
| `CLAUDE.md` | ✅ otomatik | ✅ otomatik | — | — |
| `AGENTS.md` | — | ✅ otomatik | ✅ otomatik | ✅ |
| `.cursor/rules/*.mdc` | — | — | ✅ otomatik | — |
| `.agents/skills/` | ✅ | ✅ | ✅ | — |

## Skills

| Skill | Ne Yapar |
|-------|----------|
| `medgemma-radiology` | X-ray, CT, MRI goruntu analizi, guven seviyeleri |
| `medgemma-assistant` | Lab sonuclari, ilac etkilesimleri, semptom degerlendirmesi |

## Gereksinimler

- Python 3.8+ (sadece stdlib — ek paket gerekmez)
- Internet baglantisi

## Lisans

MIT — [LICENSE](LICENSE)

---

<a name="english-setup"></a>

## English Setup

**Med-Rehber** is an open-source AI skill package for medical image analysis and clinical assistance. It works with **Zed**, **Cursor**, and **Claude Code**.

### Quick Start (Zed + OpenRouter)

1. Install [Zed](https://zed.dev/download)
2. Get an API key from [OpenRouter](https://openrouter.ai/keys)
3. In Zed: Command Palette → `agent: open settings` → paste API key in OpenRouter section
4. Clone and open:
   ```bash
   git clone https://github.com/burakcanpolat/med-rehber.git
   ```
5. Open the Agent Panel and ask: *"Analyze the X-rays in the test folder"*

### Quick Start (Claude Code)

```bash
git clone https://github.com/burakcanpolat/med-rehber.git
cd med-rehber && claude
```

### What It Does

- Collects patient information before analysis (age, gender, complaint)
- Analyzes medical images via Google's MedGemma model
- Explains findings in plain, simple language
- Saves structured reports to `reports/`

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MEDGEMMA_ENDPOINT` | MedGemma API URL | Modal hosted endpoint |
| `MEDGEMMA_MODEL` | Model name | `google/medgemma-1.5-4b-it` |
| `OPENROUTER_API_KEY` | OpenRouter API key (for Zed) | — |

---

⚠️ **Disclaimer / Sorumluluk Reddi:** These tools are for educational and informational purposes only. Always consult a healthcare professional for diagnosis and treatment. / Bu araclar egitim ve bilgilendirme amaclidir. Kesin tani ve tedavi icin doktora basvurun.
