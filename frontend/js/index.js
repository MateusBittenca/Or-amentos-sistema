const API_URL = "https://or-amentos-sistema.onrender.com";

function checkAuthentication() {
    // Verificar se existe um token de autenticação no localStorage
    const authToken = localStorage.getItem('access_token');
    
    // Se não existir token, redirecionar para a página de login
    if (!authToken) {
        window.location.href = 'index.html';
        return false;
    }
    
    return true;
}

// Executar a verificação de autenticação quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticação antes de carregar o resto do conteúdo
    if (!checkAuthentication()) {
        // Se não estiver autenticado, a função já redirecionou para login.html
        return;
    }
});

const api = {
  async fetchData(endpoint) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Erro ao buscar dados de ${endpoint}:`, error);
      throw error;
    }
  },

  async deleteActivity(id) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/delete-activity/${id}`, {
        method: "DELETE",
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.detail || "Erro desconhecido");
      }

      return true;

    } catch (error) {
      console.error("Erro ao deletar atividade:", error);
      throw error;
    }
  },

  async editActivity(id, formData) {
    try {
      const token = localStorage.getItem('access_token');
      
      // Log do FormData para debug
      console.log("Enviando dados para edição:");
      for (let pair of formData.entries()) {
        console.log(pair[0] + ': ' + pair[1]);
      }
      
      const response = await fetch(`${API_URL}/edit-activity/${id}`, {
        method: "PUT",
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Erro desconhecido");
      }

      return result;
    } catch (error) {
      console.error("Erro ao editar atividade:", error);
      throw error;
    }
  },

  async addActivity(formData) {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/add-activity`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Erro desconhecido");
      }

      return result;
    } catch (error) {
      console.error("Erro ao adicionar atividade:", error);
      throw error;
    }
  }
};

// Módulo de formatação para centralizar as funções de formatação
const formatter = {
  currency(value) {
    return `R$ ${Number(value).toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
};

// Utilitário para agrupar atividades por setor
const groupBySector = (activities) => {
  const grouped = activities.reduce((acc, activity) => {
    const sector = activity.sector || 'Sem Setor';
    if (!acc[sector]) {
      acc[sector] = [];
    }
    acc[sector].push(activity);
    return acc;
  }, {});

  // Ordenar setores alfabeticamente e retornar array ordenado
  const sortedSectors = Object.keys(grouped).sort();
  const result = [];
  
  sortedSectors.forEach(sector => {
    // Ordenar atividades dentro do setor por data (mais recente primeiro) ou por ID
    grouped[sector].sort((a, b) => {
      // Primeiro tenta ordenar por data
      if (a.date && b.date && a.date !== '-' && b.date !== '-') {
        const dateA = new Date(a.date.split('/').reverse().join('-'));
        const dateB = new Date(b.date.split('/').reverse().join('-'));
        return dateB - dateA; // Mais recente primeiro
      }
      // Se não houver data válida, ordena por ID (assumindo que ID maior = mais recente)
      return (b.id || 0) - (a.id || 0);
    });
    
    result.push(...grouped[sector]);
  });
  
  return result;
};

// Módulo de UI para gerenciar a interface do usuário
const ui = {
  showLoader() {
    document.getElementById("loader").classList.remove("hidden");
  },

  hideLoader() {
    document.getElementById("loader").classList.add("hidden");
  },

  showSuccessMessage(message) {
    const messageContainer = document.createElement("div");
    messageContainer.innerText = message;
    messageContainer.className = "success-message";
    document.body.appendChild(messageContainer);

    setTimeout(() => {
      messageContainer.remove();
    }, 5000);
  },

  updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
      element.innerText = text;
    }
  },

  showModal(activity) {
    this.updateElementText("modalId", activity.id);
    this.updateElementText("modalActivity", activity.activity);
    this.updateElementText("modalSector", activity.sector || "-");
    this.updateElementText("modalValue", formatter.currency(activity.diego_ana));
    this.updateElementText("modalValue2", formatter.currency(activity.alex_rute));
    
    // Calcula o valor restante se não estiver disponível
    const valorRestante = activity.valor_restante !== undefined ? 
      activity.valor_restante : 
      (activity.total_value || activity.value) - (activity.diego_ana + activity.alex_rute);
    
    this.updateElementText("modalRemainingValue", formatter.currency(valorRestante));
    this.updateElementText("modalTotalValue", formatter.currency(activity.total_value || activity.value));
    this.updateElementText("modalDate", activity.date || "-");

    const modal = document.getElementById("infoModal");
    modal.classList.remove("hidden");
    modal.style.display = "flex";
  },

  showModalpaid(activity) {
    
    this.updateElementText("modalPaidID", activity.id);
    this.updateElementText("modalPaidActivity", activity.activity);
    this.updateElementText("modalPaidSector", activity.sector || "-");
    this.updateElementText("modalPaidValue", formatter.currency(activity.diego_ana));
    this.updateElementText("modalPaidValue2", formatter.currency(activity.alex_rute));
    this.updateElementText("modalPaidTotalValue", formatter.currency(activity.total_value || activity.value));
    this.updateElementText("modalPaidDate", activity.date || "-");

    const modal = document.getElementById("infoModalPaid");
    modal.classList.remove("hidden");
    modal.style.display = "flex";
  },

  hideModalPaid() {
    const modal = document.getElementById("infoModalPaid");
    modal.classList.add("hidden");
    modal.style.display = "none";
  },

  hideModal() {
    const modal = document.getElementById("infoModal");
    modal.classList.add("hidden");
    modal.style.display = "none";
  },

  showDeleteConfirmModal(activityId) {
    const deleteModal = document.getElementById("deleteConfirmModal");
    deleteModal.classList.remove("hidden");
    deleteModal.style.display = "flex";

    // Store activityId for later use when confirmed
    deleteModal.dataset.activityId = activityId;
  },

  hideDeleteConfirmModal() {
    const deleteModal = document.getElementById("deleteConfirmModal");
    deleteModal.classList.add("hidden");
    deleteModal.style.display = "none";
  },

  showEditModal(activity) {
    // Log dos dados da atividade para debug
    console.log("Dados da atividade para edição:", activity);
    
    // Converter data do formato DD/MM/AAAA para AAAA-MM-DD (formato do input date)
    let formattedDate = "";
    if (activity.date && activity.date.trim() !== '-') {
      const dateParts = activity.date.split('/');
      if (dateParts.length === 3) {
        formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`;
      }
    }
    
    // Preencher o formulário com os dados da atividade
    document.getElementById("editActivityId").value = activity.id;
    document.getElementById("editAtividade").value = activity.activity;
    document.getElementById("editValor").value = activity.total_value || activity.value;
    
    // Selecionar o setor correto
    const sectorSelect = document.getElementById("editSetor");
    for (let i = 0; i < sectorSelect.options.length; i++) {
      if (sectorSelect.options[i].value === activity.sector) {
        sectorSelect.selectedIndex = i;
        break;
      }
    }
    
    document.getElementById("editData").value = formattedDate;
    document.getElementById("editDiegoAna").value = activity.diego_ana || 0;
    document.getElementById("editAlexRute").value = activity.alex_rute || 0;
    
    // Mostrar o modal
    const modal = document.getElementById("editActivityModal");
    document.body.classList.add('overflow-hidden'); // Impedir rolagem do body
    modal.classList.remove("hidden");
    modal.style.display = "flex";
  },

  hideEditModal() {
    document.body.classList.remove('overflow-hidden'); // Restaurar rolagem do body
    const modal = document.getElementById("editActivityModal");
    modal.classList.add("hidden");
    modal.style.display = "none";
  },

  confirmAction(message) {
    // The old implementation is no longer used
    // We're using a modal instead of the browser confirm dialog
    return confirm(message);
  }
};

// Módulo de atividades para gerenciar dados relacionados a atividades
const activityManager = {
  async loadActivitiesPending() {
    try {
      const pendingActivities = await api.fetchData("atividades-pendentes");
      const activitiesList = document.getElementById("activitiesList");
      activitiesList.innerHTML = "";

      // Check if pendingActivities exists and is an array
      if (pendingActivities && Array.isArray(pendingActivities)) {
        // Agrupar atividades por setor
        const groupedActivities = groupBySector(pendingActivities);
        
        let currentSector = null;
        groupedActivities.forEach(activity => {
          // Adicionar cabeçalho do setor se mudou
          if (currentSector !== activity.sector) {
            currentSector = activity.sector;
            const sectorHeader = this.createSectorHeader(currentSector || 'Sem Setor');
            activitiesList.appendChild(sectorHeader);
          }
          
          const row = this.createActivityPendingRow(activity);
          activitiesList.appendChild(row);
        });
      } else {
        console.error("Expected an array but got:", typeof pendingActivities, pendingActivities);
        
        // Display an error message in the UI
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td colspan="7" class="py-4 px-4 text-center text-gray-500">
              <i class="fas fa-exclamation-circle mr-2"></i>
              Erro ao carregar atividades pendentes. Por favor, recarregue a página.
          </td>
        `;
        activitiesList.appendChild(tr);
      }
    } catch (error) {
      console.error("Erro ao carregar atividades pendentes:", error);
      
      // Show error in the UI
      const activitiesList = document.getElementById("activitiesList");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td colspan="7" class="py-4 px-4 text-center text-gray-500">
            <i class="fas fa-exclamation-circle mr-2"></i>
            ${error.message || "Erro ao carregar atividades pendentes"}
        </td>
      `;
      activitiesList.appendChild(tr);
    }
  },

  async loadPaidActivities() {
    try {
      const paidActivities = await api.fetchData("atividades-pagas");
      const paidActivitiesList = document.getElementById("paidActivitiesList");
      paidActivitiesList.innerHTML = "";

      if (Array.isArray(paidActivities) && paidActivities.length > 0) {
        // Agrupar atividades pagas por setor
        const groupedActivities = groupBySector(paidActivities);
        
        let currentSector = null;
        groupedActivities.forEach(activity => {
          // Adicionar cabeçalho do setor se mudou
          if (currentSector !== activity.sector) {
            currentSector = activity.sector;
            const sectorHeader = this.createSectorHeader(currentSector || 'Sem Setor');
            paidActivitiesList.appendChild(sectorHeader);
          }
          
          const row = this.createPaidActivityRow(activity);
          paidActivitiesList.appendChild(row);
        });
      } else {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td colspan="6" class="py-4 px-4 text-center text-gray-500">
              <i class="fas fa-info-circle mr-2"></i>
              Nenhuma atividade paga encontrada
          </td>
        `;
        paidActivitiesList.appendChild(tr);
      }
    } catch (error) {
      console.error("Erro ao carregar atividades pagas:", error);
    }
  },

  createSectorHeader(sectorName) {
    const headerRow = document.createElement("tr");
    headerRow.className = "sector-header bg-gray-100 border-t-2 border-gray-300";
    headerRow.innerHTML = `
      <td colspan="7" class="py-3 px-4 font-bold text-gray-800 text-lg bg-gradient-to-r from-blue-50 to-blue-100">
        <i class="fas fa-folder mr-2 text-blue-600"></i>
        ${sectorName}
      </td>
    `;
    return headerRow;
  },

  createPaidActivityRow(activity) {
    const row = document.createElement("tr");
    row.className = "activity-row hover:bg-gray-50";
    row.innerHTML = `
      <td class="py-2 px-4 border-b pl-8 text-gray-600">${activity.sector}</td>
      <td class="py-2 px-4 border-b">${activity.activity}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.total_value)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.diego_ana)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.alex_rute)}</td>
      <td class="py-2 px-4 border-b">${activity.date}</td>
      <td class="py-2 px-4 border-b">
        <button class="bg-blue-500 text-white px-2 py-1 rounded view-details hover:bg-blue-600 transition-colors">Comprovante</button>
      </td>
    `;

    const viewDetailsButton = row.querySelector(".view-details");
    viewDetailsButton.addEventListener("click", () => {
      // Aqui você pode chamar uma função para exibir mais detalhes no modal
      ui.showModalpaid(activity);
    });

    return row;
  },

  createActivityAllRow(activity) {
    const row = document.createElement("tr");
    row.className = "activity-row hover:bg-gray-50";
    // Adicionar o ID da atividade como atributo de dados
    row.setAttribute("data-activity-id", activity.id);
    
    const statusClass = activity.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800';
    const status = activity.status === 'paid' ? 'Concluido' : 'Pendente';
    
    row.innerHTML = `
      <td class="py-2 px-4 border-b pl-8 text-gray-600">${activity.sector}</td>
      <td class="py-2 px-4 border-b">${activity.activity || "-"}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.value)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.diego_ana)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.alex_rute)}</td>
      <td class="py-2 px-4 border-b">${activity.date || "-"}</td>
      <td class="py-2 px-4 border-b">
        <span class="px-3 py-1 text-sm rounded-full font-medium ${statusClass}">
          ${status}
        </span>
      </td>
      <td class="py-2 px-4 border-b">
        <button class="bg-blue-500 text-white px-2 py-1 rounded info-btn hover:bg-blue-600 transition-colors">Comprovante</button>
      </td>
    `;

    const infoButton = row.querySelector(".info-btn");
    infoButton.addEventListener("click", () => {
      if (activity.status === 'paid') {
        ui.showModalpaid(activity);
      } else {
        ui.showModal(activity);
      }
    });

    return row;
  },

  createActivityPendingRow(activity) {
    const row = document.createElement("tr");
    row.className = "activity-row hover:bg-gray-50";
    row.innerHTML = `
      <td class="py-2 px-4 border-b pl-8 text-gray-600">${activity.sector}</td>
      <td class="py-2 px-4 border-b">${activity.activity || "-"}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.total_value)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.diego_ana)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.alex_rute)}</td>
      <td class="py-2 px-4 border-b">${activity.date || "-"}</td>
      <td class="py-2 px-4 border-b">
        <button class="bg-blue-500 text-white px-2 py-1 rounded pagar-btn hover:bg-blue-600 transition-colors">Comprovante</button>
      </td>
    `;

    const pagarButton = row.querySelector(".pagar-btn");
    pagarButton.addEventListener("click", (e) => {
      e.stopPropagation();
      ui.showModal(activity);
    });

    return row;
  },

  async loadAllActivities() {
    try {
      const activities = await api.fetchData("atividades");
      const allActivitiesList = document.getElementById("allActivitiesList");
      allActivitiesList.innerHTML = "";

      if (activities && Array.isArray(activities)) {
        // Agrupar todas as atividades por setor
        const groupedActivities = groupBySector(activities);
        
        let currentSector = null;
        groupedActivities.forEach(activity => {
          // Adicionar cabeçalho do setor se mudou
          if (currentSector !== activity.sector) {
            currentSector = activity.sector;
            const sectorHeader = this.createSectorHeader(currentSector || 'Sem Setor');
            allActivitiesList.appendChild(sectorHeader);
          }
          
          const row = this.createActivityAllRow(activity);
          allActivitiesList.appendChild(row);
        });
      } else {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td colspan="8" class="py-4 px-4 text-center text-gray-500">
              <i class="fas fa-exclamation-circle mr-2"></i>
              Erro ao carregar todas as atividades. Por favor, recarregue a página.
          </td>
        `;
        allActivitiesList.appendChild(tr);
      }
    } catch (error) {
      console.error("Erro ao carregar todas as atividades:", error);
      const allActivitiesList = document.getElementById("allActivitiesList");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td colspan="8" class="py-4 px-4 text-center text-gray-500">
            <i class="fas fa-exclamation-circle mr-2"></i>
            ${error.message || "Erro ao carregar todas as atividades"}
        </td>
      `;
      allActivitiesList.appendChild(tr);
    }
  },

  async loadTotalValue() {
    try {
      const data = await api.fetchData("valor-total");
      ui.updateElementText("totalValue", formatter.currency(data.total));
    } catch (error) {
      console.error("Erro ao carregar o valor total da obra:", error);
    }
  },

  async loadTotalPaid() {
    try {
      const data = await api.fetchData("valor-total-pago");
      ui.updateElementText("valorPagoObra", formatter.currency(data.total_pago));
    } catch (error) {
      console.error("Erro ao carregar o valor total pago:", error);
    }
  },

  async loadDiegoPaid() {
    try {
      const data = await api.fetchData("valor-pago-diego");
      ui.updateElementText("valorPagoDiego", formatter.currency(data.total_pago_diego));
    } catch (error) {
      console.error("Erro ao carregar o valor pago por Diego:", error);
    }
  },

  async loadAlexPaid() {
    try {
      const data = await api.fetchData("valor-pago-alex");
      ui.updateElementText("valorPagoAlex", formatter.currency(data.total_pago_alex));
    } catch (error) {
      console.error("Erro ao carregar o valor pago por Alex:", error);
    }
  },

  async loadPendingActivities() {
    try {
      const pendingActivities = await api.fetchData("atividades-pendentes");
      if (pendingActivities && Array.isArray(pendingActivities)) {
        ui.updateElementText("pendingActivities", pendingActivities.length);
      } else {
        ui.updateElementText("pendingActivities", "0");
        console.error("Expected an array for pending activities but got:", typeof pendingActivities);
      }
    } catch (error) {
      console.error("Erro ao carregar atividades pendentes:", error);
      ui.updateElementText("pendingActivities", "0");
    }
  },

  async loadTotalActivities() {
    try {
      const activities = await api.fetchData("atividades");
      if (activities && Array.isArray(activities)) {
        ui.updateElementText("totalActivities", activities.length);
      } else {
        ui.updateElementText("totalActivities", "0");
        console.error("Expected an array for total activities but got:", typeof activities);
      }
    } catch (error) {
      console.error("Erro ao carregar o total de atividades:", error);
      ui.updateElementText("totalActivities", "0");
    }
  },

  async deleteActivity(id) {
    try {
      await api.deleteActivity(id);
      ui.showSuccessMessage("Atividade deletada com sucesso!");
      this.loadActivitiesPending();
      this.refreshAllData();
    } catch (error) {
      alert("Erro ao deletar atividade: " + error.message);
    }
  },

  async addActivity(formData) {
    try {
      const result = await api.addActivity(formData);
      ui.showSuccessMessage("Atividade adicionada com sucesso!");
      this.refreshAllData();
      document.getElementById("addActivityForm").reset();
      
      // Restaurar o estado do botão após adicionar com sucesso
      const addButton = document.getElementById("addActivityButton");
      if (addButton) {
        addButton.innerHTML = `<i class="fas fa-plus mr-2"></i>Adicionar`;
        addButton.disabled = false;
        addButton.classList.remove('opacity-75');
      }
    } catch (error) {
      alert("Erro ao adicionar atividade: " + error.message);
      
      // Restaurar o estado do botão em caso de erro
      const addButton = document.getElementById("addActivityButton");
      if (addButton) {
        addButton.innerHTML = `<i class="fas fa-plus mr-2"></i>Adicionar`;
        addButton.disabled = false;
        addButton.classList.remove('opacity-75');
      }
    }
  },

  filterActivities(searchText) {
    const activitiesList = document.getElementById('activitiesList');
    const rows = activitiesList.getElementsByTagName('tr');
    const searchLower = searchText.toLowerCase();

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      
      // Pular cabeçalhos de setor
      if (row.classList.contains('sector-header')) {
        continue;
      }
      
      const cells = row.getElementsByTagName('td');
      let match = false;

      for (let j = 0; j < cells.length; j++) {
        if (cells[j].textContent.toLowerCase().includes(searchLower)) {
          match = true;
          break;
        }
      }

      row.style.display = match ? '' : 'none';
    }
    
    // Mostrar/ocultar cabeçalhos de setor baseado nas atividades visíveis
    this.toggleSectorHeaders('activitiesList');
  },

  filterpaidActivities(searchText) {
    const paidActivitiesList = document.getElementById('paidActivitiesList');
    const rows = paidActivitiesList.getElementsByTagName('tr');
    const searchLower = searchText.toLowerCase();

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      
      // Pular cabeçalhos de setor
      if (row.classList.contains('sector-header')) {
        continue;
      }
      
      const cells = row.getElementsByTagName('td');
      let match = false;

      for (let j = 0; j < cells.length; j++) {
        if (cells[j].textContent.toLowerCase().includes(searchLower)) {
          match = true;
          break;
        }
      }

      row.style.display = match ? '' : 'none';
    }
    
    // Mostrar/ocultar cabeçalhos de setor baseado nas atividades visíveis
    this.toggleSectorHeaders('paidActivitiesList');
  },

  filterAllActivities(searchText) {
    const allActivitiesList = document.getElementById('allActivitiesList');
    const rows = allActivitiesList.getElementsByTagName('tr');
    const searchLower = searchText.toLowerCase();

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      
      // Pular cabeçalhos de setor
      if (row.classList.contains('sector-header')) {
        continue;
      }
      
      const cells = row.getElementsByTagName('td');
      let match = false;

      for (let j = 0; j < cells.length; j++) {
        if (cells[j].textContent.toLowerCase().includes(searchLower)) {
          match = true;
          break;
        }
      }

      row.style.display = match ? '' : 'none';
    }
    
    // Mostrar/ocultar cabeçalhos de setor baseado nas atividades visíveis
    this.toggleSectorHeaders('allActivitiesList');
  },

  toggleSectorHeaders(listId) {
    const list = document.getElementById(listId);
    const rows = list.getElementsByTagName('tr');
    
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      
      if (row.classList.contains('sector-header')) {
        // Verificar se há atividades visíveis após este cabeçalho
        let hasVisibleActivities = false;
        
        for (let j = i + 1; j < rows.length; j++) {
          const nextRow = rows[j];
          
          // Se encontrou outro cabeçalho, para de procurar
          if (nextRow.classList.contains('sector-header')) {
            break;
          }
          
          // Se encontrou uma atividade visível, marca como verdadeiro
          if (nextRow.style.display !== 'none') {
            hasVisibleActivities = true;
            break;
          }
        }
        
        // Mostrar/ocultar o cabeçalho baseado na existência de atividades visíveis
        row.style.display = hasVisibleActivities ? '' : 'none';
      }
    }
  },

  async refreshAllData() {
    ui.showLoader();
    try {
      await Promise.all([
        this.loadTotalActivities(),
        this.loadPendingActivities(),
        this.loadActivitiesPending(),
        this.loadAllActivities(),
        this.loadTotalPaid(),
        this.loadTotalValue(),
        this.loadDiegoPaid(),
        this.loadAlexPaid(),
      ]);
    } catch (error) {
      console.error("Erro ao atualizar os dados:", error);
    } finally {
      ui.hideLoader();
    }
  },

  async editActivity(formData) {
    try {
      const id = formData.get('id');
      ui.showLoader();
      
      const result = await api.editActivity(id, formData);
      ui.showSuccessMessage("Atividade atualizada com sucesso!");
      ui.hideEditModal();
      ui.hideModal();
      
      // Garantir atualização completa da página
      await this.refreshAllData();
      await this.loadPaidActivities();
      await this.loadActivitiesPending();
      await this.loadAllActivities();
      
      return result;
    } catch (error) {
      alert("Erro ao editar atividade: " + error.message);
    } finally {
      ui.hideLoader();
    }
  }
};

// Event Listeners - Inicialização e configuração de eventos
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar dados
  activityManager.refreshAllData();
  activityManager.loadPaidActivities();
  activityManager.loadActivitiesPending();
  activityManager.loadAllActivities();

  // Configurar evento do botão de fechar modal
  document.getElementById("closeModal").addEventListener("click", () => {
    ui.hideModal();
  });

  // Configurar evento do botão de excluir
  document.getElementById("btnDelete").addEventListener("click", () => {
    const activityId = document.getElementById("modalId").innerText;
    ui.showDeleteConfirmModal(activityId);
  });

  // Configurar evento do botão de excluir para atividades pagas
  document.getElementById("btnDeletePaid").addEventListener("click", () => {
    const activityId = document.getElementById("modalPaidID").innerText;
    ui.showDeleteConfirmModal(activityId);
  });

  // Configurar eventos para os botões do modal de confirmação de exclusão
  document.getElementById("confirmDelete").addEventListener("click", async () => {
    const activityId = document.getElementById("deleteConfirmModal").dataset.activityId;
    await activityManager.deleteActivity(activityId);
    ui.hideDeleteConfirmModal();
    ui.hideModal();
    ui.hideModalPaid();
  });

  document.getElementById("cancelDelete").addEventListener("click", () => {
    ui.hideDeleteConfirmModal();
  });

  // Configurar evento do formulário de adicionar atividade
  document.getElementById("addActivityForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    // Debug log dos dados do formulário
    for (let pair of formData.entries()) {
      console.log(pair[0] + ': ' + pair[1]);
    }

    await activityManager.addActivity(formData);
  });

  // Configurar eventos de busca
  document.getElementById('searchBtn').addEventListener('click', () => {
    const searchInput = document.getElementById('searchInput').value;
    activityManager.filterActivities(searchInput);
  });

  document.getElementById('searchPaidBtn').addEventListener('click', () => {
    const searchInput = document.getElementById('searchPaidInput').value;
    activityManager.filterpaidActivities(searchInput);
  });

  document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('searchBtn').click();
    }
  });

  document.getElementById('searchPaidInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('searchPaidBtn').click();
    }
  });

  // Configurar eventos de busca para todas as atividades
  document.getElementById('searchAllBtn').addEventListener('click', () => {
    const searchInput = document.getElementById('searchAllInput').value;
    activityManager.filterAllActivities(searchInput);
  });

  document.getElementById('searchAllInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('searchAllBtn').click();
    }
  });

  // Configurar evento do botão de editar
  document.getElementById("btnEdit").addEventListener("click", () => {
    const activityId = document.getElementById("modalId").innerText;
    
    // Usar os dados já disponíveis no modal, sem fazer chamada API
    const selectedActivity = {
      id: activityId,
      activity: document.getElementById("modalActivity").innerText,
      sector: document.getElementById("modalSector").innerText,
      value: parseFloat(document.getElementById("modalTotalValue").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      total_value: parseFloat(document.getElementById("modalTotalValue").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      diego_ana: parseFloat(document.getElementById("modalValue").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      alex_rute: parseFloat(document.getElementById("modalValue2").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      date: document.getElementById("modalDate").innerText
    };
    
    ui.showEditModal(selectedActivity);
  });

  // Configurar evento do botão de editar para atividades pagas
  document.getElementById("btnEditPaid").addEventListener("click", () => {
    const activityId = document.getElementById("modalPaidID").innerText;
    
    // Usar os dados já disponíveis no modal, sem fazer chamada API
    const selectedActivity = {
      id: activityId,
      activity: document.getElementById("modalPaidActivity").innerText,
      sector: document.getElementById("modalPaidSector").innerText,
      value: parseFloat(document.getElementById("modalPaidTotalValue").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      total_value: parseFloat(document.getElementById("modalPaidTotalValue").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      diego_ana: parseFloat(document.getElementById("modalPaidValue").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      alex_rute: parseFloat(document.getElementById("modalPaidValue2").innerText.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()),
      date: document.getElementById("modalPaidDate").innerText
    };
    
    ui.showEditModal(selectedActivity);
  });

  // Configurar eventos para o modal de edição
  document.getElementById("cancelEdit").addEventListener("click", () => {
    ui.hideEditModal();
  });
  
  document.getElementById("confirmEdit").addEventListener("click", async () => {
    try {
      ui.hideEditModal();
      ui.hideModalPaid();
      ui.hideModal();
      ui.showLoader();
      
      const form = document.getElementById("editActivityForm");
      const formData = new FormData(form);
      
      // Log para debug
      console.log("Dados do formulário de edição:");
      for (const pair of formData.entries()) {
        console.log(pair[0] + ": " + pair[1]);
      }
      
      // Validações básicas
      const valor = formData.get('valor');
      if (valor && parseFloat(valor) <= 0) {
        alert("O valor total deve ser maior que zero.");
        return;
      }
      
      const diegoAna = formData.get('diego_ana');
      if (diegoAna && parseFloat(diegoAna) < 0) {
        alert("O valor pago por Diego-Ana não pode ser negativo.");
        return;
      }
      
      const alexRute = formData.get('alex_rute');
      if (alexRute && parseFloat(alexRute) < 0) {
        alert("O valor pago por Alex-Rute não pode ser negativo.");
        return;
      }
      
      await activityManager.editActivity(formData);
    } catch (error) {
      console.error("Erro ao processar edição:", error);
      alert("Ocorreu um erro ao editar a atividade: " + error.message);
    } finally {
      ui.hideLoader();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  // Seleciona todos os elementos de aba
  const tabs = document.querySelectorAll('.tab');

  // Adiciona evento de clique para cada aba
  tabs.forEach(tab => {
    tab.addEventListener('click', function () {
      // Remove a classe active de todas as abas
      tabs.forEach(t => t.classList.remove('active'));

      // Adiciona a classe active na aba clicada
      this.classList.add('active');

      // Oculta todos os conteúdos de aba
      const tabContents = document.querySelectorAll('.tab-content');
      tabContents.forEach(content => content.classList.remove('active'));

      // Mostra o conteúdo correspondente à aba clicada
      const tabId = this.getAttribute('data-tab');
      document.getElementById(`${tabId}-tab`).classList.add('active');
    });
  });
});

document.getElementById("closeModalPaid").addEventListener("click", () => {
  ui.hideModalPaid();
});