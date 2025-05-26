# Sistema de Gestão de Gastos de Obra

## Descrição do Projeto
Este projeto é um sistema de gestão de gastos de obra que automatiza o registro de pagamentos com base em comprovantes. Ele utiliza tecnologias modernas para processar imagens de comprovantes, extrair informações relevantes e registrar pagamentos em um banco de dados. O sistema também permite a visualização e gerenciamento de atividades relacionadas à obra, incluindo dashboards com gráficos para acompanhamento financeiro.

## Tecnologias Utilizadas
### Backend
- **Python**: Versão 3.10 ou superior
- **Framework**: FastAPI
- **Banco de Dados**: MySQL
- **Bibliotecas**:
    - `mysql-connector-python`: Conexão e operações com o banco de dados MySQL
    - `pytesseract`: Reconhecimento Óptico de Caracteres (OCR) para processamento de comprovantes
    - `pillow`: Processamento de imagens
    - `python-multipart`: Processamento de formulários e uploads de arquivos
    - `python-jose`: Implementação de autenticação JWT
    - `python-dotenv`: Gerenciamento de variáveis de ambiente
    - `requests`: Requisições HTTP
    - `uvicorn`: Servidor ASGI para execução da API

### Frontend
- **HTML5** e **CSS3**: Estrutura e estilização da interface
- **TailwindCSS**: Framework CSS para design responsivo
- **Font Awesome**: Ícones para melhorar a interface
- **JavaScript**: Manipulação dinâmica do DOM e integração com o backend
- **Bibliotecas JS**:
    - `jspdf`: Geração de relatórios PDF
    - `xlsx`: Manipulação de dados em formato Excel
    - `FileSaver.js`: Download de arquivos

### Ferramentas
- **Docker**: Containerização da aplicação
- **Tesseract OCR**: Extração de texto de imagens de comprovantes

## Funcionalidades
### Backend
- **Autenticação**: Sistema de login e proteção de rotas com JWT
- **Listar Atividades**: Endpoint `/atividades` para listar todas as atividades registradas
- **Listar Atividades Pendentes**: Endpoint `/atividades-pendentes` para listar atividades que ainda não foram pagas
- **Listar Atividades Pagas**: Endpoint `/atividades-pagas` para listar atividades já pagas
- **Adicionar Atividade**: Endpoint `/add-activity` para registrar novas atividades
- **Excluir Atividade**: Endpoint `/delete-activity/{id}` para remover atividades
- **Processar Comprovantes**: Endpoint `/process-receipt` para extrair informações de comprovantes enviados
- **Registrar Pagamento**: Endpoint `/register-payment` para registrar pagamentos
- **Calcular Valores Totais**: Endpoints para calcular valores totais da obra e valores pagos por cada parte

### Frontend
- **Sistema de Login**: Autenticação de usuários
- **Dashboard**: Exibe o total de atividades, valores pagos por cada parte e o valor total
- **Gráficos**: Visualização de dados em formato de gráficos para análise financeira
- **Tabela de Atividades**: Lista todas as atividades com informações detalhadas
- **Adicionar Atividade**: Formulário para registrar novas atividades
- **Processar Comprovante**: Interface para upload de comprovantes e extração de informações
- **Registrar Pagamento**: Formulário para registrar pagamentos com base nos dados extraídos
- **Design Responsivo**: Interface adaptável para diferentes tamanhos de tela

## Estrutura do Projeto
### Diretórios e Arquivos
- **`frontend/`**: Contém os arquivos do frontend
  - `index.html`: Página de login
  - `dashboard.html`: Dashboard principal
  - `graficos.html`: Página de visualização de gráficos
  - `js/`: Scripts JavaScript
  - `styles/`: Arquivos CSS
- **`backend/`**: Código do backend implementado com FastAPI
  - `main.py`: Arquivo principal com definição de rotas
  - `database.py`: Configuração e conexão com o banco de dados
  - `models.py`: Modelos de dados
  - `config.py`: Configurações da aplicação
  - `auth/`: Módulos de autenticação
  - `managers/`: Gerenciadores de funcionalidades
  - `utils/`: Utilitários e ferramentas
- **`dockerfile`**: Configuração para containerização da aplicação
- **`build.sh`**: Script para build e deploy
- **`requirements.txt`**: Dependências Python
- **`README.md`**: Documentação do projeto

