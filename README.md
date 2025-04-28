# Automatização de Pagamentos com Comprovantes em Python

## Descrição do Projeto
Este projeto é um sistema de gestão de gastos de obra que automatiza o registro de pagamentos com base em comprovantes. Ele utiliza tecnologias modernas para processar imagens de comprovantes, extrair informações relevantes e registrar pagamentos em uma planilha Excel. O sistema também permite a visualização e gerenciamento de atividades relacionadas à obra.

## Tecnologias Utilizadas
### Backend
- **Python**: Versão 3.10.12
- **Framework**: FastAPI
- **Bibliotecas**:
    - `openpyxl`: Manipulação de arquivos Excel.
    - `pytesseract`: Reconhecimento Óptico de Caracteres (OCR).
    - `os`: Manipulação de diretórios e arquivos.
    - `re`: Operações com expressões regulares.
    - `sys`: Manipulação de variáveis e funções do sistema.
    - `PIL`: Processamento de imagens.
    - `pandas`: Manipulação de dados tabulares.
    - `uuid`: Geração de identificadores únicos.

### Frontend
- **HTML5** e **CSS3**: Estrutura e estilização da interface.
- **TailwindCSS**: Framework CSS para design responsivo.
- **Font Awesome**: Ícones para melhorar a interface.
- **JavaScript**: Manipulação dinâmica do DOM e integração com o backend.

### Ferramentas
- **Microsoft Excel**: Armazenamento e gerenciamento de dados financeiros.
- **Tesseract OCR**: Extração de texto de imagens de comprovantes.

## Funcionalidades
### Backend
- **Listar Atividades**: Endpoint `/atividades` para listar todas as atividades registradas.
- **Listar Atividades Pendentes**: Endpoint `/atividades-pendentes` para listar atividades que ainda não foram pagas.
- **Adicionar Atividade**: Endpoint `/add-activity` para registrar novas atividades.
- **Processar Comprovantes**: Endpoint `/process-receipt` para extrair informações de comprovantes enviados.
- **Registrar Pagamento**: Endpoint `/register-payment` para registrar pagamentos e atualizar o status das atividades.
- **Atualizar Status**: Endpoint `/update-status` para verificar e atualizar o status de pagamento das atividades.

### Frontend
- **Dashboard**: Exibe o total de atividades, atividades pendentes e o valor total.
- **Tabela de Atividades**: Lista todas as atividades com informações detalhadas.
- **Adicionar Atividade**: Formulário para registrar novas atividades.
- **Processar Comprovante**: Interface para upload de comprovantes e extração de informações.
- **Registrar Pagamento**: Formulário para registrar pagamentos com base nos dados extraídos.

## Estrutura do Projeto
### Diretórios e Arquivos
- **`frontend/`**: Contém os arquivos do frontend.
  - `index.html`: Estrutura HTML da interface.
  - `index.js`: Lógica JavaScript para integração com o backend.
- **`projeto.py`**: Código do backend implementado com FastAPI.
- **`README.md`**: Documentação do projeto.
- **`uploads/`**: Diretório para armazenar arquivos enviados.
- **`Fluxo Caixa Construção Guaratinguetá.xlsx`**: Planilha Excel para registro de dados financeiros.

## Como Executar o Projeto
### Pré-requisitos
- Python 3.10 ou superior instalado.
- Tesseract OCR instalado e configurado.
- Node.js (opcional, para desenvolvimento do frontend).
