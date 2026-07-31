# Projenin kök klasöründeki config.py dosyasını içe aktarır.
import config

# OpenAI istemcisini içe aktarır.
from openai import OpenAI

# JSON metnini Python nesnesine çevirmek için kullanılır.
import json


# OpenAI istemcisini oluşturur.
client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


# Modelin her zaman JSON üretmesini isteyen System Prompt.
SYSTEM_PROMPT = """
Sen deneyimli bir .NET yazılım mimarısın.

Kullanıcının sorduğu konu hakkında SADECE geçerli bir JSON üret.

JSON dışında hiçbir açıklama yazma.

Aşağıdaki yapıya uy:

{
    "title": "Konu başlığı",
    "difficulty": "Easy | Medium | Hard",
    "summary": "Kısa açıklama",
    "advantages": [
        "Avantaj 1",
        "Avantaj 2",
        "Avantaj 3"
    ]
}
"""


print("=" * 60)
print("AI Engineer Road Map")
print("Lesson 6 - Structured Output (JSON)")
print("=" * 60)

question = input("\nBir konu yaz: ")


# OpenAI isteği gönderilir.
response = client.chat.completions.create(

    model="gpt-4.1",

    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ],

    # Modelin sadece JSON üretmesini sağlar.
    response_format={
        "type": "json_object"
    }
)


# Modelden gelen cevap aslında JSON formatındaki bir string'dir.
json_text = response.choices[0].message.content


print("\n")
print("=" * 60)
print("JSON STRING")
print("=" * 60)

# Henüz parse edilmemiş hali.
print(json_text)


# JSON string'ini Python Dictionary nesnesine dönüştür.
result = json.loads(json_text)


print("\n")
print("=" * 60)
print("PYTHON DICTIONARY")
print("=" * 60)

print(result)


print("\n")
print("=" * 60)
print("ALANLARA ERİŞİM")
print("=" * 60)

# Dictionary içerisindeki alanlara erişim.

print(f"Başlık      : {result['title']}")
print(f"Zorluk      : {result['difficulty']}")
print(f"Özet        : {result['summary']}")

print("\nAvantajlar")

for advantage in result["advantages"]:
    print(f"• {advantage}")