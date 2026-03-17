import streamlit as st
import pandas as pd
import plotly.express as px
from analysis import analisar_producao


st.set_page_config(

    page_title="Simulador de Capacidade Produtiva",
    layout="wide"
)

# -----------------------------
# CSS PARA CENTRALIZAR O CONTEÚDO
# -----------------------------
st.markdown(
    """
    <style>
    /* Limitar largura do conteúdo e centralizar */
    .block-container {
        max-width: 1100px;  /* largura máxima do app */
        padding-left: 2rem; /* margem esquerda */
        padding-right: 2rem; /* margem direita */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Simulador de Capacidade Produtiva")

st.markdown(
    """
    Ferramenta para análise de capacidade, gargalos e atendimento da demanda
    em linhas de produção industriais.
    """
)
# Sessão para baixar a planilha

with open("example/producao_exemplo.xlsx", "rb") as file:
    st.download_button(
        label="Baixar planilha padrão",
        data=file,
        file_name="planilha_padrao.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


uploaded_file = st.file_uploader(
    "Upload da planilha de produção",
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # -----------------------------
    # SIMULADOR DE DEMANDA
    # -----------------------------

    st.subheader("Simulação de Demanda")

    percentual = st.slider(
        "Variação de Demanda (%)",
        min_value=-50,
        max_value=200,
        value=0,
        step=5
    )

    df["demanda_original"] = df["quantidade"]

    df["quantidade"] = df["quantidade"] * (1 + percentual / 100)

    df["demanda_simulada"] = df["quantidade"]

    df["variacao_demanda"] = (
        (df["demanda_simulada"] - df["demanda_original"])
        / df["demanda_original"]
    ) * 100

    # -----------------------------
    # ANÁLISE DE PRODUÇÃO
    # -----------------------------

    df_resultado, resultados = analisar_producao(df)

    takt = resultados["takt_time_seg"]
    capacidade_linha = resultados["capacidade_linha_pecas_turno"]
    producao_real = resultados["producao_real"]
    demanda = resultados["producao_planejada"]
    gargalo = resultados["gargalo_processo"]
    eficiencia = resultados["eficiencia_balanceamento"]
    ociosidade_percent = resultados["ociosidade_percent"]
    atendimento = resultados["nivel_atendimento"]
    throughput = resultados["throughput_por_hora"]
    lead_time_peca = resultados["lead_time_peca_h"]
    lead_time_lote = resultados["lead_time_lote_h"]

    gap = demanda - producao_real

    # -----------------------------
    # KPIs PRINCIPAIS
    # -----------------------------

    st.subheader("Indicadores Principais")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Demanda",
        f"{demanda:.0f}"
    )

    col2.metric(
        "Capacidade da Linha",
        f"{capacidade_linha:.0f}"
    )

    col3.metric(
        "Atendimento",
        f"{atendimento*100:.1f}%"
    )

    col4.metric(
        "Takt Time",
        f"{takt:.1f} s"
    )

    if gap > 0:
        st.warning(
            "A linha Não Atende a demanda simulada."
        )
        st.error(

            f"Déficit Total de capacidade: * {gap:.0f}* peças por turno"
        )

    else:

        st.success(
            "A linha atende a demanda simulada."
        )

    # -----------------------------
    # TABELA DETALHADA
    # -----------------------------

    st.subheader("Detalhamento dos Processos")

    tabela = df_resultado.copy()
    tabela["Capacidade"] = tabela["capacidade_processo"].round(0).astype(int)
    tabela["Utilização (%)"] = tabela["utilizacao_percent"].apply(lambda x: f"{x:.1f}%")

    tabela["status_gargalo"] = tabela["utilizacao_percent"].apply(
        lambda x: "🟢 Saudável" if x < 80 else ("🟡 Atenção" if x <= 100 else "🔴 Gargalo")
    )

    def cor_status(val):

        if "Gargalo" in val:
            return "color: #e74c3c; font-weight: bold"

        elif "Atenção" in val:
            return "color: #f39c12; font-weight: bold"

        elif "Saudável" in val:
            return "color: #2ecc71; font-weight: bold"

        return ""

    st.dataframe(
        tabela[
            [
                "processo",
                "maquina",
                "tempo_ciclo_seg",
                "Capacidade",
                "Utilização (%)",
                "status_gargalo"
            ]
        ].style.map(cor_status, subset=["status_gargalo"]),
        width='stretch'
    )

    # -----------------------------
    # GRÁFICO TAKT VS CICLO
    # -----------------------------

    st.subheader("Balanceamento da Linha")

    df_plot = df_resultado.copy()

    fig_balance = px.bar(
        df_plot,
        x="processo",
        y="tempo_ciclo_seg",
        title="Tempo de Ciclo por Processo",
        labels={
            "tempo_ciclo_seg": "Tempo (seg)",
            "processo": "Processo"
        }
    )

    fig_balance.add_hline(
        y=takt,
        line_dash="dash",
        annotation_text="Takt Time"
    )

    st.plotly_chart(fig_balance, use_container_width=True)

    # -----------------------------
    # UTILIZAÇÃO DAS MÁQUINAS
    # -----------------------------

    st.subheader("Análise de Utilização por Máquinas")

    def classificar(x):

        if x < 80:
            return "Saudável"

        elif x <= 100:
            return "Atenção"

        else:
            return "Gargalo"

    df_resultado["status"] = df_resultado["utilizacao_percent"].apply(
        classificar)

    fig_util = px.bar(
        df_resultado,
        x="maquina",
        y="utilizacao_percent",
        color="status",
        title="% Utilização das Máquinas",
        labels={
            "utilizacao_percent": "Utilização (%)",
            "maquina": "Máquina"
        },
        color_discrete_map={
            "Saudável": "#2ecc71",
            "Atenção": "#f39c12",
            "Gargalo": "#e74c3c"
        }
    )

    st.plotly_chart(fig_util, use_container_width=True)

    # -----------------------------
    # GRÁFICO GAP de capacidade
    # -----------------------------

    st.subheader("Gap de Capacidade por Processo")

    fig_gap = px.bar(
        df_resultado,
        x="processo",
        y="deficit_pecas",
        title="Déficit de capacidade por processo",
        labels={
            "deficit_pecas": "Déficit (peças)",
            "processo": "Processo"
        },
        color_discrete_sequence=["gray"]
    )

    st.plotly_chart(fig_gap, use_container_width=True)

    # -----------------------------
    # INDICADORES OPERACIONAIS
    # -----------------------------

    st.subheader("Indicadores Operacionais")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Throughput (peças/h)",
        f"{throughput:.1f}"
    )

    col2.metric(
        "Eficiência de Balanceamento",
        f"{eficiencia*100:.1f}%"
    )

    col3.metric(
        "Ociosidade da Linha",
        f"{ociosidade_percent:.1f}%"
    )

    col4.metric(
        "Lead Time Lote (h)",
        f"{lead_time_lote:.2f}"
    )

    # -----------------------------
    # ANÁLISE DE GARGALOS
    # -----------------------------

    st.subheader("Análise de Gargalos")

    gargalos = df_resultado[
        df_resultado["utilizacao_percent"] > 100
    ].sort_values("utilizacao_percent", ascending=False)

    if gargalos.empty:

        st.success("Nenhum gargalo identificado.")

    else:

        for _, row in gargalos.iterrows():

            st.warning(
                f"""
    🔴 **Processo crítico identificado**

    **Processo:** {row['processo']}
    **Máquina:** {row['maquina']}

    **Utilização:** {row['utilizacao_percent']:.1f}%
    **Excesso de carga:** {row['excesso_carga_percent']:.1f}%

    **Déficit de capacidade:** {row['deficit_pecas']:.0f} peças/turno

    **Tempo acima do takt:** {row['tempo_acima_takt']:.1f} s

    **Máquinas adicionais necessárias:** {row['maquinas_adicionais']}
    """
            )
