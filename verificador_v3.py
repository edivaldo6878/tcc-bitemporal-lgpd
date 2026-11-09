#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime

try:
    import psycopg2
except ImportError:
    sys.exit("Instale psycopg2-binary antes de continuar.")


MARCADOR = "[DADO PESSOAL REMOVIDO]"

PESSOAIS = [
    "nome",
    "nome_social",
    "nr_documento",
    "dt_nascimento",
    "email",
    "telefone",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
    "cep",
]

NAO_PESSOAIS = [
    "id_processo",
    "tp_pessoa",
    "participacao",
    "tp_documento",
]


def parse_args():
    p = argparse.ArgumentParser(description="Verificador v3 do dominio final")
    p.add_argument("--ground-truth", default="ground_truth_v3.jsonl")
    p.add_argument("--host", default=os.environ.get("PGHOST", "localhost"))
    p.add_argument("--port", default=os.environ.get("PGPORT", "5433"))
    p.add_argument("--dbname", default="tcc_dominio")
    p.add_argument("--user", default=os.environ.get("PGUSER", "dba"))
    p.add_argument("--exemplos", type=int, default=5)
    return p.parse_args()


def canon(valores):
    ajustados = []
    for v in valores:
        if isinstance(v, (date, datetime)):
            ajustados.append(v.isoformat())
        else:
            ajustados.append(v)

    return hashlib.md5(
        json.dumps(ajustados, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def carregar_gt(caminho):
    processos = {}
    partes = {}

    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue

            p = json.loads(linha)
            processos[p["id_processo"]] = p

            for parte in p["partes"]:
                partes[parte["id_parte"]] = parte

    return processos, partes



def carregar_versoes(cur):
    versoes = defaultdict(list)

    cur.execute("""
        SELECT
            id_parte,
            id_processo,
            tp_pessoa,
            participacao,
            nome,
            nome_social,
            tp_documento,
            nr_documento,
            dt_nascimento,
            email,
            telefone,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            uf,
            cep,
            lower(valid_at),
            upper(valid_at),
            lower(sys_period),
            upper(sys_period),
            agente,
            origem,
            txid,
            finalidade,
            'historico' AS origem_tabela
        FROM parte_historico

        UNION ALL

        SELECT
            id_parte,
            id_processo,
            tp_pessoa,
            participacao,
            nome,
            nome_social,
            tp_documento,
            nr_documento,
            dt_nascimento,
            email,
            telefone,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            uf,
            cep,
            lower(valid_at),
            upper(valid_at),
            lower(sys_period),
            upper(sys_period),
            agente,
            origem,
            txid,
            finalidade,
            'corrente'
        FROM parte
    """)

    for r in cur:
        (
            id_parte,
            id_processo,
            tp_pessoa,
            participacao,
            nome,
            nome_social,
            tp_documento,
            nr_documento,
            dt_nascimento,
            email,
            telefone,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            uf,
            cep,
            valid_ini,
            valid_fim,
            sys_ini,
            sys_fim,
            agente,
            origem,
            txid,
            finalidade,
            origem_tabela,
        ) = r

        pessoais = [
            nome,
            nome_social,
            nr_documento,
            dt_nascimento,
            email,
            telefone,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            uf,
            cep,
        ]

        nao_pessoais = [
            id_processo,
            tp_pessoa,
            participacao,
            tp_documento,
        ]

        versoes[id_parte].append({
            "nome": nome,
            "hp": canon(pessoais),
            "hn": canon(nao_pessoais),
            "valid_ini": valid_ini,
            "valid_fim": valid_fim,
            "sys_ini": sys_ini,
            "sys_fim": sys_fim,
            "agente": agente,
            "origem": origem,
            "txid": txid,
            "finalidade": finalidade,
            "tabela": origem_tabela,
        })

    for id_parte in versoes:
        versoes[id_parte].sort(key=lambda x: x["sys_ini"])

    return versoes


def carregar_modelo_a(cur):
    r = {}

    cur.execute("""
        SELECT
            id_parte,
            id_processo,
            tp_pessoa,
            participacao,
            nome,
            nome_social,
            tp_documento,
            nr_documento,
            dt_nascimento,
            email,
            telefone,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            uf,
            cep
        FROM parte_controle
    """)

    for linha in cur:
        r[linha[0]] = linha[1:]

    return r



def main():
    args = parse_args()

    if not os.environ.get("PGPASSWORD"):
        sys.exit("Defina PGPASSWORD antes de executar.")

    try:
        gt_processos, gt_partes = carregar_gt(args.ground_truth)

        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            dbname=args.dbname,
            user=args.user,
            application_name="verificador_v3",
        )

        conn.set_session(readonly=True)
        cur = conn.cursor()

        versoes = carregar_versoes(cur)
        modelo_a = carregar_modelo_a(cur)

        cur.execute("SELECT count(*) FROM processo")
        n_processos_banco = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM movimentacao_processual")
        n_mov_banco = cur.fetchone()[0]

        cur.execute("""
            SELECT id_parte, count(*), bool_and(btrim(fundamento) <> '')
            FROM anonimizacao_log
            GROUP BY id_parte
        """)
        logs = {
            r[0]: (r[1], r[2])
            for r in cur
        }

        cur.execute("""
            WITH v AS (
                SELECT
                    id_parte,
                    valid_at,
                    sys_period,
                    row_number() OVER () AS rn
                FROM (
                    SELECT id_parte, valid_at, sys_period
                    FROM parte_historico

                    UNION ALL

                    SELECT id_parte, valid_at, sys_period
                    FROM parte
                ) x
            )
            SELECT count(*)
            FROM v a
            JOIN v b
              ON a.id_parte = b.id_parte
             AND a.rn < b.rn
            WHERE a.valid_at && b.valid_at
              AND a.sys_period && b.sys_period
        """)

        sobreposicoes = cur.fetchone()[0]

        conn.close()

    except Exception as e:
        print("ERRO DE EXECUCAO:", e)
        sys.exit(2)

    falhas = defaultdict(list)


    # TC-V3-01: numero de processos
    if n_processos_banco != len(gt_processos):
        falhas["TC-V3-01"].append(
            f"processos: gabarito={len(gt_processos)}, banco={n_processos_banco}"
        )

    # numero esperado de movimentacoes
    mov_esperadas = sum(p["n_mov"] for p in gt_processos.values())

    if n_mov_banco != mov_esperadas:
        falhas["TC-V3-02"].append(
            f"movimentacoes: gabarito={mov_esperadas}, banco={n_mov_banco}"
        )

    # nenhuma sobreposicao bitemporal
    if sobreposicoes != 0:
        falhas["TC-V3-03"].append(
            f"{sobreposicoes} pares de versoes com sobreposicao bitemporal"
        )

    total_versoes = 0
    total_encerradas = 0
    anonimizadas = 0

    for id_parte, esp in gt_partes.items():
        obt = versoes.get(id_parte, [])
        esperado = esp["transicoes"]

        total_versoes += len(obt)

        if len(obt) != len(esperado):
            falhas["TC-V3-04"].append(
                f"id_parte={id_parte}: esperado {len(esperado)} versoes, obtido {len(obt)}"
            )
            continue

        anon = esp["anonimizada"]

        if anon:
            anonimizadas += 1

        # As transicoes do ground truth registram o sys_lower exato.
        # Nao comparar pela posicao: diferentes segmentos validos da mesma
        # entidade podem ser versionados em ordem temporal diferente.
        obt_por_sys = {}

        for o in obt:
            if o["sys_ini"] in obt_por_sys:
                falhas["TC-V3-08"].append(
                    f"id_parte={id_parte}: sys_lower duplicado {o['sys_ini']}"
                )
            obt_por_sys[o["sys_ini"]] = o

        for i, e in enumerate(esperado):
            sys_esperado = datetime.fromisoformat(e["sys_lower"])
            o = obt_por_sys.get(sys_esperado)

            if o is None:
                falhas["TC-V3-08"].append(
                    f"id_parte={id_parte} versao={i}: "
                    f"sys_lower esperado nao encontrado: {sys_esperado}"
                )
                continue

            # dados pessoais
            if anon:
                if o["nome"] != MARCADOR:
                    falhas["TC-V3-05"].append(
                        f"id_parte={id_parte} versao={i}: "
                        "dado pessoal nao anonimizado"
                    )
            else:
                if o["hp"] != e["hp"]:
                    falhas["TC-V3-05"].append(
                        f"id_parte={id_parte} versao={i}: "
                        "hash de dados pessoais divergente"
                    )

            # dados nao pessoais devem permanecer
            if o["hn"] != esp["hn"]:
                falhas["TC-V3-06"].append(
                    f"id_parte={id_parte} versao={i}: "
                    "dados nao pessoais divergentes"
                )

            vi = date.fromisoformat(e["valid_ini"])
            vf = date.fromisoformat(e["valid_fim"]) if e["valid_fim"] else None

            if (o["valid_ini"], o["valid_fim"]) != (vi, vf):
                falhas["TC-V3-07"].append(
                    f"id_parte={id_parte} versao={i}: "
                    "valid time divergente"
                )

            # O pareamento ja foi feito pelo proprio sys_lower.
            if o["sys_ini"] != sys_esperado:
                falhas["TC-V3-08"].append(
                    f"id_parte={id_parte} versao={i}: "
                    "transaction time divergente"
                )

            if not (
                o["agente"]
                and o["origem"]
                and o["txid"] is not None
                and o["finalidade"]
            ):
                falhas["TC-V3-09"].append(
                    f"id_parte={id_parte} versao={i}: "
                    "metadado de governanca ausente"
                )

        # contiguidade de transaction time
        inicios = {x["sys_ini"] for x in obt}

        for o in obt:
            if o["sys_fim"] is not None:
                total_encerradas += 1
                if o["sys_fim"] not in inicios:
                    falhas["TC-V3-10"].append(
                        f"id_parte={id_parte}: versao encerrada sem sucessora contigua"
                    )

        # anonimização + log
        if anon:
            qtd, fundamento_ok = logs.get(id_parte, (0, False))

            if qtd != 1 or not fundamento_ok:
                falhas["TC-V3-11"].append(
                    f"id_parte={id_parte}: log de anonimizacao inconsistente"
                )

        # Modelo A deve equivaler ao periodo valido aberto
        abertas = [
            o for o in obt
            if o["tabela"] == "corrente"
            and o["valid_fim"] is None
        ]

        if len(abertas) != 1:
            falhas["TC-V3-12"].append(
                f"id_parte={id_parte}: {len(abertas)} periodos validos abertos"
            )
        elif id_parte not in modelo_a:
            falhas["TC-V3-12"].append(
                f"id_parte={id_parte}: ausente no Modelo A"
            )
        elif modelo_a[id_parte][3] != abertas[0]["nome"]:
            # posição 3 = nome, porque linha armazenada começa em id_processo
            falhas["TC-V3-12"].append(
                f"id_parte={id_parte}: nome diferente entre Modelo A e Modelo B"
            )


    testes = {
        "TC-V3-01": "Quantidade de processos igual ao gabarito",
        "TC-V3-02": "Quantidade de movimentacoes igual ao gabarito",
        "TC-V3-03": "Ausencia de sobreposicao bitemporal",
        "TC-V3-04": "Numero de versoes por parte",
        "TC-V3-05": "Conteudo pessoal de cada versao",
        "TC-V3-06": "Dados nao pessoais preservados",
        "TC-V3-07": "Tempo valido correto",
        "TC-V3-08": "Inicio do tempo de transacao correto",
        "TC-V3-09": "Metadados de governanca presentes",
        "TC-V3-10": "Contiguidade do tempo de transacao",
        "TC-V3-11": "Anonimizacao registrada e fundamentada",
        "TC-V3-12": "Modelo A consistente com o estado corrente",
    }

    print("=" * 78)
    print("VERIFICADOR V3 - DOMINIO FINAL")
    print("Banco:", args.dbname)
    print("Processos:", n_processos_banco)
    print("Partes no gabarito:", len(gt_partes))
    print("Versoes analisadas:", total_versoes)
    print("Versoes encerradas:", total_encerradas)
    print("Movimentacoes:", n_mov_banco)
    print("Anonimizadas:", anonimizadas)
    print("=" * 78)

    reprovou = False

    for codigo, descricao in testes.items():
        n = len(falhas[codigo])

        if n:
            reprovou = True
            status = "REPROVADO"
        else:
            status = "APROVADO "

        print(f"{codigo:8} {status}  {descricao}  ({n} falhas)")

        for exemplo in falhas[codigo][:args.exemplos]:
            print("           -", exemplo)

        if n > args.exemplos:
            print(f"           ... e mais {n - args.exemplos}")

    print("=" * 78)
    print("RESULTADO GERAL:", "REPROVADO" if reprovou else "APROVADO")

    sys.exit(1 if reprovou else 0)


if __name__ == "__main__":
    main()
