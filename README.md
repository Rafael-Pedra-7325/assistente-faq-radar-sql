[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://assistente-faq-radar-sql.streamlit.app/)
# 💬 Assistente de FAQ com Radar de Dúvidas (Python + SQL + API REST + IA)

Chatbot de atendimento ao cliente projetado para responder **exclusivamente** com base na política oficial da empresa (prevenção de alucinações via *grounding* e saída estruturada em JSON) e registrar automaticamente perguntas não respondidas em um banco **SQL** para análise de lacunas de conhecimento.

## 🎯 Dor Real Resolvida
Em operações de atendimento digital, chatbots tradicionais sofrem de dois problemas críticos:
1. **Alucinação:** Inventam prazos, descontos ou políticas que não existem quando não encontram a resposta na base.
2. **Cegueira de Negócio:** Gestores não sabem quais dúvidas recorrentes dos clientes estão ficando sem resposta para atualizar o FAQ.

## ⚙️ Arquitetura e Stack Técnica
- **Python 3 + Streamlit:** Interface interativa com botões de teste rápido e painel de observabilidade.
- **Consumo de API REST (`requests`):** Integração direta via HTTP POST com a API do Gemini (`gemini-2.5-flash`), forçando resposta estruturada (`application/json`) e medindo latência em milissegundos.
- **Banco de Dados Relacional (`SQLite` + SQL Puro):** Persistência de logs (`INSERT`) e consultas analíticas (`GROUP BY`, `CASE WHEN`, agregações) sem depender de ORMs pesados.

## 🚀 Como Executar Localmente

```bash
git clone [https://github.com/Rafael-Pedra-7325/assistente-faq-radar-sql.git](https://github.com/Rafael-Pedra-7325/assistente-faq-radar-sql.git)
cd assistente-faq-radar-sql
pip install -r requirements.txt
streamlit run app.py
