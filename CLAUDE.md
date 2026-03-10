# MedGemma Skills — Proje Talimatları

Bu proje tıbbi görüntü analizi ve genel tıbbi asistanlık için skill dosyaları içerir.

## Skill Dosyaları

Aşağıdaki skill dosyalarını oku ve talimatlarına uy:

- **Tıbbi görüntü sorusu geldiğinde** → `skills/radiology-skill.md` talimatlarını uygula
- **Lab sonucu, ilaç, semptom sorusu geldiğinde** → `skills/medical-assistant-skill.md` talimatlarını uygula

## MedGemma Pipeline (Görüntü Analizi)

Tıbbi görüntü analizi için kendi vision yeteneğini DEĞİL, MedGemma modelini kullan. MedGemma tıbbi görüntülerde senden çok daha iyi.

**Akış:**
1. Kullanıcı görüntü paylaşır veya `images/` klasörüne koyar
2. `medgemma_api.py` script'ini çalıştırarak görüntüyü MedGemma'ya gönder:
   - Tek görüntü: `python medgemma_api.py images/xray.jpeg`
   - Çoklu görüntü: `python medgemma_api.py images/day0.jpg images/day1.jpg images/day2.jpg`
3. MedGemma'dan gelen ham İngilizce çıktıyı al
4. `skills/radiology-skill.md` formatına göre Türkçe yapılandırılmış rapora dönüştür

**Önemli:** MedGemma çıktısı İngilizce ve formatsız gelir. Senin görevin onu BULGULAR / İZLENİM / GÜVEN SEVİYESİ / ÖNERİLER formatında Türkçe sunmak.

## Görsel Yönetimi

- Kullanıcı görsel paylaştığında `images/` klasörüne kaydet
- ZIP dosyası gelirse çıkart, görselleri `images/` klasörüne koy
- Kullanıcı "images klasöründekileri analiz et" derse, klasördeki tüm görselleri sırayla analiz et
- `sample-xrays/` klasöründe test için hazır örnek görseller var

## Dil

Türkçe yanıt ver. Tıbbi terimleri hem Türkçe hem İngilizce/Latince yaz.

## Önemli

Bu araç eğitim ve bilgilendirme amaçlıdır. Kesin tanı koyma, ilaç reçetesi yazma — bunlar hekim yetkisindedir. Her analizin sonunda bunu belirt.
