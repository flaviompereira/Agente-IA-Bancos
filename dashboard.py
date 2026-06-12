import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Plataforma de Rating Macrossistémico", layout="wide")
st.title("🏛️ Plataforma Avançada de Avaliação de Risco Bancário")

# Lê a URL da API configurada nos secrets do Streamlit Cloud, fallback para localhost
API_URL = st.secrets.get("API_URL", "http://localhost:8000")

# --- MENUS DE CONTROLO MACROECONÓMICO ---
st.sidebar.header("Matriz de Indicadores Macro")
banco = st.sidebar.selectbox("Instituição Alvo", ["Itaú", "Bradesco", "Banco do Brasil"])

selic = st.sidebar.slider("Taxa de Juros Selic (%)", 5.0, 18.0, 10.5, 0.25)
pib = st.sidebar.slider("Crescimento do PIB (%)", -4.0, 6.0, 1.5, 0.1)
inflacao = st.sidebar.slider("Inflação IPCA (%)", 1.0, 15.0, 4.5, 0.1)
cambio = st.sidebar.slider("Taxa de Câmbio (USD/BRL)", 4.0, 6.5, 5.20, 0.05)
desemprego = st.sidebar.slider("Taxa de Desemprego (%)", 4.0, 16.0, 7.8, 0.1)
risco_pais = st.sidebar.slider("Risco-País CDS (Pontos)", 80, 500, 180, 10)

st.sidebar.divider()
st.sidebar.header("Ações do Agente Autónomo")
if st.sidebar.button("🤖 Forçar Execução e Envio de E-mail Diário"):
    with st.spinner("Agente executando rotina macro prudencial profunda..."):
        try:
            res_rotina = requests.post(f"{API_URL}/rodar-rotina-manual").json()
            st.sidebar.success("Briefing completo enviado por e-mail!")
        except Exception as e:
            st.sidebar.error(f"Falha de ligação com o servidor: {e}")

# --- CORPO DA INTERFACE ---
aba1, aba2 = st.tabs(["📊 Simulação Multivariada", "📜 Histórico de Auditoria (DB)"])

with aba1:
    if st.button("Executar Teste de Estresse Ponderado"):
        url = f"{API_URL}/simular-customizado"
        payload = {
            "banco": banco, "selic": selic, "pib": pib, "inflacao_ipca": inflacao,
            "cambio_usd": cambio, "desemprego": desemprego, "risco_pais_cds": risco_pais
        }
       
        with st.spinner("Processando correlações sistémicas..."):
            try:
                res = requests.post(url, json=payload).json()
               
                if "erro" in res:
                    st.error(res["erro"])
                else:
                    st.subheader(f"📋 Resultado do Cenário de Estresse - {banco}")
                    c1, c2 = st.columns(2)
                    c1.metric("Score de Resiliência Global", f"{res['score']} / 100")
                    c2.subheader(f"Classificação Prudencial: {res['rating']}")
                   
                    st.divider()
                    kpis = res["kpis"]
                    col1, col2, col3 = st.columns(3)
                    col1.metric("ROE Ajustado", f"{kpis['roe']}%")
                    col2.metric("NPL Projetado (Inadimplência)", f"{kpis['npl']}%")
                    col3.metric("Rácio de Capital (Basileia III)", f"{kpis['basileia']}%")
                   
                    st.divider()
                    st.markdown("#### 🤖 Parecer Rápido do Agente")
                    st.info(res["parecer_customizado"])
               
            except Exception as e:
                st.error(f"Erro ao conectar ao back-end: {e}")

with aba2:
    st.subheader(f"📋 Histórico Registado para: {banco}")
    try:
        resposta = requests.get(f"{API_URL}/historico/{banco}").json()
        historico = resposta.get("historico", [])
       
        if historico:
            df = pd.DataFrame(historico)
           
            st.markdown(f"#### 🏛️ Último Parecer Técnico Académico Gravado ({historico[0]['data']})")
            st.write(historico[0]['insight'])
           
            st.divider()
            st.markdown("#### Curva Temporal de Resiliência")
            st.line_chart(df.iloc[::-1].set_index("data")["score"])
           
            st.divider()
            st.markdown("#### Livro de Registos (Auditoria de Dados)")
            st.dataframe(df[["data", "score", "rating", "roe", "npl"]])
        else:
            st.info("Nenhum dado gravado no histórico. Force a execução na barra lateral.")
    except Exception as e:
        st.error(f"Erro ao ler registos do servidor: {e}")

