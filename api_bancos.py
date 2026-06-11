from fastapi import FastAPI
from pydantic import BaseModel

# Inicializando a API
app = FastAPI(title="API do Agente Bancário IA", version="1.0")

# Estrutura dos dados que a API vai receber do Dashboard
class ParametrosSimulacao(BaseModel):
    banco: str
    selic: float
    crescimento_pib: float

# Banco de Dados Mock (Cobaia) para testes iniciais
bancos_db = {
    "Itaú": {"roe_base": 20.5, "basileia_base": 15.2, "npl_base": 3.1, "nii_base": 25.0},
    "Bradesco": {"roe_base": 11.2, "basileia_base": 13.5, "npl_base": 5.4, "nii_base": 15.5},
    "Nubank": {"roe_base": 23.0, "basileia_base": 18.1, "npl_base": 5.5, "nii_base": 8.0}
}

@app.get("/")
def home():
    return {"status": "API do Agente Bancário Operacional"}

@app.get("/bancos")
def listar_bancos():
    """Retorna a lista de bancos disponíveis no sistema."""
    return {"bancos": list(bancos_db.keys())}

@app.post("/simular")
def simular_cenario(params: ParametrosSimulacao):
    """
    O Agente Matemático atua aqui.
    Recebe os dados do cenário e recalcula as métricas.
    """
    if params.banco not in bancos_db:
        return {"erro": "Banco não encontrado no banco de dados."}
        
    dados_base = bancos_db[params.banco]
    
    # --- Lógica de Simulação do Agente Matemático ---
    # Premissa básica: Alta da Selic aumenta a inadimplência (NPL) e derruba o ROE.
    # A Selic base atual considerada para o cálculo mock é de 10.5%.
    impacto_selic = (params.selic - 10.5) * 0.15 
    
    npl_simulado = dados_base["npl_base"] + impacto_selic
    roe_simulado = dados_base["roe_base"] - (impacto_selic * 1.8) + (params.crescimento_pib * 0.5)
    
    # Evitando que métricas fiquem negativas por conta de extrapolações irreais
    npl_simulado = max(0.0, npl_simulado)
    
    # Gerando o Insight em texto
    insight = (
        f"Com a simulação da Selic a {params.selic}% e PIB a {params.crescimento_pib}%, "
        f"estimamos que a inadimplência do {params.banco} seja de {round(npl_simulado, 2)}%, "
        f"levando o ROE projetado para {round(roe_simulado, 2)}%."
    )
    
    # Retornando o pacote completo para o Front-end
    return {
        "banco": params.banco,
        "kpis": {
            "roe_projetado": round(roe_simulado, 2),
            "basileia_projetada": dados_base["basileia_base"], # Mantido estático no exemplo
            "inadimplencia_npl": round(npl_simulado, 2),
            "nii": dados_base["nii_base"]
        },
        "insight_agente": insight
    }
