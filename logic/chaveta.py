"""Dimensionamento e verificacao de chaveta paralela conforme DIN 6885-1."""

# Tolerancias sugeridas para a largura (b) do rasgo de chaveta.
TOLERANCIA_VEIO = "N9"   # veio (ajuste fixo/normal)
TOLERANCIA_CUBO = "P9"   # cubo

# Propriedades admissiveis para chaveta de aco padrao (ex.: C45 / AISI 1045).
# Ja consideram um coeficiente de seguranca tipico; o torque usado na verificacao
# e o Torque de Projeto (que ja inclui o Fator de Servico).
P_ADM_ESMAGAMENTO = 100.0  # MPa (N/mm^2) - pressao de contato admissivel (aco)
TAU_ADM_CISALHAMENTO = 60.0  # MPa (N/mm^2) - tensao de corte admissivel (aco)

# Modo laboratorio: folga radial (mm) furo/eixo acima da qual emitimos alerta.
FOLGA_MAX_RECOMENDADA_MM = 0.05  # ~50 um (montagem H7/j6..k6 tipica)


def dimensionar_chaveta(diametro_mm: float, tabela_din: dict) -> dict | None:
    """Devolve as cotas da chaveta para o diametro do veio informado.

    `tabela_din` e o dicionario carregado de norma_din6885.json.

    Retorna dict com b, h, t1, t2, faixa e tolerancias, ou None se o
    diametro estiver fora do intervalo coberto pela norma (10 a 150 mm).
    """
    for linha in tabela_din.get("tabela", []):
        if linha["d_min"] < diametro_mm <= linha["d_max"]:
            return {
                "diametro": diametro_mm,
                "faixa": f"{linha['d_min']} < d <= {linha['d_max']} mm",
                "b": linha["b"],
                "h": linha["h"],
                "t1": linha["t1"],
                "t2": linha["t2"],
                "tolerancia_veio": TOLERANCIA_VEIO,
                "tolerancia_cubo": TOLERANCIA_CUBO,
            }
    return None


def verificar_esmagamento(
    torque_projeto_nm: float,
    diametro_mm: float,
    dims_chaveta: dict,
    comprimento_mm: float,
    p_adm: float = P_ADM_ESMAGAMENTO,
    tau_adm: float = TAU_ADM_CISALHAMENTO,
) -> dict:
    """Verifica a chaveta ao esmagamento (pressao de contato) e ao cisalhamento.

    Modelo mecanico (chaveta paralela):
      - Torque de projeto convertido para N.mm: T = torque_projeto_nm * 1000
      - Forca tangencial no raio do veio:        F = 2 * T / d           [N]
      - Altura de contato (governa o menor lado): h_c = min(t1, t2)      [mm]
      - Area de esmagamento:                      A_esm = L * h_c        [mm^2]
      - Area de cisalhamento:                     A_cis = L * b          [mm^2]
      - Pressao de esmagamento:                   p   = F / A_esm        [MPa]
      - Tensao de cisalhamento:                   tau = F / A_cis        [MPa]

    A chaveta e aprovada se p <= p_adm E tau <= tau_adm.
    Retorna dict com forcas, tensoes, limites, utilizacoes e o veredito.
    """
    if comprimento_mm <= 0:
        raise ValueError("O comprimento da chaveta deve ser maior que zero.")

    T = torque_projeto_nm * 1000.0  # N.mm
    F = 2.0 * T / diametro_mm        # N

    h_contato = min(dims_chaveta["t1"], dims_chaveta["t2"])
    area_esm = comprimento_mm * h_contato
    area_cis = comprimento_mm * dims_chaveta["b"]

    p = F / area_esm
    tau = F / area_cis

    aprov_esm = p <= p_adm
    aprov_cis = tau <= tau_adm

    return {
        "forca_N": F,
        "comprimento_mm": comprimento_mm,
        "altura_contato_mm": h_contato,
        "pressao_MPa": p,
        "p_adm_MPa": p_adm,
        "util_esmagamento_pct": p / p_adm * 100.0,
        "aprovado_esmagamento": aprov_esm,
        "cisalhamento_MPa": tau,
        "tau_adm_MPa": tau_adm,
        "util_cisalhamento_pct": tau / tau_adm * 100.0,
        "aprovado_cisalhamento": aprov_cis,
        "aprovado": aprov_esm and aprov_cis,
    }


def diagnosticar_custom(
    dims_custom: dict,
    dims_nominal: dict | None,
    folga_mm: float,
    folga_max_mm: float = FOLGA_MAX_RECOMENDADA_MM,
) -> list[str]:
    """Diagnosticos do Modo Laboratorio (geometria personalizada).

    Compara a geometria digitada (`dims_custom`) com a nominal da DIN 6885
    (`dims_nominal`) e avalia a folga furo/eixo simulada.

    Retorna uma lista de mensagens de alerta (vazia se nada a assinalar):
      * chaveta rebaixada -> reducao da area util de esmagamento;
      * folga excessiva entre furo e eixo.
    """
    alertas: list[str] = []

    # Chaveta rebaixada: altura de contato util menor que a nominal da norma.
    h_custom = min(dims_custom["t1"], dims_custom["t2"])
    if dims_nominal:
        h_nom = min(dims_nominal["t1"], dims_nominal["t2"])
        if h_nom > 0 and h_custom < h_nom:
            reducao_pct = (1.0 - h_custom / h_nom) * 100.0
            alertas.append(
                f"Chaveta rebaixada: altura util de contato {h_custom:.2f} mm < "
                f"nominal DIN {h_nom:.2f} mm. Area de esmagamento reduzida "
                f"~{reducao_pct:.0f}% (pressao de contato mais alta)."
            )

    # Folga excessiva entre furo e eixo (furo folgado/desgastado).
    if folga_mm and folga_mm > folga_max_mm:
        alertas.append(
            f"Folga excessiva furo/eixo: {folga_mm:.3f} mm > recomendado "
            f"{folga_max_mm:.3f} mm. Risco de batimento, desalinhamento e "
            "martelamento da chaveta sob inversao de carga."
        )

    return alertas
