import json
import time
import requests
from knowledge_base import BASE_CONHECIMENTO

BASE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
MODELOS_CANDIDATOS = [
    "gemini-3.8-flash",
    "gemini-3.8-flash-lite",
    "gemini-3.5-flash",
]


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
    ultimo_erro = "Nenhum modelo respondeu."

    for modelo in MODELOS_CANDIDATOS:
        url = f"{BASE_API_URL}/{modelo}:generateContent"

        for tentativa in range(2):
            try:
                response = requests.post(
                    url,
                    params={"key": api_key.strip()},
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=20,
                )

                if response.status_code == 200:
                    latencia_ms = int((time.perf_counter() - inicio) * 1000)
                    body = response.json()
                    texto_json = body["candidates"][0]["content"]["parts"][0]["text"]
                    resultado = json.loads(texto_json)
                    resultado["_modelo_utilizado"] = modelo

                    return {
                        "respondido": bool(resultado.get("respondido", False)),
                        "topico": str(resultado.get("topico", "Geral")).strip(),
                        "resposta": str(resultado.get("resposta", "")).strip(),
                        "latencia_ms": latencia_ms,
                        "raw_json": resultado,
                    }

                # Chave inválida ou erro de requisição: não adianta tentar outros modelos
                if response.status_code in (400, 401, 403):
                    return {
                        "erro": f"Erro de autenticação/requisição ({response.status_code}): verifique sua Gemini API Key."
                    }

                # 503 (alta demanda) ou 429 (rate limit): espera breve e tenta novamente antes de trocar de modelo
                if response.status_code in (429, 503):
                    ultimo_erro = f"Servidor temporariamente sobrecarregado (HTTP {response.status_code} no {modelo})."
                    if tentativa == 0:
                        time.sleep(1.5)
                        continue
                    break

                # 404 ou outro status específico do modelo: pula direto para o próximo modelo da lista
                ultimo_erro = f"HTTP {response.status_code} em {modelo}"
                break

            except requests.exceptions.Timeout:
                ultimo_erro = f"Timeout ao consultar {modelo}."
                break
            except Exception as e:
                ultimo_erro = f"Falha ao processar resposta ({modelo}): {str(e)}"
                break

    return {
        "erro": f"Os modelos de IA estão com alta demanda no momento ({ultimo_erro}). Aguarde alguns segundos e clique novamente."
    }
