import sqlite3
from datetime import datetime, timedelta

DB_PATH = "faq_radar.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS interacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT NOT NULL,
        resposta TEXT NOT NULL,
        respondido INTEGER NOT NULL CHECK (respondido IN (0, 1)),
        topico TEXT NOT NULL,
        latencia_ms INTEGER NOT NULL,
        criado_em TEXT NOT NULL
    );
    """
    with get_connection() as conn:
        conn.execute(ddl)
        total = conn.execute("SELECT COUNT(*) FROM interacoes;").fetchone()[0]
        if total == 0:
            seed_dados_iniciais(conn)


def seed_dados_iniciais(conn):
    base_time = datetime.now() - timedelta(days=2)
    registros = [
        (
            "Vocês fazem entrega para Portugal?",
            "Não encontrei essa informação na política atual ou ainda não atendemos essa demanda. Registrei sua dúvida para nossa equipe avaliar.",
            0,
            "Entrega Internacional",
            410,
        ),
        (
            "Qual o prazo de entrega para capitais?",
            "O prazo padrão para capitais é de 3 a 7 dias úteis após a confirmação do pagamento.",
            1,
            "Frete e Prazos",
            380,
        ),
        (
            "Consigo pagar com Pix parcelado?",
            "Não encontrei essa opção na nossa política de pagamentos. Aceitamos apenas Pix à vista com 5% de desconto.",
            0,
            "Pix Parcelado",
            395,
        ),
        (
            "Vocês emitem nota fiscal e vendem para CNPJ?",
            "Atendemos exclusivamente consumidores finais (CPF); ainda não possuímos canal de vendas B2B ou faturamento para CNPJ.",
            1,
            "Vendas Corporativas (CNPJ)",
            350,
        ),
        (
            "Tem como enviar via motoboy no mesmo dia em São Paulo?",
            "Não encontrei essa modalidade de entrega na nossa política oficial. Registrei sua solicitação para análise do time de logística.",
            0,
            "Entrega Expressa / Motoboy",
            430,
        ),
        (
            "Como funciona a devolução por arrependimento?",
            "Você tem até 7 dias corridos após o recebimento para solicitar a devolução, desde que o produto esteja lacrado e na embalagem original.",
            1,
            "Trocas e Devoluções",
            360,
        ),
        (
            "Vocês aceitam Pix parcelado em 4x?",
            "No momento aceitamos apenas Pix à vista. Registrei seu interesse em Pix parcelado para nossa equipe.",
            0,
            "Pix Parcelado",
            405,
        ),
        (
            "Qual o valor mínimo para frete grátis?",
            "O frete é grátis para compras acima de R$ 250,00 destinadas às regiões Sul, Sudeste e Centro-Oeste.",
            1,
            "Frete e Prazos",
            340,
        ),
        (
            "Posso retirar o produto em alguma loja física?",
            "Não há informação sobre retirada em loja física na nossa política de atendimento. Registrei sua dúvida para o time.",
            0,
            "Retirada em Loja Física",
            415,
        ),
        (
            "Entrega nos Estados Unidos?",
            "Não realizamos entregas internacionais no momento; atendemos apenas todo o território nacional (Brasil).",
            1,
            "Entrega Internacional",
            375,
        ),
    ]

    insert_sql = """
    INSERT INTO interacoes (pergunta, resposta, respondido, topico, latencia_ms, criado_em)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    for idx, (perg, resp, status, topico, lat) in enumerate(registros):
        timestamp = (base_time + timedelta(hours=idx * 3)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(insert_sql, (perg, resp, status, topico, lat, timestamp))
    conn.commit()


def registrar_interacao(pergunta: str, resposta: str, respondido: bool, topico: str, latencia_ms: int) -> str:
    query = """
    INSERT INTO interacoes (pergunta, resposta, respondido, topico, latencia_ms, criado_em)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(query, (pergunta, resposta, int(respondido), topico, latencia_ms, agora))
        conn.commit()
    return query.strip()


def obter_metricas_gerais():
    query = """
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN respondido = 1 THEN 1 ELSE 0 END) AS respondidas,
        SUM(CASE WHEN respondido = 0 THEN 1 ELSE 0 END) AS nao_respondidas,
        ROUND(AVG(latencia_ms), 0) AS latencia_media
    FROM interacoes;
    """
    with get_connection() as conn:
        row = conn.execute(query).fetchone()
    return {
        "total": row[0] or 0,
        "respondidas": row[1] or 0,
        "nao_respondidas": row[2] or 0,
        "latencia_media": int(row[3] or 0),
        "sql": query.strip(),
    }


def obter_radar_lacunas():
    query = """
    SELECT
        topico AS "Tópico da Dúvida",
        COUNT(*) AS "Ocorrências",
        MAX(pergunta) AS "Exemplo de Pergunta do Cliente",
        MAX(criado_em) AS "Último Registro"
    FROM interacoes
    WHERE respondido = 0
    GROUP BY topico
    ORDER BY COUNT(*) DESC, MAX(criado_em) DESC;
    """
    with get_connection() as conn:
        cursor = conn.execute(query)
        colunas = [desc[0] for desc in cursor.description]
        dados = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    return dados, query.strip()


def obter_historico(filtro: str = "Todos"):
    if filtro == "Sem Resposta (Radar)":
        where_clause = "WHERE respondido = 0"
    elif filtro == "Respondidas":
        where_clause = "WHERE respondido = 1"
    else:
        where_clause = ""

    query = f"""
    SELECT
        id AS "ID",
        CASE WHEN respondido = 1 THEN '✅ Respondida' ELSE '🚨 Sem Resposta' END AS "Status",
        topico AS "Tópico",
        pergunta AS "Pergunta",
        resposta AS "Resposta do Bot",
        latencia_ms AS "Latência (ms)",
        criado_em AS "Data/Hora"
    FROM interacoes
    {where_clause}
    ORDER BY id DESC;
    """
    with get_connection() as conn:
        cursor = conn.execute(query)
        colunas = [desc[0] for desc in cursor.description]
        dados = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    return dados, query.strip()
