"""Geracao do relatorio tecnico em PDF (usa fpdf2)."""

import struct
from io import BytesIO

from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _png_size(png_bytes: bytes) -> tuple[int, int]:
    """Le (largura, altura) em pixels do cabecalho IHDR de um PNG (sem PIL)."""
    w_px, h_px = struct.unpack(">II", png_bytes[16:24])
    return w_px, h_px


def _s(texto) -> str:
    """Sanitiza texto para as fontes core do FPDF (Latin-1)."""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, _s("Relatorio de Dimensionamento de Acoplamento"),
                  border=0, align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, _s(f"Pagina {self.page_no()}"), align="C")


def _titulo(pdf: _PDF, texto: str):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, _s(texto), border=0, align="L", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def _linha(pdf: _PDF, rotulo: str, valor: str):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(55, 6, _s(rotulo))
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _s(valor), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _texto(pdf: _PDF, texto: str, style: str = "", size: int = 10):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", style, size)
    pdf.multi_cell(0, 6, _s(texto), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def gerar_pdf(dados: dict) -> bytes:
    """Gera o relatorio em PDF a partir do dicionario `dados` e devolve bytes.

    Estrutura esperada de `dados`:
      data, aplicacao{potencia_kw, rpm, acionamento, maquina, d_motor, d_movido, fs},
      torques{nominal, projeto},
      selecao{modo, texto, aprovado, detalhes[]},
      chavetas[ {veio, diametro, b, h, t1, t2, esmag{...}, desenho_png,
                 folga, diagnosticos[], d_ext, e_parede} ],
      comprimento_chaveta,
      ajuste_chaveta{label, eixo, cubo}, ajuste_furo{label, furo, eixo},
      modo_laboratorio (bool)
    """
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    if dados.get("data"):
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, _s(f"Data: {dados['data']}"), align="R")
        pdf.ln(8)

    # Banner de laboratorio (configuracao especial / geometria personalizada).
    if dados.get("modo_laboratorio"):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(198, 40, 40)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(
            0, 9, _s("RELATORIO DE TESTE / CONFIGURACAO ESPECIAL DE LABORATORIO"),
            border=0, align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(
            0, 6,
            _s("Cotas personalizadas substituem a DIN 6885 - valido apenas para ensaio."),
            align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.ln(4)

    # --- 1. Dados da aplicacao ---
    app = dados["aplicacao"]
    _titulo(pdf, "1. Dados da Aplicacao")
    _linha(pdf, "Potencia:", f"{app['potencia_cv']:.2f} CV ({app['potencia_kw']:.2f} kW)")
    _linha(pdf, "Rotacao:", f"{app['rpm']:.0f} RPM")
    _linha(pdf, "Acionamento:", app["acionamento"])
    _linha(pdf, "Maquina movida:", app["maquina"])
    _linha(pdf, "Diametro eixo motor:", f"{app['d_motor']:.0f} mm")
    _linha(pdf, "Diametro eixo movido:", f"{app['d_movido']:.0f} mm")
    _linha(pdf, "Fator de servico (FS):", f"{app['fs']:.2f}")
    pdf.ln(4)

    # --- 2. Torques ---
    t = dados["torques"]
    _titulo(pdf, "2. Cargas Calculadas")
    _linha(pdf, "Torque nominal:", f"{t['nominal']:.1f} Nm")
    _linha(pdf, "Torque de projeto:", f"{t['projeto']:.1f} Nm")
    pdf.ln(4)

    # --- 3. Acoplamento ---
    sel = dados["selecao"]
    _titulo(pdf, "3. Acoplamento")
    _linha(pdf, "Modo:", sel["modo"])
    _texto(pdf, sel["texto"], style="B")
    _linha(pdf, "Resultado:", "APROVADO" if sel["aprovado"] else "REPROVADO")
    for d in sel.get("detalhes", []):
        _texto(pdf, f"- {d}")

    sp = sel.get("specs")
    if sp:
        pdf.ln(1)
        _linha(pdf, "Peso:", f"{sp.get('Peso (kg)', '-')} kg")
        _linha(pdf, "Momento de inercia:",
               f"{sp.get('Momento de Inercia (kg.m2)', '-')} kg.m2")
        _linha(pdf, "Desalinhamento adm.:",
               f"angular {sp.get('Desalinhamento Angular (graus)', '-')} graus | "
               f"radial {sp.get('Desalinhamento Radial (mm)', '-')} mm | "
               f"axial {sp.get('Desalinhamento Axial (mm)', '-')} mm")
    pdf.ln(4)

    # --- 4. Chavetas e ajuste do furo ---
    _titulo(pdf, "4. Dimensionamento das Chavetas (DIN 6885) e Ajuste do Furo (ISO 286)")
    _texto(pdf, f"Comprimento considerado: {dados.get('comprimento_chaveta', '-')} mm")
    chaveta_fit = dados.get("ajuste_chaveta") or {}
    tol_eixo = chaveta_fit.get("eixo", "N9")
    tol_cubo = chaveta_fit.get("cubo", "P9")
    if chaveta_fit.get("label"):
        _linha(pdf, "Ajuste da chaveta (DIN 6885):", chaveta_fit["label"])
    furo_fit = dados.get("ajuste_furo") or {}
    if furo_fit.get("label"):
        _linha(pdf, "Ajuste do furo (ISO 286):", furo_fit["label"])
    pdf.ln(1)
    for ch in dados["chavetas"]:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _s(f"{ch['veio']} - diametro {ch['diametro']:.0f} mm"),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        _texto(pdf, f"Chaveta b x h: {ch['b']} x {ch['h']} mm")
        _texto(pdf, f"Rasgo no eixo (t1): {ch['t1']} mm - tolerancia {tol_eixo}")
        _texto(pdf, f"Rasgo no cubo (t2): {ch['t2']} mm - tolerancia {tol_cubo}")
        if furo_fit.get("furo") and furo_fit.get("eixo"):
            folga = ch.get("folga") or 0.0
            furo_diam = ch["diametro"] + folga
            extra = f" (folga simulada +{folga:.3f} mm)" if folga else ""
            _texto(
                pdf,
                f"Furo do cubo: diametro {furo_diam:.3f} mm - tolerancia "
                f"{furo_fit['furo']}{extra} | Eixo: {ch['diametro']:.0f} mm - "
                f"tolerancia {furo_fit['eixo']}",
            )
        if ch.get("d_ext"):
            _texto(
                pdf,
                f"Diametro do cubo / gola (D_ext): {ch['d_ext']:.0f} mm "
                f"| Parede critica restante (e): {ch.get('e_parede', 0.0):.1f} mm",
            )
        for diag in ch.get("diagnosticos") or []:
            _texto(pdf, f"[ALERTA LAB] {diag}", style="B", size=9)
        e = ch.get("esmag")
        if e:
            status = "OK" if e["aprovado"] else "FALHA"
            _texto(
                pdf,
                f"Esmagamento: {e['pressao_MPa']:.1f} / {e['p_adm_MPa']:.0f} MPa "
                f"({e['util_esmagamento_pct']:.0f}%) | "
                f"Cisalhamento: {e['cisalhamento_MPa']:.1f} / {e['tau_adm_MPa']:.0f} MPa "
                f"({e['util_cisalhamento_pct']:.0f}%) -> {status}",
            )
        pdf.ln(3)

    _texto(
        pdf,
        "b = Largura | h = Altura | t1 = Profundidade no eixo | t2 = Profundidade no cubo",
        style="I", size=9,
    )
    pdf.ln(2)

    # --- 5. Croqui tecnico de usinagem da oficina ---
    _titulo(pdf, "5. Croqui Tecnico de Usinagem da Oficina")

    # Tabela completa de tolerancias selecionadas (DIN 6885 + ISO 286).
    _tabela_tolerancias(pdf, tol_eixo, tol_cubo, furo_fit)
    pdf.ln(2)

    # Desenhos 2D (corte frontal) por eixo, lado a lado.
    croquis = [c for c in dados["chavetas"] if c.get("desenho_png")]
    if croquis:
        _texto(
            pdf,
            "Corte frontal do conjunto eixo/cubo com o rasgo da chaveta.",
            style="I", size=9,
        )
        img_w = 84.0            # largura de cada croqui (mm)
        gap = 6.0
        xs = [pdf.l_margin, pdf.l_margin + img_w + gap]
        y_top = pdf.get_y()
        alturas = []
        for i, c in enumerate(croquis[:2]):
            x = xs[i]
            pdf.set_xy(x, y_top)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(img_w, 6, _s(f"{c['veio']} - diametro {c['diametro']:.0f} mm"),
                     align="C")
            png = c["desenho_png"]
            w_px, h_px = _png_size(png)
            img_h = img_w * h_px / w_px
            pdf.image(BytesIO(png), x=x, y=y_top + 7, w=img_w)
            alturas.append(img_h)
        pdf.set_y(y_top + 7 + (max(alturas) if alturas else 0) + 3)

    pdf.ln(2)
    _texto(
        pdf,
        "Valores de catalogo e fatores de servico ilustrativos. Confirmar com o "
        "datasheet do fabricante antes da especificacao final.",
        style="I", size=8,
    )

    saida = pdf.output()
    return bytes(saida)


def _tabela_tolerancias(pdf: _PDF, tol_eixo: str, tol_cubo: str, furo_fit: dict):
    """Tabela 3 colunas: Elemento | Cota | Tolerancia (norma)."""
    larguras = (78, 46, 50)
    cab = ("Elemento", "Cota", "Tolerancia")
    linhas = [
        ("Rasgo da chaveta - eixo", "Largura (b)", f"{tol_eixo}  (DIN 6885)"),
        ("Rasgo da chaveta - cubo", "Largura (b)", f"{tol_cubo}  (DIN 6885)"),
        ("Furo do cubo", "Diametro (Ø)",
         f"{furo_fit.get('furo', '-')}  (ISO 286)"),
        ("Eixo", "Diametro (Ø)", f"{furo_fit.get('eixo', '-')}  (ISO 286)"),
    ]
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(224, 224, 224)
    for w, texto in zip(larguras, cab):
        pdf.cell(w, 7, _s(texto), border=1, align="C", fill=True)
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    for elem, cota, tol in linhas:
        pdf.set_x(pdf.l_margin)
        pdf.cell(larguras[0], 6, _s(elem), border=1)
        pdf.cell(larguras[1], 6, _s(cota), border=1, align="C")
        pdf.cell(larguras[2], 6, _s(tol), border=1, align="C")
        pdf.ln(6)
