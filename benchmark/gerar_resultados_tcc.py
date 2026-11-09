#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "tcc-bitemporal"
OUT = ROOT / "relatorios"
OUT.mkdir(parents=True, exist_ok=True)

ARQ = OUT / "CAPITULO_4_RESULTADOS_DISCUSSÃO.md"

resultados = [
    ("SELECT", 30307.90, 26026.73),
    ("UPDATE", 3115.30, 2668.54),
    ("INSERT", 3139.97, 2628.16)
]

linhas = [
    "# 4. RESULTADOS E DISCUSSÃO",
    "",
    f"*Versão preliminar — {datetime.now():%d/%m/%Y}*",
    "",
    "## 4.1 Ambiente experimental",
    "",
    "Os experimentos utilizaram PostgreSQL 18.4 em contêiner",
    "Podman, executado em ambiente AlmaLinux sobre WSL2.",
    "Foram empregados conjuntos de dados sintéticos.",
    "",
    "Dois modelos foram examinados: o Modelo A, convencional,",
    "representado por `parte_controle`, e o Modelo B, temporal,",
    "representado por `parte` e `parte_historico`.",
    "",
    "## 4.2 Validação funcional",
    "",
    "O verificador V3 foi aprovado nas bases de 10 mil e",
    "100 mil partes após correções de divergências temporais.",
    "Os testes de consistência e concorrência também foram",
    "aprovados nos cenários executados.",
    "",
    "As evidências demonstram o atendimento aos critérios",
    "funcionais automatizados, sem representar certificação",
    "integral de conformidade com a LGPD.",
    "",
    "## 4.3 Desempenho comparativo",
    "",
    "| Operação | Modelo A (TPS) | Modelo B (TPS) | Redução B |",
    "|---|---:|---:|---:|"
]

for operacao, a, b in resultados:
    reducao = (a - b) / a * 100
    linhas.append(
        f"| {operacao} | {a:,.2f} | {b:,.2f} | {reducao:.2f}% |"
    )

linhas += [
    "",
    "Os valores representam medianas de cinco rodadas",
    "por modelo em cada operação.",
    "",
    "O Modelo B apresentou menor taxa de processamento",
    "nas cargas avaliadas, com reduções entre aproximadamente",
    "14% e 16%.",
    "",
    "## 4.4 Armazenamento",
    "",
    "Após 80.000 inserções, o crescimento físico observado",
    "foi de 9.969.664 bytes no Modelo A e 21.110.784 bytes",
    "no Modelo B. Isso corresponde a 124,62 e 263,88 bytes",
    "por inserção, respectivamente.",
    "",
    "A relação entre os crescimentos foi de aproximadamente",
    "2,12 vezes, sob as condições experimentais adotadas.",
    "",
    "## 4.5 Recuperação temporal",
    "",
    "As consultas por tempo válido utilizaram o índice",
    "`parte_pkey`, com planos `Index Only Scan`.",
    "A consulta histórica examinada utilizou o índice",
    "`ix_parte_hist_tempo`, com filtro adicional por tempo válido.",
    "",
    "Esses resultados caracterizam consultas diagnósticas.",
    "Não constituem benchmark histórico abrangente.",
    "",
    "## 4.6 Discussão e limitações",
    "",
    "Os resultados evidenciam uma relação de compromisso",
    "entre funcionalidades temporais, desempenho e espaço.",
    "",
    "As principais limitações compreendem dados sintéticos,",
    "ambiente virtualizado, diferenças funcionais e físicas",
    "entre modelos e ausência de benchmark histórico amplo.",
    "",
    "Embora a arquitetura ofereça mecanismos relevantes",
    "para rastreabilidade, auditoria e governança de dados,",
    "não é possível inferir conformidade integral com a LGPD",
    "apenas a partir dos experimentos realizados.",
    "",
    "## 4.7 Síntese",
    "",
    "A implementação demonstrou viabilidade funcional",
    "nos critérios testados e custos mensuráveis de desempenho",
    "e armazenamento na carga experimental.",
    "",
    "Os resultados permitem discutir a arquitetura temporal",
    "como alternativa de apoio à governança de dados pessoais,",
    "desde que acompanhada por controles organizacionais",
    "e regras adequadas de tratamento e retenção.",
    ""
]

ARQ.write_text("\n".join(linhas), encoding="utf-8")

print("CAPITULO_GERADO:", ARQ)
print("SECOES: 7")
print("STATUS: PRELIMINAR")
