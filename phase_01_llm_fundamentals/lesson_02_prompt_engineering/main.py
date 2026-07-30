# Projenin kök klasöründeki config.py dosyasını içe aktarır.
import config

# OpenAI API istemcisini içe aktarır.
from openai import OpenAI


# OpenAI istemcisini oluşturur.
# API anahtarı config.py içerisinden alınır.
client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


# Modelin sohbet boyunca nasıl davranacağını belirleyen system prompt.
SYSTEM_PROMPT = """
Sen deneyimli bir .NET yazılım mimarı ve eğitmensin.

Aşağıdaki kurallara göre cevap ver:

1. Cevaplarını Türkçe yaz.
2. Konuyu önce kısa bir tanımla açıkla.
3. Ardından adım adım detaylandır.
4. Uygun olduğunda C# kod örneği ver.
5. Karmaşık kavramları basit benzetmelerle anlat.
6. Cevaplarını başlıklar ve maddeler halinde düzenle.
7. Gereksiz derecede uzun cevaplar verme.
8. Emin olmadığın bilgileri kesinmiş gibi sunma.
9. Kullanıcının hatalı bir varsayımı varsa nazikçe düzelt.
10. Cevabın sonunda kısa bir özet ver.
"""


# Sohbet geçmişinin tutulduğu liste.
# İlk mesaj modelin davranış kurallarını içerir.
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


print("AI Engineer Road Map - Faz 1 / Lesson 2")
print("Çıkmak için 'exit' yazabilirsin.\n")


# Kullanıcı çıkış yapana kadar sohbet devam eder.
while True:

    # Kullanıcıdan soru alır ve gereksiz boşlukları temizler.
    question = input("Sen: ").strip()

    # Kullanıcı exit yazdığında program sonlandırılır.
    if question.lower() == "exit":
        print("Sohbet sonlandırıldı.")
        break

    # Boş mesaj gönderilmişse API isteği yapılmaz.
    if not question:
        print("Lütfen bir soru yaz.\n")
        continue

    # Kullanıcının sorusu konuşma geçmişine eklenir.
    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    try:
        # Mesajların tamamı OpenAI modeline gönderilir.
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages
        )

        # Modelin verdiği metin cevabı alınır.
        answer = response.choices[0].message.content

        # Cevap terminal ekranında gösterilir.
        print(f"\nAI:\n{answer}\n")

        # Model cevabı sohbet geçmişine eklenir.
        # Böylece sonraki sorularda önceki konuşmalar hatırlanır.
        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    except Exception as error:
        # API veya bağlantı hatasında programın tamamen kapanmasını önler.
        print(f"\nBir hata oluştu: {error}\n")

        # API isteği başarısız olduğu için son kullanıcı mesajını kaldırır.
        # Böylece konuşma geçmişinde cevapsız mesaj kalmaz.
        messages.pop()