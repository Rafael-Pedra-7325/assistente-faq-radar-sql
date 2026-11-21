import streamlit as st
from ai_service import consultar_assistente
from database import (
    init_db,
    obter_historico,
    obter_metricas_gerais,
    obter_radar_lacunas,
    registrar_interacao,
)
from knowledge_base import BASE_CONHECIMENTO

st.set_page_config(
    page_title="Assistente FAQ + Radar SQL",
    page_icon="💬",
    layout="wide",
)

init_db()

# Recupera chave dos Secrets (Streamlit Cloud) ou permite digitar na barra lateral
default_key = ""
try:
    default_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    default_key = ""

with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        help="Gere gratuitamente no Google AI Studio ou configure em Secrets no Streamlit Cloud.",
    )
    st.caption("A chave é usada apenas na sessão atual via requisição REST.")

    st.divider()
    with st.expander("📄 Ver Base de Conhecimento (Grounding)", expanded=False):
        st.markdown(BASE_CONHECIMENTO)

st.title("💬 Assistente de FAQ com Radar de Dúvidas (SQL + IA)")
st.markdown(
    "Chatbot treinado para responder **apenas** com base nas regras oficiais da empresa. "
    "Quando não sabe a resposta, evita alucinações e registra a lacuna em um banco **SQL**."
)

aba_chat, aba_radar = st.tabs(
    ["🤖 Chat de Atendimento", "📊 Radar de Dúvidas Sem Resposta (SQL)"]
)

# ==========================================
# ABA 1: CHAT COM ANTI-ALUCINAÇÃO
# ==========================================
with aba_chat:
    st.subheader("Teste rápido em 1 clique")
    col1, col2, col3, col4 = st.columns(4)

    pergunta_rapida = None
    if col1.button("✅ Prazo de devolução", use_container_width=True):
        pergunta_rapida = "Qual o prazo para devolver um produto que comprei por arrependimento?"
    if col2.button("✅ Frete grátis", use_container_width=True):
        pergunta_rapida = "A partir de qual valor o frete é grátis para Brasília?"
    if col3.button("🚨 Pix parcelado (Fora)", use_container_width=True):
        pergunta_rapida = "Vocês aceitam pagamento via Pix parcelado?"
    if col4.button("🚨 Retirada em loja (Fora)", use_container_width=True):
        pergunta_rapida = "Posso comprar no site e retirar em uma loja física hoje?"

    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []

    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "meta" in msg:
                meta = msg["meta"]
                if meta["respondido"]:
                    st.success(f"Respondido via Base Oficial | Tópico: **{meta['topico']}** | {meta['latencia_ms']} ms")
                else:
                    st.warning(f"Lacuna detectada e salva no Radar SQL | Tópico: **{meta['topico']}** | {meta['latencia_ms']} ms")

                with st.expander("🔍 Por baixo dos panos (JSON da API REST + SQL INSERT)"):
                    st.json(meta["raw_json"])
                    st.code(meta["sql_insert"], language="sql")

    prompt_usuario = st.chat_input("Digite uma dúvida de cliente...")
    pergunta_final = pergunta_rapida or prompt_usuario

    if pergunta_final:
        st.session_state.mensagens.append({"role": "user", "content": pergunta_final})
        with st.chat_message("user"):
            st.markdown(pergunta_final)

        with st.chat_message("assistant"):
            with st.spinner("Consultando base oficial via API REST..."):
                resultado = consultar_assistente(pergunta_final, api_key)

            if "erro" in resultado:
                st.error(resultado["erro"])
            else:
                sql_executado = registrar_interacao(
                    pergunta=pergunta_final,
                    resposta=resultado["resposta"],
                    respondido=resultado["respondido"],
                    topico=resultado["topico"],
                    latencia_ms=resultado["latencia_ms"],
                )

                st.markdown(resultado["resposta"])
                if resultado["respondido"]:
                    st.success(
                        f"Respondido via Base Oficial | Tópico: **{resultado['topico']}** | {resultado['latencia_ms']} ms"
                    )
                else:
                    st.warning(
                        f"Lacuna detectada e salva no Radar SQL | Tópico: **{resultado['topico']}** | {resultado['latencia_ms']} ms"
                    )

                with st.expander("🔍 Por baixo dos panos (JSON da API REST + SQL INSERT)"):
                    st.json(resultado["raw_json"])
                    st.code(sql_executado, language="sql")

                st.session_state.mensagens.append(
                    {
                        "role": "assistant",
                        "content": resultado["resposta"],
                        "meta": {
                            "respondido": resultado["respondido"],
                            "topico": resultado["topico"],
                            "latencia_ms": resultado["latencia_ms"],
                            "raw_json": resultado["raw_json"],
                            "sql_insert": sql_executado,
                        },
                    }
                )

# ==========================================
# ABA 2: RADAR ANALÍTICO SQL
# ==========================================
with aba_radar:
    metricas = obter_metricas_gerais()
    taxa_resolucao = (
        round((metricas["respondidas"] / metricas["total"]) * 100, 1)
        if metricas["total"] > 0
        else 0.0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Perguntas", metricas["total"])
    m2.metric("Taxa de Resolução", f"{taxa_resolucao}%")
    m3.metric("Dúvidas Sem Resposta", metricas["nao_respondidas"])
    m4.metric("Latência Média (API)", f"{metricas['latencia_media']} ms")

    st.divider()
    st.subheader("🎯 Ranking de Lacunas na Base de Conhecimento")
    st.caption("Agrupamento SQL (`WHERE respondido = 0 GROUP BY topico`) para priorizar o que deve ser adicionado ao FAQ.")

    radar_dados, sql_radar = obter_radar_lacunas()
    if radar_dados:
        st.dataframe(radar_dados, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma dúvida sem resposta registrada até o momento.")

    st.divider()
    st.subheader("📋 Histórico Completo de Interações")
    filtro = st.selectbox(
        "Filtrar registros:",
        ["Todos", "Sem Resposta (Radar)", "Respondidas"],
    )
    historico_dados, sql_historico = obter_historico(filtro)
    st.dataframe(historico_dados, use_container_width=True, hide_index=True)

    with st.expander("🗄️ Ver Queries SQL Executadas neste Painel"):
        st.markdown("**1. Métricas Agregadas:**")
        st.code(metricas["sql"], language="sql")
        st.markdown("**2. Radar de Lacunas (`GROUP BY`):**")
        st.code(sql_radar, language="sql")
        st.markdown("**3. Histórico Filtrado:**")
        st.code(sql_historico, language="sql")
