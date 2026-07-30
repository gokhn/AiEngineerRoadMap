# Projenin kök klasöründeki config.py dosyasını içe aktarır.
import config

# OpenAI API istemcisini içe aktarır.
from openai import OpenAI

# OpenAI istemcisini oluşturur.
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

# Konuşma geçmişinde tutulacak maksimum mesaj sayısı.
# System mesajı bu limite dahil değildir.
MAX_HISTORY = 10


def trim_message_history(messages: list, max_history: int) -> list:
    """
    Konuşma geçmişini belirtilen limite göre kısaltır.

    System mesajını korur.
    Son max_history adet mesajı saklar.
    """

    system_message = messages[0]
    conversation = messages[1:]

    if len(conversation) <= max_history:
        return messages

    conversation = conversation[-max_history:]

    return [system_message] + conversation


def print_statistics(messages: list):
    """
    Konuşma geçmişi hakkında bilgi verir.
    """

    roles = [message["role"] for message in messages]

    print("\n" + "=" * 50)
    print("Conversation Statistics")
    print("=" * 50)
    print(f"Toplam Mesaj : {len(messages)}")
    print(f"System       : {roles.count('system')}")
    print(f"User         : {roles.count('user')}")
    print(f"Assistant    : {roles.count('assistant')}")
    print("=" * 50)


# Sohbet geçmişinin tutulduğu liste.
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

print("=" * 50)
print("AI Engineer Road Map")
print("Faz 1 - Lesson 3 : Context Management")
print("=" * 50)
print("Çıkmak için 'exit' yazabilirsin.\n")


while True:

    # Kullanıcıdan soru al.
    question = input("Sen: ").strip()

    # Programdan çık.
    if question.lower() == "exit":
        print("\nSohbet sonlandırıldı.")
        break

    # Boş mesaj kontrolü.
    if not question:
        print("Lütfen bir soru yaz.\n")
        continue

    # Kullanıcı mesajını oluştur.
    user_message = {
        "role": "user",
        "content": question
    }

    # Konuşma geçmişine ekle.
    messages.append(user_message)

    try:

        # API isteği gönder.
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages
        )

        # AI cevabını al.
        answer = response.choices[0].message.content

        # Terminale yazdır.
        print(f"\nAI:\n{answer}\n")

        # Assistant mesajını oluştur.
        assistant_message = {
            "role": "assistant",
            "content": answer
        }

        # Geçmişe ekle.
        messages.append(assistant_message)

        # Konuşma geçmişini temizle.
        messages = trim_message_history(
            messages,
            MAX_HISTORY
        )

        # İstatistikleri göster.
        print_statistics(messages)

    except Exception as error:

        print(f"\nBir hata oluştu: {error}\n")

        # Hata olursa son kullanıcı mesajını sil.
        if messages and messages[-1]["role"] == "user":
            messages.pop()