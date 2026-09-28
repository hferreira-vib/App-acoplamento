# Dimensionamento, Selecao e Auditoria de Acoplamentos Industriais

Aplicacao web (Streamlit) para dimensionar, selecionar e auditar acoplamentos
industriais de varias tecnologias, com verificacao da chaveta (DIN 6885),
auditoria de esmagamento/cisalhamento e relatorio em PDF.

## Estrutura

```
App acoplamento/
├── app.py                     # Interface Streamlit (ficheiro principal)
├── requirements.txt           # streamlit, pandas, fpdf2
├── iniciar_app.bat            # Arranque com dois cliques (Windows)
├── data/
│   ├── fator_servico.json           # Matriz Acionamento x Maquina -> FS
│   ├── catalogo_acoplamentos.json   # FALK Steelflex T10 (real) + KTR Rotex,
│   │                                #   Flender N-EUPEX, FALK Lifelign G20, KTR Radex-N
│   └── norma_din6885.json           # Chavetas 10-150 mm (b, h, t1, t2)
└── logic/
    ├── calculos.py            # Torque nominal, torque de projeto, FS
    ├── chaveta.py             # DIN 6885 + verificacao esmagamento/cisalhamento
    ├── selecao.py             # Modo 1 (sugerir) e Modo 2 (verificar)
    └── relatorio.py           # Geracao do relatorio PDF (fpdf2)
```

## Como iniciar (2 cliques)

1. Instale o **Python 3.10+** (marque "Add Python to PATH" no instalador).
2. Faca duplo clique em **`iniciar_app.bat`**.
   - Na 1a execucao instala as dependencias (streamlit, pandas, fpdf2).
   - Depois abre a aplicacao no navegador (http://localhost:8501).

### Atalho na Area de Trabalho
Botao direito em `iniciar_app.bat` -> **Enviar para -> Area de trabalho (criar atalho)**.

## Formulas e criterios

- Torque Nominal (Nm) = (Potencia [kW] * 9550) / RPM
- Torque de Projeto (Nm) = Torque Nominal * Fator de Servico (FS)
- Chaveta (DIN 6885): b, h, t1 (eixo, N9), t2 (cubo, P9)
- Auditoria da chaveta (aco padrao): F = 2*T/d; esmagamento p = F/(L*min(t1,t2));
  cisalhamento tau = F/(L*b). Admissiveis: p_adm = 100 MPa, tau_adm = 60 MPa.

## Modos

- **Sugerir Acoplamento Ideal**: menor modelo com Torque Max >= Projeto,
  Furo Max >= maior veio e RPM Max >= RPM (opcionalmente filtrado por categoria).
- **Verificar Modelo Especifico**: parecer Aprovado/Reprovado com o motivo exato.

> Valores de catalogo e fatores de servico ilustrativos (FALK Steelflex T10 com
> valores reais). Confirme sempre com o datasheet do fabricante.
