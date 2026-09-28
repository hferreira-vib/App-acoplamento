"""Desenho tecnico 2D (corte frontal) do conjunto eixo/cubo com rasgo de chaveta.

Gera um croqui esquematico para a oficina, mostrando:
  * o furo/eixo com o diametro nominal e a tolerancia (ISO 286);
  * o rasgo da chaveta no topo com a largura b e a tolerancia (DIN 6885);
  * as profundidades t1 (eixo) e t2 (cubo).

A funcao devolve o objeto matplotlib `fig` (para o Streamlit via st.pyplot) e
`figura_para_png` exporta a mesma figura como bytes PNG (para embutir no PDF).
"""

from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # backend headless: funciona no Streamlit e na geracao do PDF

import matplotlib.pyplot as plt  # noqa: E402  (apos definir o backend)
from matplotlib.patches import Circle, Rectangle  # noqa: E402


def estimar_diametro_externo(d_furo_max_mm: float) -> float:
    """Estimativa tecnica do diametro externo do cubo (D_ext) quando o
    catalogo nao o traz explicitamente.

    Baseada na geometria real da gola do cubo do Falk Steelflex T10
    (D_cubo ~ 1.42 x furo maximo), e nao na carcaca externa bipartida (A).
    """
    return round(1.42 * d_furo_max_mm)


def espessura_parede(d_ext_mm: float, d_mm: float, t2_mm: float) -> float:
    """Espessura da parede restante no topo do rasgo do cubo (mm):
    e = ((D_ext - d) / 2) - t2."""
    return round(((d_ext_mm - d_mm) / 2.0) - t2_mm, 1)


def gerar_desenho_chaveta(d_mm, b_mm, t1_mm, t2_mm, tol_chaveta, tol_furo,
                          d_ext_mm=None):
    """Corte frontal do cubo/eixo com o rasgo da chaveta.

    Args:
        d_mm: diametro do eixo/furo (mm).
        b_mm: largura da chaveta (mm).
        t1_mm: profundidade do rasgo no eixo (mm).
        t2_mm: profundidade do rasgo no cubo (mm).
        tol_chaveta: rotulo de tolerancia da largura b (ex.: "N9").
        tol_furo: rotulo de tolerancia do diametro do furo (ex.: "H7").
        d_ext_mm: diametro externo do cubo (mm). Se None, estimado como
            round(1.65 * d_mm).

    Returns:
        matplotlib.figure.Figure com o desenho.
    """
    r = d_mm / 2.0
    if d_ext_mm is None:
        d_ext_mm = estimar_diametro_externo(d_mm)
    # Garante proporcao desenhavel mesmo com parede muito fina/negativa.
    r_ext = max(d_ext_mm / 2.0, r + t2_mm + 1.0)
    e_parede = espessura_parede(d_ext_mm, d_mm, t2_mm)

    fig, ax = plt.subplots(figsize=(4.9, 4.9))
    ax.set_aspect("equal")
    ax.axis("off")

    # Contorno externo do cubo e furo/eixo (proporcao fiel via D_ext).
    ax.add_patch(Circle((0, 0), r_ext, facecolor="#eceff1",
                        edgecolor="#546e7a", lw=1.5, zorder=1))
    ax.add_patch(Circle((0, 0), r, facecolor="#ffffff",
                        edgecolor="#1565c0", lw=1.6, zorder=2))

    # Rasgo da chaveta no topo: do fundo no eixo (y=r-t1) ao fundo no cubo (y=r+t2).
    ax.add_patch(Rectangle((-b_mm / 2.0, r - t1_mm), b_mm, t1_mm + t2_mm,
                          facecolor="#fff3e0", edgecolor="#e65100",
                          lw=1.4, zorder=3))

    # Linha de referencia = superficie nominal do eixo (y = r), separa t1 de t2.
    ax.plot([-b_mm * 1.4, b_mm * 1.4], [r, r],
            color="#9e9e9e", lw=0.8, ls="--", zorder=4)

    # --- Cotas ---
    # Diametro do furo/eixo (cota horizontal pelo centro).
    ax.annotate("", xy=(r, 0), xytext=(-r, 0),
                arrowprops=dict(arrowstyle="<->", color="#1565c0", lw=1.2))
    ax.text(0, -r * 0.14, f"Ø {d_mm:.0f} mm  ({tol_furo})",
            ha="center", va="top", fontsize=9, color="#1565c0")

    # Diametro externo do cubo (cota vertical, lado esquerdo).
    x_ext = -r_ext - r_ext * 0.18
    ax.annotate("", xy=(x_ext, r_ext), xytext=(x_ext, -r_ext),
                arrowprops=dict(arrowstyle="<->", color="#455a64", lw=1.2))
    ax.plot([x_ext, 0], [r_ext, r_ext], color="#b0bec5", lw=0.6, ls=":", zorder=1)
    ax.plot([x_ext, 0], [-r_ext, -r_ext], color="#b0bec5", lw=0.6, ls=":",
            zorder=1)
    ax.text(x_ext - r_ext * 0.04, 0,
            f"Ø {d_ext_mm:.0f} mm (D_cubo - gola)",
            ha="center", va="center", fontsize=9, color="#455a64", rotation=90)

    # Largura b (cota horizontal acima do cubo).
    yb = r_ext + r_ext * 0.12
    ax.annotate("", xy=(b_mm / 2.0, yb), xytext=(-b_mm / 2.0, yb),
                arrowprops=dict(arrowstyle="<->", color="#e65100", lw=1.2))
    ax.text(0, yb + r_ext * 0.03, f"b = {b_mm:.0f} mm  ({tol_chaveta})",
            ha="center", va="bottom", fontsize=9, color="#e65100")

    # t1 (eixo) e t2 (cubo): cotas verticais a direita do rasgo.
    xt = b_mm / 2.0 + r_ext * 0.12
    ax.annotate("", xy=(xt, r), xytext=(xt, r - t1_mm),
                arrowprops=dict(arrowstyle="<->", color="#2e7d32", lw=1.1))
    ax.text(xt + r_ext * 0.03, r - t1_mm / 2.0,
            f"t1 (eixo) = {t1_mm:.1f} mm",
            ha="left", va="center", fontsize=8, color="#2e7d32")

    ax.annotate("", xy=(xt, r), xytext=(xt, r + t2_mm),
                arrowprops=dict(arrowstyle="<->", color="#6a1b9a", lw=1.1))
    ax.text(xt + r_ext * 0.03, r + t2_mm / 2.0,
            f"t2 (cubo) = {t2_mm:.1f} mm",
            ha="left", va="center", fontsize=8, color="#6a1b9a")

    # Parede critica restante (e): do fundo do rasgo no cubo (r+t2) ao Ø externo.
    ax.annotate("", xy=(0, r_ext), xytext=(0, r + t2_mm),
                arrowprops=dict(arrowstyle="<->", color="#c62828", lw=1.4),
                zorder=6)
    ax.annotate(
        f"Parede (e) = {e_parede:.1f} mm",
        xy=(0, (r + t2_mm + r_ext) / 2.0),
        xytext=(-r_ext * 1.15, r_ext * 1.02),
        ha="center", va="bottom", fontsize=8, color="#c62828",
        arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.0), zorder=6,
    )

    # Vista.
    lim = r_ext * 1.55
    ax.set_xlim(-lim * 1.2, lim * 1.12)
    ax.set_ylim(-lim, lim + r_ext * 0.24)
    ax.set_title("Corte frontal - cubo/eixo com rasgo de chaveta",
                 fontsize=9, color="#37474f")
    fig.tight_layout()
    return fig


def figura_para_png(fig, dpi=150):
    """Exporta a figura matplotlib como bytes PNG (BytesIO) para embutir no PDF."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


def fechar(fig):
    """Liberta a figura da memoria (evita acumulo de figuras no Streamlit)."""
    plt.close(fig)
