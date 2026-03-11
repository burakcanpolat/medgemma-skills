# MedGemma Skills

Google'ın açık kaynak tıbbi AI modeli [MedGemma](https://huggingface.co/google/medgemma-1.5-4b-it) için hazır skill paketi. Cursor, Claude Code, Antigravity veya herhangi bir AI IDE ile kullanılabilir.

## Ne Yapıyor?

Bu repo'yu bir AI IDE'de açtığınızda, AI asistanınız:
1. Önce sizden **hasta bilgisi** alır (yaş, cinsiyet, şikayet)
2. Görüntüleri **MedGemma** ile analiz eder (X-ray, CT, MRI)
3. Sonuçları **herkesin anlayacağı sade Türkçe** ile sunar
4. Raporu otomatik olarak `reports/` klasörüne kaydeder

## Yapı

```
medgemma-skills/
├── CLAUDE.md                     ← Claude Code talimatları
├── .cursor/rules/medgemma.mdc   ← Cursor talimatları (yeni format)
├── medgemma_api.py               ← MedGemma API client (Modal, max 85 görüntü/istek)
├── skills/
│   ├── radiology-skill.md        ← Görüntü analizi (sade dil)
│   └── medical-assistant-skill.md ← Lab, ilaç, semptom
├── images/                       ← Görsellerinizi buraya atın
├── reports/                      ← Raporlar otomatik kaydedilir
│   └── hasta_bilgisi.md          ← Hasta context (persistent)
└── sample-xrays/                 ← Test görselleri
    ├── normal/       (3 X-ray)
    ├── pneumonia/    (2 X-ray)
    └── temporal/     (3 günlük seri)
```

## Hızlı Başlangıç

### 1. Klonla ve IDE'de aç

```bash
git clone https://github.com/burakcanpolat/medgemma-skills.git
```

Cursor, Antigravity veya Claude Code ile açın.

### 2. AI asistana sor

AI önce hasta bilgisi soracak (yaş, cinsiyet, şikayet), sonra analiz yapacak:

> "sample-xrays klasöründeki X-ray'leri analiz et"

> "Bu ZIP'i analiz et" *(ZIP'i images/ klasörüne atın)*

> "WBC: 12.500, Hb: 9.2, Ferritin: 8 — bu değerleri yorumla"

### 3. Terminal (manuel)

```bash
python medgemma_api.py images/xray.jpeg
python medgemma_api.py images/seri1.jpg images/seri2.jpg images/seri3.jpg
python medgemma_api.py gorseller.zip
```

## Pipeline

```
Hasta bilgisi al (yaş, cinsiyet, şikayet)
        ↓
Görüntü → medgemma_api.py → Modal API (MedGemma)
  ├── Seri ≤85 görüntü → tek istek
  └── Seri >85 → 85'lik batch'ler
        ↓
Ham İngilizce analiz
        ↓
AI Asistan → Türkçe sade rapor
  ├── NE GÖRÜYORUZ?
  ├── NE ANLAMA GELİYOR?
  ├── NE KADAR EMİNİZ? (🟢🟡🔴)
  └── NE YAPMALI?
        ↓
reports/ klasörüne kaydet
```

## Gereksinimler

- Python 3.8+ (ek paket gerekmez — sadece stdlib)
- İnternet bağlantısı (Modal API)

## Sorumluluk Reddi

⚠️ Bu araçlar **eğitim ve bilgilendirme amaçlıdır**. Kesin tanı ve tedavi için mutlaka doktora başvurun.

## Lisans

MIT
