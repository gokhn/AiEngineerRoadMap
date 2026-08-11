# ============================================================
# Lesson 8
# Function / Tool Calling
#
# Önceki derste modele "şu şemaya uygun JSON üret" dedik.
# Bu derste bir adım öteye geçiyoruz:
#
# Modele elimizdeki gerçek Python fonksiyonlarını TANITIYORUZ.
# Model, kullanıcının sorusunu cevaplamak için bu fonksiyonlardan
# birini çağırmak isteyip istemediğine kendisi karar veriyor.
#
# ÖNEMLİ: Model fonksiyonu KENDİSİ ÇALIŞTIRMAZ.
# Sadece "şu fonksiyonu, şu parametrelerle çağırmak istiyorum"
# der. Fonksiyonu bizim kodumuz çalıştırır ve sonucu tekrar
# modele geri gönderiveririz. Model de son cevabı bu sonuca
# bakarak üretir.
#
# Akış:
#   1) Kullanıcı soru sorar.
#   2) Model, soruyu cevaplamak için bir tool çağırmaya karar verir.
#   3) Biz o tool'u (Python fonksiyonunu) gerçekten çalıştırırız.
#   4) Sonucu tekrar modele göndeririz.
#   5) Model, elindeki gerçek veriyle son cevabı üretir.
# ============================================================

# config.py dosyasını içe aktarır.
# OPENAI_API_KEY değişkenini buradan okuyacağız.
import config

# Modelin ürettiği "arguments" alanı JSON string olarak gelir.
# Python dictionary'sine çevirmek için kullanılır.
import json

# OpenAI istemcisini içe aktarır.
from openai import OpenAI


# ============================================================
# OpenAI Client
# ============================================================

client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


# ============================================================
# GERÇEK PYTHON FONKSİYONLARI (Tool'ların kendisi)
#
# Bunlar sıradan Python fonksiyonları.
# Model bunları göremez, sadece aşağıdaki "tools" şemasındaki
# isim/parametre tanımını görür.
# ============================================================

def turkish_lower(text: str) -> str:
    """
    Python'ın standart .lower() metodu Türkçe karakterlerde yanlış
    çalışır. Özellikle büyük "İ" harfi normalde küçük "i" olması
    gerekirken, Python bunu "i" + görünmez bir nokta karakterine
    (U+0307) çevirir. Bu yüzden "İstanbul".lower() -> "istanbul"
    DEĞİL, "i̇stanbul" olur ve sözlükteki anahtarla eşleşmez.

    Bu fonksiyon önce Türkçe büyük harfleri elle karşılığına çevirip
    sonra .lower() çağırarak bu sorunu çözer.
    """

    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def get_weather(city: str) -> dict:
    """
    Gerçek bir hava durumu API'si yerine sahte (mock) veri döndürür.
    Amacımız API entegrasyonu değil, tool-calling akışını öğrenmek.
    """

    # Örnek amaçlı sabit bir veri tabanı.
    fake_weather_db = {
        "istanbul": {"sicaklik": 24, "durum": "Parçalı bulutlu"},
        "ankara": {"sicaklik": 19, "durum": "Açık"},
        "izmir": {"sicaklik": 28, "durum": "Güneşli"},
    }

    # Türkçe karakter sorunlarına karşı özel lower() kullanıyoruz.
    key = turkish_lower(city.strip())

    if key in fake_weather_db:
        data = fake_weather_db[key]
        return {
            "city": city,
            "temperature_c": data["sicaklik"],
            "condition": data["durum"]
        }

    # Bilmediğimiz bir şehir sorulursa modele bunu söyleriz.
    return {
        "city": city,
        "error": "Bu şehir için veri bulunamadı."
    }


def calculate(expression: str) -> dict:
    """
    Basit bir matematiksel ifadeyi hesaplar.
    Örnek: "12 * (3 + 4)"

    NOT: eval() normalde güvenli değildir. Burada sadece
    öğretim amaçlı, çok basit bir örnek olarak kullanıyoruz.
    """

    try:
        # Sadece rakam, boşluk ve temel operatörlere izin veriyoruz.
        allowed_chars = set("0123456789+-*/(). ")

        if not set(expression) <= allowed_chars:
            return {"error": "İfade geçersiz karakterler içeriyor."}

        result = eval(expression)
        return {"expression": expression, "result": result}

    except Exception as error:
        return {"error": f"Hesaplama hatası: {error}"}


# Fonksiyon adını gerçek Python fonksiyonuna eşleyen sözlük.
# Model bize sadece fonksiyonun "adını" gönderecek.
# Biz de bu isim üzerinden gerçek fonksiyonu bulup çalıştıracağız.
available_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
}


# ============================================================
# TOOLS ŞEMASI
#
# Modele "elinde şu fonksiyonlar var" dediğimiz yer burasıdır.
# Her tool için: isim, açıklama ve parametre şeması tanımlanır.
#
# Model buradaki "description" alanlarını okuyarak
# hangi tool'u ne zaman kullanacağına karar verir.
# Bu yüzden açıklamalar net ve anlaşılır olmalı.
# ============================================================

tools = [

    {
        "type": "function",
        "function": {

            "name": "get_weather",

            "description": (
                "Belirtilen bir şehrin güncel hava durumunu döndürür. "
                "Kullanıcı hava durumu, sıcaklık gibi bir şey sorduğunda kullanılır."
            ),

            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Hava durumu öğrenilecek şehir adı. Örn: 'İstanbul'"
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }

        }
    },

    {
        "type": "function",
        "function": {

            "name": "calculate",

            "description": (
                "Basit bir matematiksel ifadeyi hesaplar. "
                "Kullanıcı bir hesaplama, toplama, çarpma vb. istediğinde kullanılır."
            ),

            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Hesaplanacak matematiksel ifade. Örn: '12 * (3 + 4)'"
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }

        }
    }

]


print("=" * 60)
print("AI Engineer Road Map")
print("Lesson 8 - Function / Tool Calling")
print("=" * 60)

# Kullanıcıdan soru alınır.
# Örnek: "İstanbul'da hava nasıl?" ya da "12 çarpı 4 kaç eder?"
question = input("\nBir soru sorun (hava durumu ya da hesaplama): ")


# Konuşma geçmişi. Tool-calling akışında birden fazla mesaj
# eklenecek, bu yüzden liste olarak tutuyoruz.
messages = [
    {
        "role": "system",
        "content": "Sen yardımsever bir asistansın. Gerekli olduğunda elindeki tool'ları kullan."
    },
    {
        "role": "user",
        "content": question
    }
]


# ============================================================
# 1. API ÇAĞRISI
#
# Modele hem mesajları hem de kullanabileceği tool'ları gönderiyoruz.
# tool_choice="auto" -> Model, tool kullanıp kullanmayacağına
# kendisi karar versin demek.
# ============================================================

first_response = client.chat.completions.create(
    model="gpt-4.1",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

response_message = first_response.choices[0].message

print("\n")
print("=" * 60)
print("MODELİN İLK CEVABI (ham)")
print("=" * 60)
print(response_message)


# ============================================================
# 2. MODEL BİR TOOL ÇAĞIRMAK İSTEDİ Mİ?
#
# Eğer model bir tool çağırmak istiyorsa, bu bilgi
# response_message.tool_calls içinde gelir.
# Eğer boşsa, model soruyu tool'suz da cevaplayabilmiş demektir.
# ============================================================

if response_message.tool_calls:

    # Modelin verdiği "assistant" mesajını (tool_calls dahil)
    # konuşma geçmişine ekliyoruz. Bu adım zorunludur;
    # API, tool sonuçlarını bu mesajla eşleştirir.
    messages.append(response_message)

    print("\n")
    print("=" * 60)
    print("MODEL TOOL ÇAĞIRMAK İSTEDİ")
    print("=" * 60)

    # Model aynı anda birden fazla tool çağırmak isteyebilir.
    # Bu yüzden hepsini tek tek işliyoruz.
    for tool_call in response_message.tool_calls:

        function_name = tool_call.function.name

        # Modelin gönderdiği parametreler JSON string olarak gelir.
        # Python dictionary'sine çeviriyoruz.
        function_args = json.loads(tool_call.function.arguments)

        print(f"\nÇağrılan fonksiyon : {function_name}")
        print(f"Parametreler       : {function_args}")

        # İsim üzerinden gerçek Python fonksiyonunu buluyoruz.
        function_to_call = available_functions[function_name]

        # Fonksiyonu gerçekten çalıştırıyoruz.
        # **function_args -> dictionary'yi anahtar kelime
        # parametrelerine açar. Örn: {"city": "İstanbul"} -> city="İstanbul"
        function_result = function_to_call(**function_args)

        print(f"Fonksiyon sonucu   : {function_result}")

        # ====================================================
        # Tool sonucunu konuşma geçmişine ekliyoruz.
        #
        # role="tool" -> Bu mesajın bir tool sonucu olduğunu belirtir.
        # tool_call_id -> Bu sonucun HANGİ tool çağrısına ait
        # olduğunu API'ye söyler. Birden fazla tool çağrısı varsa
        # bu eşleştirme kritik önem taşır.
        # ====================================================
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(function_result, ensure_ascii=False)
        })

    # ========================================================
    # 3. API ÇAĞRISI (İKİNCİ TUR)
    #
    # Artık modele: soru + kendi tool çağrısı + tool'un gerçek
    # sonucunu birlikte gönderiyoruz. Model bu sefer gerçek
    # veriye dayanarak doğal dilde bir cevap üretecek.
    # ========================================================
    second_response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages
    )

    final_answer = second_response.choices[0].message.content

    print("\n")
    print("=" * 60)
    print("MODELİN SON CEVABI")
    print("=" * 60)
    print(final_answer)

else:
    # Model hiç tool çağırmadan direkt cevap verdiyse
    # (örneğin soru tool gerektirmiyorsa) sonucu direkt gösteririz.
    print("\n")
    print("=" * 60)
    print("MODEL TOOL KULLANMADAN CEVAP VERDİ")
    print("=" * 60)
    print(response_message.content)
