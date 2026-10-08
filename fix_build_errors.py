#!/usr/bin/env python3
"""
fix_build_errors.py

Le o log de build do GeneXus (saida do gradlew/javac) e, para cada erro do tipo:

    C:\\KBs\\FoccoLojasJava18u6\\javaoracle\\web\\src\\main\\java\\wbpvenprojeto_v2_impl.java:760: error: ...

localiza o arquivo .java e a linha indicada e:
  - por padrao, COMENTA a linha (prefixo "// ")
  - com --delete, REMOVE a linha inteira

Uso:
    python fix_build_errors.py --log build_log.txt
    python fix_build_errors.py --log build_log.txt --delete
    python fix_build_errors.py --log build_log.txt --dry-run
    cat build_log.txt | python fix_build_errors.py --log -

Se o caminho do arquivo no log nao existir no disco atual (ex: log veio de outra
maquina), use --base-dir para trocar o prefixo do caminho por uma pasta local
onde os .java realmente estao.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# Captura "algumcaminho\arquivo.java:123: error:" (aceita \ ou / no caminho)
ERROR_RE = re.compile(r"^(.*?\.java):(\d+):\s*error:", re.MULTILINE)


def parse_errors(log_text: str):
    """Retorna dict {caminho_arquivo: set(linhas_com_erro)}"""
    erros = defaultdict(set)
    for path_str, line_str in ERROR_RE.findall(log_text):
        erros[path_str.strip()].add(int(line_str))
    return erros


def resolve_path(path_str: str, base_dir: str | None) -> Path:
    p = Path(path_str)
    if base_dir:
        # troca tudo ate a pasta "java\" (ou a raiz que voce apontar) pelo base_dir informado,
        # mantendo apenas o nome do arquivo
        p = Path(base_dir) / p.name
    return p


def apply_fix(path: Path, line_numbers: set[int], delete: bool, dry_run: bool):
    if not path.exists():
        print(f"[AVISO] arquivo nao encontrado, pulando: {path}")
        return

    linhas = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    alterou = False
    for n in sorted(line_numbers, reverse=True):  # reverse: seguro tanto pra delete quanto comment
        idx = n - 1
        if idx < 0 or idx >= len(linhas):
            print(f"[AVISO] linha {n} fora do intervalo em {path} (arquivo tem {len(linhas)} linhas)")
            continue

        original = linhas[idx]
        if delete:
            acao = "REMOVER"
            nova = None
        else:
            acao = "COMENTAR"
            indent = original[: len(original) - len(original.lstrip())]
            conteudo = original[len(indent):]
            nova = f"{indent}// {conteudo}" if not conteudo.lstrip().startswith("//") else original

        print(f"[{acao}] {path}:{n} -> {original.rstrip()!r}")

        if not dry_run:
            if delete:
                del linhas[idx]
            else:
                linhas[idx] = nova
            alterou = True

    if alterou:
        path.write_text("".join(linhas), encoding="utf-8")
        print(f"  => salvo: {path}")


def main():
    ap = argparse.ArgumentParser(description="Comenta/remove linhas com erro de build indicadas no log do GeneXus.")
    ap.add_argument("--log", required=True, help="Caminho do arquivo de log (ou '-' para ler do stdin)")
    ap.add_argument("--delete", action="store_true", help="Remove a linha em vez de comentar (padrao: comenta)")
    ap.add_argument("--dry-run", action="store_true", help="So mostra o que seria feito, sem alterar arquivos")
    ap.add_argument("--base-dir", default=None,
                     help="Pasta local onde estao os .java, caso o caminho do log nao exista neste computador")
    args = ap.parse_args()

    log_text = sys.stdin.read() if args.log == "-" else Path(args.log).read_text(encoding="utf-8", errors="replace")

    erros = parse_errors(log_text)
    if not erros:
        print("Nenhum erro do tipo 'arquivo.java:linha: error:' encontrado no log.")
        return

    print(f"Encontrados erros em {len(erros)} arquivo(s):")
    for path_str, linhas in erros.items():
        print(f"  - {path_str}: linhas {sorted(linhas)}")
    print()

    for path_str, linhas in erros.items():
        path = resolve_path(path_str, args.base_dir)
        apply_fix(path, linhas, delete=args.delete, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
