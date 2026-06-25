# 🎨 Stampa ERP - Sistema de Gestão de Estampas

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Ativo-brightgreen)

Aplicativo desktop completo para gerenciamento de clientes, pedidos e artes de estampa em camisas. Desenvolvido em Python com interface gráfica intuitiva e armazenamento de dados em CSV.

## 📋 Índice

- [Características](##características)
- [Pré-requisitos](##pré-requisitos)
- [Instalação](##instalação)
- [Como Usar](##como-usar)
- [Estrutura de Dados](##estrutura-de-dados)
- [Compilação](##compilação)
- [Contribuindo](##contribuindo)

## ✨ Características

- ✅ **Gestão de Clientes**: Cadastro, edição e exclusão de clientes
- ✅ **Gestão de Pedidos**: Criar, atualizar e acompanhar pedidos
- ✅ **Rastreamento de Artes**: Organização de arquivos de arte por pedido
- ✅ **Sincronização de Dados**: Suporte para backup e sincronização de dados
- ✅ **Interface Amigável**: Aplicação desktop intuitiva
- ✅ **Multiplataforma**: Funciona via Python (Windows, Mac, Linux)

## 🔧 Pré-requisitos

- **Python 3.8 ou superior**
- **pip** (gerenciador de pacotes Python)
- Windows, macOS ou Linux

## 📥 Instalação

### Opção 1: Executável (Windows) - Recomendado para Usuários Finais

1. Faça download do instalador mais recente na seção [Releases](../../releases)
2. Execute `StampaSaaSInstaller.exe`
3. Siga as instruções do instalador
4. O aplicativo será iniciado automaticamente após a instalação

### Opção 2: Rodando com Python (Desenvolvimento)

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/mateusarvz/Stampa_ERP.git
   cd Stampa_ERP
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o aplicativo:**
   ```bash
   python main.py
   ```

## 📖 Como Usar

### 1️⃣ Gerenciar Clientes

- **Adicionar Cliente**: Clique em "Novo Cliente" e preecha os dados (empresa, email, telefone)
- **Editar Cliente**: Selecione um cliente na lista e clique em "Editar"
- **Remover Cliente**: Selecione um cliente e clique em "Remover"

### 2️⃣ Gerenciar Pedidos

- **Criar Pedido**: Acesse a aba de pedidos, selecione um cliente e adicione detalhes do pedido
- **Atualizar Status**: Altere o status para "Em andamento" ou "Finalizado"
- **Adicionar Artes**: Cada pedido possui uma pasta para armazenar arquivos de arte

### 3️⃣ Gerenciar Artes

- As artes são automaticamente organizadas por pedido em `PEDIDO_ARTES/`
- Você pode adicionar, remover ou visualizar arquivos de arte

## 📊 Estrutura de Dados

Os dados são salvos em CSV no diretório de dados do Windows:
- **Localização**: `%LOCALAPPDATA%\Stampa_SaaS\`
- **Arquivos**: `CLIENTES.csv`, `PEDIDOS.csv`, `PEDIDO_ARTES/`

### Schema do Banco de Dados

**CLIENTES.csv**
| Campo | Tipo |
|-------|------|
| id_clientes | Integer |
| ClienteEmpresa | String |
| email | String |
| telefone | String |
| data_criação | Date |

**PEDIDOS.csv**
| Campo | Tipo |
|-------|------|
| id_pedidos | Integer |
| id_cliente | Integer |
| cliente_empresa | String |
| quantidade | Integer |
| valor | Float |
| data | Date |
| descrição | String |
| status | String (Em andamento/Finalizado) |

## 🔨 Compilação

### Gerar Executável (Windows)

```bash
# Instale o PyInstaller
pip install pyinstaller

# Execute o script de build
build_exe.bat

# O executável será gerado em dist/StampaSaaS.exe
```

### Gerar Instalador (Windows)

1. Baixe e instale [Inno Setup](http://www.jrsoftware.org/isdl.php)
2. Abra `StampaSaaSInstaller.iss` no Inno Setup
3. Clique em "Compile"
4. O instalador será gerado como `StampaSaaSInstaller.exe`

## 🐳 Docker (Experimental)

O projeto inclui suporte Docker para ambientes containerizados:

```bash
docker-compose up -d
```

Para mais detalhes, veja [README_DOCKER.md](README_DOCKER.md)

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -am 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através das [Issues](../../issues) do repositório.

## 📚 Documentação Adicional

- [Tutorial de Instalação (PT-BR)](TUTORIAL_INSTALACAO.md)
- [Guia Docker](README_DOCKER.md)
- [Info da Build](BUILD_INFO.md)
