# Projenin kök klasöründeki config.py dosyasını içe aktarır.
# Bu dosya API anahtarını (.env) yüklemek için kullanılır.
import config

# OpenAI istemcisini içe aktarır.
from openai import OpenAI


# OpenAI istemcisini oluşturur.
# API anahtarı config.py içerisinden okunur.
client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


# Modelin sohbet boyunca nasıl davranacağını belirleyen System Prompt.
SYSTEM_PROMPT = """
Sen deneyimli bir .NET yazılım mimarı ve eğitmensin.

Soruları Türkçe cevapla.
Kod örnekleri ver.
Başlıklar kullan.
Anlaşılır ve öğretici anlat.
"""


# Konuşma geçmişini tutan liste.
# İlk mesaj her zaman System Prompt olmalıdır.
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


print("=" * 60)
print("AI Engineer Road Map")
print("Lesson 5 - Streaming")
print("=" * 60)
print("Çıkmak için 'exit' yazabilirsiniz.\n")


# Kullanıcı çıkış yapana kadar sohbet devam eder.
while True:

    # Kullanıcının sorusunu al.
    question = input("Sen: ").strip()

    # Kullanıcı exit yazdıysa program sonlandırılır.
    if question.lower() == "exit":
        print("\nSohbet sonlandırıldı.")
        break

    # Boş mesaj gönderilmesini engelle.
    if not question:
        print("Lütfen bir soru yazınız.\n")
        continue

    # Kullanıcı mesajını oluştur.
    user_message = {
        "role": "user",
        "content": question
    }

    # Kullanıcının mesajını konuşma geçmişine ekle.
    messages.append(user_message)

    try:

        # ==========================================================
        # STREAMING API ÇAĞRISI
        #
        # stream=True sayesinde model cevabı tek seferde döndürmez.
        # Cevap oluşturuldukça küçük parçalar (chunk) halinde gönderilir.
        # ==========================================================
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            stream=True
        )

        # AI başlığını yazdır.
        # end="" sayesinde alt satıra geçmeden yazmaya devam eder.
        print("\nAI: ", end="")

        # Streaming sırasında gelen parçaları burada birleştireceğiz.
        full_answer = ""

        # Response artık tek bir nesne değildir.
        # Iterator döndürür.
        # Her döngüde cevabın küçük bir kısmı gelir.
        for chunk in response:

            # Gelen parçadaki metni al.
            # İlk veya son paketlerde content None olabilir.
            delta = chunk.choices[0].delta.content

            # Gerçekten metin geldiyse ekrana yazdır.
            if delta is not None:

                # end=""
                # Alt satıra geçmeden yazdır.

                # flush=True
                # Yazının anında terminale gönderilmesini sağlar.
                print(delta, end="", flush=True)

                # Gelen parçaları tek bir string içerisinde biriktir.
                full_answer += delta

        # Streaming tamamlandıktan sonra bir satır boşluk bırak.
        print("\n")

        # Assistant mesajını oluştur.
        assistant_message = {
            "role": "assistant",
            "content": full_answer
        }

        # AI cevabını konuşma geçmişine ekle.
        # Böylece sonraki sorularda model önceki cevabını da bilir.
        messages.append(assistant_message)

    except Exception as error:

        print(f"\nBir hata oluştu: {error}\n")

        # API isteği başarısız olursa son kullanıcı mesajını sil.
        # Böylece konuşma geçmişinde cevapsız mesaj kalmaz.
        if messages and messages[-1]["role"] == "user":
            messages.pop()