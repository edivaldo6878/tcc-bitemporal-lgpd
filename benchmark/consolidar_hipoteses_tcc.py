#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import hashlib

ROOT = Path.home() / "tcc-bitemporal"
EV = ROOT / "evidencias"
OUT = EV / "tcc_auditoria"
OUT.mkdir(parents=True, exist_ok=True)

ARQUIVO = OUT / "MATRIZ_H1_H4_CONSOLIDADA.md"

fontes = {
    "V3 100k": EV / "TC_V3_100K_POS_FIX_20261003_1842.txt",
    "V3 10k": EV / "TC_V3_10K_POS_FIX_20261003_1842.txt",
    "Consistencia": EV / "TC_C_E_DOMINIO_20261003_1814.txt",
    "SELECT": EV / "h3/select/resultados_select.csv",
    "UPDATE": EV / "h3/update/lote_20261008_000101/resultados_update.csv",
    "INSERT": EV / "h3/insert/lote_20261008_005153/resultados_insert.csv",
    "Armazenamento A": EV / "h3/armazenamento/ARMAZENAMENTO_POS_INSERT_A.txt",
    "Armazenamento B": EV / "h3/armazenamento/ARMAZENAMENTO_POS_INSERT_B.txt",
}

ausentes = [nome for nome, arq in fontes.items() if not arq.is_file()]

if ausentes:
    print("ERRO: fontes ausentes:", ", ".join(ausentes))
    raise SystemExit(1)

def aprovado(nome):
    texto = fontes[nome].read_text(
        encoding="utf-8", errors="replace"
    )
    return "RESULTADO GERAL: APROVADO" in texto

h1_ok = aprovado("V3 100k") and aprovado("V3 10k")
ce_ok = aprovado("Consistencia")

linhas = [
    "# Matriz de rastreabilidade — H1 a H4",
    "",
    f"Data: {datetime.now().isoformat(timespec='seconds')}",
    "",
    "## 1. Matriz de resultados",
    "",
    "| Hipotese | Evidencias | Avaliacao |",
    "|---|---|---|",
    f"| H1 — Temporalidade | V3 10k e 100k | {'Aprovada nos criterios testados' if h1_ok else 'Revisao necessaria'} |",
    f"| H2 — Auditoria | V3 e testes C/E | {'Evidencias funcionais positivas' if ce_ok else 'Revisao necessaria'}; conferir cobertura dos metadados |",
    "| H3 — Desempenho | CSVs oficiais e armazenamento | Resultados quantitativos disponiveis |",
    "| H4 — Governanca | Mecanismos de auditoria e anonimizacao | Analise qualitativa necessaria |",
    "",
    "## 2. Resultados de desempenho",
    "",
    "| Operacao | Modelo A TPS | Modelo B TPS |",
    "|---|---:|---:|",
    "| SELECT | 30307.90 | 26026.73 |",
    "| UPDATE | 3115.30 | 2668.54 |",
    "| INSERT | 3139.97 | 2628.16 |",
    "",
    "Os valores de TPS acima correspondem as medianas",
    "conferidas anteriormente nos CSVs oficiais.",
    "",
    "## 3. Armazenamento",
    "",
    "- Modelo A: 9.969.664 bytes adicionais.",
    "- Modelo B: 21.110.784 bytes adicionais.",
    "- Mesma carga experimental: 80.000 insercoes.",
    "- Relacao aproximada B/A: 2,12 vezes.",
    "",
    "## 4. Limitacoes",
    "",
    "- Uso de dados sinteticos.",
    "- Execucao em ambiente virtualizado WSL2 e Podman.",
    "- Implementacoes com funcionalidades e indices distintos.",
    "- Consultas historicas ainda sem benchmark amplo.",
    "- Conformidade LGPD nao certificada pelos testes.",
    "- Texto vigente da metodologia ainda nao confrontado.",
    "",
    "## 5. Manifesto de evidencias",
    ""
]

for nome, arq in fontes.items():
    digest = hashlib.sha256(arq.read_bytes()).hexdigest()
    linhas.append(f"- **{nome}**: `{arq.relative_to(ROOT)}`")
    linhas.append(f"  - SHA-256: `{digest}`")

ARQUIVO.write_text("\n".join(linhas) + "\n", encoding="utf-8")

print("MATRIZ_GERADA:", ARQUIVO)
print("H1:", "APROVADA_NOS_TESTES" if h1_ok else "PENDENTE")
print("CONSISTENCIA_CONCORRENCIA:",
      "APROVADA" if ce_ok else "PENDENTE")
print("H3:", "RESULTADOS_DISPONIVEIS")
print("H4:", "ANALISE_QUALITATIVA_PENDENTE")
print("STATUS_GERAL: CONSOLIDACAO_PRELIMINAR_CONCLUIDA")
