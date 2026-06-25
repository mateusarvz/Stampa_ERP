# 📦 Tutorial: Como Instalar Stampa SaaS em Novo Computador

## ✅ Pré-Requisitos

- **Windows 10+** (ou Windows 11)
- **Python 3.9+** instalado (veja abaixo)
- **Internet** para primeira execução

---

## 🔧 Opção 1: Instalação Automática (RECOMENDADO)

### Passo 1: Baixar o Executável

1. Coloque o arquivo `StampaSaaS.exe` em uma pasta (ex: `C:\Programas\`)
2. Clique 2x no arquivo para executar

### Passo 2: Primeira Execução

- Programa vai criar pastas automaticamente em:
  ```
  C:\Users\[SeuUsuario]\AppData\Local\Stampa_SaaS\
  ```
- Vai criar:
  - `CLIENTES.csv` (lista de clientes)
  - `PEDIDOS.csv` (lista de pedidos)
  - `stampa_data.db` (banco de dados)

✅ **PRONTO!** Programa está funcional.

---

## 🔧 Opção 2: Instalação Manual (Mais Controle)

Se quiser compilar você mesmo ou não tem o `.exe`:

### Passo 1: Instalar Python

1. Acesse: https://python.org/downloads/
2. Baixe **Python 3.11** (Windows installer)
3. Execute instalador:
   - ✅ Marque: **"Add Python to PATH"**
   - ✅ Marque: **"Install pip"**
   - Clique "Install Now"
4. Abra Prompt de Comando (Win + R, `cmd`):
   ```bash
   python --version
   ```
   Deve mostrar: `Python 3.11.x`

### Passo 2: Copiar Pasta do Projeto

1. Copie a pasta `Stampa_SaaS` para sua máquina
2. Abra Prompt de Comando na pasta:
   ```bash
   cd C:\Users\[SeuUsuario]\Desktop\Stampa_SaaS
   ```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

⏳ Aguarde (pode levar 2-5 min)

### Passo 4: Primeira Execução

```bash
python main_standalone.py
```

Ou execute clicando 2x em `main_standalone.py`

### Passo 5: Gerar Executável (Opcional)

Se quiser criar um `.exe` para compartilhar:

```bash
build_exe.bat
```

Será criado em: `dist\StampaSaaS.exe`

---

## 📱 Uso do Programa

### Aba: **Clientes**
- Adicione novos clientes
- Veja histórico de clientes

### Aba: **Pedidos**
- Crie novos pedidos
- Acompanhe status (Aguardando → Finalizado)
- Filtre por datas

### Aba: **Dashboard**
- Veja gráficos de receita
- Status de pedidos
- Métricas gerais

### Aba: **Agente de IA** 🤖
- Faça perguntas sobre dados
- Gemini analisa automaticamente
- Recebe relatórios em Markdown

### Aba: **Relatórios**
- Gere relatórios customizados
- Análise por período
- Download em HTML

---

## 🐛 Solução de Problemas

### "Python não encontrado"
**Solução:**
1. Abra Prompt de Comando
2. Copie e cole:
   ```bash
   python --version
   ```
3. Se não funcionar, reinstale Python (veja "Passo 1")

### "Arquivo não encontrado"
**Solução:**
- Certifique que copiar TODAS as pastas da projeto:
  - `main.py`
  - `main_standalone.py`
  - `setup_app.py`
  - `LOGO.ico`
  - `requirements.txt`
  - Etc.

### "Erro ao executar o programa"
**Solução:**
1. Abra Prompt de Comando na pasta
2. Execute:
   ```bash
   python main_standalone.py
   ```
3. Copie mensagem de erro e envie

### "Gemini não responde"
**Solução:**
- Abra arquivo `.env` na pasta
- Adicione sua chave API Gemini:
  ```
  GEMINI_API_KEY=sua_chave_aqui
  ```
- Obtém chave grátis em: https://makersuite.google.com/app/apikey

---

## 💾 Dados Ficam Guardados?

**SIM!** Todos dados salvam automaticamente em:
```
C:\Users\[SeuUsuario]\AppData\Local\Stampa_SaaS\
```

Pastas criadas:
- `CLIENTES.csv` - Lista de clientes
- `PEDIDOS.csv` - Lista de pedidos
- `stampa_data.db` - Banco de dados
- `PEDIDO_ARTES/` - Arquivos de arte

---

## 📤 Transferir Dados Para Outro Computador

1. Vá para: `C:\Users\[SeuUsuario]\AppData\Local\Stampa_SaaS\`
2. Copie arquivos `.csv` e `.db`
3. No outro computador:
   - Execute `StampaSaaS.exe` 1x (cria estrutura)
   - Cole os arquivos na mesma pasta
   - Reinicie programa

---

## 🎯 Quick Start (Resumido)

```
1. Baixe StampaSaaS.exe
2. Execute (clique 2x)
3. Pronto! Use normalmente
4. Dados salvam automaticamente
```

---

## 📞 Suporte

Se tiver problema:
1. Verifique "Solução de Problemas" acima
2. Tente reinstalar Python
3. Verifique internet (Gemini precisa)

---

**Versão:** 1.0  
**Atualizado:** 2026-06-17
