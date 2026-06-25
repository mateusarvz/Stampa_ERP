# Docker Setup - Stampa SaaS

## Estrutura

```
Dockerfile              # Build image
docker-compose.yml      # Default (dev-like, com GUI)
docker-compose.dev.yml  # Dev: hot-reload código
docker-compose.prod.yml # Prod: otimizado
entrypoint.sh          # Launcher script
.dockerignore          # Exclusões build
```

## Instalação Rápida

### 1. Pré-requisitos

- **Docker Desktop** (Windows/Mac)
- **Docker + Docker Compose** (Linux)
- VSCode: Extensions **Dev Containers** + **Docker**

### 2. Build image

```bash
docker build -t stampa-saas .
```

Ou automático:
```bash
docker-compose build
```

### 3. Rodar container

#### Modo padrão (GUI com dados persistentes)
```bash
docker-compose up -d
```

#### Modo dev (código hot-reload)
```bash
docker-compose -f docker-compose.dev.yml up
```

#### Modo prod (otimizado)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Modos de execução

Passar modo via entrypoint:

```bash
# GUI (padrão)
docker-compose run stampa-saas gui

# CLI setup
docker-compose run stampa-saas cli

# Sincronizar DB
docker-compose run stampa-saas db

# Cleanup
docker-compose run stampa-saas cleanup

# Shell bash interativo
docker-compose run stampa-saas shell

# Testes
docker-compose run stampa-saas test
```

## Opções avançadas

### X11 Forwarding (GUI em Linux/Mac)

Descomente linhas em `docker-compose.yml`:

```yaml
volumes:
  - /tmp/.X11-unix:/tmp/.X11-unix:rw
  - /home/$USER/.Xauthority:/home/appuser/.Xauthority:rw
```

Depois:
```bash
docker-compose up
```

### Dados persistentes

- Volume automático: `stampa-data`
- Local máquina (inspect):
  ```bash
  docker volume inspect stampa-data
  ```

- Backup:
  ```bash
  docker run --rm -v stampa-data:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/data-backup.tar.gz -C /data .
  ```

### Dev Containers (VSCode)

1. Instalar extension **Dev Containers**
2. `Ctrl+Shift+P` → **Dev Containers: Reopen in Container**
3. Selecionar Dockerfile
4. VSCode abre terminal dentro container

## Limpeza

```bash
# Stop + remove
docker-compose down

# Remove dados também
docker-compose down -v

# Remove image
docker image rm stampa-saas:latest

# Sistema completo
docker system prune -a
```

## Troubleshooting

| Erro | Solução |
|------|---------|
| `permission denied` | User ID mismatch. Rodar: `docker build --build-arg UID=$(id -u) .` |
| GUI não abre | X11 no host? Testar: `echo $DISPLAY` |
| Dados não persistem | Volume não mounted? Check: `docker volume ls` |
| Slow em WSL2 | Performance issue. Use `-f docker-compose.dev.yml` com `./app:/app` |

## Estrutura dados em container

```
/data/
  Stampa_SaaS/
    CLIENTES.csv
    PEDIDOS.csv
    stampa_data.db
    PEDIDO_ARTES/
      pedido_1/
      pedido_2/
      ...
```

## Environment vars

Passar .env para container:

```bash
# Via arquivo
docker-compose --env-file .env up

# Via CLI
docker-compose run -e GEMINI_API_KEY=xxx stampa-saas gui
```

## Push registry (Docker Hub)

```bash
docker tag stampa-saas:latest seu-docker-user/stampa-saas:latest
docker push seu-docker-user/stampa-saas:latest
```

Depois, qualquer máquina:
```bash
docker run -v stampa-data:/data seu-docker-user/stampa-saas:latest
```
