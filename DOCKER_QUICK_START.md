## 🐳 Docker Setup Concluído!

### Arquivos criados:

```
Dockerfile                     # Image build config (multi-stage)
docker-compose.yml             # Default compose (dev-like)
docker-compose.dev.yml         # Dev mode (hot-reload)
docker-compose.prod.yml        # Prod mode (otimizado)
.devcontainer/devcontainer.json # VSCode Dev Containers
entrypoint.sh                  # Launcher script (múltiplos modos)
.dockerignore                  # Build exclusions
docker-setup.sh                # Setup script
Makefile                       # Convenient commands
README_DOCKER.md               # Full documentation
```

---

## ⚡ Início rápido

### Opção 1: VSCode Dev Containers (Recomendado)

Modo mais fácil + integrado. VSCode abre terminal dentro container automaticamente.

1. Instalar extension: **Dev Containers**
2. `Ctrl+Shift+P` → **Dev Containers: Reopen in Container**
3. Selecionar `Dockerfile`
4. VSCode reinicia → terminal dentro container
5. Code com hot-reload automático

### Opção 2: Docker Compose (Rápido)

```bash
# Setup inicial
bash docker-setup.sh

# ou manual
docker build -t stampa-saas .

# Rodar (GUI com dados persistentes)
docker-compose up

# Outro terminal: acesso shell
docker-compose run stampa-saas shell
```

### Opção 3: Makefile (Mais simples)

```bash
make build        # Build image
make up           # Start (default)
make dev          # Start dev mode
make shell        # Open shell
make gui          # Run GUI
make down         # Stop
make help         # Todos targets
```

---

## 🎯 Modos de execução

Após `docker-compose up`:

```bash
# Via novo terminal
docker-compose run stampa-saas [MODE]

# Modos disponíveis:
gui       # GUI Tkinter (padrão)
cli       # Setup wizard (interactive)
db        # Sincronizar CSV → SQLite
cleanup   # Limpar temporários
shell     # Bash interativo
test      # Rodar testes
```

---

## 📊 Dados persistem?

**SIM!** Volume automático `stampa-data` guarda:
- CLIENTES.csv
- PEDIDOS.csv
- stampa_data.db
- PEDIDO_ARTES/ (imagens)

```bash
# Inspecionar volume
docker volume inspect stampa-data

# Backup
docker run --rm -v stampa-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/backup.tar.gz -C /data .
```

---

## 🔧 Troubleshooting

| Problema | Solução |
|----------|---------|
| `permission denied` | Use `sudo` ou configure Docker socket |
| GUI não abre | X11 needed. Descrição em README_DOCKER.md |
| Container slow | Dev mode + WSL2 = IO slow. Use volumes diretos |
| Port 5000 occupied | Change `ports: ["5001:5000"]` em compose |

---

## 🚀 Deploy (Qualquer máquina)

1. Instalar Docker
2. Clone repo
3. `docker-compose up`

**Pronto!** Mesmo setup, mesmas versões, qualquer OS.

---

## 📚 Documentação completa

Ver [README_DOCKER.md](README_DOCKER.md)
