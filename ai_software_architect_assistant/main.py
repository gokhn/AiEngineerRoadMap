# ============================================================
# AI Software Architect Assistant
#
# phase_01_llm_fundamentals'daki 10 dersin tekniklerini tek bir
# mini projede birleştiren bir CLI asistanı:
#
#   - Prompt Engineering    (lesson 2) -> SYSTEM_PROMPT
#   - Context Management    (lesson 3) -> messages listesi + /reset
#   - Model Parameters      (lesson 4) -> /temp komutu
#   - Streaming             (lesson 5) -> sohbet cevapları
#   - Structured Outputs    (lesson 6-7) -> /proposal komutu
#   - Function/Tool Calling (lesson 8-9) -> agent loop + tools.py
#   - Multimodal            (lesson 10) -> /image komutu
#
# Asistan, kullanıcıyla bir yazılım projesinin mimarisi üzerine
# sohbet eder; istenirse yapılandırılmış bir mimari öneri (JSON)
# üretir ve isterse bunu markdown olarak diske kaydeder.
# ============================================================

import sys
import json
import base64
from pathlib import Path

# config.py repo kökünde yaşıyor. Bu dosya nereden çalıştırılırsa
# çalıştırılsın kökü bulup sys.path'e ekliyoruz ki "import config"
# her koşulda çalışsın.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from openai import OpenAI

from schemas import ARCHITECTURE_PROPOSAL_SCHEMA
from tools import tools, available_functions, save_architecture_doc


MODEL = "gpt-4.1"
MAX_AGENT_TURNS = 5

client = OpenAI(api_key=config.OPENAI_API_KEY)


SYSTEM_PROMPT = """
Sen deneyimli bir Yazılım Mimarısın (Senior Software Architect).

Görevin, kullanıcıyla birlikte bir yazılımın mimarisini netleştirmek:
- Gereksinimleri anlamak için gerekirse netleştirici sorular sor.
- Bileşenleri, veri akışını, teknoloji seçimlerini ve trade-off'ları açıkça anlat.
- Kesin cevaplar yerine gerekçeli öneriler sun.
- Karmaşıklık tahmini veya teknoloji karşılaştırması gerektiğinde elindeki
  araçları (tool) kullan.
- Türkçe ve öğretici bir dille, gereksiz uzatmadan cevap ver.
"""

# Mimari kararlarda tutarlılık istediğimiz için düşük tutuyoruz.
# /temp komutuyla sohbet sırasında değiştirilebilir.
TEMPERATURE = 0.4


# ============================================================
# GÖRÜNTÜ YARDIMCI FONKSİYONU (lesson 10)
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
# STREAMING AGENT LOOP (lesson 5 + lesson 9 birleşimi)
#
# Model tool çağırmayı bırakıp elinde nihai bir metin cevabı
# olana kadar döner. Lesson 9'daki agent loop'tan farkı: burada
# stream=True kullanıyoruz, bu yüzden hem metin parçalarını
# (delta.content) hem de tool çağrısı parçalarını
# (delta.tool_calls) chunk chunk kendimiz topluyoruz.
# ============================================================

def run_agent_turn(messages, tool_choice="auto"):

    for turn in range(1, MAX_AGENT_TURNS + 1):

        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice if turn == 1 else "auto",
            temperature=TEMPERATURE,
            stream=True,
        )

        content = ""
        # index -> {"id":..., "name":..., "arguments":...}
        # Parça parça gelen tool çağrılarını burada birleştiriyoruz.
        tool_call_chunks = {}
        header_printed = False

        for chunk in stream:

            delta = chunk.choices[0].delta

            if delta.content:
                if not header_printed:
                    print("\nMimar: ", end="", flush=True)
                    header_printed = True
                print(delta.content, end="", flush=True)
                content += delta.content

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    entry = tool_call_chunks.setdefault(
                        tc_delta.index, {"id": None, "name": "", "arguments": ""}
                    )
                    if tc_delta.id:
                        entry["id"] = tc_delta.id
                    if tc_delta.function and tc_delta.function.name:
                        entry["name"] += tc_delta.function.name
                    if tc_delta.function and tc_delta.function.arguments:
                        entry["arguments"] += tc_delta.function.arguments

        if content:
            print()  # streaming bitince satırı kapat

        if not tool_call_chunks:
            # Model tool çağırmadı -> elinde nihai cevap var.
            messages.append({"role": "assistant", "content": content})
            return content

        # Tool çağrıları tamamlandı, sırayla çalıştırıp sonuçları ekleyelim.
        tool_calls_list = [
            {
                "id": entry["id"],
                "type": "function",
                "function": {"name": entry["name"], "arguments": entry["arguments"]},
            }
            for entry in tool_call_chunks.values()
        ]

        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls_list,
        })

        print(f"\n[Model {len(tool_calls_list)} araç çağırdı]")

        for tool_call in tool_calls_list:
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])

            print(f"  -> çağrılan araç : {function_name}({function_args})")

            function_result = available_functions[function_name](**function_args)

            print(f"     sonuç         : {function_result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(function_result, ensure_ascii=False),
            })

    print("\nMimar: Maksimum tur sayısına ulaşıldı, cevabı tamamlayamadım.")
    return None


# ============================================================
# STRUCTURED OUTPUT: /proposal KOMUTU (lesson 6-7)
# ============================================================

def generate_proposal(messages):

    print("\n" + "=" * 60)
    print("YAPILANDIRILMIŞ MİMARİ ÖNERİSİ ÜRETİLİYOR...")
    print("=" * 60)

    proposal_messages = messages + [
        {
            "role": "user",
            "content": "Şimdiye kadarki konuşmaya dayanarak resmi bir mimari önerisi hazırla.",
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=proposal_messages,
        response_format=ARCHITECTURE_PROPOSAL_SCHEMA,
        temperature=TEMPERATURE,
    )

    proposal = json.loads(response.choices[0].message.content)
    print_proposal(proposal)
    return proposal


def print_proposal(proposal):

    print(f"\nProje            : {proposal['project_name']}")
    print(f"Özet             : {proposal['summary']}")

    print("\nBileşenler:")
    for component in proposal["components"]:
        print(f"  - {component['name']} ({component['technology']}): {component['responsibility']}")

    print("\nTeknoloji Yığını :", ", ".join(proposal["tech_stack"]))

    print("\nVeri Akışı:")
    print(f"  {proposal['data_flow']}")

    print("\nRiskler:")
    for risk in proposal["risks"]:
        print(f"  - {risk['risk']} -> {risk['mitigation']}")

    print("\nSonraki Adımlar:")
    for step in proposal["next_steps"]:
        print(f"  - {step}")


def proposal_to_markdown(proposal) -> str:

    lines = [f"# {proposal['project_name']}", "", proposal["summary"], "", "## Bileşenler", ""]

    for component in proposal["components"]:
        lines.append(f"- **{component['name']}** ({component['technology']}): {component['responsibility']}")

    lines += ["", "## Teknoloji Yığını", ""]
    lines += [f"- {tech}" for tech in proposal["tech_stack"]]

    lines += ["", "## Veri Akışı", "", proposal["data_flow"], "", "## Riskler", ""]
    for risk in proposal["risks"]:
        lines.append(f"- **{risk['risk']}**: {risk['mitigation']}")

    lines += ["", "## Sonraki Adımlar", ""]
    lines += [f"- {step}" for step in proposal["next_steps"]]

    return "\n".join(lines)


# ============================================================
# MULTIMODAL: /image KOMUTU (lesson 10)
# ============================================================

def handle_image_command(argument, messages):

    image_path = argument.strip()

    if not image_path:
        print("Kullanım: /image <dosya_yolu>")
        return

    try:
        data_url = local_image_to_data_url(image_path)
    except FileNotFoundError:
        print(f"Dosya bulunamadı: {image_path}")
        return

    question = input(
        "Bu görüntü hakkında ne sormak istersin? (boş = genel değerlendirme): "
    ).strip()

    if not question:
        question = "Bu mimari diyagramı/görüntüyü bir yazılım mimarı gözüyle değerlendir."

    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    })

    run_agent_turn(messages)


# ============================================================
# KOMUTLAR VE ANA DÖNGÜ
# ============================================================

def print_help():
    print(
        "\nKomutlar:\n"
        "  <soru>          - mimarla normal sohbet et\n"
        "  /proposal       - konuşmadan yapılandırılmış bir mimari önerisi üret\n"
        "  /image <yol>    - yerel bir görüntüyü (diyagram, ekran görüntüsü) analiz ettir\n"
        "  /temp <0-2>     - model temperature değerini göster/değiştir\n"
        "  /reset          - konuşma geçmişini sıfırla\n"
        "  /help           - bu listeyi tekrar göster\n"
        "  /exit           - çık"
    )


def main():

    global TEMPERATURE

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 60)
    print("AI Software Architect Assistant")
    print("=" * 60)
    print_help()

    while True:

        user_input = input("\nSen: ").strip()

        if not user_input:
            continue

        command = user_input.lower()

        if command in ("/exit", "exit"):
            print("Görüşmek üzere.")
            break

        if command == "/help":
            print_help()
            continue

        if command == "/reset":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("Konuşma geçmişi sıfırlandı.")
            continue

        if command.startswith("/temp"):
            parts = user_input.split()
            if len(parts) == 2:
                try:
                    TEMPERATURE = max(0.0, min(2.0, float(parts[1])))
                    print(f"Temperature -> {TEMPERATURE}")
                except ValueError:
                    print("Kullanım: /temp <0.0-2.0>")
            else:
                print(f"Mevcut temperature: {TEMPERATURE}")
            continue

        if command.startswith("/image"):
            handle_image_command(user_input[len("/image"):], messages)
            continue

        if command == "/proposal":
            proposal = generate_proposal(messages)
            save_choice = input("\nMarkdown olarak kaydedilsin mi? (e/h): ").strip().lower()
            if save_choice == "e":
                filename = input("Dosya adı (uzantısız): ").strip() or "architecture-proposal"
                result = save_architecture_doc(filename, proposal_to_markdown(proposal))
                print(f"Kaydedildi: {result['saved_to']}")
            continue

        # Komut değilse normal bir sohbet mesajı olarak işle.
        messages.append({"role": "user", "content": user_input})

        try:
            run_agent_turn(messages)
        except Exception as error:
            print(f"\nBir hata oluştu: {error}")
            if messages and messages[-1]["role"] == "user":
                messages.pop()


if __name__ == "__main__":
    main()
