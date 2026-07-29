# config.py dosyasındaki ayarları kullanabilmek için içe aktarır.
# Bu dosyanın içinde OPENAI_API_KEY değişkeninin tanımlı olduğunu varsayıyoruz.
import config

# OpenAI API ile iletişim kurmamızı sağlayan istemci sınıfını içe aktarır.
from openai import OpenAI


# OpenAI istemcisini oluşturur.
# API anahtarı config.py dosyasından alınır.
client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


# Sohbet boyunca gönderilecek mesajların tutulduğu liste.
# Bu liste sayesinde yapay zekâ önceki konuşmaları hatırlayabilir.
messages = [
    {
        # System mesajı, yapay zekânın nasıl davranacağını belirler.
        "role": "system",

        # Yapay zekâya bir rol ve uzmanlık alanı veriyoruz.
        "content": "Sen deneyimli bir .NET yazılım mimarısın."
    }
]


# Kullanıcı "exit" yazana kadar sohbetin devam etmesini sağlar.
while True:

    # Kullanıcıdan soru alır.
    # strip() baştaki ve sondaki gereksiz boşlukları temizler.
    question = input("Sen: ").strip()

    # Kullanıcı exit yazdıysa programdan çıkar.
    # lower() sayesinde EXIT, Exit veya exit aynı şekilde çalışır.
    if question.lower() == "exit":
        print("Sohbet sonlandırıldı.")
        break

    # Kullanıcı hiçbir şey yazmadan Enter'a bastıysa
    # API isteği göndermeden döngünün başına döner.
    if not question:
        continue

    # Kullanıcının mesajını konuşma geçmişine ekler.
    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    try:
        # OpenAI API'ye sohbet isteği gönderir.
        response = client.chat.completions.create(
            # Kullanılacak OpenAI modeli.
            model="gpt-4.1",

            # System, user ve assistant mesajlarının tamamını gönderir.
            # Böylece model önceki konuşmaları hatırlar.
            messages=messages
        )

        # API'den dönen cevabın metin kısmını alır.
        answer = response.choices[0].message.content

        # Yapay zekânın cevabını terminalde gösterir.
        print(f"\nAI: {answer}\n")

        # Yapay zekânın cevabını konuşma geçmişine ekler.
        # Böylece bir sonraki soruda önceki cevap da modele gönderilir.
        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    except Exception as error:
        # API bağlantısı, internet, model veya API anahtarıyla ilgili
        # bir hata oluşursa programın kapanmasını engeller.
        print(f"\nBir hata oluştu: {error}\n")