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

        // Adicionar planilha de atividades
        const ws_data = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws_data, 'Atividades');

        // Adicionar planilha de resumo
        const ws_resumo = XLSX.utils.json_to_sheet(resumo);
        XLSX.utils.book_append_sheet(wb, ws_resumo, 'Resumo Financeiro');

        // Adicionar planilha de setores
        const ws_setores = XLSX.utils.json_to_sheet(setores);
        XLSX.utils.book_append_sheet(wb, ws_setores, 'Análise por Setor');

        // Exportar para arquivo Excel
        XLSX.writeFile(wb, 'Gestao_Gastos_Obra.xlsx');

    } catch (error) {
        console.error('Erro ao exportar Excel:', error);
        alert('Erro ao exportar Excel. Verifique o console para mais detalhes.');
    }

    // Esconder loading
    hideLoading(exportExcelBtn);
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