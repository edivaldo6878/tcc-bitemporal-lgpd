#!/usr/bin/env python3
import csv
import hashlib
import re
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / "tcc-bitemporal"
OUT = ROOT / "evidencias" / "tcc_auditoria"
OUT.mkdir(parents=True, exist_ok=True)

DATE = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = OUT / f"AUDITORIA_ETAPA4_{DATE}.md"
CSV = OUT / f"INVENTARIO_ETAPA4_{DATE}.csv"
SHA = OUT / f"MANIFESTO_SHA256_{DATE}.txt"
PACKAGE = OUT / f"AUDITORIA_ETAPA4_{DATE}.tar.gz"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def search_files():
    extensions = {
        ".sql", ".py", ".sh", ".csv", ".txt",
        ".json", ".jsonl", ".md", ".tex",
        ".docx", ".pdf"
    }
    roots = [
        ROOT / "benchmark",
        ROOT / "evidencias",
        ROOT / "db-dominio"
    ]
    seen = set()
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in extensions:
                continue
            if OUT in p.parents:
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p

def classify(path):
    s = str(path.relative_to(ROOT)).lower()

    if "ground_truth" in s or "verificador" in s:
        return "H1/H2 - Validacao funcional"
    if "anonimiz" in s or "auditor" in s:
        return "H2/H4 - Governanca"
    if "select" in s:
        return "H3 - SELECT"
    if "update" in s:
        return "H3 - UPDATE"
    if "insert" in s:
        return "H3 - INSERT"
    if "armazenamento" in s:
        return "H3 - Armazenamento"
    if "historico" in s or "bitemporal" in s:
        return "H1/H3 - Consultas temporais"
    if "metodolog" in s or "etapa" in s:
        return "Documento/metodologia"
    return "Outras evidencias"

def pg_query(sql):
    cmd = [
        "podman", "exec", "tcc_postgres",
        "psql", "-X", "-v", "ON_ERROR_STOP=1",
        "-U", "dba", "-d", "tcc_h3_update",
        "-At", "-F", "|", "-c", sql
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        timeout=90, check=True
    )
    return result.stdout.strip()

print("Iniciando auditoria da Etapa 4...")

files = sorted(search_files())
inventory = []

for path in files:
    inventory.append({
        "arquivo": str(path.relative_to(ROOT)),
        "categoria": classify(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path)
    })

with CSV.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["arquivo", "categoria", "bytes", "sha256"]
    )
    writer.writeheader()
    writer.writerows(inventory)

with SHA.open("w", encoding="utf-8") as f:
    for item in inventory:
        f.write(f"{item['sha256']}  {item['arquivo']}\n")

db_status = "NAO_VERIFICADO"
counts = ""
indexes = ""
triggers = ""

try:
    database = pg_query("SELECT current_database();")
    if database != "tcc_h3_update":
        raise RuntimeError("Banco inesperado")

    counts = pg_query("""
SELECT 'parte_controle',count(*) FROM parte_controle
UNION ALL
SELECT 'parte',count(*) FROM parte
UNION ALL
SELECT 'parte_historico',count(*) FROM parte_historico;
""")

    indexes = pg_query("""
SELECT tablename,indexname,indexdef
FROM pg_indexes
WHERE schemaname='public'
AND tablename IN ('parte','parte_controle','parte_historico')
ORDER BY tablename,indexname;
""")

    triggers = pg_query("""
SELECT event_object_table,trigger_name,
       event_manipulation,action_timing
FROM information_schema.triggers
WHERE event_object_schema='public'
AND event_object_table IN ('parte','parte_controle')
ORDER BY event_object_table,trigger_name;
""")

    db_status = "CONSULTADO_COM_SUCESSO"
except Exception as exc:
    db_status = f"NAO_VERIFICADO: {exc}"

categories = {}
for item in inventory:
    key = item["categoria"]
    categories[key] = categories.get(key, 0) + 1

# Valores consolidados a partir dos experimentos anteriores;
# NÃO são recalculados a partir dos arquivos pelo script.
metrics = {
    "SELECT": (30307.90, 26026.73),
    "UPDATE": (3115.30, 2668.54),
    "INSERT": (3139.97, 2628.16)
}

lines = [
    "# Auditoria da Etapa 4 — TCC UFABC",
    "",
    f"Data de execução: {datetime.now().isoformat(timespec='seconds')}",
    "",
    "## 1. Escopo",
    "",
    "Auditoria documental e estrutural, sem alterar dados.",
    "Os resultados científicos dependem da interpretação",
    "dos verificadores e dos protocolos experimentais.",
    "",
    "## 2. Estado do banco experimental",
    "",
    f"Status: **{db_status}**",
    "",
    "### Contagens",
    "```text", counts or "Indisponíveis", "```",
    "",
    "### Índices",
    "```text", indexes or "Indisponíveis", "```",
    "",
    "### Triggers",
    "```text", triggers or "Indisponíveis", "```",
    "",
    "## 3. Inventário de evidências",
    "",
    f"Arquivos catalogados: **{len(inventory)}**",
    ""
]

for category, count in sorted(categories.items()):
    lines.append(f"- {category}: {count} arquivo(s)")

lines += [
    "",
    "## 4. Resultados experimentais informados",
    "",
    "| Operação | Modelo A (TPS) | Modelo B (TPS) | Redução B |",
    "|---|---:|---:|---:|"
]

for op, (a, b) in metrics.items():
    reduction = 100 * (a - b) / a
    lines.append(f"| {op} | {a:.2f} | {b:.2f} | {reduction:.2f}% |")

a_growth = 33054720 - 23085056
b_growth = 62439424 - 41328640

lines += [
    "",
    "Valores acima são transcrições dos resultados já",
    "consolidados e exigem conferência com os logs oficiais.",
    "",
    "## 5. Armazenamento incremental",
    "",
    f"- Modelo A: {a_growth} bytes / 80000 inserções.",
    f"- Modelo B: {b_growth} bytes / 80000 inserções.",
    f"- Relação B/A: {b_growth / a_growth:.3f}.",
    "",
    "## 6. Matriz de coerência científica",
    "",
    "| Hipótese | Evidência necessária | Situação |",
    "|---|---|---|",
    "| H1 — Temporalidade | Verificador + testes de recuperação | Conferir resultados oficiais |",
    "| H2 — Auditoria | Metadados, histórico e operações DML | Conferir cobertura funcional |",
    "| H3 — Desempenho | Logs SELECT/UPDATE/INSERT e armazenamento | Resultados registrados |",
    "| H4 — Governança | Regras, rastreabilidade e limitações LGPD | Exige análise qualitativa |",
    "",
    "## 7. Pontos de atenção",
    "",
    "1. A conformidade com a LGPD não é demonstrada apenas pela existência de recursos técnicos.",
    "2. Os modelos A e B não possuem equivalência funcional completa para consultas históricas.",
    "3. Os valores de TPS devem ser conferidos nos CSVs oficiais antes da publicação.",
    "4. Os testes históricos atuais são diagnósticos, não benchmark representativo.",
    "5. O crescimento de armazenamento reflete as cargas e condições físicas observadas.",
    "6. A auditoria de coerência com a metodologia exige acesso ao texto acadêmico vigente.",
    "7. Inventariar um arquivo não equivale a validar seu conteúdo ou aprovar um teste.",
    "",
    "## 8. Próximas providências",
    "",
    "- Confrontar hipóteses e métricas com a metodologia da versão vigente do TCC.",
    "- Validar a correspondência entre cada resultado e sua evidência oficial.",
    "- Separar resultados observados de interpretações e limitações.",
    "- Revisar o capítulo Resultados e Discussão.",
    ""
]

REPORT.write_text("\n".join(lines), encoding="utf-8")

with tarfile.open(PACKAGE, "w:gz") as tar:
    for p in (REPORT, CSV, SHA):
        tar.add(p, arcname=p.name)

with tarfile.open(PACKAGE, "r:gz") as tar:
    bad = tar.getmembers()
    if len(bad) != 3:
        raise RuntimeError("Pacote incompleto")

print("AUDITORIA_CONCLUIDA")
print("Banco:", db_status)
print("Arquivos catalogados:", len(inventory))
print("Relatorio:", REPORT)
print("Inventario:", CSV)
print("Manifesto:", SHA)
print("Pacote:", PACKAGE)
print("SHA256_PACOTE:", sha256(PACKAGE))
