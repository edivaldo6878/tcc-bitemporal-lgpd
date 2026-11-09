#!/usr/bin/env python3
"""
gerar_dominio_v3.py

Popula, com dados 100% ficticios, o modelo de dominio de tres tabelas:
  processo                 (sem tratamento temporal)
  parte                    (bitemporal: valid_at + sys_period/trigger)
  movimentacao_processual  (somente insercao)
e o Modelo A (parte_controle) ao final. Gera o ground truth (gabarito) em JSONL.

Cenarios cobertos (Secao 7.6 do Capitulo de Metodo):
  (a) atualizacao simples de dados cadastrais (nome, e-mail, telefone, endereco)
  (b) correcao retroativa do inicio do tempo valido
  (b2) mudanca real: encerra o periodo valido aberto e abre outro (mesmo id_parte)
  (f) anonimizacao controlada via anonimizar_parte()
Os cenarios (c) sobreposicao e (e) concorrencia ficam em testes proprios.

Garantias de ficcao: CPF e CNPJ com digito verificador INVALIDO por construcao;
e-mails em @exemplo.invalid; telefones com DDD 00; CEP iniciado em 000; numero de
processo com tribunal 99 e unidade 9999.

Reprodutivel: data de referencia fixa e semente fixa. Senha so via PGPASSWORD.

Uso:
    export PGPASSWORD=...
    python3 gerar_dominio_v3.py --escala pequena --dbname tcc_dominio
    python3 gerar_dominio_v3.py --n 300 --dbname tcc_dominio --ground-truth gt_teste.jsonl
A escala conta PARTES (as entidades bitemporais): 10 mil / 100 mil / 1 milhao.
"""

import argparse
import hashlib
import json
import os
import random
import sys
import time
import unicodedata
from datetime import date, datetime, time as dtime, timedelta, timezone

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit("Dependencia faltando: pip3 install --user psycopg2-binary")
try:
    from faker import Faker
except ImportError:
    sys.exit("Dependencia faltando: pip3 install --user Faker")

ESCALAS = {"pequena": 10_000, "intermediaria": 100_000, "estresse": 1_000_000}
DATA_REF = date(2026, 9, 1)
P_PESSOA_FISICA = 0.70
P_ATUALIZACAO = 0.30      # (a) por parte
P_RETRO = 0.08            # (b) por atualizacao
P_MUDANCA_REAL = 0.15     # (b2) por parte
P_ANONIMIZACAO = 0.02     # (f) por parte
MAX_ATUALIZACOES = 3
BATCH = 1000              # commit a cada N partes
MARCADOR = "[DADO PESSOAL REMOVIDO]"
FUNDAMENTO = "art. 18, VI LGPD - eliminacao de dado desnecessario (cenario sintetico)"
FIN_CARGA = "carga_sintetica"
BASE_CARGA = "art. 7, III LGPD (dados sinteticos)"

PESSOAIS = ["nome", "nome_social", "nr_documento", "dt_nascimento", "email", "telefone",
            "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "cep"]
NAO_PESSOAIS = ["id_processo", "tp_pessoa", "participacao", "tp_documento"]
COLUNAS_ENDERECO = ["logradouro", "numero", "complemento", "bairro", "cidade", "uf", "cep"]

CLASSES = ["Procedimento Comum", "Mandado de Seguranca Civel", "Execucao Fiscal",
           "Cumprimento de Sentenca", "Acao Previdenciaria", "Procedimento do Juizado Especial",
           "Embargos a Execucao", "Tutela Cautelar Antecedente"]
TIPOS_MOV = ["JUNTADA", "DESPACHO", "DECISAO", "INTIMACAO", "CITACAO", "AUDIENCIA",
             "CONCLUSAO", "PUBLICACAO"]


def parse_args():
    p = argparse.ArgumentParser(description="Gerador v3 - dominio de 3 tabelas")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--escala", choices=ESCALAS.keys())
    g.add_argument("--n", type=int, help="Numero exato de PARTES")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--id-parte-start", type=int, default=1000)
    p.add_argument("--id-processo-start", type=int, default=1)
    p.add_argument("--host", default=os.environ.get("PGHOST", "localhost"))
    p.add_argument("--port", default=os.environ.get("PGPORT", "5433"))
    p.add_argument("--dbname", default=os.environ.get("PGDATABASE", "tcc_dominio"))
    p.add_argument("--user", default=os.environ.get("PGUSER", "dba"))
    p.add_argument("--ground-truth", default="ground_truth_v3.jsonl")
    return p.parse_args()


# ---------------------------------------------------------------- utilidades
def canon(valores):
    """Serializacao canonica (a mesma do verificador) para calcular hashes."""
    ajustados = [v.isoformat() if isinstance(v, date) else v for v in valores]
    return hashlib.md5(json.dumps(ajustados, ensure_ascii=False).encode("utf-8")).hexdigest()


def hash_pessoais(d):
    return canon([d[c] for c in PESSOAIS])


def hash_nao_pessoais(d):
    return canon([d[c] for c in NAO_PESSOAIS])


def ascii_slug(texto):
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum()) or "x"


def _dv_cpf(digitos):
    s = sum(x * (len(digitos) + 1 - i) for i, x in enumerate(digitos))
    r = (s * 10) % 11
    return 0 if r == 10 else r


def cpf_invalido(rng):
    d = [rng.randint(0, 9) for _ in range(9)]
    d.append(_dv_cpf(d))
    d.append((_dv_cpf(d) + 1) % 10)  # segundo digito deliberadamente errado
    return "".join(map(str, d))


def _dv_cnpj(digitos):
    pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if len(digitos) == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    r = sum(x * p for x, p in zip(digitos, pesos)) % 11
    return 0 if r < 2 else 11 - r


def cnpj_invalido(rng):
    d = [rng.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    d.append(_dv_cnpj(d))
    d.append((_dv_cnpj(d) + 1) % 10)
    return "".join(map(str, d))


def telefone(rng):
    return f"(00) 9{rng.randint(0, 9999):04d}-{rng.randint(0, 9999):04d}"


def endereco(fake, rng):
    return {"logradouro": fake.street_name(), "numero": str(rng.randint(1, 9999)),
            "complemento": f"Apto {rng.randint(1, 300)}" if rng.random() < 0.3 else None,
            "bairro": fake.bairro(), "cidade": fake.city(), "uf": fake.estado_sigla(),
            "cep": f"000{rng.randint(0, 99999):05d}"}


def nova_parte(fake, rng, id_parte, id_processo, participacao):
    fisica = rng.random() < P_PESSOA_FISICA
    d = {"id_processo": id_processo, "tp_pessoa": "F" if fisica else "J",
         "participacao": participacao, "tp_documento": "CPF" if fisica else "CNPJ"}
    if fisica:
        primeiro = fake.first_name()
        d["nome"] = f"{primeiro} {fake.last_name()}"
        d["nome_social"] = primeiro.split()[0] if rng.random() < 0.05 else None
        d["nr_documento"] = cpf_invalido(rng)
        d["dt_nascimento"] = DATA_REF - timedelta(days=rng.randint(18 * 365, 90 * 365))
    else:
        d["nome"] = fake.company()
        d["nome_social"] = None
        d["nr_documento"] = cnpj_invalido(rng)
        d["dt_nascimento"] = None
    slug = ascii_slug(d["nome"])[:20]
    d["email"] = f"{slug}.{id_parte}@exemplo.invalid" if rng.random() < 0.7 else None
    d["telefone"] = telefone(rng) if rng.random() < 0.8 else None
    if rng.random() < 0.9:
        d.update(endereco(fake, rng))
    else:
        d.update({c: None for c in COLUNAS_ENDERECO})
    return d


def alteracao(fake, rng, d, id_parte):
    """Escolhe um campo e devolve {coluna: novo_valor} (e aplica em d)."""
    opcoes = ["nome", "email", "telefone", "endereco"] + (["nome_social"] if d["tp_pessoa"] == "F" else [])
    campo = rng.choice(opcoes)
    if campo == "nome":
        novo = {"nome": (f"{d['nome'].split()[0]} {fake.last_name()}" if d["tp_pessoa"] == "F" else fake.company())}
    elif campo == "email":
        novo = {"email": f"{ascii_slug(d['nome'])[:20]}.{id_parte}.{rng.randint(1, 999)}@exemplo.invalid"}
    elif campo == "telefone":
        novo = {"telefone": telefone(rng)}
    elif campo == "nome_social":
        novo = {"nome_social": d["nome"].split()[0]}
    else:
        novo = endereco(fake, rng)
    d.update(novo)
    return novo


def cnj(seq, rng):
    ano = rng.randint(2019, 2026)
    return f"{seq:07d}-{(seq * 7) % 100:02d}.{ano}.4.99.9999"


INS_PARTE = ("INSERT INTO parte (id_parte, id_processo, tp_pessoa, participacao, nome, nome_social, "
             "tp_documento, nr_documento, dt_nascimento, email, telefone, logradouro, numero, complemento, "
             "bairro, cidade, uf, cep, valid_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
             "%s, %s, %s, %s, %s, daterange(%s, %s)) RETURNING lower(sys_period)")


def inserir_parte(cur, id_parte, d, vini):
    cur.execute(INS_PARTE, (id_parte, d["id_processo"], d["tp_pessoa"], d["participacao"], d["nome"],
                            d["nome_social"], d["tp_documento"], d["nr_documento"], d["dt_nascimento"],
                            d["email"], d["telefone"], d["logradouro"], d["numero"], d["complemento"],
                            d["bairro"], d["cidade"], d["uf"], d["cep"], vini, None))
    return cur.fetchone()[0]


def transicao(d, vini, vfim, ts, op):
    return {"hp": hash_pessoais(d), "nome": d["nome"], "valid_ini": vini.isoformat(),
            "valid_fim": vfim.isoformat() if vfim else None, "sys_lower": ts.isoformat(), "operacao": op}


# ------------------------------------------------------------ ciclo de vida
def ciclo_parte(cur, fake, rng, id_parte, id_processo, participacao, dt_autuacao):
    d = nova_parte(fake, rng, id_parte, id_processo, participacao)
    hn = hash_nao_pessoais(d)
    vs = min(dt_autuacao + timedelta(days=rng.randint(0, 30)), DATA_REF - timedelta(days=90))
    trs = [transicao(d, vs, None, inserir_parte(cur, id_parte, d, vs), "I")]

    n_upd = rng.randint(1, MAX_ATUALIZACOES) if rng.random() < P_ATUALIZACAO else 0
    for _ in range(n_upd):
        novo = alteracao(fake, rng, d, id_parte)
        sets, vals, op = [f"{c} = %s" for c in novo], list(novo.values()), "U"
        if rng.random() < P_RETRO:
            vs = vs - timedelta(days=rng.randint(1, 60))
            sets.append("valid_at = daterange(%s, NULL)")
            vals.append(vs)
            op = "U-retroativa"
        cur.execute(f"UPDATE parte SET {', '.join(sets)} WHERE id_parte = %s AND upper_inf(valid_at) "
                    "RETURNING lower(sys_period)", vals + [id_parte])
        trs.append(transicao(d, vs, None, cur.fetchone()[0], op))

    n_segmentos = 1
    if rng.random() < P_MUDANCA_REAL:
        m = vs + timedelta(days=rng.randint(1, (DATA_REF - vs).days))
        cur.execute("UPDATE parte SET valid_at = daterange(%s, %s) WHERE id_parte = %s AND upper_inf(valid_at) "
                    "RETURNING lower(sys_period)", (vs, m, id_parte))
        trs.append(transicao(d, vs, m, cur.fetchone()[0], "U-encerramento"))
        alteracao_endereco = endereco(fake, rng)
        d.update(alteracao_endereco)
        if rng.random() < 0.5:
            d["telefone"] = telefone(rng)
        trs.append(transicao(d, m, None, inserir_parte(cur, id_parte, d, m), "I-mudanca"))
        vs, n_segmentos = m, 2
        n_upd2 = rng.randint(1, 2) if rng.random() < P_ATUALIZACAO else 0
        for _ in range(n_upd2):
            novo = alteracao(fake, rng, d, id_parte)
            cur.execute(f"UPDATE parte SET {', '.join(f'{c} = %s' for c in novo)} "
                        "WHERE id_parte = %s AND upper_inf(valid_at) RETURNING lower(sys_period)",
                        list(novo.values()) + [id_parte])
            trs.append(transicao(d, m, None, cur.fetchone()[0], "U"))

    anon = False
    if rng.random() < P_ANONIMIZACAO:
        cur.execute("SELECT anonimizar_parte(%s, %s)", (id_parte, FUNDAMENTO))
        anon = True
        cur.execute("SELECT lower(valid_at), upper(valid_at), lower(sys_period) FROM parte "
                    "WHERE id_parte = %s ORDER BY lower(valid_at)", (id_parte,))
        for vini, vfim, ts in cur.fetchall():
            trs.append({"hp": None, "nome": MARCADOR, "valid_ini": vini.isoformat(),
                        "valid_fim": vfim.isoformat() if vfim else None, "sys_lower": ts.isoformat(),
                        "operacao": "anonimizacao"})
    return {"id_parte": id_parte, "hn": hn, "anonimizada": anon, "transicoes": trs}


def movimentacoes(fake, rng, id_processo, dt_autuacao, situacao):
    n = rng.randint(3, 12)
    t = datetime.combine(dt_autuacao, dtime(9, 0), tzinfo=timezone.utc)
    passo_max = max(1, (DATA_REF - dt_autuacao).days // n)
    linhas = []
    for i in range(n):
        if i == 0:
            tipo = "DISTRIBUICAO"
        elif i == n - 1 and situacao == "B":
            tipo = "BAIXA"
        else:
            tipo = rng.choice(TIPOS_MOV)
        linhas.append((id_processo, t, tipo, f"{tipo.capitalize()} registrada (sintetico)",
                       f"{fake.first_name()} {fake.last_name()}"))
        t = t + timedelta(days=rng.randint(1, passo_max), hours=rng.randint(0, 8), minutes=rng.randint(0, 59))
    return linhas


def hash_movimentacoes(linhas):
    return canon([[tp, dt.astimezone(timezone.utc).isoformat(), desc, ag] for (_, dt, tp, desc, ag) in linhas])


def main():
    args = parse_args()
    n_total = ESCALAS[args.escala] if args.escala else args.n
    if not os.environ.get("PGPASSWORD"):
        sys.exit("Defina PGPASSWORD no ambiente (a senha nao fica no codigo).")

    rng = random.Random(args.seed)
    fake = Faker("pt_BR")
    Faker.seed(args.seed)

    conn = psycopg2.connect(host=args.host, port=args.port, dbname=args.dbname,
                            user=args.user, application_name="gerador_dominio_v3")
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute("SELECT (SELECT count(*) FROM processo) + (SELECT count(*) FROM parte)")
    if cur.fetchone()[0] > 0:
        sys.exit(f"O banco '{args.dbname}' ja tem dados. Crie um banco novo (nao ha --truncar).")
    cur.execute("SELECT set_config('tcc.finalidade', %s, false), set_config('tcc.base_legal', %s, false)",
                (FIN_CARGA, BASE_CARGA))
    conn.commit()

    print(f"Gerando {n_total} partes (seed={args.seed}, data_ref={DATA_REF}, banco={args.dbname})...")
    inicio = time.time()
    n_partes = n_proc = n_mov = 0
    id_parte = args.id_parte_start
    id_processo = args.id_processo_start
    with open(args.ground_truth, "w", encoding="utf-8") as gt:
        while n_partes < n_total:
            dt_aut = DATA_REF - timedelta(days=rng.randint(120, 5 * 365))
            situacao = rng.choices(["A", "S", "B"], [0.80, 0.05, 0.15])[0]
            cur.execute("INSERT INTO processo VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (id_processo, cnj(id_processo, rng), rng.choice(CLASSES),
                         f"Vara Federal Sintetica {rng.randint(1, 20)}", dt_aut, situacao, rng.random() < 0.05))
            movs = movimentacoes(fake, rng, id_processo, dt_aut, situacao)
            psycopg2.extras.execute_values(
                cur, "INSERT INTO movimentacao_processual (id_processo, dt_movimentacao, tp_movimentacao, "
                     "descricao, ds_agente) VALUES %s", movs)
            n_mov += len(movs)

            qtd = min(rng.choices([2, 3, 4], [0.6, 0.3, 0.1])[0], n_total - n_partes)
            participacoes = (["A", "P"] + [rng.choice(["T", "T", "F"]) for _ in range(qtd)])[:qtd]
            partes = []
            for p in participacoes:
                partes.append(ciclo_parte(cur, fake, rng, id_parte, id_processo, p, dt_aut))
                id_parte += 1
                n_partes += 1
            gt.write(json.dumps({"id_processo": id_processo, "n_mov": len(movs),
                                 "mov_hash": hash_movimentacoes(movs), "partes": partes},
                                ensure_ascii=False) + "\n")
            n_proc += 1
            id_processo += 1
            if n_partes % BATCH < qtd:
                conn.commit()
                taxa = n_partes / (time.time() - inicio)
                print(f"  {n_partes:>9}/{n_total} partes ({taxa:,.0f}/s)", flush=True)
        conn.commit()

    cur.execute("INSERT INTO parte_controle (id_parte, id_processo, tp_pessoa, participacao, nome, nome_social, "
                "tp_documento, nr_documento, dt_nascimento, email, telefone, logradouro, numero, complemento, "
                "bairro, cidade, uf, cep) SELECT id_parte, id_processo, tp_pessoa, participacao, nome, "
                "nome_social, tp_documento, nr_documento, dt_nascimento, email, telefone, logradouro, numero, "
                "complemento, bairro, cidade, uf, cep FROM parte WHERE upper_inf(valid_at)")
    conn.commit()

    cur.execute("SELECT (SELECT count(*) FROM processo), (SELECT count(*) FROM parte), "
                "(SELECT count(*) FROM parte_historico), (SELECT count(*) FROM parte_controle), "
                "(SELECT count(*) FROM movimentacao_processual), (SELECT count(*) FROM anonimizacao_log)")
    c = cur.fetchone()
    dur = time.time() - inicio
    print(f"\nConcluido em {dur:,.1f}s ({n_total / dur:,.0f} partes/s).")
    print(f"  processo:                    {c[0]}")
    print(f"  parte (versoes correntes):   {c[1]}")
    print(f"  parte_historico:             {c[2]}")
    print(f"  parte_controle (Modelo A):   {c[3]}")
    print(f"  movimentacao_processual:     {c[4]}")
    print(f"  anonimizacao_log:            {c[5]}")
    print(f"Ground truth: {args.ground_truth}")
    conn.close()


if __name__ == "__main__":
    main()
