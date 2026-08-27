# ============================================================
# Lesson 9
# Tool Calling (İleri Seviye)
#
# Lesson 8'de tool-calling'in temel mekaniğini gördük:
# model bir tool çağırmak istiyorsa bunu bize söylüyor, biz
# fonksiyonu çalıştırıp sonucu geri gönderiyorduk. Ama orada
# akış TEK TURLA sınırlıydı (if tool_calls: ... else: ...).
#
# Gerçek hayatta model:
#   - Aynı anda BİRDEN FAZLA tool çağırabilir (parallel tool calls)
#   - Bir tool sonucunu görüp, cevabı tamamlamak için BAŞKA bir
#     tool'a daha ihtiyaç duyabilir (çok turlu / ardışık çağrılar)
#
# Bu derste iki yeni kavrama odaklanıyoruz:
#
#   1) AGENT LOOP
#      Tek seferlik if/else yerine, model tool çağırmayı
#      bırakana kadar dönen genel bir döngü yazıyoruz.
#
#   2) tool_choice PARAMETRESİ
#      Modelin tool kullanıp kullanmayacağını NE KADAR kontrol
#      edebileceğimizi (auto / required / none / belirli bir
#      fonksiyonu zorlama) örneklerle görüyoruz.
# ============================================================

import config
import json
from openai import OpenAI


# ============================================================
# OpenAI Client
# ============================================================

client = OpenAI(
    api_key=config.OPENAI_API_KEY
)


# ============================================================
# GERÇEK PYTHON FONKSİYONLARI (Tool'ların kendisi)
# ============================================================

def turkish_lower(text: str) -> str:
    """Python'ın .lower() metodu Türkçe 'İ' harfinde hatalı davranır. Bu yardımcı fonksiyon o sorunu bertaraf eder."""

    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def get_weather(city: str) -> dict:
    """Sahte (mock) hava durumu verisi döndürür."""

    fake_weather_db = {
        "istanbul": {"sicaklik": 24, "durum": "Parçalı bulutlu"},
        "ankara": {"sicaklik": 19, "durum": "Açık"},
        "izmir": {"sicaklik": 28, "durum": "Güneşli"},
    }

    key = turkish_lower(city.strip())

    if key in fake_weather_db:
        data = fake_weather_db[key]
        return {
            "city": city,
            "temperature_c": data["sicaklik"],
            "condition": data["durum"]
        }

    return {
        "city": city,
        "error": "Bu şehir için veri bulunamadı."
    }


def calculate(expression: str) -> dict:
    """Basit bir matematiksel ifadeyi hesaplar. NOT: eval() öğretim amaçlıdır, üretimde kullanılmaz."""

    try:
        allowed_chars = set("0123456789+-*/(). ")

        if not set(expression) <= allowed_chars:
            return {"error": "İfade geçersiz karakterler içeriyor."}

        result = eval(expression)
        return {"expression": expression, "result": result}

    except Exception as error:
        return {"error": f"Hesaplama hatası: {error}"}


def get_current_time(city: str) -> dict:
    """
    Sahte (mock) yerel saat verisi döndürür.

    Bu üçüncü tool'u özellikle ekledik: kullanıcı "İstanbul'da hava
    nasıl ve saat kaç?" gibi bir soru sorduğunda, model TEK bir
    cevapta hem get_weather hem get_current_time'ı çağırmak
    isteyecek. Böylece "parallel tool calls" davranışını canlı
    olarak görebileceğiz.
    """

    fake_time_db = {
        "istanbul": "14:32",
        "ankara": "14:32",
        "izmir": "14:32",
        "tokyo": "20:32",
        "new york": "07:32",
    }

    key = turkish_lower(city.strip())
    local_time = fake_time_db.get(key)

    if local_time is None:
        return {"city": city, "error": "Bu şehir için saat verisi bulunamadı."}

    return {"city": city, "local_time": local_time}


available_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
    "get_current_time": get_current_time,
}


# ============================================================
# TOOLS ŞEMASI
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": (
                "Belirtilen bir şehirdeki güncel yerel saati döndürür. "
                "Kullanıcı saat, saat kaç gibi bir şey sorduğunda kullanılır."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Saati öğrenilecek şehir adı. Örn: 'Tokyo'"
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }
        }
    }
]


# ============================================================
# TOOL ÇAĞRILARINI ÇALIŞTIRAN YARDIMCI FONKSİYON
#
# Bir response_message içindeki tool_calls listesini gezip
# her birini çalıştırır ve sonuçlarını messages listesine
# "role": "tool" mesajları olarak ekler.
#
# Model aynı anda birden fazla tool çağırdıysa (parallel tool
# calls), hepsi bu listede yan yana gelir; döngü hepsini sırayla
# işler.
# ============================================================

def execute_tool_calls(response_message, messages):

    for tool_call in response_message.tool_calls:

        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"  -> çağrılan fonksiyon : {function_name}({function_args})")

        function_to_call = available_functions[function_name]
        function_result = function_to_call(**function_args)

        print(f"     sonuç             : {function_result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(function_result, ensure_ascii=False)
        })


# ============================================================
# AGENT LOOP
#
# Lesson 8'deki tek seferlik if/else akışını genelleştiriyoruz.
#
# Fikir basit: model tool çağırmayı bırakana (yani elinde
# nihai bir metin cevabı olana) kadar API'yi tekrar tekrar
# çağırıyoruz. Her turda:
#   1) Modele mesajları + tools şemasını gönderiyoruz.
#   2) Model tool çağırdıysa -> hepsini çalıştırıp sonucu
#      messages'a ekliyoruz, döngü devam ediyor.
#   3) Model tool çağırmadıysa -> elimizde nihai cevap var,
#      döngüden çıkıyoruz.
#
# max_turns -> modelin sonsuz döngüye girmesini engelleyen
# bir güvenlik sınırı. Üretim kodunda bu tür sınırlar olmazsa
# olmazdır.
# ============================================================

def run_agent(messages, tool_choice="auto", max_turns=5):

    for turn in range(1, max_turns + 1):

        print(f"\n--- Tur {turn} ---")

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=tools,
            # İlk turdan sonra tool_choice'u "auto"ya çeviriyoruz.
            # Aksi halde "required" gibi bir zorlama sürekli tool
            # çağırmaya devam eder ve model asla son cevabı vermez.
            tool_choice=tool_choice if turn == 1 else "auto"
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if not response_message.tool_calls:
            # Model tool çağırmadı -> elinde nihai cevap var demektir.
            print("Model tool çağırmadan cevap verdi, döngü bitti.")
            return response_message.content

        # Model bir ya da birden fazla tool çağırdı (parallel olabilir).
        print(f"Model {len(response_message.tool_calls)} tool çağrısı yaptı.")
        execute_tool_calls(response_message, messages)

    return "Maksimum tur sayısına ulaşıldı, model hâlâ tool çağırmak istiyor."


# ============================================================
# tool_choice MODLARI
#
# "auto"     -> Model tool kullanıp kullanmayacağına kendi karar
#               verir (varsayılan, lesson 8'de kullandığımız).
# "required" -> Model MUTLAKA bir tool çağırmak zorunda kalır,
#               düz metin cevap veremez.
# "none"     -> Model hiçbir tool kullanamaz, elindeki tools
#               şemasını görmezden gelir.
# {"type": "function", "function": {"name": "..."}}
#            -> Model BELİRLİ bir fonksiyonu çağırmaya zorlanır.
#               Örn: her zaman calculate ile başlamasını istiyorsak.
#
# Aşağıda bu farkı tek bir soru üzerinden canlı gösteriyoruz.
# ============================================================

def demo_tool_choice_modes():

    print("\n")
    print("=" * 60)
    print("tool_choice MODLARI DEMOSU")
    print("=" * 60)

    demo_question = "Merhaba, nasılsın?"
    demo_messages = [
        {"role": "system", "content": "Sen yardımsever bir asistansın."},
        {"role": "user", "content": demo_question}
    ]

    # "none" -> tool'lar tanımlı olsa bile model onları kullanamaz.
    none_response = client.chat.completions.create(
        model="gpt-4.1",
        messages=demo_messages,
        tools=tools,
        tool_choice="none"
    )
    print("\n[tool_choice='none']")
    print("tool_calls  :", none_response.choices[0].message.tool_calls)
    print("content     :", none_response.choices[0].message.content)

    # "required" -> soru tool gerektirmese bile model bir tool
    # çağırmak ZORUNDA kalır. Bu soruda uygun bir tool olmadığı
    # için model elindeki tool'lardan birini "zorla" seçecektir.
    required_response = client.chat.completions.create(
        model="gpt-4.1",
        messages=demo_messages,
        tools=tools,
        tool_choice="required"
    )
    print("\n[tool_choice='required']")
    print("tool_calls  :", required_response.choices[0].message.tool_calls)

    # Belirli bir fonksiyonu zorlama -> model, isteğe uymasa bile
    # calculate fonksiyonunu çağırmak zorunda kalır.
    forced_response = client.chat.completions.create(
        model="gpt-4.1",
        messages=demo_messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "calculate"}}
    )
    print("\n[tool_choice=belirli fonksiyon: 'calculate']")
    print("tool_calls  :", forced_response.choices[0].message.tool_calls)


# ============================================================
# ÇALIŞTIRMA
# ============================================================

print("=" * 60)
print("AI Engineer Road Map")
print("Lesson 9 - Tool Calling (Agent Loop & tool_choice)")
print("=" * 60)

demo_tool_choice_modes()

print("\n")
print("=" * 60)
print("AGENT LOOP DEMOSU")
print("=" * 60)
print("İpucu: hem hava durumu hem saat gerektiren bir soru sorarsan")
print("(örn: 'İstanbul'da hava nasıl ve saat kaç?'), modelin AYNI")
print("turda iki tool'u birden çağırdığını göreceksin.")

question = input("\nBir soru sorun: ")

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

final_answer = run_agent(messages, tool_choice="auto")

print("\n")
print("=" * 60)
print("NİHAİ CEVAP")
print("=" * 60)
print(final_answer)
