# ============================================================
# Lesson 10
# Multimodal Basics (Görüntü + Metin)
#
# Şimdiye kadar modele hep METİN gönderdik. Ama chat modelleri
# (gpt-4.1 gibi) aynı mesaj içinde METİN + GÖRÜNTÜ'yü birlikte
# kabul edebilir. Buna "multimodal input" diyoruz.
#
# Mekanik olarak tek fark: "content" alanı artık düz bir string
# değil, bir LİSTE. Listenin içinde birden fazla "part" olabilir:
#
#   {"type": "text", "text": "..."}
#   {"type": "image_url", "image_url": {"url": "...", "detail": "..."}}
#
# Görüntüyü modele iki şekilde verebiliriz:
#   1) Herkese açık bir URL (model resmi kendi indirir)
#   2) base64 data URL (yerel dosyayı biz kodlayıp gömeriz)
#
# Bu derste dört şeyi göreceğiz:
#   1) URL ile tek görüntü analizi
#   2) Yerel dosyayı base64'e çevirip gönderme
#   3) Aynı mesajda BİRDEN FAZLA görüntü (karşılaştırma)
#   4) "detail" parametresi (low / high / auto) -> kalite/maliyet dengesi
# ============================================================

import base64
import config
from openai import OpenAI


# ============================================================
# OpenAI Client
# ============================================================

client = OpenAI(
    api_key=config.OPENAI_API_KEY
)

MODEL = "gpt-4.1"


# ============================================================
# YEREL GÖRÜNTÜYÜ base64 DATA URL'E ÇEVİRME
#
# API'ye URL veremediğimiz (örn. kendi bilgisayarımızdaki bir
# dosya) durumlarda görüntüyü base64 string'e çevirip
# "data:image/<uzantı>;base64,<veri>" formatında göndeririz.
# Model bunu, herkese açık bir URL'den farksız şekilde okur.
# ============================================================

def local_image_to_data_url(image_path: str) -> str:

    extension = image_path.rsplit(".", 1)[-1].lower()

    mime_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    mime_type = mime_types.get(extension, "image/jpeg")

    with open(image_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# DEMO 1: URL İLE TEK GÖRÜNTÜ ANALİZİ
#
# En basit senaryo: internette duran bir görüntünün URL'ini
# doğrudan "image_url" içine veriyoruz, model kendisi indirip
# okuyor.
# ============================================================

def demo_image_from_url():

    print("\n")
    print("=" * 60)
    print("DEMO 1: URL'den Görüntü Analizi")
    print("=" * 60)

    image_url = "https://www.visualwatermark.com/images/posts/how-to-add-text-to-picture.jpg"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Bu görüntüde ne görüyorsun? Kısaca anlat."},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    print("\nGörüntü URL:", image_url)
    print("\nModelin cevabı:")
    print(response.choices[0].message.content)


# ============================================================
# DEMO 2: YEREL DOSYADAN GÖRÜNTÜ ANALİZİ (base64)
#
# Kullanıcıdan bir dosya yolu istiyoruz. Dosya bulunamazsa ya
# da boş bırakılırsa demoyu atlıyoruz -- bu ders için bir
# görüntü dosyası şart değil.
# ============================================================

def demo_image_from_local_file():

    print("\n")
    print("=" * 60)
    print("DEMO 2: Yerel Dosyadan Görüntü Analizi (base64)")
    print("=" * 60)

    image_path = input(
        "\nAnaliz edilecek yerel bir görüntü dosyasının yolu "
        "(atlamak için boş bırakıp Enter'a basın): "
    ).strip()

    if not image_path:
        print("Atlandı.")
        return

    try:
        data_url = local_image_to_data_url(image_path)
    except FileNotFoundError:
        print(f"Dosya bulunamadı: {image_path}")
        return

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Bu görüntüde ne görüyorsun? Kısaca anlat."},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    print("\nModelin cevabı:")
    print(response.choices[0].message.content)


# ============================================================
# DEMO 3: BİRDEN FAZLA GÖRÜNTÜ (KARŞILAŞTIRMA)
#
# "content" listesine ikinci bir image_url part'ı daha ekleyerek
# modelden iki görüntüyü KARŞILAŞTIRMASINI isteyebiliriz. Model,
# hangi görüntünün "birinci", hangisinin "ikinci" olduğunu
# mesajdaki sırayla anlar.
# ============================================================

def demo_multiple_images():

    print("\n")
    print("=" * 60)
    print("DEMO 3: Birden Fazla Görüntü Karşılaştırma")
    print("=" * 60)

    image_url_1 = "https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"
    image_url_2 = "https://upload.wikimedia.org/wikipedia/commons/b/b6/Felis_catus-cat_on_snow.jpg"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Bu iki görüntü arasındaki en belirgin farkı tek cümleyle söyle."},
                {"type": "image_url", "image_url": {"url": image_url_1}},
                {"type": "image_url", "image_url": {"url": image_url_2}}
            ]
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    print("\nGörüntü 1:", image_url_1)
    print("Görüntü 2:", image_url_2)
    print("\nModelin cevabı:")
    print(response.choices[0].message.content)


# ============================================================
# DEMO 4: "detail" PARAMETRESİ (low / high / auto)
#
# image_url.detail üç değer alabilir:
#   "low"  -> görüntü düşük çözünürlükte işlenir. Sabit ve düşük
#             token maliyeti, ama küçük detaylar (yazı, ince
#             çizgiler) kaçabilir. Hızlı/ucuz demek.
#   "high" -> görüntü yüksek çözünürlükte, parçalara bölünerek
#             işlenir. Daha fazla token harcar ama küçük
#             detayları da yakalar.
#   "auto" -> (varsayılan) modelin görüntü boyutuna göre kendi
#             karar vermesini sağlar.
#
# Aynı görüntüyü "low" ve "high" ile sorgulayıp, kullanılan
# token sayısındaki farkı canlı görelim.
# ============================================================

def demo_detail_parameter():

    print("\n")
    print("=" * 60)
    print("DEMO 4: 'detail' Parametresi (low vs high)")
    print("=" * 60)

    image_url = "https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"
    question = "Bu görüntüde ne var? Tek cümleyle özetle."

    for detail_level in ("low", "high"):

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": detail_level}}
                ]
            }
        ]

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        print(f"\n[detail='{detail_level}']")
        print("cevap        :", response.choices[0].message.content)
        print("prompt_tokens:", response.usage.prompt_tokens)


# ============================================================
# ÇALIŞTIRMA
# ============================================================

print("=" * 60)
print("AI Engineer Road Map")
print("Lesson 10 - Multimodal Basics (Görüntü + Metin)")
print("=" * 60)

demo_image_from_url()
demo_image_from_local_file()
demo_multiple_images()
demo_detail_parameter()
