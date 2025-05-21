// Configuração da API
        const API_URL = 'http://localhost:10000'; // Ajuste para seu endereço de API

        // Inicialização de gráficos
        let charts = {};

        // Referências para todos os elementos do DOM
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');

        // Elementos de resumo
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const balanceBar = document.getElementById('balanceBar');
        const diegoPercentage = document.getElementById('diegoPercentage');
        const alexPercentage = document.getElementById('alexPercentage');
        const completedActivities = document.getElementById('completedActivities');
        const pendingActivities = document.getElementById('pendingActivities');
        const totalActivities = document.getElementById('totalActivities');

        // Botões de navegação
        const homeBtn = document.getElementById('homeBtn');
        const graphicBtn = document.getElementById('graphicBtn');
        const docsBtn = document.getElementById('docsBtn');

        // Botões de update
        const overviewUpdateBtn = document.getElementById('overviewUpdateBtn');
        const sectorUpdateBtn = document.getElementById('sectorUpdateBtn');
        const timelineUpdateBtn = document.getElementById('timelineUpdateBtn');
        const paymentUpdateBtn = document.getElementById('paymentUpdateBtn');

        // Botões de exportação
        const exportPdfBtn = document.getElementById('exportPdfBtn');
        const exportExcelBtn = document.getElementById('exportExcelBtn');
        const exportImagesBtn = document.getElementById('exportImagesBtn');

        // ===== Funções Utilitárias =====

        // Função para formatação de valores monetários
        function formatCurrency(value) {
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        }

        // Função para converter data do formato DD/MM/YYYY para objeto Date
        function parseDate(dateString) {
            if (!dateString) return null;
            const parts = dateString.split('/');
            if (parts.length !== 3) return null;
            // Formato DD/MM/YYYY para Date (mês é baseado em zero)
            return new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
        }

        // Função para filtrar atividades por período
        function filterActivitiesByPeriod(activities, periodFilter) {
            if (periodFilter === 'all') return activities;

            const now = new Date();
            let cutoffDate;

            switch (periodFilter) {
                case 'month':
                    cutoffDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
                    break;
                case 'quarter':
                    cutoffDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
                    break;
                case 'year':
                    cutoffDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
                    break;
                default:
                    return activities;
            }

            return activities.filter(activity => {
                const activityDate = parseDate(activity.date);
                return activityDate && activityDate >= cutoffDate;
            });
        }

        // Função para mostrar loading em um elemento
        function showLoading(element) {
            element.classList.add('loading');
        }

        // Função para esconder loading em um elemento
        function hideLoading(element) {
            element.classList.remove('loading');
        }

        // Destruir gráfico se existir
        function destroyChart(chartId) {
            if (charts[chartId]) {
                charts[chartId].destroy();
                charts[chartId] = null;
            }
        }

        // ===== Funções de API =====

        // Função para buscar todas as atividades
        async function fetchAllActivities() {
            try {
                const response = await fetch(`${API_URL}/atividades`);
                if (!response.ok) {
                    throw new Error('Erro ao buscar atividades');
                }
                return await response.json();
            } catch (error) {
                console.error('Erro:', error);
                return [];
            }
        }

        // Função para buscar atividades pendentes
        async function fetchPendingActivities() {
            try {
                const response = await fetch(`${API_URL}/atividades-pendentes`);
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
                const response = await fetch(`${API_URL}/atividades-pagas`);
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
                const response = await fetch(`${API_URL}/valor-total`);
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
                const response = await fetch(`${API_URL}/valor-total-pago`);
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
                const response = await fetch(`${API_URL}/valor-pago-diego`);
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
                const response = await fetch(`${API_URL}/valor-pago-alex`);
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

        // ===== Funções para criar gráficos =====

        // Gráfico de Status das Atividades
        function createStatusChart(activities) {
            const pendingCount = activities.filter(a => a.diego_ana + a.alex_rute < a.value).length;
            const completedCount = activities.length - pendingCount;

            destroyChart('statusChart');

            const ctx = document.getElementById('statusChart').getContext('2d');
            charts.statusChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Concluídas', 'Pendentes'],
                    datasets: [{
                        data: [completedCount, pendingCount],
                        backgroundColor: ['#10B981', '#FBBF24'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // Gráfico de Distribuição de Gastos
        function createExpenseDistributionChart(activities) {
            const labels = activities.map(a => a.activity);
            const data = activities.map(a => a.value);

            destroyChart('expenseDistributionChart');

            const ctx = document.getElementById('expenseDistributionChart').getContext('2d');
            charts.expenseDistributionChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Distribuição de Gastos',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gráfico de Evolução de Gastos
        function createExpenseEvolutionChart(activities) {
            const labels = activities.map(a => a.date);
            const data = activities.map(a => a.value);

            destroyChart('expenseEvolutionChart');

            const ctx = document.getElementById('expenseEvolutionChart').getContext('2d');
            charts.expenseEvolutionChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Evolução de Gastos',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderColor: '#3B82F6',
                        fill: false,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
        // Gráfico de Comparativo de Pagamentos
        function createPaymentComparisonChart(activities) {
            const labels = activities.map(a => a.activity);
            const dataDiego = activities.map(a => a.diego_ana);
            const dataAlex = activities.map(a => a.alex_rute);

            destroyChart('paymentComparisonChart');

            const ctx = document.getElementById('paymentComparisonChart').getContext('2d');
            charts.paymentComparisonChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Diego-Ana',
                            data: dataDiego,
                            backgroundColor: '#3B82F6',
                            borderWidth: 1
                        },
                        {
                            label: 'Alex-Rute',
                            data: dataAlex,
                            backgroundColor: '#FBBF24',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }

        // Gráfico de Gastos por Setor
        function createSectorExpenseChart(activities) {
            // Soma os valores por setor
            const sectorSums = {};
            activities.forEach(a => {
                if (!sectorSums[a.sector]) sectorSums[a.sector] = 0;
                sectorSums[a.sector] += a.value;
            });
            const labels = Object.keys(sectorSums);
            const data = Object.values(sectorSums);

            destroyChart('sectorExpenseChart');

            const ctx = document.getElementById('sectorExpenseChart').getContext('2d');
            charts.sectorExpenseChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Gastos por Setor',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gráfico de Atividades por Setor (já está correto)
        function createSectorActivityChart(activities) {
            const sectorCounts = {};
            activities.forEach(a => {
                if (!sectorCounts[a.sector]) sectorCounts[a.sector] = 0;
                sectorCounts[a.sector]++;
            });
            const labels = Object.keys(sectorCounts);
            const data = Object.values(sectorCounts);

            destroyChart('sectorActivityChart');

            const ctx = document.getElementById('sectorActivityChart').getContext('2d');
            charts.sectorActivityChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Atividades por Setor',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gráfico de Detalhamento do Setor
        function createSectorDetailChart(activities) {
            const labels = activities.map(a => a.activity);
            const data = activities.map(a => a.value);

            destroyChart('sectorDetailChart');

            const ctx = document.getElementById('sectorDetailChart').getContext('2d');
            charts.sectorDetailChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Detalhamento do Setor',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gráfico de Atividades por Período (REMOVER activity_count)
        function createActivityTimelineChart(activities) {
            // Agrupa por data e conta atividades
            const dateCounts = {};
            activities.forEach(a => {
                if (!dateCounts[a.date]) dateCounts[a.date] = 0;
                dateCounts[a.date]++;
            });
            const labels = Object.keys(dateCounts);
            const data = Object.values(dateCounts);

            destroyChart('activityTimelineChart');

            const ctx = document.getElementById('activityTimelineChart').getContext('2d');
            charts.activityTimelineChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Atividades por Período',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gráfico de Pagamentos por Período (REMOVER payment_count)
        function createPaymentTimelineChart(activities) {
            // Soma pagamentos por data
            const dateSums = {};
            activities.forEach(a => {
                if (!dateSums[a.date]) dateSums[a.date] = 0;
                dateSums[a.date] += (a.diego_ana || 0) + (a.alex_rute || 0);
            });
            const labels = Object.keys(dateSums);
            const data = Object.values(dateSums);

            destroyChart('paymentTimelineChart');

            const ctx = document.getElementById('paymentTimelineChart').getContext('2d');
            charts.paymentTimelineChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Pagamentos por Período',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gráfico de Histórico de Pagamentos por Setor (REMOVER payment_count)
        function createSectorPaymentHistoryChart(activities) {
            // Soma pagamentos por setor
            const sectorSums = {};
            activities.forEach(a => {
                if (!sectorSums[a.sector]) sectorSums[a.sector] = 0;
                sectorSums[a.sector] += (a.diego_ana || 0) + (a.alex_rute || 0);
            });
            const labels = Object.keys(sectorSums);
            const data = Object.values(sectorSums);

            destroyChart('sectorPaymentHistoryChart');

            const ctx = document.getElementById('sectorPaymentHistoryChart').getContext('2d');
            charts.sectorPaymentHistoryChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Histórico de Pagamentos por Setor',
                        data: data,
                        backgroundColor: '#3B82F6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // ===== Funções de Inicialização =====
        async function init() {
            // Carregar atividades
            const activities = await fetchAllActivities();

            // Atualizar gráficos iniciais
            createStatusChart(activities);
            createExpenseDistributionChart(activities);
            createExpenseEvolutionChart(activities);
            createPaymentComparisonChart(activities);
            createSectorExpenseChart(activities);
            createSectorActivityChart(activities);
            createSectorDetailChart(activities);

            // Atualizar resumo financeiro
            const totalValue = await fetchTotalValue();
            const totalPaidValue = await fetchTotalPaidValue();
            const diegoPaidValue = await fetchDiegoPaidValue();
            const alexPaidValue = await fetchAlexPaidValue();

            progressBar.style.width = `${(totalPaidValue / totalValue) * 100}%`;
            progressPercentage.textContent = `${((totalPaidValue / totalValue) * 100).toFixed(2)}%`;

            balanceBar.style.width = `${(diegoPaidValue / (diegoPaidValue + alexPaidValue)) * 100}%`;
            diegoPercentage.textContent = `${((diegoPaidValue / (diegoPaidValue + alexPaidValue)) * 100).toFixed(2)}%`;
            alexPercentage.textContent = `${((alexPaidValue / (diegoPaidValue + alexPaidValue)) * 100).toFixed(2)}%`;

            completedActivities.textContent = activities.filter(a => a.diego_ana + a.alex_rute >= a.value).length;
            pendingActivities.textContent = activities.filter(a => a.diego_ana + a.alex_rute < a.value).length;
            totalActivities.textContent = activities.length;
        }
        // ===== Eventos de Clique =====
        homeBtn.addEventListener('click', () => {
            window.location.href = 'dashboard.html';
        });
        graphicBtn.addEventListener('click', () => {
            window.location.href = 'graficos.html';
        });
        docsBtn.addEventListener('click', () => {
            window.location.href = 'documentos.html';
        });
        overviewUpdateBtn.addEventListener('click', async () => {
            showLoading(overviewUpdateBtn);
            const activities = await fetchAllActivities();
            createStatusChart(activities);
            hideLoading(overviewUpdateBtn);
        });
        sectorUpdateBtn.addEventListener('click', async () => {
            showLoading(sectorUpdateBtn);
            const activities = await fetchAllActivities();
            createSectorExpenseChart(activities);
            hideLoading(sectorUpdateBtn);
        });
        timelineUpdateBtn.addEventListener('click', async () => {
            showLoading(timelineUpdateBtn);
            const activities = await fetchAllActivities();
            createTimelineChart(activities);
            hideLoading(timelineUpdateBtn);
        });
        paymentUpdateBtn.addEventListener('click', async () => {
            showLoading(paymentUpdateBtn);
            const activities = await fetchAllActivities();
            createPaymentComparisonChart(activities);
            hideLoading(paymentUpdateBtn);
        });
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

        // Adicione este código no seu arquivo JavaScript existente, antes do final do script

        // ===== Gerenciamento de Abas =====

        // Adiciona eventos de clique às abas
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove a classe 'active' de todas as abas
                tabs.forEach(t => t.classList.remove('active'));

                // Adiciona a classe 'active' à aba clicada
                tab.classList.add('active');

                // Oculta todos os conteúdos de abas
                tabContents.forEach(content => content.classList.remove('active'));

                // Exibe o conteúdo correspondente à aba clicada
                const tabId = tab.getAttribute('data-tab');
                document.getElementById(`${tabId}-tab`).classList.add('active');

                // Atualiza os gráficos correspondentes à aba selecionada
                updateChartsForTab(tabId);
            });
        });

        // Função para atualizar os gráficos com base na aba selecionada
        async function updateChartsForTab(tabId) {
            const activities = await fetchAllActivities();

            switch (tabId) {
                case 'overview':
                    // Atualizar gráficos da visão geral
                    createStatusChart(activities);
                    createExpenseDistributionChart(activities);
                    createExpenseEvolutionChart(activities);
                    createPaymentComparisonChart(activities);
                    break;

                case 'sector':
                    // Atualizar gráficos da aba de setor
                    const sectorFilter = document.getElementById('sectorFilter').value;
                    const filteredBySector = sectorFilter === 'all'
                        ? activities
                        : activities.filter(a => a.sector === sectorFilter);

                    createSectorExpenseChart(filteredBySector);
                    createSectorActivityChart(filteredBySector);
                    createSectorDetailChart(filteredBySector);
                    break;

                case 'timeline':
                    // Atualizar gráficos da linha do tempo
                    createActivityTimelineChart(activities);
                    createPaymentTimelineChart(activities);

                    // Implementar timeline chart que estava faltando
                    createTimelineChart(activities);
                    break;

                case 'payment':
                    // Atualizar gráficos de pagamentos
                    createPaymentComparisonChart(activities);
                    createSectorPaymentHistoryChart(activities);
                    createPaymentDistributionChart(activities);
                    createContributionComparisonChart(activities);
                    break;
            }
        }

        // Função para criar o gráfico de timeline que estava faltando
        function createTimelineChart(activities) {
            // Organizar dados por data
            const sortedActivities = [...activities].sort((a, b) => {
                return parseDate(a.date) - parseDate(b.date);
            });

            const labels = sortedActivities.map(a => a.date);
            const values = sortedActivities.map(a => a.value);
            const cumulativeValues = [];
            let sum = 0;

            values.forEach(value => {
                sum += value;
                cumulativeValues.push(sum);
            });

            destroyChart('timelineChart');

            const ctx = document.getElementById('timelineChart').getContext('2d');
            charts.timelineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Valor por Período',
                            data: values,
                            backgroundColor: '#3B82F6',
                            borderColor: '#3B82F6',
                            borderWidth: 2,
                            fill: false,
                        },
                        {
                            label: 'Valor Acumulado',
                            data: cumulativeValues,
                            backgroundColor: '#10B981',
                            borderColor: '#10B981',
                            borderWidth: 2,
                            fill: false,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }

        // Funções que estavam faltando para a aba de pagamentos
        function createPaymentDistributionChart(activities) {
            // Somar totais de pagamentos por pagador
            let diegoTotal = 0;
            let alexTotal = 0;

            activities.forEach(a => {
                diegoTotal += a.diego_ana || 0;
                alexTotal += a.alex_rute || 0;
            });

            destroyChart('paymentDistributionChart');

            const ctx = document.getElementById('paymentDistributionChart').getContext('2d');
            charts.paymentDistributionChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Diego-Ana', 'Alex-Rute'],
                    datasets: [{
                        data: [diegoTotal, alexTotal],
                        backgroundColor: ['#3B82F6', '#FBBF24'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        function createContributionComparisonChart(activities) {
            // Agrupar por setor e calcular contribuições de cada pagador
            const sectorData = {};

            activities.forEach(a => {
                if (!sectorData[a.sector]) {
                    sectorData[a.sector] = {
                        diego: 0,
                        alex: 0
                    };
                }

                sectorData[a.sector].diego += a.diego_ana || 0;
                sectorData[a.sector].alex += a.alex_rute || 0;
            });

            const labels = Object.keys(sectorData);
            const diegoData = labels.map(sector => sectorData[sector].diego);
            const alexData = labels.map(sector => sectorData[sector].alex);

            destroyChart('contributionComparisonChart');

            const ctx = document.getElementById('contributionComparisonChart').getContext('2d');
            charts.contributionComparisonChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Diego-Ana',
                            data: diegoData,
                            backgroundColor: '#3B82F6',
                            borderWidth: 1
                        },
                        {
                            label: 'Alex-Rute',
                            data: alexData,
                            backgroundColor: '#FBBF24',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            stacked: false
                        },
                        y: {
                            stacked: false
                        }
                    }
                }
            });
        }

        // Implementar os event listeners para os filtros
        document.getElementById('sectorFilter').addEventListener('change', () => {
            const tabId = 'sector';
            updateChartsForTab(tabId);
        });

        document.getElementById('sectorPeriodFilter').addEventListener('change', () => {
            const tabId = 'sector';
            updateChartsForTab(tabId);
        });

        document.getElementById('timelineViewFilter').addEventListener('change', () => {
            const tabId = 'timeline';
            updateChartsForTab(tabId);
        });

        document.getElementById('timelineTypeFilter').addEventListener('change', () => {
            const tabId = 'timeline';
            updateChartsForTab(tabId);
        });

        document.getElementById('paymentPersonFilter').addEventListener('change', () => {
            const tabId = 'payment';
            updateChartsForTab(tabId);
        });

        document.getElementById('paymentPeriodFilter').addEventListener('change', () => {
            const tabId = 'payment';
            updateChartsForTab(tabId);
        });

        function exportToPDF() {
            // Mostrar loading
            showLoading(exportPdfBtn);

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
            showLoading(exportExcelBtn);

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
            showLoading(exportImagesBtn);

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
        // Inicializar gráficos e resumo financeiro
        init();