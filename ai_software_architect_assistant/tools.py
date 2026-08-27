# ============================================================
# Tool Calling - Mimari Asistanın Kullanabileceği Araçlar
#
# Lesson 8-9'da gördüğümüz function/tool calling mekaniğini
# gerçek bir senaryoya uyguluyoruz. Model, sohbet sırasında
# ihtiyaç duyarsa bu fonksiyonlardan birini "çağırmak" ister,
# biz de gerçek Python fonksiyonunu çalıştırıp sonucu modele
# geri veririz.
# ============================================================

import json
from pathlib import Path


def estimate_complexity(feature: str) -> dict:
    """Bir özelliğin geliştirme karmaşıklığını kabaca tahmin eder (mock)."""

    word_count = len(feature.split())

    if word_count <= 3:
        level, effort = "Düşük", "1-3 gün"
    elif word_count <= 8:
        level, effort = "Orta", "1-2 hafta"
    else:
        level, effort = "Yüksek", "3-6 hafta"

    return {
        "feature": feature,
        "complexity": level,
        "estimated_effort": effort,
        "note": "Bu kaba bir tahmindir, gerçek bir planlama aracı değildir."
    }


def compare_technologies(option_a: str, option_b: str, criteria: str) -> dict:
    """İki teknolojiyi verilen kritere göre karşılaştırmak için bağlam üretir (mock)."""

    return {
        "option_a": option_a,
        "option_b": option_b,
        "criteria": criteria,
        "note": (
            f"'{criteria}' kriterine göre kesin bir kazanan yoktur; karar "
            "ekibin tecrübesine, ölçeklenme ihtiyacına ve operasyonel "
            "maliyete bağlıdır. Asistan bu farkları sohbette değerlendirir."
        )
    }


def save_architecture_doc(filename: str, content: str) -> dict:
    """Verilen içeriği proje klasöründeki 'output' alt klasörüne markdown olarak kaydeder."""

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    if not filename.endswith(".md"):
        filename += ".md"

    file_path = output_dir / filename
    file_path.write_text(content, encoding="utf-8")

    return {
        "saved_to": str(file_path),
        "size_bytes": len(content.encode("utf-8"))
    }


# İsim -> gerçek Python fonksiyonu eşlemesi.
# Model bir tool çağırdığında, hangi fonksiyonu çalıştıracağımızı
# buradan buluyoruz.
available_functions = {
    "estimate_complexity": estimate_complexity,
    "compare_technologies": compare_technologies,
    "save_architecture_doc": save_architecture_doc,
}


# ============================================================
# TOOLS ŞEMASI
#
# Modele hangi araçların var olduğunu ve nasıl çağrılacağını
# anlatan JSON Schema tanımları.
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "estimate_complexity",
            "description": (
                "Tek bir özelliğin/gereksinimin geliştirme karmaşıklığını "
                "ve kabaca süresini tahmin eder."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "feature": {
                        "type": "string",
                        "description": "Karmaşıklığı tahmin edilecek özellik. Örn: 'gerçek zamanlı bildirim sistemi'"
                    }
                },
                "required": ["feature"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_technologies",
            "description": "İki teknoloji/aracı belirli bir kritere göre karşılaştırmak için kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "option_a": {"type": "string", "description": "Birinci teknoloji. Örn: 'PostgreSQL'"},
                    "option_b": {"type": "string", "description": "İkinci teknoloji. Örn: 'MongoDB'"},
                    "criteria": {"type": "string", "description": "Karşılaştırma kriteri. Örn: 'yazma performansı'"}
                },
                "required": ["option_a", "option_b", "criteria"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_architecture_doc",
            "description": (
                "Üzerinde konuşulan mimari notlarını markdown formatında diske "
                "kaydeder. Kullanıcı 'kaydet' dediğinde kullanılır."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Kaydedilecek dosya adı. Örn: 'e-ticaret-mimarisi'"},
                    "content": {"type": "string", "description": "Markdown formatında dosya içeriği."}
                },
                "required": ["filename", "content"],
                "additionalProperties": False
            }
        }
    }
]


def execute_tool_calls(response_message, messages):
    """
    response_message.tool_calls içindeki her çağrıyı çalıştırır ve
    sonucu bir "tool" mesajı olarak messages listesine ekler.

    (Streaming olmayan / SDK mesaj nesnesi ile çalışan akışlar için.
    Streaming agent loop'u, parça parça gelen tool_call verisini kendi
    içinde topladığından bu fonksiyonu kullanmaz.)
    """

    for tool_call in response_message.tool_calls:

        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"  -> çağrılan araç : {function_name}({function_args})")

        function_to_call = available_functions[function_name]
        function_result = function_to_call(**function_args)

        print(f"     sonuç         : {function_result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(function_result, ensure_ascii=False)
        })
