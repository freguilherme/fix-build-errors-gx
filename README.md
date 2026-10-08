# Fix Build Errors – GeneXus / Java

Ferramenta para destravar builds do GeneXus (Java) quando a compilação falha. Ela lê o log do build, encontra os erros do `javac` no formato:

```
C:\KBs\MinhaKB\javaoracle\web\src\main\java\wbpvenprojeto_v2_impl.java:760: error: ...
```

e **comenta** (ou **remove**) a linha indicada (`760`) no arquivo `.java` correspondente.

> ⚠️ **Atenção:** os `.java` são gerados pelo GeneXus. Qualquer novo build/regeneração sobrescreve essas edições. Use como correção **temporária** para liberar uma build local. O erro real normalmente está no objeto GeneXus de origem (ex.: assinatura de `execute` diferente da esperada).

---

## Recursos

- Interface gráfica simples (Tkinter, sem dependências externas)
- Cola o log do build direto na tela ou carrega de um arquivo `.log`/`.txt`
- Funciona com várias KBs: basta trocar a pasta dos `.java`
- Lembra a última pasta usada e as 8 mais recentes (lista suspensa)
- Lembra as opções escolhidas (comentar/remover, simular)
- Modo **Simular** (dry-run): mostra o que seria alterado sem tocar nos arquivos
- Trata vários erros e vários arquivos no mesmo log
- Versão em linha de comando (CLI) também disponível

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `fix_build_errors_gui.py` | Programa principal (interface gráfica) |
| `fix_build_errors.py` | Versão em linha de comando |
| `Abrir Fix Build Errors.bat` | Abre a interface com duplo clique, sem terminal |
| `build_exe.bat` | Gera um `.exe` standalone (PyInstaller) |

---

## Requisitos

- Windows
- [Python 3.10+](https://www.python.org/downloads/) com a opção **"Add Python to PATH"** marcada na instalação

Não é necessário instalar nenhuma biblioteca extra para rodar o programa.
(Ou gere o `.exe` – veja [Gerando o executável](#gerando-o-executável-sem-precisar-de-python).)

---

## Como usar (interface gráfica)

1. Dê duplo clique em **`Abrir Fix Build Errors.bat`**
   (ou rode `python fix_build_errors_gui.py`).
2. Em **Pasta da KB atual**, informe a pasta onde estão os `.java` gerados, por exemplo:
   `C:\KBs\MinhaKB\javaoracle\web\src\main\java`
3. Cole o log do build na caixa de texto (ou use **Carregar arquivo de log...**).
4. Escolha a ação:
   - **Comentar linha** (`// ...`) – mais seguro, fácil de reverter
   - **Remover linha**
5. Deixe **Simular** marcado na primeira vez para conferir o resultado. Depois desmarque e clique em **Executar** para aplicar de verdade.

Os arquivos são localizados **pelo nome** dentro da pasta informada, então o caminho que aparece no log (`C:\KBs\...`) não precisa existir na máquina atual.

### Onde ficam as configurações

As preferências (última pasta, pastas recentes, modo, simular) são salvas em:

```
%USERPROFILE%\.fix_build_errors_gui.json
```

---

## Como usar (linha de comando)

```bash
# Comenta as linhas com erro
python fix_build_errors.py --log build_log.txt

# Remove as linhas com erro
python fix_build_errors.py --log build_log.txt --delete

# Apenas simula
python fix_build_errors.py --log build_log.txt --dry-run

# Log veio de outra máquina: aponte a pasta local dos .java
python fix_build_errors.py --log build_log.txt --base-dir "C:\KBs\MinhaKB\javaoracle\web\src\main\java"

# Lendo do stdin
type build_log.txt | python fix_build_errors.py --log -
```

| Opção | Descrição |
|---|---|
| `--log` | Arquivo de log (ou `-` para stdin) – obrigatório |
| `--delete` | Remove a linha em vez de comentar |
| `--dry-run` | Só mostra o que seria feito |
| `--base-dir` | Pasta local onde estão os `.java` |

---

## Gerando o executável (sem precisar de Python)

Para distribuir para máquinas **sem Python instalado**:

1. Em uma máquina que tenha Python, deixe `build_exe.bat` e `fix_build_errors_gui.py` na mesma pasta.
2. Dê duplo clique em `build_exe.bat`.
3. O executável será gerado em `dist\FixBuildErrors.exe`.
4. Copie apenas esse `.exe` para qualquer outro computador Windows.

Observações:
- O `.exe` fica grande (15–40 MB) porque embute o Python.
- Antivírus corporativos podem alertar em arquivos gerados com PyInstaller; se acontecer, libere uma exceção.
- Ao alterar o código, rode `build_exe.bat` novamente para atualizar o `.exe`.

---

## Como funciona

1. Uma expressão regular procura no log linhas no formato `<caminho>.java:<linha>: error:`.
2. Agrupa as linhas com erro por arquivo.
3. Para cada arquivo, localiza-o na pasta informada e processa as linhas **da maior para a menor**, evitando que a remoção de uma linha desloque a numeração das demais.
4. Comenta (preservando a indentação) ou remove a linha e salva o arquivo.

---

## Limitações

- Reconhece apenas erros do `javac` no formato `arquivo.java:NN: error:`.
- Comentar uma linha pode gerar novos erros de compilação (ex.: variável não declarada, `}` desbalanceado) – nesse caso rode o build novamente e repita o processo.
- Edições são perdidas quando o GeneXus regenera os fontes.
- Recomenda-se manter backup/controle de versão da pasta gerada antes de aplicar sem `Simular`.
