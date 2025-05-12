
const API_URL = "http://localhost:8000";


const api = {
  async fetchData(endpoint) {
    try {
      const response = await fetch(`${API_URL}/${endpoint}`);
      return await response.json();
    } catch (error) {
      console.error(`Erro ao buscar dados de ${endpoint}:`, error);
      throw error;
    }
  },

  async deleteActivity(id) {
    try {
      const response = await fetch(`${API_URL}/delete-activity/${id}`, {
        method: "DELETE",
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

  async addActivity(formData) {
    try {
      const response = await fetch(`${API_URL}/add-activity`, {
        method: "POST",
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
    this.updateElementText("modalRemainingValue", formatter.currency(activity.valor_restante));
    this.updateElementText("modalTotalValue", formatter.currency(activity.total_value));
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
    this.updateElementText("modalPaidTotalValue", formatter.currency(activity.total_value));
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

  confirmAction(message) {
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

      if (Array.isArray(pendingActivities)) {
        pendingActivities.forEach(activity => {
          const row = this.createActivityRow(activity);
          activitiesList.appendChild(row);
        });
      } else {
        console.error("Expected an array but got:", pendingActivities);
      }
    } catch (error) {
      console.error("Erro ao carregar atividades pendentes:", error);
    }
  },

  async loadPaidActivities() {
    try {
      const paidActivities = await api.fetchData("atividades-pagas");
      const paidActivitiesList = document.getElementById("paidActivitiesList");
      paidActivitiesList.innerHTML = "";

      if (Array.isArray(paidActivities) && paidActivities.length > 0) {
        paidActivities.forEach(activity => {
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

  createPaidActivityRow(activity) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="py-2 px-4 border-b">${activity.activity}</td>
      <td class="py-2 px-4 border-b">${activity.sector}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.total_value)}</td>
      <td class="py-2 px-4 border-b">${activity.date}</td>
      <td class="py-2 px-4 border-b">
        <button class="bg-blue-500 text-white px-2 py-1 rounded view-details">Informação</button>
      </td>
    `;

    const viewDetailsButton = row.querySelector(".view-details");
    viewDetailsButton.addEventListener("click", () => {
      // Aqui você pode chamar uma função para exibir mais detalhes no modal
      ui.showModalpaid(activity);
    });

    return row;
  },


  createActivityRow(activity) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="py-2 px-4 border-b">${activity.activity}</td>
      <td class="py-2 px-4 border-b">${activity.sector || "-"}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.valor_restante)}</td>
      <td class="py-2 px-4 border-b">${formatter.currency(activity.total_value)}</td>
      <td class="py-2 px-4 border-b">${activity.date || "-"}</td>
      <td class="py-2 px-4 border-b">
        <button class="bg-blue-500 text-white px-2 py-1 rounded pagar-btn">Informação</button>
      </td>
    `;

    const pagarButton = row.querySelector(".pagar-btn");
    pagarButton.addEventListener("click", (e) => {
      e.stopPropagation();
      ui.showModal(activity);
    });

    return row;
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
      ui.updateElementText("pendingActivities", pendingActivities.length);
    } catch (error) {
      console.error("Erro ao carregar atividades pendentes:", error);
    }
  },

  async loadTotalActivities() {
    try {
      const activities = await api.fetchData("atividades");
      ui.updateElementText("totalActivities", activities.length);
    } catch (error) {
      console.error("Erro ao carregar o total de atividades:", error);
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
      formData.reset(); // Limpa o formulário após adicionar a atividade
    } catch (error) {
      alert("Erro ao adicionar atividade: " + error.message);
    }
  },

  filterActivities(searchText) {
    const activitiesList = document.getElementById('activitiesList');
    const rows = activitiesList.getElementsByTagName('tr');
    const searchLower = searchText.toLowerCase();

    for (let i = 0; i < rows.length; i++) {
      const cells = rows[i].getElementsByTagName('td');
      let match = false;

      for (let j = 0; j < cells.length; j++) {
        if (cells[j].textContent.toLowerCase().includes(searchLower)) {
          match = true;
          break;
        }
      }

      rows[i].style.display = match ? '' : 'none';
    }
  },

  filterpaidActivities(searchText) {
    const paidActivitiesList = document.getElementById('paidActivitiesList');
    const rows = paidActivitiesList.getElementsByTagName('tr');
    const searchLower = searchText.toLowerCase();

    for (let i = 0; i < rows.length; i++) {
      const cells = rows[i].getElementsByTagName('td');
      let match = false;

      for (let j = 0; j < cells.length; j++) {
        if (cells[j].textContent.toLowerCase().includes(searchLower)) {
          match = true;
          break;
        }
      }

      rows[i].style.display = match ? '' : 'none';
    }
  },

  async refreshAllData() {
    ui.showLoader();
    try {
      await Promise.all([
        this.loadTotalActivities(),
        this.loadPendingActivities(),
        this.loadActivitiesPending(),
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
  }
};

// Event Listeners - Inicialização e configuração de eventos
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar dados
  activityManager.refreshAllData();
  activityManager.loadPaidActivities();
  activityManager.loadActivitiesPending();

  // Configurar evento do botão de fechar modal
  document.getElementById("closeModal").addEventListener("click", () => {
    ui.hideModal();
  });

  // Configurar evento do botão de excluir
  document.getElementById("btnDelete").addEventListener("click", async () => {
    const activityId = document.getElementById("modalId").innerText;

    if (ui.confirmAction("Tem certeza que deseja deletar esta atividade?")) {
      await activityManager.deleteActivity(activityId);
      ui.hideModal();
    }
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