# Stampa SaaS

Aplicativo Python para gerenciar clientes e pedidos de uma empresa de estampa em camisas.

## Estrutura de dados

Os dados são salvos em CSV dentro de um diretório de dados do usuário no Windows, tipicamente:

- `%LOCALAPPDATA%\Stampa_SaaS\CLIENTES.csv`
- `%LOCALAPPDATA%\Stampa_SaaS\PEDIDOS.csv`
- `%LOCALAPPDATA%\Stampa_SaaS\PEDIDO_ARTES\`

As colunas são:

- `CLIENTES.csv`
  - `id_clientes`
  - `ClienteEmpresa`
  - `email`
  - `telefone`
  - `data_criação`

- `PEDIDOS.csv`
  - `id_pedidos`
  - `id_cliente`
  - `cliente_empresa`
  - `quantidade`
  - `valor`
  - `data`
  - `descrição`
  - `status`

## Como executar

1. Abra um terminal no diretório do projeto:
   ```powershell
   cd c:\Users\Mateus\Desktop\PythonApps\Stampa_SaaS
   ```
2. Execute o aplicativo:
   ```powershell
   python main.py
   ```

## Como gerar o executável

1. Instale o PyInstaller (se ainda não estiver instalado):
   ```powershell
   pip install pyinstaller
   ```
2. Execute o script de build:
   ```powershell
   .\build_exe.bat
   ```
3. O executável será gerado em `dist\StampaSaaS.exe`.

## Como gerar o instalador (Windows)

1. Instale o Inno Setup.
2. Abra `StampaSaaSInstaller.iss` no Inno Setup e compile o script.
3. O instalador gerado será `StampaSaaSInstaller.exe`.

## Como o aplicativo armazena os dados

- Ao instalar e executar, o aplicativo usa `%LOCALAPPDATA%\Stampa_SaaS` como diretório de dados.
- Os arquivos CSV e a pasta de artes são criados automaticamente na primeira execução.
- Esse diretório é reutilizado sempre que o programa for aberto no mesmo computador.

## Observações

- O aplicativo cria automaticamente os arquivos CSV na pasta `STAMPA_FILES` na primeira execução.
- Para cada cliente cadastrado também é gerado um CSV de resumo com o nome `Cliente_<ClienteEmpresa>.csv`.
- O campo `cliente` em pedidos é preenchido somente com clientes cadastrados.
- Você pode cadastrar, atualizar e remover clientes, bem como criar, atualizar e excluir pedidos.
- A mudança de status dos pedidos pode ser feita por meio da lista de pedidos selecionando um pedido e escolhendo `Em andamento` ou `Finalizado`.
- Ao criar um pedido, é criada uma pasta em `STAMPA_FILES/PEDIDO_ARTES/pedido_<id_pedidos>`.
