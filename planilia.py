from openpyxl import load_workbook
from openpyxl.styles import PatternFill

def marcar_pagamento(nome_pessoa, arquivo_planilha):
    wb = load_workbook(arquivo_planilha)
    ws = wb.active

    # Preenchimento verde (pago)
    verde = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")

    # Encontrar coluna da pessoa no cabeçalho
    # Encontrar coluna da pessoa no cabeçalho
    col_index = None
    for cell in ws[1]:
        if cell.value and nome_pessoa.strip().lower() in str(cell.value).strip().lower():
            col_index = cell.column
            break

    if not col_index:
        print(f"Coluna da pessoa '{nome_pessoa}' não encontrada.")
        return

    # Percorrer as células da pessoa (a partir da segunda linha)
    for row in ws.iter_rows(min_row=2):
        cell = row[col_index - 1]  # index começa em 1
        if cell.fill.start_color.index != "FF00FF00":  # se não for verde
            if cell.value:  # só marca se tiver valor
                cell.fill = verde
                print(f"Pagamento marcado como feito na linha {cell.row}.")
                break

    wb.save(arquivo_planilha)
    print("Planilha atualizada com sucesso.")
marcar_pagamento("Diego-Ana", "Fluxo_Caixa_Construção_Guaratinguetá_Despesas.xlsx")
