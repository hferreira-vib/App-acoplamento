"""
Dimensionamento, Selecao e Auditoria de Acoplamentos Industriais
================================================================
Aplicacao web em Streamlit.

Executar:  python -m streamlit run app.py
"""

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from logic import calculos, chaveta, selecao, relatorio, desenho, fator_servico

# ---------------------------------------------------------------------------
# Configuracao da pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dimensionamento de Acoplamentos",
    page_icon="⚙️",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"
IMG_DIR = Path(__file__).parent / "img"

# Mapeia cada categoria do catalogo para um ficheiro de imagem ilustrativo
# (guardado em img/). Nomes padronizados, minusculas, terminados em .jpg.
CATEGORIA_IMAGENS = {
    "Grade Elastica (FALK Steelflex T10)": "grade.jpg",
    "Engrenagem (FALK Lifelign G20)": "engrenagem.jpg",
    "Engrenagem (Flender ZAPEX ZW)": "engrenagem_zapex.jpg",
    "Garras/Elastomero (KTR Rotex 98 ShA)": "garras_rotex.jpg",
    "Garras (Lovejoy L-Type)": "garras_lovejoy.jpg",
    "Elastomero Bipartido (Rexnord Omega E)": "omega.jpg",
    "Pinos/Buchas (Flender N-EUPEX)": "pinos.jpg",
    "Laminas (KTR Radex-N)": "laminas.jpg",
    "Pneu/Borracha (Fenner Fenaflex)": "pneu.jpg",
    "Elastomero PU (FALK Wrapflex)": "wrapflex.jpg",
    "Acoplamento Hidraulico (HDA / Voith)": "hidraulico.jpg",
    "Garras (HDA Linha HA)": "garras_ha.jpg",
    "Elastomero Bipartido (Rexnord Viva)": "viva.jpg",
    "Laminas/Disco (Rexnord Thomas Disc)": "disco_thomas.jpg",
}


def mostrar_imagem_categoria(categoria: str) -> None:
    """Mostra a imagem ilustrativa da categoria, ou uma dica se ainda nao existir.

    Nunca quebra a interface: se a categoria nao estiver mapeada, nao faz nada.
    """
    nome_ficheiro = CATEGORIA_IMAGENS.get(categoria)
    if not nome_ficheiro:
        return

    caminho = IMG_DIR / nome_ficheiro
    if os.path.isfile(caminho):
        st.image(str(caminho), width=250, caption=categoria)
    else:
        st.info(
            f"Para visualizar a foto, guarde uma imagem do acoplamento como "
            f"**{nome_ficheiro}** dentro da pasta img/."
        )


# Mensagens de alerta da secao 3 (Selecao do Acoplamento).
MSG_EIXO_LIMITE = (
    "⚠️ Atenção: O diâmetro do eixo está no limite de furação do cubo deste acoplamento. "
    "Exige usinagem de precisão extrema. Considere o tamanho acima se o ambiente "
    "tiver muita vibração."
)
MSG_SUPERDIMENSIONADO = (
    "ℹ️ Nota: Acoplamento bastante superdimensionado para o torque exigido "
    "(geralmente selecionado para atender ao diâmetro do eixo)."
)

# Ajustes do rasgo de chaveta (DIN 6885): rotulo -> (tolerancia eixo, tolerancia cubo).
# A primeira entrada e o padrao apresentado no selectbox.
AJUSTES_CHAVETA = {
    "Normal / Transição (Eixo N9 | Cubo JS9)": ("N9", "JS9"),
    "Fixo / Aperto (Eixo P9 | Cubo P9)": ("P9", "P9"),
    "Deslizante (Eixo H9 | Cubo D10)": ("H9", "D10"),
}

# Ajustes do diametro furo (cubo) x eixo (ISO 286): rotulo -> (tol. furo, tol. eixo).
# A primeira entrada e o padrao apresentado no selectbox.
AJUSTES_FURO = {
    "H7 / j6 (Justo - Montagem manual/batida leve)": ("H7", "j6"),
    "H7 / k6 (Transição - Batida firme)": ("H7", "k6"),
    "H7 / m6 (Interferência - Montagem a quente / prensa)": ("H7", "m6"),
    "H7 / h6 (Deslizante livre)": ("H7", "h6"),
}


def alertas_selecao(modelo: dict, furo_requerido: float, margem_pct: float) -> None:
    """Exibe avisos de eixo no limite de furacao e de superdimensionamento."""
    folga_furo = modelo["Furo Maximo (mm)"] - furo_requerido
    if 0 <= folga_furo <= 2:
        st.warning(MSG_EIXO_LIMITE)
    if margem_pct > 250:
        st.info(MSG_SUPERDIMENSIONADO)


def ficha_tecnica_md(m: dict) -> str:
    """Markdown com a ficha tecnica estimada de um modelo do catalogo."""
    peso = m.get("Peso (kg)", "-")
    inercia = m.get("Momento de Inercia (kg.m2)", "-")
    ang = m.get("Desalinhamento Angular (graus)", "-")
    rad = m.get("Desalinhamento Radial (mm)", "-")
    ax = m.get("Desalinhamento Axial (mm)", "-")
    return (
        f"**Ficha tecnica (estimada):** "
        f"Peso `{peso} kg` · Inercia `{inercia} kg·m²`  \n"
        f"**Desalinhamento admissivel:** "
        f"angular `{ang}°` · radial `{rad} mm` · axial `{ax} mm`"
    )


# ---------------------------------------------------------------------------
# Carregamento de dados (com cache)
# ---------------------------------------------------------------------------
@st.cache_data
def carregar_json(nome_ficheiro: str) -> dict:
    with open(DATA_DIR / nome_ficheiro, "r", encoding="utf-8") as f:
        return json.load(f)


try:
    dados_fs = carregar_json("fator_servico.json")
    catalogo = carregar_json("catalogo_acoplamentos.json")
    tabela_din = carregar_json("norma_din6885.json")
except FileNotFoundError as e:
    st.error(f"Ficheiro de dados nao encontrado: {e}. Verifique a pasta /data.")
    st.stop()


# ---------------------------------------------------------------------------
# Cabecalho
# ---------------------------------------------------------------------------
st.title("⚙️ Dimensionamento de Acoplamentos Industriais")
st.caption(
    "Calculo de torque, selecao de acoplamento, auditoria de chaveta (DIN 6885) "
    "e relatorio em PDF."
)

# ---------------------------------------------------------------------------
# SIDEBAR - Dados de entrada
# ---------------------------------------------------------------------------
st.sidebar.header("1. Dados de Entrada")

unidade_potencia = st.sidebar.radio(
    "Unidade de potencia", ["CV", "kW"], horizontal=True,
    help="1 CV = 0.7355 kW. O torque e sempre calculado a partir do valor em kW.",
)
if unidade_potencia == "CV":
    potencia_cv = st.sidebar.number_input(
        "Potencia (CV)", min_value=0.1, value=20.0, step=0.5, format="%.2f",
        help="Cavalo-vapor metrico (1 CV = 0.7355 kW).",
    )
    potencia_kw = calculos.cv_para_kw(potencia_cv)
    st.sidebar.caption(f"= {potencia_kw:.2f} kW")
else:
    potencia_kw = st.sidebar.number_input(
        "Potencia (kW)", min_value=0.1, value=15.0, step=0.5, format="%.2f",
        help="Potencia em quilowatts (usada diretamente no calculo do torque).",
    )
    potencia_cv = potencia_kw / calculos.CV_PARA_KW
    st.sidebar.caption(f"= {potencia_cv:.2f} CV")

rpm = st.sidebar.number_input(
    "Rotacao (RPM)", min_value=0.1, value=1750.0, step=10.0, format="%.0f"
)

st.sidebar.subheader("Eixos")
diametro_motor = st.sidebar.number_input(
    "Diametro do Eixo Motor (mm)", min_value=0.1, max_value=150.0, value=48.0, step=1.0
)
diametro_movido = st.sidebar.number_input(
    "Diametro do Eixo Movido (mm)", min_value=0.1, max_value=150.0, value=42.0, step=1.0
)
ajuste_chaveta = st.sidebar.selectbox(
    "Ajuste da Chaveta (DIN 6885)", list(AJUSTES_CHAVETA.keys()),
    help="Define a tolerancia da largura (b) do rasgo no eixo e no cubo.",
)
tol_eixo, tol_cubo = AJUSTES_CHAVETA[ajuste_chaveta]

ajuste_furo = st.sidebar.selectbox(
    "Ajuste do Furo (ISO 286)", list(AJUSTES_FURO.keys()),
    help="Define a tolerancia do diametro do furo do cubo e do eixo (montagem).",
)
tol_furo, tol_eixo_diam = AJUSTES_FURO[ajuste_furo]

# --- Modo Laboratorio / Personalizacao de Geometria (Custom Fit) ---
modo_lab = st.sidebar.checkbox(
    "Modo Laboratório / Personalização de Geometria",
    help="Substitui as cotas da DIN 6885 por valores digitados, para ensaios "
    "e simulacao de furos folgados/desgastados.",
)
custom_geom = None
if modo_lab:
    with st.sidebar.expander("Parâmetros Especiais de Usinagem", expanded=True):
        st.caption(
            "As cotas abaixo substituem a norma DIN 6885 para **ambos os eixos** "
            "(geometria de ensaio)."
        )
        b_custom = st.number_input(
            "Largura da Chaveta (b, mm)", min_value=1.0, max_value=100.0,
            value=14.0, step=0.5,
        )
        t1_custom = st.number_input(
            "Profundidade no Eixo (t1, mm)", min_value=0.2, max_value=30.0,
            value=5.5, step=0.1,
        )
        t2_custom = st.number_input(
            "Profundidade no Cubo (t2, mm)", min_value=0.2, max_value=30.0,
            value=3.8, step=0.1,
        )
        folga_custom = st.number_input(
            "Folga / Desvio do Diâmetro (mm)", min_value=0.0, max_value=5.0,
            value=0.0, step=0.01, format="%.3f",
            help="Aumento simulado do diametro do furo (furo folgado/desgastado).",
        )
        dext_custom = st.number_input(
            "Diâmetro Externo do Cubo (D_ext em mm)", min_value=0.0,
            max_value=500.0, value=0.0, step=1.0,
            help="Medida real de paquimetro / bancada. 0 = usar estimativa "
            "automatica (1.42 x furo maximo).",
        )
    custom_geom = {
        "b": b_custom, "t1": t1_custom, "t2": t2_custom, "folga": folga_custom,
        "d_ext": dext_custom,
    }

st.sidebar.subheader("Aplicacao")
acionamentos = fator_servico.listar_acionamentos(dados_fs)
acionamento = st.sidebar.selectbox("Tipo de Acionamento", acionamentos)
maquinas = fator_servico.listar_maquinas(dados_fs, acionamento)
maquina = st.sidebar.selectbox("Maquina Movida / Equipamento", maquinas)

# ---------------------------------------------------------------------------
# CALCULOS PRINCIPAIS
# ---------------------------------------------------------------------------
try:
    fs = fator_servico.get_fator_servico(dados_fs, acionamento, maquina)
    t_nom = calculos.torque_nominal(potencia_kw, rpm)
    t_proj = calculos.torque_projeto(t_nom, fs)
except (ValueError, KeyError) as e:
    st.error(f"Erro nos calculos: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# 2. Cards de resultados
# ---------------------------------------------------------------------------
st.header("2. Cargas Calculadas")
c1, c2, c3 = st.columns(3)
c1.metric("Fator de Servico (FS)", f"{fs:.2f}")
c2.metric("Torque Nominal", f"{t_nom:,.1f} Nm")
c3.metric("Torque de Projeto", f"{t_proj:,.1f} Nm", delta=f"x{fs:.2f}")

if fator_servico.is_bancada(maquina):
    st.caption(
        f"🧪 **{maquina}** — FS base limpo de bancada/ensaio contínuo "
        f"(FS = {fs:.2f}), aplicado independentemente do tipo de acionamento."
    )

st.divider()

# ---------------------------------------------------------------------------
# 3. Selecao do acoplamento
# ---------------------------------------------------------------------------
st.header("3. Selecao do Acoplamento")
modo = st.radio(
    "Modo de operacao",
    ["Sugerir Acoplamento Ideal", "Verificar Modelo Especifico"],
    horizontal=True,
)
furo_requerido = max(diametro_motor, diametro_movido)

# Dados que serao usados no relatorio PDF.
sel_para_pdf = {"modo": modo, "texto": "", "aprovado": False, "detalhes": [], "specs": None}
modelo_selecionado = None

# --------------------------- MODO 1: SUGERIR ------------------------------
if modo == "Sugerir Acoplamento Ideal":
    categorias = ["Todas"] + selecao.listar_categorias(catalogo)
    col_filtro, col_img = st.columns([2, 1])
    with col_filtro:
        categoria_filtro = st.selectbox("Filtrar por Categoria", categorias)

    resultado = selecao.sugerir_acoplamento(
        catalogo, torque_projeto=t_proj, furo_motor=diametro_motor,
        furo_movido=diametro_movido, rpm=rpm, categoria=categoria_filtro,
    )

    # Ilustra a categoria escolhida; se for "Todas", ilustra a recomendada.
    categoria_ilustrada = categoria_filtro
    if categoria_filtro == "Todas" and resultado["encontrado"]:
        categoria_ilustrada = resultado["modelo"]["Categoria"]
    if categoria_ilustrada != "Todas":
        with col_img:
            mostrar_imagem_categoria(categoria_ilustrada)

    if resultado["encontrado"]:
        m = resultado["modelo"]
        modelo_selecionado = m
        st.success(f"✅ Acoplamento recomendado: **{m['Categoria']} — {m['Modelo']}**")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Torque Maximo", f"{m['Torque Maximo (Nm)']:,} Nm")
        r2.metric("Furo Maximo", f"{m['Furo Maximo (mm)']} mm")
        r3.metric("Rotacao Maxima", f"{m['Rotacao Maxima (RPM)']:,} RPM")
        margem = (m["Torque Maximo (Nm)"] / t_proj - 1) * 100 if t_proj else 0
        r4.metric("Margem de Torque", f"+{margem:.0f}%")

        st.markdown(ficha_tecnica_md(m))

        alertas_selecao(m, furo_requerido, margem)

        sel_para_pdf["texto"] = f"{m['Categoria']} - {m['Modelo']}"
        sel_para_pdf["specs"] = m
        sel_para_pdf["aprovado"] = True
        sel_para_pdf["detalhes"] = [
            f"Torque max {m['Torque Maximo (Nm)']} Nm >= projeto {t_proj:.1f} Nm",
            f"Furo max {m['Furo Maximo (mm)']} mm >= maior eixo {furo_requerido:.0f} mm",
            f"RPM max {m['Rotacao Maxima (RPM)']} >= trabalho {rpm:.0f}",
        ]
    else:
        st.error(
            "Nenhum modelo no catálogo atende a estes requisitos. "
            "Reduza a carga ou procure opções pesadas/sob medida."
        )
        st.caption(
            f"Requisitos exigidos: Torque ≥ {t_proj:.1f} Nm · "
            f"Furo ≥ {furo_requerido:.0f} mm · RPM ≥ {rpm:.0f}."
        )
        # Interrompe graciosamente: sem modelo valido nao ha o que auditar/gerar.
        st.stop()

# ----------------------- MODO 2: VERIFICAR --------------------------------
else:
    v1, v2 = st.columns(2)
    with v1:
        categoria_sel = st.selectbox("Categoria", selecao.listar_categorias(catalogo))
    with v2:
        modelos = selecao.listar_modelos(catalogo, categoria_sel)
        modelo_sel = st.selectbox("Modelo", modelos)

    col_img2, _ = st.columns([1, 2])
    with col_img2:
        mostrar_imagem_categoria(categoria_sel)

    modelo = selecao.obter_modelo(catalogo, categoria_sel, modelo_sel)
    if modelo:
        modelo_selecionado = modelo
        f1, f2, f3 = st.columns(3)
        f1.metric("Torque Maximo", f"{modelo['Torque Maximo (Nm)']:,} Nm")
        f2.metric("Furo Maximo", f"{modelo['Furo Maximo (mm)']} mm")
        f3.metric("Rotacao Maxima", f"{modelo['Rotacao Maxima (RPM)']:,} RPM")

        st.markdown(ficha_tecnica_md(modelo))

        margem_modelo = (modelo["Torque Maximo (Nm)"] / t_proj - 1) * 100 if t_proj else 0
        alertas_selecao(modelo, furo_requerido, margem_modelo)

        parecer = selecao.verificar_modelo(
            modelo, torque_projeto=t_proj, furo_motor=diametro_motor,
            furo_movido=diametro_movido, rpm=rpm,
        )

        st.subheader("Parecer Tecnico")
        if parecer["aprovado"]:
            st.success(f"✅ APROVADO — **{modelo_sel}** atende a todos os requisitos.")
        else:
            st.error(f"❌ REPROVADO — **{modelo_sel}** nao atende:")
            for motivo in parecer["motivos"]:
                st.warning(f"• {motivo}")

        sel_para_pdf["texto"] = f"{categoria_sel} - {modelo_sel}"
        sel_para_pdf["specs"] = modelo
        sel_para_pdf["aprovado"] = parecer["aprovado"]
        sel_para_pdf["detalhes"] = (
            parecer["motivos"] if not parecer["aprovado"]
            else ["Todos os criterios atendidos."]
        )

st.divider()

# ---------------------------------------------------------------------------
# 4. Chavetas - layout em cartoes + auditoria de esmagamento
# ---------------------------------------------------------------------------
st.header("4. Dimensionamento e Auditoria da Chaveta (DIN 6885)")

if custom_geom:
    st.warning(
        "🧪 **Modo Laboratório ativo** — as cotas da DIN 6885 foram substituídas "
        "pelos valores personalizados. Resultado apenas para ensaio/simulação."
    )

# O comprimento util da chaveta (L) e o comprimento do cubo do acoplamento
# selecionado/verificado. O helper aplica fallback seguro (1.5 x furo maximo)
# se a chave nao existir, para a auditoria nunca parar de calcular.
comprimento_cubo = modelo_selecionado.get(
    "Comprimento do Cubo (mm)",
    round(1.5 * modelo_selecionado.get("Furo Maximo (mm)", 0)),
) if modelo_selecionado else 0.0

if comprimento_cubo:
    st.caption(
        f"Comprimento da chaveta assumido: **{comprimento_cubo:.0f} mm** "
        "(baseado no comprimento do cubo do acoplamento selecionado)."
    )
else:
    st.warning("Comprimento do cubo não encontrado no catálogo.")

chavetas_para_pdf = []

for nome, diametro in [("Eixo Motor", diametro_motor), ("Eixo Movido", diametro_movido)]:
    with st.container(border=True):
        st.subheader(f"{nome}")

        ch = chaveta.dimensionar_chaveta(diametro, tabela_din)
        if ch is None:
            st.warning(
                f"Diametro {diametro:.0f} mm fora do intervalo da norma "
                "(10 a 150 mm)."
            )
            continue

        # Modo Laboratorio: cotas digitadas substituem a DIN; a folga simula
        # um furo folgado/desgastado (Ø efetivo = diametro + folga).
        diagnosticos_lab = []
        if custom_geom:
            dims = {
                "b": custom_geom["b"], "h": ch["h"],
                "t1": custom_geom["t1"], "t2": custom_geom["t2"],
                "faixa": ch["faixa"],
            }
            diametro_furo = diametro + custom_geom["folga"]
            diagnosticos_lab = chaveta.diagnosticar_custom(
                dims_custom=dims, dims_nominal=ch, folga_mm=custom_geom["folga"],
            )
        else:
            dims = ch
            diametro_furo = diametro

        # Diametro externo do cubo: valor manual (Modo Laboratorio) tem prioridade;
        # senao estimativa da gola do cubo (1.42 x furo max). A parede critica e
        # recalculada a partir do D_ext efetivo.
        furo_max = (
            modelo_selecionado.get("Furo Maximo (mm)") if modelo_selecionado else None
        )
        if custom_geom and custom_geom.get("d_ext", 0) > 0:
            d_ext = custom_geom["d_ext"]
            d_ext_origem = "medido (paquímetro)"
        else:
            d_ext = desenho.estimar_diametro_externo(furo_max or diametro_furo)
            d_ext_origem = "estimado (1.42 x furo máx)"
        e_parede = desenho.espessura_parede(d_ext, diametro_furo, dims["t2"])

        # Cartao de auditoria (esquerda) + desenho tecnico 2D (direita).
        col_dados, col_desenho = st.columns([1, 1])

        with col_dados:
            if custom_geom:
                st.caption("🧪 Geometria personalizada (Modo Laboratório)")
            st.markdown(f"**Diametro do eixo:** `{diametro:.0f} mm`")
            st.metric("Chaveta (b x h)", f"{dims['b']} x {dims['h']} mm")

            st.markdown(
                f"""
- **Rasgo no Eixo (t1):** `{dims['t1']} mm`  ·  Tolerancia **{tol_eixo}**
- **Rasgo no Cubo (t2):** `{dims['t2']} mm`  ·  Tolerancia **{tol_cubo}**
- **Faixa DIN:** {ch['faixa']}
"""
            )

            # Ajuste do diametro furo/eixo (ISO 286)
            folga_txt = (
                f"  ·  Folga simulada **+{custom_geom['folga']:.3f} mm**"
                if custom_geom and custom_geom["folga"] else ""
            )
            st.markdown(
                f"""
- **Furo do Cubo:** `Ø {diametro_furo:.3f} mm`  ·  Tolerancia **{tol_furo}**{folga_txt}
- **Eixo:** `Ø {diametro:.0f} mm`  ·  Tolerancia **{tol_eixo_diam}**
- **Diâmetro do cubo — gola (D_ext):** `Ø {d_ext:.0f} mm` _{d_ext_origem}_
- **Parede crítica restante (e):** `{e_parede:.1f} mm`
"""
            )

            if e_parede <= 0:
                st.error(
                    "❌ Parede do cubo inviável (e ≤ 0): o rasgo t2 é maior que a "
                    "parede disponível. Rever D_ext, t2 ou o diâmetro do furo."
                )
            elif e_parede < 2.0:
                st.warning(
                    f"⚠️ Parede crítica muito fina (e = {e_parede:.1f} mm): risco "
                    "de ruptura do cubo. Considerar cubo maior ou menor t2."
                )

            # Diagnosticos especificos do Modo Laboratorio.
            for alerta in diagnosticos_lab:
                st.warning(f"⚠️ {alerta}")

            # Auditoria de esmagamento / cisalhamento.
            # L = comprimento do cubo do acoplamento selecionado.
            esmag = None
            if comprimento_cubo:
                esmag = chaveta.verificar_esmagamento(
                    torque_projeto_nm=t_proj,
                    diametro_mm=diametro,
                    dims_chaveta=dims,
                    comprimento_mm=comprimento_cubo,
                )

                st.markdown("**Auditoria da chaveta (Torque de Projeto):**")
                if esmag["aprovado"]:
                    st.success(
                        f"✅ OK — Esmagamento {esmag['pressao_MPa']:.1f} MPa "
                        f"({esmag['util_esmagamento_pct']:.0f}% de {esmag['p_adm_MPa']:.0f}) "
                        f"| Cisalhamento {esmag['cisalhamento_MPa']:.1f} MPa "
                        f"({esmag['util_cisalhamento_pct']:.0f}% de {esmag['tau_adm_MPa']:.0f})"
                    )
                else:
                    falhas = []
                    if not esmag["aprovado_esmagamento"]:
                        falhas.append(
                            f"Esmagamento {esmag['pressao_MPa']:.1f} MPa > "
                            f"admissivel {esmag['p_adm_MPa']:.0f} MPa"
                        )
                    if not esmag["aprovado_cisalhamento"]:
                        falhas.append(
                            f"Cisalhamento {esmag['cisalhamento_MPa']:.1f} MPa > "
                            f"admissivel {esmag['tau_adm_MPa']:.0f} MPa"
                        )
                    st.error("❌ FALHA — " + " | ".join(falhas))
                    st.caption(
                        "Sugestao: usar chaveta dupla, rever o material ou escolher "
                        "um acoplamento com cubo mais longo."
                    )

        with col_desenho:
            fig = desenho.gerar_desenho_chaveta(
                d_mm=diametro_furo, b_mm=dims["b"], t1_mm=dims["t1"],
                t2_mm=dims["t2"], tol_chaveta=tol_eixo,
                tol_furo="CUSTOM" if custom_geom else tol_furo,
                d_ext_mm=d_ext,
            )
            st.pyplot(fig, use_container_width=True)
            desenho_png = desenho.figura_para_png(fig)
            desenho.fechar(fig)

        chavetas_para_pdf.append(
            {
                "veio": nome, "diametro": diametro,
                "b": dims["b"], "h": dims["h"], "t1": dims["t1"], "t2": dims["t2"],
                "esmag": esmag,
                "desenho_png": desenho_png,
                "folga": custom_geom["folga"] if custom_geom else 0.0,
                "diagnosticos": diagnosticos_lab,
                "d_ext": d_ext,
                "e_parede": e_parede,
            }
        )

st.info(
    "b = Largura | h = Altura | t1 = Profundidade a usinar no eixo | "
    "t2 = Profundidade a usinar no cubo (furo do acoplamento)"
)

# --- Guia de tolerancias e ajustes de montagem ---
with st.expander("📚 Guia de Tolerancias e Ajustes de Montagem (DIN 6885)"):
    st.markdown(
        """
| Tipo de Ajuste | Tolerancia Eixo | Tolerancia Cubo | Aplicacao recomendada |
|---|:---:|:---:|---|
| **Fixo / Aperto (Interferencia)** | `P9` | `P9` | Sistemas com choques severos ou inversao de marcha |
| **Normal / Transicao** | `N9` | `JS9` | Padrao para a maioria das aplicacoes industriais e acoplamentos |
| **Deslizante** | `H9` | `D10` | Quando o cubo necessita de deslizar axialmente ao longo do eixo |
"""
    )
    st.caption(
        "Tolerancias `N9` / `P9` / `JS9` aplicadas a **largura (b)** do rasgo de "
        "chaveta (DIN 6885). Os cartoes acima refletem o ajuste selecionado na "
        "barra lateral ('Ajuste da Chaveta')."
    )

    st.markdown("**Ajuste do diametro (furo do cubo x eixo) — ISO 286**")
    st.markdown(
        """
| Tipo de Ajuste | Furo (cubo) | Eixo | Aplicacao recomendada |
|---|:---:|:---:|---|
| **Montagem manual / deslizante** | `H7` | `j6` | Montagem/desmontagem manual, transicao leve |
| **Aperto leve (recomendado)** | `H7` | `k6` | Boa centragem, transmissao com choques moderados |
"""
    )
    st.caption(
        "O ajuste do **diametro** (furo do cubo sobre o eixo) e independente da "
        "tolerancia da largura do rasgo. Para o acoplamento sobre o eixo, o padrao "
        "recomendado e `H7/j6` (montagem manual) ou `H7/k6` (aperto leve)."
    )

st.divider()

# ---------------------------------------------------------------------------
# 5. Relatorio PDF
# ---------------------------------------------------------------------------
st.header("5. Relatorio")

dados_pdf = {
    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
    "aplicacao": {
        "potencia_cv": potencia_cv, "potencia_kw": potencia_kw, "rpm": rpm,
        "acionamento": acionamento, "maquina": maquina,
        "d_motor": diametro_motor, "d_movido": diametro_movido, "fs": fs,
    },
    "torques": {"nominal": t_nom, "projeto": t_proj},
    "selecao": sel_para_pdf,
    "chavetas": chavetas_para_pdf,
    "comprimento_chaveta": comprimento_cubo if comprimento_cubo else "-",
    "ajuste_chaveta": {
        "label": ajuste_chaveta, "eixo": tol_eixo, "cubo": tol_cubo,
    },
    "ajuste_furo": {
        "label": ajuste_furo, "furo": tol_furo, "eixo": tol_eixo_diam,
    },
    "modo_laboratorio": bool(custom_geom),
}

try:
    pdf_bytes = relatorio.gerar_pdf(dados_pdf)
    st.download_button(
        label="📄 Descarregar Relatorio (PDF)",
        data=pdf_bytes,
        file_name="relatorio_acoplamento.pdf",
        mime="application/pdf",
        type="primary",
    )
except Exception as e:  # noqa: BLE001 - mostrar erro amigavel na UI
    st.error(f"Nao foi possivel gerar o PDF: {e}")

st.caption(
    "⚠️ Valores de catalogo e fatores de servico ilustrativos. "
    "Chaveta de aco padrao (p_adm=100 MPa, tau_adm=60 MPa). "
    "Confirme sempre com o datasheet do fabricante."
)
