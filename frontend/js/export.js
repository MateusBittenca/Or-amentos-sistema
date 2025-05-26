const url_api = 'https://or-amentos-sistema.onrender.com';

const exportPdfBtn = document.getElementById('exportPdfBtn');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const exportImagesBtn = document.getElementById('exportImagesBtn');

exportPdfBtn.addEventListener('click', () => {
    // Lógica para exportar como PDF
    exportToPDF();

});
exportExcelBtn.addEventListener('click', () => {
    // Lógica para exportar como Excel
    exportToExcel();
});
exportImagesBtn.addEventListener('click', () => {
    // Lógica para exportar gráficos como imagens
    exportChartImages();
});


async function fetchAllActivities() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/atividades`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar atividades');
        }
        return await response.json();
    } catch (error) {
        console.error('Erro:', error);
        return [];
    }
}
async function fetchPendingActivities() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/atividades-pendentes`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar atividades pendentes');
        }
        return await response.json();
    } catch (error) {
        console.error('Erro:', error);
        return [];
    }
}

// Função para buscar atividades pagas
async function fetchPaidActivities() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/atividades-pagas`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar atividades pagas');
        }
        return await response.json();
    } catch (error) {
        console.error('Erro:', error);
        return [];
    }
}

// Função para buscar valor total
async function fetchTotalValue() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/valor-total`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar valor total');
        }
        const data = await response.json();
        return data.total;
    } catch (error) {
        console.error('Erro:', error);
        return 0;
    }
}

// Função para buscar valor total pago
async function fetchTotalPaidValue() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/valor-total-pago`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar valor total pago');
        }
        const data = await response.json();
        return data.total_pago;
    } catch (error) {
        console.error('Erro:', error);
        return 0;
    }
}

// Função para buscar valor pago por Diego-Ana
async function fetchDiegoPaidValue() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/valor-pago-diego`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar valor pago por Diego-Ana');
        }
        const data = await response.json();
        return data.total_pago_diego;
    } catch (error) {
        console.error('Erro:', error);
        return 0;
    }
}

// Função para buscar valor pago por Alex-Rute
async function fetchAlexPaidValue() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${url_api}/valor-pago-alex`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            throw new Error('Erro ao buscar valor pago por Alex-Rute');
        }
        const data = await response.json();
        return data.total_pago_alex;
    } catch (error) {
        console.error('Erro:', error);
        return 0;
    }
}

function exportToPDF() {
    // Mostrar loading


    setTimeout(() => {
        try {
            // Criar novo documento PDF
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF('landscape', 'mm', 'a4');

            // Título do documento
            doc.setFontSize(18);
            doc.setTextColor(59, 130, 246); // Azul do Tailwind
            doc.text('Relatório de Gestão de Gastos de Obra', 20, 20);

            // Data de exportação
            const today = new Date().toLocaleDateString('pt-BR');
            doc.setFontSize(10);
            doc.setTextColor(100, 100, 100);
            doc.text(`Exportado em: ${today}`, 20, 28);

            // Adicionar resumo financeiro
            doc.setFontSize(14);
            doc.setTextColor(0, 0, 0);
            doc.text('Resumo Financeiro', 20, 40);

            doc.setFontSize(10);
            const progress = progressPercentage.textContent;
            doc.text(`Progresso financeiro: ${progress}`, 20, 48);
            doc.text(`Balanceamento: Diego-Ana ${diegoPercentage.textContent} | Alex-Rute ${alexPercentage.textContent}`, 20, 54);
            doc.text(`Atividades concluídas: ${completedActivities.textContent}`, 20, 60);
            doc.text(`Atividades pendentes: ${pendingActivities.textContent}`, 20, 66);
            doc.text(`Total de atividades: ${totalActivities.textContent}`, 20, 72);

            // Converter os gráficos para imagens e adicionar ao PDF
            // Visão geral
            let verticalPosition = 85;
            doc.setFontSize(14);
            doc.text('Visão Geral', 20, verticalPosition);
            verticalPosition += 8;

            // Adicionar gráfico de Status
            if (charts.statusChart) {
                const statusChartImg = charts.statusChart.toBase64Image();
                doc.addImage(statusChartImg, 'PNG', 20, verticalPosition, 80, 50);
            }

            // Adicionar gráfico de Distribuição de Gastos
            if (charts.expenseDistributionChart) {
                const expenseDistImg = charts.expenseDistributionChart.toBase64Image();
                doc.addImage(expenseDistImg, 'PNG', 110, verticalPosition, 80, 50);
            }

            // Nova página
            doc.addPage();

            // Adicionar gráfico de Evolução de Gastos
            doc.setFontSize(14);
            doc.text('Evolução e Comparativo', 20, 20);

            if (charts.expenseEvolutionChart) {
                const evolutionImg = charts.expenseEvolutionChart.toBase64Image();
                doc.addImage(evolutionImg, 'PNG', 20, 30, 80, 50);
            }

            // Adicionar gráfico de Comparativo de Pagamentos
            if (charts.paymentComparisonChart) {
                const comparisonImg = charts.paymentComparisonChart.toBase64Image();
                doc.addImage(comparisonImg, 'PNG', 110, 30, 80, 50);
            }

            // Gráficos por setor
            doc.setFontSize(14);
            doc.text('Análise por Setor', 20, 90);

            if (charts.sectorExpenseChart) {
                const sectorExpenseImg = charts.sectorExpenseChart.toBase64Image();
                doc.addImage(sectorExpenseImg, 'PNG', 20, 100, 80, 50);
            }

            if (charts.sectorActivityChart) {
                const sectorActivityImg = charts.sectorActivityChart.toBase64Image();
                doc.addImage(sectorActivityImg, 'PNG', 110, 100, 80, 50);
            }

            // Nova página para timeline
            doc.addPage();
            doc.setFontSize(14);
            doc.text('Linha do Tempo', 20, 20);

            if (charts.timelineChart) {
                const timelineImg = charts.timelineChart.toBase64Image();
                doc.addImage(timelineImg, 'PNG', 20, 30, 170, 50);
            }

            if (charts.activityTimelineChart) {
                const activityTimelineImg = charts.activityTimelineChart.toBase64Image();
                doc.addImage(activityTimelineImg, 'PNG', 20, 90, 80, 50);
            }

            if (charts.paymentTimelineChart) {
                const paymentTimelineImg = charts.paymentTimelineChart.toBase64Image();
                doc.addImage(paymentTimelineImg, 'PNG', 110, 90, 80, 50);
            }

            // Nova página para pagamentos
            doc.addPage();
            doc.setFontSize(14);
            doc.text('Análise de Pagamentos', 20, 20);

            if (charts.paymentDistributionChart) {
                const paymentDistImg = charts.paymentDistributionChart.toBase64Image();
                doc.addImage(paymentDistImg, 'PNG', 20, 30, 80, 50);
            }

            if (charts.contributionComparisonChart) {
                const contribCompImg = charts.contributionComparisonChart.toBase64Image();
                doc.addImage(contribCompImg, 'PNG', 110, 30, 80, 50);
            }

            if (charts.sectorPaymentHistoryChart) {
                const sectorPaymentImg = charts.sectorPaymentHistoryChart.toBase64Image();
                doc.addImage(sectorPaymentImg, 'PNG', 20, 90, 170, 50);
            }

            // Adicionar informações de rodapé
            const pageCount = doc.internal.getNumberOfPages();
            for (let i = 1; i <= pageCount; i++) {
                doc.setPage(i);
                doc.setFontSize(8);
                doc.setTextColor(100, 100, 100);
                doc.text(`Página ${i} de ${pageCount}`, doc.internal.pageSize.getWidth() - 40, doc.internal.pageSize.getHeight() - 10);
                doc.text('Sistema de Gestão de Gastos de Obra', 20, doc.internal.pageSize.getHeight() - 10);
            }

            // Salvar o PDF
            doc.save('Relatório_Gestão_Gastos_Obra.pdf');

        } catch (error) {
            console.error('Erro ao exportar PDF:', error);
            alert('Erro ao exportar PDF. Verifique o console para mais detalhes.');
        }

        // Esconder loading
        hideLoading(exportPdfBtn);
    }, 500);
}

// Função para exportar como Excel
async function exportToExcel() {
    // Mostrar loading

    try {
        // Buscar atividades da API
        const activities = await fetchAllActivities();

        // Preparar dados para Excel
        const data = activities.map(activity => ({
            'ID': activity.id,
            'Data': activity.date,
            'Atividade': activity.activity,
            'Setor': activity.sector,
            'Valor': activity.value,
            'Pago Diego-Ana': activity.diego_ana || 0,
            'Pago Alex-Rute': activity.alex_rute || 0,
            'Total Pago': (activity.diego_ana || 0) + (activity.alex_rute || 0),
            'Restante': activity.value - ((activity.diego_ana || 0) + (activity.alex_rute || 0)),
            'Status': (activity.diego_ana || 0) + (activity.alex_rute || 0) >= activity.value ? 'Concluída' : 'Pendente'
        }));

        // Preparar resumo financeiro
        const totalValue = await fetchTotalValue();
        const totalPaidValue = await fetchTotalPaidValue();
        const diegoPaidValue = await fetchDiegoPaidValue();
        const alexPaidValue = await fetchAlexPaidValue();

        const resumo = [
            { 'Resumo Financeiro': 'Valor Total', 'Valor': totalValue },
            { 'Resumo Financeiro': 'Valor Pago', 'Valor': totalPaidValue },
            { 'Resumo Financeiro': 'Valor Restante', 'Valor': totalValue - totalPaidValue },
            { 'Resumo Financeiro': 'Pago Diego-Ana', 'Valor': diegoPaidValue },
            { 'Resumo Financeiro': 'Pago Alex-Rute', 'Valor': alexPaidValue },
            { 'Resumo Financeiro': 'Progresso', 'Valor': `${((totalPaidValue / totalValue) * 100).toFixed(2)}%` }
        ];

        // Dados por setor
        const sectorData = {};
        activities.forEach(a => {
            if (!sectorData[a.sector]) {
                sectorData[a.sector] = {
                    total: 0,
                    paid: 0,
                    count: 0
                };
            }

            sectorData[a.sector].total += a.value;
            sectorData[a.sector].paid += (a.diego_ana || 0) + (a.alex_rute || 0);
            sectorData[a.sector].count++;
        });

        const setores = Object.keys(sectorData).map(sector => ({
            'Setor': sector,
            'Total Atividades': sectorData[sector].count,
            'Valor Total': sectorData[sector].total,
            'Valor Pago': sectorData[sector].paid,
            'Valor Pendente': sectorData[sector].total - sectorData[sector].paid,
            'Progresso': `${((sectorData[sector].paid / sectorData[sector].total) * 100).toFixed(2)}%`
        }));

        // Criar workbook
        const wb = XLSX.utils.book_new();

        // ===== PLANILHA DE ATIVIDADES =====
        const ws_data = XLSX.utils.json_to_sheet(data);
        
        // Formatação da planilha de atividades
        const range = XLSX.utils.decode_range(ws_data['!ref']);
        
        // Definir largura das colunas
        ws_data['!cols'] = [
            { wch: 8 },   // ID
            { wch: 12 },  // Data
            { wch: 30 },  // Atividade
            { wch: 15 },  // Setor
            { wch: 12 },  // Valor
            { wch: 15 },  // Pago Diego-Ana
            { wch: 15 },  // Pago Alex-Rute
            { wch: 12 },  // Total Pago
            { wch: 12 },  // Restante
            { wch: 12 }   // Status
        ];

        // Aplicar estilos
        if (!ws_data['!style']) ws_data['!style'] = {};

        // Estilo do cabeçalho (linha 1)
        for (let col = range.s.c; col <= range.e.c; col++) {
            const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
            if (!ws_data[cellAddress]) continue;
            
            ws_data[cellAddress].s = {
                fill: { fgColor: { rgb: "2E5BBA" } }, // Azul escuro
                font: { color: { rgb: "FFFFFF" }, bold: true, sz: 12 },
                alignment: { horizontal: "center", vertical: "center" },
                border: {
                    top: { style: "thin", color: { rgb: "000000" } },
                    bottom: { style: "thin", color: { rgb: "000000" } },
                    left: { style: "thin", color: { rgb: "000000" } },
                    right: { style: "thin", color: { rgb: "000000" } }
                }
            };
        }

        // Estilo para linhas de dados
        for (let row = 1; row <= range.e.r; row++) {
            const statusCell = ws_data[XLSX.utils.encode_cell({ r: row, c: 9 })]; // Coluna Status
            const isCompleted = statusCell && statusCell.v === 'Concluída';
            
            for (let col = range.s.c; col <= range.e.c; col++) {
                const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
                if (!ws_data[cellAddress]) continue;
                
                ws_data[cellAddress].s = {
                    fill: { 
                        fgColor: { 
                            rgb: isCompleted ? "D4EDDA" : (row % 2 === 0 ? "F8F9FA" : "FFFFFF") 
                        } 
                    }, // Verde claro para concluídas, alternando cinza/branco para outras
                    font: { 
                        color: { rgb: isCompleted ? "155724" : "000000" },
                        bold: isCompleted && col === 9 // Status em negrito se concluída
                    },
                    alignment: { 
                        horizontal: col === 2 ? "left" : "center", // Atividade à esquerda, resto centralizado
                        vertical: "center" 
                    },
                    border: {
                        top: { style: "thin", color: { rgb: "DEE2E6" } },
                        bottom: { style: "thin", color: { rgb: "DEE2E6" } },
                        left: { style: "thin", color: { rgb: "DEE2E6" } },
                        right: { style: "thin", color: { rgb: "DEE2E6" } }
                    },
                    numFmt: (col >= 4 && col <= 8) ? '#,##0.00' : undefined // Formato de moeda para valores
                };
            }
        }

        XLSX.utils.book_append_sheet(wb, ws_data, 'Atividades');

        // ===== PLANILHA DE RESUMO =====
        const ws_resumo = XLSX.utils.json_to_sheet(resumo);
        
        // Formatação da planilha de resumo
        const resumoRange = XLSX.utils.decode_range(ws_resumo['!ref']);
        
        ws_resumo['!cols'] = [
            { wch: 20 }, // Resumo Financeiro
            { wch: 15 }  // Valor
        ];

        // Cabeçalho do resumo
        for (let col = 0; col <= 1; col++) {
            const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
            if (!ws_resumo[cellAddress]) continue;
            
            ws_resumo[cellAddress].s = {
                fill: { fgColor: { rgb: "28A745" } }, // Verde
                font: { color: { rgb: "FFFFFF" }, bold: true, sz: 12 },
                alignment: { horizontal: "center", vertical: "center" },
                border: {
                    top: { style: "thin", color: { rgb: "000000" } },
                    bottom: { style: "thin", color: { rgb: "000000" } },
                    left: { style: "thin", color: { rgb: "000000" } },
                    right: { style: "thin", color: { rgb: "000000" } }
                }
            };
        }

        // Dados do resumo
        for (let row = 1; row <= resumoRange.e.r; row++) {
            for (let col = 0; col <= 1; col++) {
                const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
                if (!ws_resumo[cellAddress]) continue;
                
                ws_resumo[cellAddress].s = {
                    fill: { fgColor: { rgb: row % 2 === 0 ? "F8F9FA" : "FFFFFF" } },
                    font: { color: { rgb: "000000" }, bold: col === 0 },
                    alignment: { horizontal: col === 0 ? "left" : "center", vertical: "center" },
                    border: {
                        top: { style: "thin", color: { rgb: "DEE2E6" } },
                        bottom: { style: "thin", color: { rgb: "DEE2E6" } },
                        left: { style: "thin", color: { rgb: "DEE2E6" } },
                        right: { style: "thin", color: { rgb: "DEE2E6" } }
                    },
                    numFmt: col === 1 && !ws_resumo[cellAddress].v.toString().includes('%') ? '#,##0.00' : undefined
                };
            }
        }

        XLSX.utils.book_append_sheet(wb, ws_resumo, 'Resumo Financeiro');

        // ===== PLANILHA DE SETORES =====
        const ws_setores = XLSX.utils.json_to_sheet(setores);
        
        // Formatação da planilha de setores
        const setoresRange = XLSX.utils.decode_range(ws_setores['!ref']);
        
        ws_setores['!cols'] = [
            { wch: 20 }, // Setor
            { wch: 15 }, // Total Atividades
            { wch: 15 }, // Valor Total
            { wch: 12 }, // Valor Pago
            { wch: 15 }, // Valor Pendente
            { wch: 12 }  // Progresso
        ];

        // Cabeçalho dos setores
        for (let col = 0; col <= 5; col++) {
            const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
            if (!ws_setores[cellAddress]) continue;
            
            ws_setores[cellAddress].s = {
                fill: { fgColor: { rgb: "FD7E14" } }, // Laranja
                font: { color: { rgb: "FFFFFF" }, bold: true, sz: 12 },
                alignment: { horizontal: "center", vertical: "center" },
                border: {
                    top: { style: "thin", color: { rgb: "000000" } },
                    bottom: { style: "thin", color: { rgb: "000000" } },
                    left: { style: "thin", color: { rgb: "000000" } },
                    right: { style: "thin", color: { rgb: "000000" } }
                }
            };
        }

        // Dados dos setores
        for (let row = 1; row <= setoresRange.e.r; row++) {
            for (let col = 0; col <= 5; col++) {
                const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
                if (!ws_setores[cellAddress]) continue;
                
                ws_setores[cellAddress].s = {
                    fill: { fgColor: { rgb: row % 2 === 0 ? "F8F9FA" : "FFFFFF" } },
                    font: { color: { rgb: "000000" } },
                    alignment: { horizontal: col === 0 ? "left" : "center", vertical: "center" },
                    border: {
                        top: { style: "thin", color: { rgb: "DEE2E6" } },
                        bottom: { style: "thin", color: { rgb: "DEE2E6" } },
                        left: { style: "thin", color: { rgb: "DEE2E6" } },
                        right: { style: "thin", color: { rgb: "DEE2E6" } }
                    },
                    numFmt: (col >= 2 && col <= 4) ? '#,##0.00' : undefined
                };
            }
        }

        XLSX.utils.book_append_sheet(wb, ws_setores, 'Análise por Setor');

        // Exportar para arquivo Excel
        XLSX.writeFile(wb, 'Gestao_Gastos_Obra.xlsx');

    } catch (error) {
        console.error('Erro ao exportar Excel:', error);
        alert('Erro ao exportar Excel. Verifique o console para mais detalhes.');
    }

    // Esconder loading
}

// Função para exportar gráficos como imagens
function exportChartImages() {
    // Mostrar loading
    setTimeout(() => {
        try {
            // Lista de gráficos e seus nomes
            const chartsToExport = [
                { chart: charts.statusChart, name: 'Status_Atividades' },
                { chart: charts.expenseDistributionChart, name: 'Distribuicao_Gastos' },
                { chart: charts.expenseEvolutionChart, name: 'Evolucao_Gastos' },
                { chart: charts.paymentComparisonChart, name: 'Comparativo_Pagamentos' },
                { chart: charts.sectorExpenseChart, name: 'Gastos_por_Setor' },
                { chart: charts.sectorActivityChart, name: 'Atividades_por_Setor' },
                { chart: charts.sectorDetailChart, name: 'Detalhamento_Setor' },
                { chart: charts.timelineChart, name: 'Linha_do_Tempo' },
                { chart: charts.activityTimelineChart, name: 'Atividades_por_Periodo' },
                { chart: charts.paymentTimelineChart, name: 'Pagamentos_por_Periodo' },
                { chart: charts.paymentDistributionChart, name: 'Distribuicao_Pagamentos' },
                { chart: charts.contributionComparisonChart, name: 'Comparativo_Contribuicoes' },
                { chart: charts.sectorPaymentHistoryChart, name: 'Historico_Pagamentos_Setor' }
            ];

            // Verificar quais gráficos existem e exportá-los
            let exportedCount = 0;

            chartsToExport.forEach(item => {
                if (item.chart) {
                    const url = item.chart.toBase64Image();

                    // Para navegadores modernos: usar FileSaver.js
                    // Converter a URL base64 para Blob
                    fetch(url)
                        .then(res => res.blob())
                        .then(blob => {
                            saveAs(blob, `Grafico_${item.name}.png`);
                            exportedCount++;

                            // Se for o último gráfico, mostrar mensagem
                            if (exportedCount === chartsToExport.filter(c => c.chart).length) {
                                alert(`${exportedCount} gráficos exportados com sucesso!`);
                            }
                        });
                }
            });

            // Se nenhum gráfico foi encontrado
            if (chartsToExport.filter(c => c.chart).length === 0) {
                alert('Nenhum gráfico disponível para exportação.');
            }

        } catch (error) {
            console.error('Erro ao exportar imagens:', error);
            alert('Erro ao exportar imagens. Verifique o console para mais detalhes.');
        }

        // Esconder loading
        hideLoading(exportImagesBtn);
    }, 500);
}