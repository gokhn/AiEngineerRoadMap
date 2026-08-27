# AI Software Architect Assistant

`phase_01_llm_fundamentals` derslerinde öğrenilen tekniklerin bir araya
getirildiği mini bir CLI projesi. Kullanıcıyla bir yazılım projesinin
mimarisi üzerine sohbet eder, istenirse yapılandırılmış bir mimari öneri
(JSON) üretir ve markdown olarak diske kaydedebilir.

## Hangi ders, nerede kullanıldı?

| Ders | Konu | Bu projede karşılığı |
|---|---|---|
| 2 | Prompt Engineering | `SYSTEM_PROMPT` — mimar personası |
| 3 | Context Management | `messages` listesi, `/reset` komutu |
| 4 | Model Parameters | `TEMPERATURE`, `/temp` komutu |
| 5 | Streaming | Sohbet cevapları token token yazdırılır |
| 6-7 | Structured Outputs / JSON Schema | `/proposal` komutu, `schemas.py` |
| 8-9 | Function / Tool Calling | `tools.py`, streaming agent loop |
| 10 | Multimodal | `/image <dosya_yolu>` komutu |

## Çalıştırma

Repo kökündeki `.env` dosyasında `OPENAI_API_KEY` tanımlı olmalı.

```
python ai_software_architect_assistant/main.py
```

## Komutlar

- `<soru>` — mimarla normal sohbet et (streaming, gerekirse tool çağırır)
- `/proposal` — konuşmadan yapılandırılmış bir mimari önerisi üret, isteğe bağlı markdown kaydet
- `/image <yol>` — yerel bir görüntüyü (diyagram, ekran görüntüsü) analiz ettir
- `/temp <0-2>` — model temperature değerini göster/değiştir
- `/reset` — konuşma geçmişini sıfırla
- `/help` — komut listesini göster
- `/exit` — çık

Kaydedilen mimari önerileri `output/` klasörüne yazılır (git'e dahil edilmez).
