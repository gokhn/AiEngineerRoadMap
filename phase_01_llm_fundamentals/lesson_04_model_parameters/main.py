import config
from openai import OpenAI

# OpenAI istemcisini oluştur.
client = OpenAI(
    api_key=config.OPENAI_API_KEY
)

# ============================================================
# MODEL PARAMETRELERİ
# ============================================================

# Modelin ne kadar yaratıcı cevap vereceğini belirler.
#
# 0.0  -> Aynı soruya neredeyse her zaman aynı cevabı verir.
# 0.2  -> Teknik konular ve kod üretimi için önerilir.
# 0.7  -> Günlük sohbet için idealdir.
# 1.0+ -> Daha yaratıcı cevaplar üretir.
TEMPERATURE = 0.2


# Modelin kelime seçim havuzunu belirler.
#
# 1.0 -> Tüm olası kelimeler değerlendirilebilir.
# 0.9 -> Daha dar bir seçim havuzu oluşturur.
#
# Genellikle temperature ile birlikte değiştirilmesi önerilmez.
TOP_P = 1


# Aynı kelime veya ifadelerin tekrar edilmesini azaltır.
#
# 0   -> Tekrarlara izin verir.
# 1   -> Tekrarları azaltır.
# 2   -> Tekrarları ciddi şekilde azaltır.
FREQUENCY_PENALTY = 0


# Modelin yeni konu ve fikirler açmasını teşvik eder.
#
# 0   -> Mevcut konuya bağlı kalır.
# 1   -> Yeni konular açmaya başlar.
# 2   -> Sürekli yeni fikirler üretmeye çalışır.
PRESENCE_PENALTY = 0


# Modelin üreteceği maksimum cevap uzunluğu.
#
# Çok küçük verilirse cevap yarıda kesilebilir.
MAX_TOKENS = 1000

# ============================================================

question = input("Bir soru sor: ")

response = client.chat.completions.create(
    model="gpt-4.1",

    messages=[
        {
            "role": "system",
            "content": "Sen deneyimli bir .NET yazılım mimarısın."
        },
        {
            "role": "user",
            "content": question
        }
    ],

    # Model Parametreleri
    temperature= TEMPERATURE,
    top_p=TOP_P,
    frequency_penalty=FREQUENCY_PENALTY,
    presence_penalty=PRESENCE_PENALTY,
    max_tokens=MAX_TOKENS
)

print("\n" + "=" * 60)
print("MODEL CEVABI")
print("=" * 60)

print(response.choices[0].message.content)