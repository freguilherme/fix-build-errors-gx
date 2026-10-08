#!/usr/bin/env python3
"""
fix_build_errors_gui.py

Interface grafica (Tkinter, sem dependencias externas) para:
  1. Colar (ou carregar) o log de build do GeneXus/Java
  2. Apontar a pasta onde estao os .java da KB atual
     (ex: C:\\KBs\\FoccoLojasJava18u6\\javaoracle\\web\\src\\main\\java)
  3. Comentar ou remover a(s) linha(s) indicadas nos erros do tipo:
         algumArquivo.java:760: error: ...

Como o campo "Pasta da KB" fica separado, basta trocar esse caminho
para reaproveitar a ferramenta em qualquer outra KB/projeto GeneXus.

Executar:
    python fix_build_errors_gui.py
"""

import json
import re
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

ERROR_RE = re.compile(r"^(.*?\.java):(\d+):\s*error:", re.MULTILINE)

# Config salvo no perfil do usuario, funciona independente de onde o script roda
CONFIG_PATH = Path.home() / ".fix_build_errors_gui.json"
MAX_RECENTES = 8


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_kb_dir": "", "recent_kb_dirs": [], "modo": "comentar", "dry_run": True}


def save_config(cfg: dict):
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # falha ao salvar config nao deve travar o programa


def parse_errors(log_text: str):
    """Retorna dict {nome_arquivo: set(linhas_com_erro)}"""
    erros = defaultdict(set)
    for path_str, line_str in ERROR_RE.findall(log_text):
        nome_arquivo = Path(path_str.strip()).name
        erros[nome_arquivo].add(int(line_str))
    return erros


def apply_fix(path: Path, line_numbers: set, delete: bool, dry_run: bool, log_fn):
    if not path.exists():
        log_fn(f"[AVISO] arquivo nao encontrado, pulando: {path}")
        return False

    linhas = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    alterou = False

    for n in sorted(line_numbers, reverse=True):
        idx = n - 1
        if idx < 0 or idx >= len(linhas):
            log_fn(f"[AVISO] linha {n} fora do intervalo em {path.name} (arquivo tem {len(linhas)} linhas)")
            continue

        original = linhas[idx]
        if delete:
            acao = "REMOVER"
        else:
            acao = "COMENTAR"
            indent = original[: len(original) - len(original.lstrip())]
            conteudo = original[len(indent):]
            nova = f"{indent}// {conteudo}" if not conteudo.lstrip().startswith("//") else original

        log_fn(f"[{acao}] {path.name}:{n} -> {original.rstrip()!r}")

        if not dry_run:
            if delete:
                del linhas[idx]
            else:
                linhas[idx] = nova
            alterou = True

    if alterou:
        path.write_text("".join(linhas), encoding="utf-8")
        log_fn(f"  => salvo: {path}")

    return alterou


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fix Build Errors - GeneXus/Java")
        self.geometry("900x700")

        self.cfg = load_config()

        pad = {"padx": 8, "pady": 4}

        # --- Pasta da KB ---
        frame_kb = ttk.LabelFrame(self, text="Pasta da KB atual (onde estao os .java)")
        frame_kb.pack(fill="x", **pad)

        self.kb_dir_var = tk.StringVar(value=self.cfg.get("last_kb_dir", ""))
        self.kb_combo = ttk.Combobox(
            frame_kb, textvariable=self.kb_dir_var, values=self.cfg.get("recent_kb_dirs", [])
        )
        self.kb_combo.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)
        ttk.Button(frame_kb, text="Selecionar pasta...", command=self.selecionar_pasta).pack(
            side="left", padx=(0, 8), pady=6
        )

        # --- Log ---
        frame_log = ttk.LabelFrame(self, text="Log do build (cole aqui ou carregue de um arquivo)")
        frame_log.pack(fill="both", expand=True, **pad)

        toolbar = ttk.Frame(frame_log)
        toolbar.pack(fill="x", padx=4, pady=(4, 0))
        ttk.Button(toolbar, text="Carregar arquivo de log...", command=self.carregar_log).pack(side="left")
        ttk.Button(toolbar, text="Limpar", command=lambda: self.log_text.delete("1.0", "end")).pack(
            side="left", padx=6
        )

        self.log_text = scrolledtext.ScrolledText(frame_log, height=14, wrap="none")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # --- Opcoes ---
        frame_opts = ttk.LabelFrame(self, text="Opcoes")
        frame_opts.pack(fill="x", **pad)

        self.modo_var = tk.StringVar(value=self.cfg.get("modo", "comentar"))
        ttk.Radiobutton(frame_opts, text="Comentar linha (// ...)", variable=self.modo_var, value="comentar").pack(
            side="left", padx=8, pady=6
        )
        ttk.Radiobutton(frame_opts, text="Remover linha", variable=self.modo_var, value="remover").pack(
            side="left", padx=8, pady=6
        )

        self.dry_run_var = tk.BooleanVar(value=self.cfg.get("dry_run", True))
        ttk.Checkbutton(frame_opts, text="Simular (nao alterar arquivos)", variable=self.dry_run_var).pack(
            side="left", padx=20, pady=6
        )

        ttk.Button(frame_opts, text="Executar", command=self.executar).pack(side="right", padx=8, pady=6)

        # --- Resultado ---
        frame_out = ttk.LabelFrame(self, text="Resultado")
        frame_out.pack(fill="both", expand=True, **pad)
        self.out_text = scrolledtext.ScrolledText(frame_out, height=12, wrap="word", state="disabled")
        self.out_text.pack(fill="both", expand=True, padx=4, pady=4)

        # Salva a config ao fechar a janela (garante que o ultimo estado fica gravado)
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com os .java da KB")
        if pasta:
            self.kb_dir_var.set(pasta)
            self._registrar_kb_dir(pasta)

    def _registrar_kb_dir(self, pasta: str):
        """Atualiza a lista de pastas recentes (mais usada primeiro) e salva a config."""
        recentes = [p for p in self.cfg.get("recent_kb_dirs", []) if p != pasta]
        recentes.insert(0, pasta)
        recentes = recentes[:MAX_RECENTES]

        self.cfg["last_kb_dir"] = pasta
        self.cfg["recent_kb_dirs"] = recentes
        self.kb_combo["values"] = recentes
        save_config(self.cfg)

    def ao_fechar(self):
        self.cfg["modo"] = self.modo_var.get()
        self.cfg["dry_run"] = self.dry_run_var.get()
        kb_dir = self.kb_dir_var.get().strip()
        if kb_dir:
            self.cfg["last_kb_dir"] = kb_dir
        save_config(self.cfg)
        self.destroy()

    def carregar_log(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo de log", filetypes=[("Log/Texto", "*.log *.txt"), ("Todos", "*.*")]
        )
        if not caminho:
            return
        conteudo = Path(caminho).read_text(encoding="utf-8", errors="replace")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", conteudo)

    def escrever_saida(self, texto: str):
        self.out_text.configure(state="normal")
        self.out_text.insert("end", texto + "\n")
        self.out_text.see("end")
        self.out_text.configure(state="disabled")

    def executar(self):
        self.out_text.configure(state="normal")
        self.out_text.delete("1.0", "end")
        self.out_text.configure(state="disabled")

        kb_dir = self.kb_dir_var.get().strip()
        log_text = self.log_text.get("1.0", "end")

        if not kb_dir:
            messagebox.showwarning("Atencao", "Selecione a pasta da KB primeiro.")
            return
        if not Path(kb_dir).exists():
            messagebox.showwarning("Atencao", f"Pasta nao encontrada:\n{kb_dir}")
            return

        self._registrar_kb_dir(kb_dir)

        erros = parse_errors(log_text)
        if not erros:
            self.escrever_saida("Nenhum erro do tipo 'arquivo.java:linha: error:' encontrado no log.")
            return

        delete = self.modo_var.get() == "remover"
        dry_run = self.dry_run_var.get()

        self.escrever_saida(f"Encontrados erros em {len(erros)} arquivo(s):")
        for nome, linhas in erros.items():
            self.escrever_saida(f"  - {nome}: linhas {sorted(linhas)}")
        self.escrever_saida("")

        alterados = 0
        for nome, linhas in erros.items():
            caminho = Path(kb_dir) / nome
            if apply_fix(caminho, linhas, delete=delete, dry_run=dry_run, log_fn=self.escrever_saida):
                alterados += 1

        self.escrever_saida("")
        if dry_run:
            self.escrever_saida("Simulacao concluida. Nenhum arquivo foi alterado (desmarque 'Simular' para aplicar).")
        else:
            self.escrever_saida(f"Concluido. {alterados} arquivo(s) alterado(s).")


if __name__ == "__main__":
    App().mainloop()
