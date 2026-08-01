# ============================================================
# Lesson 7
# Structured Outputs (JSON Schema)
#
# Bu derste modelden sadece JSON istemiyoruz.
# Aynı zamanda dönecek JSON'un yapısını da tanımlıyoruz.
#
# Böylece model istediği alanları üretmek yerine,
# bizim belirlediğimiz şemaya uymak zorunda kalıyor.
# ============================================================

# config.py dosyasını içe aktarır.
# OPENAI_API_KEY değişkenini buradan okuyacağız.
import config

# JSON string'ini Python Dictionary nesnesine çevirmek için kullanılır.
import json

# OpenAI istemcisini içe aktarır.
from openai import OpenAI


# ============================================================
# OpenAI Client
# ============================================================

# OpenAI istemcisini oluşturur.
client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


print("=" * 60)
print("AI Engineer Road Map")
print("Lesson 7 - Structured Outputs (JSON Schema)")
print("=" * 60)

# Kullanıcıdan konu alınır.
question = input("\nBir konu giriniz: ")


# ============================================================
# OpenAI API ÇAĞRISI
# ============================================================

response = client.chat.completions.create(

    # Kullanılacak model.
    model="gpt-4.1",

    # Modele gönderilecek mesajlar.
    messages=[

        # System Prompt
        {
            "role": "system",
            "content": (
                "Sen deneyimli bir .NET yazılım mimarısın."
            )
        },

        # Kullanıcının sorusu
        {
            "role": "user",
            "content": question
        }
    ],

    # ========================================================
    # response_format
    #
    # Modelin cevabını hangi formatta üretmesini istediğimizi
    # belirtir.
    #
    # Burada 'json_schema' kullanıyoruz.
    # Böylece model sadece JSON değil,
    # bizim tanımladığımız JSON'u üretmek zorunda kalır.
    # ========================================================
    response_format={

        "type": "json_schema",

        "json_schema": {

            # Şemanın adı.
            # İleride birden fazla schema olduğunda ayırt etmek için
            # kullanılır.
            "name": "topic_information",

            # Asıl JSON Schema burada tanımlanır.
            "schema": {

                # JSON'un en üst seviyesi bir nesne olacak.
                "type": "object",

                # JSON içerisindeki alanlar.
                "properties": {

                    # ----------------------------------------
                    # title
                    # ----------------------------------------
                    "title": {

                        # String tipinde olacak.
                        "type": "string"

                    },

                    # ----------------------------------------
                    # difficulty
                    # ----------------------------------------
                    "difficulty": {

                        "type": "string",

                        # Model yalnızca bu üç değeri döndürebilir.
                        "enum": [

                            "Easy",
                            "Medium",
                            "Hard"

                        ]

                    },

                    # ----------------------------------------
                    # summary
                    # ----------------------------------------
                    "summary": {

                        "type": "string"

                    },

                    # ----------------------------------------
                    # advantages
                    # ----------------------------------------
                    "advantages": {

                        # Bir liste olacak.
                        "type": "array",

                        # Listenin her elemanı string olacak.
                        "items": {

                            "type": "string"

                        }

                    }

                },

                # ===================================================
                # required
                #
                # Model bu alanların tamamını üretmek zorundadır.
                # ===================================================
                "required": [

                    "title",
                    "difficulty",
                    "summary",
                    "advantages"

                ],

                # ===================================================
                # additionalProperties
                #
                # False olursa model ekstra alan ekleyemez.
                #
                # Örneğin aşağıdakini üretemez.
                #
                # {
                #     "abc":"..."
                # }
                # ===================================================
                "additionalProperties": False

            }

        }

    }

)

# ============================================================
# API'den gelen cevap
# ============================================================

# Modelden gelen veri JSON formatındaki bir string'dir.
json_text = response.choices[0].message.content


print("\n")
print("=" * 60)
print("MODELDEN GELEN JSON")
print("=" * 60)

print(json_text)


# ============================================================
# JSON Parse
# ============================================================

# JSON string'ini Python Dictionary nesnesine çevir.
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

# Dictionary içerisindeki alanlara erişiyoruz.

print(f"Başlık      : {result['title']}")
print(f"Zorluk      : {result['difficulty']}")
print(f"Özet        : {result['summary']}")

print("\nAvantajlar")

# advantages bir liste olduğu için for döngüsü ile dolaşıyoruz.
for item in result["advantages"]:
    print(f"- {item}")