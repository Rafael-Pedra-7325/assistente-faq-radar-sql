import json
import time
import requests
from knowledge_base import BASE_CONHECIMENTO

GEMINI_REST_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)


def consultar_assistente(pergunta: str, api_key: str) -> dict:
    if not api_key or not api_key.strip():
        return {
            "erro": "Chave de API não informada. Insira sua Gemini API Key na barra lateral para testar ao vivo."
        }

    system_prompt = f"""
Você é um assistente virtual de atendimento ao cliente da NovaTech Store.
Sua missão é responder à pergunta do cliente usando EXCLUSIVAMENTE as informações contidas na BASE DE CONHECIMENTO abaixo.

REGRAS ESTRITAS ANTI-ALUCINAÇÃO:
1. Nunca invente, deduza ou presuma políticas, prazos, formas de pagamento ou serviços que não estejam explicitamente escritos na base.
2. Se a base responder completamente à dúvida do cliente, defina "respondido" como true e escreva uma resposta clara, cordial e objetiva.
3. Se a pergunta abordar qualquer assunto ausente ou não coberto pela base, defina "respondido" como false e responda educadamente que essa informação não consta na política oficial e que a dúvida foi registrada para a equipe.
4. Classifique a pergunta em um "topico" curto de 2 a 4 palavras (ex: "Frete e Prazos", "Pix Parcelado", "Garantia", "Retirada em Loja").

Retorne OBRIGATORIAMENTE um JSON válido no formato:
{{
  "respondido": true ou false,
  "topico": "Categoria curta da dúvida",
  "resposta": "Texto da resposta ao cliente"
}}

BASE DE CONHECIMENTO:
{BASE_CONHECIMENTO}
"""

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": pergunta}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    inicio = time.perf_counter()
    try:
        response = requests.post(
            GEMINI_REST_URL,
            params={"key": api_key.strip()},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        latencia_ms = int((time.perf_counter() - inicio) * 1000)

        if response.status_code != 200:
            return {
                "erro": f"Erro HTTP {response.status_code} na API REST: {response.text[:200]}"
            }

        body = response.json()
        texto_json = body["candidates"][0]["content"]["parts"][0]["text"]
        resultado = json.loads(texto_json)

        return {
            "respondido": bool(resultado.get("respondido", False)),
            "topico": str(resultado.get("topico", "Geral")).strip(),
            "resposta": str(resultado.get("resposta", "")).strip(),
            "latencia_ms": latencia_ms,
            "raw_json": resultado,
        }

    except requests.exceptions.Timeout:
        return {"erro": "Tempo limite excedido ao chamar a API REST (Timeout)."}
    except Exception as e:
        return {"erro": f"Falha ao processar resposta da API: {str(e)}"}
