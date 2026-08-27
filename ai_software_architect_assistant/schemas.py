# ============================================================
# JSON Schema Tanımları
#
# Lesson 6-7'de öğrendiğimiz "Structured Outputs" tekniğini
# kullanıyoruz: modelden serbest metin yerine, önceden
# tanımladığımız bu yapıya birebir uyan bir JSON istiyoruz.
# ============================================================

ARCHITECTURE_PROPOSAL_SCHEMA = {

    "type": "json_schema",

    "json_schema": {

        # Şemanın adı.
        "name": "architecture_proposal",

        # strict=True -> model şemadan asla sapamaz.
        "strict": True,

        "schema": {

            "type": "object",

            "properties": {

                "project_name": {
                    "type": "string",
                    "description": "Projenin kısa adı."
                },

                "summary": {
                    "type": "string",
                    "description": "Mimarinin 2-3 cümlelik özeti."
                },

                "components": {
                    "type": "array",
                    "description": "Sistemi oluşturan ana bileşenler.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "responsibility": {"type": "string"},
                            "technology": {"type": "string"}
                        },
                        "required": ["name", "responsibility", "technology"],
                        "additionalProperties": False
                    }
                },

                "tech_stack": {
                    "type": "array",
                    "description": "Önerilen teknoloji listesi.",
                    "items": {"type": "string"}
                },

                "data_flow": {
                    "type": "string",
                    "description": "Verinin sistem içinde nasıl aktığının açıklaması."
                },

                "risks": {
                    "type": "array",
                    "description": "Olası riskler ve önlemleri.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "risk": {"type": "string"},
                            "mitigation": {"type": "string"}
                        },
                        "required": ["risk", "mitigation"],
                        "additionalProperties": False
                    }
                },

                "next_steps": {
                    "type": "array",
                    "description": "Uygulamaya geçmek için önerilen ilk adımlar.",
                    "items": {"type": "string"}
                }

            },

            "required": [
                "project_name",
                "summary",
                "components",
                "tech_stack",
                "data_flow",
                "risks",
                "next_steps"
            ],

            "additionalProperties": False

        }

    }

}
