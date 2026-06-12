import os
import sqlite3
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. CARREGAMENTO DE VARIÁVEIS DE AMBIENTE ---
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_REMETENTE = os.getenv("SMTP_EMAIL_REMETENTE")
EMAIL_SENHA_APP = os.getenv("SMTP_SENHA_APP")
EMAIL_DESTINATARIO = os.getenv("SMTP_EMAIL_DESTINATARIO")

if not all([GEMINI_KEY, EMAIL_REMETENTE, EMAIL_SENHA_APP, EMAIL_DESTINATARIO]):
    logging.warning("AVISO: Variáveis de ambiente ausentes no arquivo .env.")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
else:
    modelo_ia = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AuditoriaBancariaSOTA")

DB_NAME = "inteligencia_bancaria.db"

def obter_conexao_db():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def inicializar_banco():
    with obter_conexao_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_sistemico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                banco TEXT,
                score_sistemico REAL,
                rating_global TEXT,
                roe_stressado REAL,
                npl_stressado REAL,
                selic REAL,
                pib REAL,
                inflacao REAL,
                cambio REAL,
                desemprego REAL,
                risco_pais REAL,
                parecer_profundo TEXT
            )
        """)
        conn.commit()

inicializar_banco()
app = FastAPI(title="Plataforma SOTA - Multi-Agentes", version="11.0")

MEDIAS_SETOR_BR = {"roe_medio_setor": 16.5, "basileia_media_setor": 14.5, "npl_medio_setor": 3.5, "eficiencia_media_setor": 42.0}
DADOS_CAMELS_BANCOS = {
    "Itaú": {"banco": "Itaú", "ticker": "ITUB4", "roe_base": 21.0, "basileia": 15.2, "npl_base": 3.0, "eficiencia": 39.5},
    "Bradesco": {"banco": "Bradesco", "ticker": "BBDC4", "roe_base": 11.5, "basileia": 13.2, "npl_base": 5.2, "eficiencia": 47.0},
    "Banco do Brasil": {"banco": "Banco do Brasil", "ticker": "BBAS3", "roe_base": 21.5, "basileia": 16.1, "npl_base": 2.7, "eficiencia": 31.0}
}

class InputSimulacaoAvancada(BaseModel):
    banco: str; selic: float; pib: float; inflacao_ipca: float; cambio_usd: float; desemprego: float; risco_pais_cds: float

def agente_scraping_roe(ticker: str) -> float:
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resposta = requests.get(url, headers=headers, timeout=5.0)
        if resposta.status_code != 200: return None
        soup = BeautifulSoup(resposta.text, 'html.parser')
        for td in soup.find_all('td', class_='txt'):
            if 'ROE' in td.text:
                v = td.find_next_sibling('td').text
                return float(v.replace('%', '').replace('.', '').replace(',', '.').strip())
    except: return None

def algoritmo_camels_avancado(banco_dados, params: InputSimulacaoAvancada):
    score_capital = min(max((banco_dados["basileia"] / MEDIAS_SETOR_BR["basileia_media_setor"]) * 25, 0), 25)
    fator_estresse_credito = (params.selic * 0.04) + (params.desemprego * 0.12) + (params.inflacao_ipca * 0.05)
    npl_stressado = banco_dados["npl_base"] + fator_estresse_credito
    score_ativos = min(max((MEDIAS_SETOR_BR["npl_medio_setor"] / npl_stressado) * 30, 0), 30)
    fator_estresse_lucro = (params.pib * 0.8) - (params.risco_pais_cds * 0.02) - (params.cambio_usd * 0.05)
    roe_stressado = banco_dados["roe_base"] + fator_estresse_lucro - (fator_estresse_credito * 1.2)
    score_lucro = min(max((roe_stressado / MEDIAS_SETOR_BR["roe_medio_setor"]) * 25, 0), 25)
    score_gestao = min(max((MEDIAS_SETOR_BR["eficiencia_media_setor"] / banco_dados["eficiencia"]) * 20, 0), 20)
   
    score_final = score_capital + score_ativos + score_lucro + score_gestao
    if score_final >= 88: rating = "AAA (Excelente Solvabilidade Sistémica)"
    elif score_final >= 75: rating = "AA a A (Alta Resiliência Macroeconómica)"
    elif score_final >= 55: rating = "BBB (Risco Moderado / Grau de Investimento)"
    else: rating = "BB a C (Grau Especulativo / Alerta de Risco)"
    return round(score_final, 1), rating, round(npl_stressado, 2), round(roe_stressado, 2)

# --- O NOVO TRIBUNAL MULTI-AGENTE (SOTA) ---
def orquestrar_debate_multi_agente(nome_banco, params_padrao, score, rating, roe_st, npl_st, basileia_real):
    contexto_dados = f"Cenário: Selic {params_padrao.selic}%, PIB {params_padrao.pib}%, Inflação {params_padrao.inflacao_ipca}%, Desemprego {params_padrao.desemprego}%. Instituição: {nome_banco}. ROE {roe_st}%, NPL {npl_st}%, Basileia {basileia_real}%. Rating Algorítmico: {rating}."
   
    # Agente 1: O Otimista (Bull)
    prompt_bull = f"Você é um analista 'Bull' de fundo de hedge. Foque apenas nas fortalezas, capacidade de repasse de juros e resiliência de capital do banco baseado nestes dados: {contexto_dados}. Seja breve (3 linhas)."
    parecer_bull = modelo_ia.generate_content(prompt_bull).text

    # Agente 2: O Pessimista (Bear / Red Team)
    prompt_bear = f"Você é um analista 'Bear' focado em short selling e risco de contágio sistêmico. Ataque as vulnerabilidades deste banco com base na matriz macroeconômica. Ignore coisas boas: {contexto_dados}. Seja breve e agressivo nos riscos (3 linhas)."
    parecer_bear = modelo_ia.generate_content(prompt_bear).text

    # Agente 3: O Juiz (Economista-Chefe)
    prompt_juiz = f"""
    Você é o Economista-Chefe do Comitê de Risco. Avalie o debate entre seus dois analistas seniores sobre o banco {nome_banco}.
    Argumento do Agente Bull: '{parecer_bull}'
    Argumento do Agente Bear (Red Team): '{parecer_bear}'
   
    Escreva o PARECER EXECUTIVO FINAL (Veredito), cortando vieses emocionais. Entregue um parágrafo denso e formal abordando:
    1. A realidade da liquidez frente ao cenário macro.
    2. O veredito sobre a nota técnica ({rating}).
    Sem saudações, vá direto à análise técnica.
    """
    parecer_final = modelo_ia.generate_content(prompt_juiz).text
    return parecer_final

def enviar_email_sistemico(dados_consolidados, data_hoje):
    if not all([EMAIL_REMETENTE, EMAIL_SENHA_APP, EMAIL_DESTINATARIO]): return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏛️ SOTA BRIEFING: Comitê de Risco Multi-Agente - {data_hoje}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    conteudo_html = f"""
    <html><body style="font-family: Arial; padding: 20px; background-color: #f8fafc;">
        <div style="max-width: 750px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px;">
            <h2 style="color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px;">Veredito do Comitê Multi-Agente (SOTA)</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <tr style="background-color: #0f172a; color: #fff;">
                    <th style="padding: 10px; border: 1px solid #cbd5e1;">Banco</th>
                    <th style="padding: 10px; border: 1px solid #cbd5e1;">Score</th>
                    <th style="padding: 10px; border: 1px solid #cbd5e1;">Rating</th>
                </tr>
    """
    for d in dados_consolidados:
        conteudo_html += f"<tr><td style='padding: 10px; border: 1px solid #cbd5e1;'>{d['banco']}</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>{d['score']}</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>{d['rating']}</td></tr>"
    conteudo_html += "</table>"
   
    for d in dados_consolidados:
        insight_formatado = d['insight'].replace('\n', '<br>')
        conteudo_html += f"<div style='background-color: #f8fafc; padding: 15px; border-left: 5px solid #1e3a8a; margin-bottom: 20px;'><b>{d['banco']} - Veredito do Juiz:</b><br><br>{insight_formatado}</div>"
    conteudo_html += "</div></body></html>"
    msg.attach(MIMEText(conteudo_html, 'html'))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        logger.info("Briefing SOTA enviado.")
    except Exception as e: logger.error(f"Erro e-mail: {e}")

def executar_analise_sistemica_diaria():
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    dados_dia_email = []
    params_padrao = InputSimulacaoAvancada(banco="Setor", selic=10.5, pib=1.5, inflacao_ipca=4.5, cambio_usd=5.20, desemprego=7.8, risco_pais_cds=200.0)
   
    for nome_banco, banco_dados in DADOS_CAMELS_BANCOS.items():
        roe_capturado = agente_scraping_roe(banco_dados["ticker"])
        if roe_capturado: banco_dados["roe_base"] = roe_capturado
        score, rating, npl_st, roe_st = algoritmo_camels_avancado(banco_dados, params_padrao)
       
        if modelo_ia:
            parecer_final = orquestrar_debate_multi_agente(nome_banco, params_padrao, score, rating, roe_st, npl_st, banco_dados['basileia'])
        else:
            parecer_final = f"Rating algorítmico: {rating}."
           
        with obter_conexao_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historico_sistemico (data, banco, score_sistemico, rating_global, roe_stressado, npl_stressado, selic, pib, inflacao, cambio, desemprego, risco_pais, parecer_profundo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data_hoje, nome_banco, score, rating, roe_st, npl_st, params_padrao.selic, params_padrao.pib, params_padrao.inflacao_ipca, params_padrao.cambio_usd, params_padrao.desemprego, params_padrao.risco_pais_cds, parecer_final))
            conn.commit()
           
        dados_dia_email.append({"banco": nome_banco, "score": score, "rating": rating, "roe_st": roe_st, "npl_st": npl_st, "insight": parecer_final})
    enviar_email_sistemico(dados_dia_email, data_hoje)

scheduler = BackgroundScheduler()
scheduler.add_job(executar_analise_sistemica_diaria, 'cron', hour=2, minute=0)
scheduler.start()

@app.post("/rodar-rotina-manual")
def forcar_ciclo_diario():
    try: executar_analise_sistemica_diaria(); return {"status": "Sucesso"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/simular-customizado")
def simular_customizado(params: InputSimulacaoAvancada):
    if params.banco not in DADOS_CAMELS_BANCOS: raise HTTPException(status_code=404, detail="Banco não encontrado.")
    banco_dados = DADOS_CAMELS_BANCOS[params.banco]
    roe_capturado = agente_scraping_roe(banco_dados["ticker"]) or banco_dados["roe_base"]
    banco_dados["roe_base"] = roe_capturado
    score, rating, npl_st, roe_st = algoritmo_camels_avancado(banco_dados, params)
   
    if modelo_ia:
        parecer = orquestrar_debate_multi_agente(params.banco, params, score, rating, roe_st, npl_st, banco_dados['basileia'])
    else: parecer = "Simulação sem IA ativa."

    return {"score": score, "rating": rating, "kpis": {"roe": roe_st, "npl": npl_st, "basileia": banco_dados["basileia"]}, "parecer_customizado": parecer}

@app.get("/historico/{banco}")
def obter_historico(banco: str):
    with obter_conexao_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data, score_sistemico, rating_global, roe_stressado, npl_stressado, parecer_profundo FROM historico_sistemico WHERE banco = ? ORDER BY data DESC", (banco,))
        linhas = cursor.fetchall()
    return {"banco": banco, "historico": [{"data": l[0], "score": l[1], "rating": l[2], "roe": l[3], "npl": l[4], "insight": l[5]} for l in linhas]}



