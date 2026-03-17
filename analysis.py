import math


def analisar_producao(df):

    # -----------------------------
    # PADRONIZAR COLUNAS
    # -----------------------------

    df.columns = df.columns.str.lower().str.strip()

    # -----------------------------
    # VALIDAÇÃO DE COLUNAS
    # -----------------------------

    colunas_necessarias = [
        "processo",
        "maquina",
        "tempo_ciclo_seg",
        "quantidade",
        "turno_horas"
    ]

    for col in colunas_necessarias:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória não encontrada: {col}")

    # -----------------------------
    # TEMPO DISPONÍVEL
    # -----------------------------

    tempo_disponivel_seg = df["turno_horas"].iloc[0] * 3600

    # -----------------------------
    # DEMANDA
    # -----------------------------

    demanda = df["quantidade"].iloc[0]

    # -----------------------------
    # TAKT TIME
    # -----------------------------

    takt_time = tempo_disponivel_seg / demanda

    # -----------------------------
    # TEMPO DE PROCESSO
    # -----------------------------

    df["tempo_processo_seg"] = df["tempo_ciclo_seg"] * demanda

    df["lead_time_processo_h"] = df["tempo_processo_seg"] / 3600

    # -----------------------------
    # CAPACIDADE POR PROCESSO
    # -----------------------------

    df["capacidade_processo"] = (
        tempo_disponivel_seg /
        df["tempo_ciclo_seg"]
    )

    # -----------------------------
    # UTILIZAÇÃO DOS PROCESSOS
    # -----------------------------

    df["utilizacao"] = (
        df["tempo_processo_seg"] /
        tempo_disponivel_seg
    )

    df["utilizacao_percent"] = df["utilizacao"] * 100

    # -----------------------------
    # EXCESSO DE CARGA
    # -----------------------------

    df["excesso_carga_percent"] = (
        df["utilizacao_percent"] - 100
    ).clip(lower=0)

    # -----------------------------
    # DÉFICIT DE CAPACIDADE
    # -----------------------------

    df["deficit_pecas"] = (
        demanda - df["capacidade_processo"]
    ).clip(lower=0)

    # -----------------------------
    # TEMPO ACIMA DO TAKT
    # -----------------------------

    df["tempo_acima_takt"] = (
        df["tempo_ciclo_seg"] - takt_time
    ).clip(lower=0)

    # -----------------------------
    # PRIORIDADE DO GARGALO
    # -----------------------------

    df["prioridade_gargalo"] = df["utilizacao_percent"].rank(
        ascending=False
    )

    # -----------------------------
    # MÁQUINAS NECESSÁRIAS
    # -----------------------------

    df["maquinas_necessarias"] = df["utilizacao"].apply(
        lambda x: math.ceil(x)
    )

    df["maquinas_adicionais"] = (
        df["maquinas_necessarias"] - 1
    ).clip(lower=0)

    # -----------------------------
    # IDENTIFICAÇÃO DO GARGALO
    # -----------------------------

    gargalo = df.loc[df["tempo_ciclo_seg"].idxmax()]

    ciclo_gargalo = gargalo["tempo_ciclo_seg"]

    # -----------------------------
    # CAPACIDADE DA LINHA
    # -----------------------------

    capacidade_linha = tempo_disponivel_seg / ciclo_gargalo

    # -----------------------------
    # PRODUÇÃO REAL
    # -----------------------------

    producao_real = min(demanda, capacidade_linha)

    # -----------------------------
    # THROUGHPUT DA LINHA
    # -----------------------------

    throughput_por_hora = 3600 / ciclo_gargalo

    # -----------------------------
    # ATENDIMENTO DA DEMANDA
    # -----------------------------

    nivel_atendimento = producao_real / demanda

    # -----------------------------
    # EFICIÊNCIA DE BALANCEAMENTO
    # -----------------------------

    eficiencia_balanceamento = (
        df["tempo_ciclo_seg"].sum() /
        (len(df) * ciclo_gargalo)
    )
    ociosidade_percent = (1 - eficiencia_balanceamento) * 100
    
    # -----------------------------
    # TEMPO OCIOSO
    # -----------------------------

    df["tempo_ocioso_seg"] = (
        ciclo_gargalo - df["tempo_ciclo_seg"]
    ).clip(lower=0)

    # -----------------------------
    # LEAD TIME DE UMA PEÇA
    # -----------------------------

    lead_time_peca_seg = df["tempo_ciclo_seg"].sum()

    lead_time_peca_h = lead_time_peca_seg / 3600

    # -----------------------------
    # LEAD TIME DO LOTE
    # -----------------------------

    lead_time_lote_seg = (
        lead_time_peca_seg +
        (demanda - 1) * ciclo_gargalo
    )

    lead_time_lote_h = lead_time_lote_seg / 3600

    # -----------------------------
    # RESULTADOS
    # -----------------------------

    resultados = {

        "takt_time_seg": takt_time,

        "gargalo_processo": gargalo["processo"],

        "ciclo_gargalo_seg": ciclo_gargalo,

        "capacidade_linha_pecas_turno": capacidade_linha,

        "throughput_por_hora": throughput_por_hora,

        "producao_planejada": demanda,

        "producao_real": producao_real,

        "nivel_atendimento": nivel_atendimento,

        "eficiencia_balanceamento": eficiencia_balanceamento,

        "ociosidade_percent": ociosidade_percent,

        "lead_time_peca_h": lead_time_peca_h,

        "lead_time_lote_h": lead_time_lote_h

    }

    return df, resultados
