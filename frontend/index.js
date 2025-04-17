const API_URL = "http://localhost:8000";


// Função para carregar atividades
async function loadActivities() {
    try {
        const response = await fetch(`${API_URL}/atividades-pendentes`);
        const pendingActivities = await response.json();

        const activitiesList = document.getElementById("activitiesList");
        activitiesList.innerHTML = "";

        if (Array.isArray(pendingActivities)) {
            pendingActivities.forEach(activity => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td class="py-2 px-4 border-b">${activity.id}</td>
                    <td class="py-2 px-4 border-b">${activity.activity}</td>
                    <td class="py-2 px-4 border-b">${activity.sector || "-"}</td>
                    <td class="py-2 px-4 border-b">R$ ${Number(activity.valor_restante).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="py-2 px-4 border-b">R$ ${Number(activity.total_value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="py-2 px-4 border-b">${activity.date || "-"}</td>
                    <td class="py-2 px-4 border-b">
                        <button class="bg-green-500 text-white px-2 py-1 rounded">Pagar</button>
                    </td>
                `;

                // Adicionar evento de clique para exibir o modal
                row.addEventListener("click", () => showModal(activity));

                activitiesList.appendChild(row);
            });
        } else {
            console.error("Expected an array but got:", pendingActivities);
        }
    } catch (error) {
        console.error("Erro ao carregar atividades pendentes:", error);
    }
}

function showModal(activity) {
    document.getElementById("modalId").innerText = activity.id;
    document.getElementById("modalActivity").innerText = activity.activity;
    document.getElementById("modalSector").innerText = activity.sector || "-";
    document.getElementById("modalValue").innerText = `R$ ${Number(activity.diego_ana).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("modalValue2").innerText = `R$ ${Number(activity.alex_rute).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("modalRemainingValue").innerText = `R$ ${Number(activity.valor_restante).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("modalTotalValue").innerText = `R$ ${Number(activity.total_value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("modalDate").innerText = activity.date || "-";

    // Exibir o modal
    const modal = document.getElementById("infoModal");
    modal.classList.remove("hidden");
    modal.style.display = "flex"; // Exibir o modal
}

// Função para fechar o modal
document.getElementById("closeModal").addEventListener("click", () => {
    const modal = document.getElementById("infoModal");
    modal.classList.add("hidden");
    modal.style.display = "none"; // Ocultar o modal
});
async function loadTotalValue() {
    try {
        const response = await fetch(`${API_URL}/valor-total`);
        const data = await response.json();
        const totalValueElement = document.getElementById("totalValue");
        totalValueElement.innerText = `R$ ${Number(data.total).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    } catch (error) {
        console.error("Erro ao carregar o valor total da obra:", error);
    }
}

// Atualizar o valor total da obra ao carregar a página
document.addEventListener("DOMContentLoaded", () => {
    loadTotalValue();
});


// Função para adicionar uma nova atividade
document.getElementById("addActivityForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch(`${API_URL}/add-activity`, {
        method: "POST",
        body: formData,
    });

    if (response.ok) {
        alert("Atividade adicionada com sucesso!");
        loadActivities();
    } else {
        alert("Erro ao adicionar atividade.");
    }
});

// Função para processar comprovante
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("receiptFile");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const response = await fetch(`${API_URL}/processar-comprovante`, {
        method: "POST",
        body: formData,
    });

    if (response.ok) {
        const data = await response.json();
        document.getElementById("extractedValue").innerText = data.valor || "-";
        document.getElementById("extractedDate").innerText = data.data || "-";
        document.getElementById("extractedName").innerText = data.nome || "-";
    } else {
        alert("Erro ao processar comprovante.");
    }
});

// Carregar atividades ao carregar a página
document.addEventListener("DOMContentLoaded", loadActivities);

async function loadPendingActivities() {
    try {
        const response = await fetch(`${API_URL}/atividades-pendentes`);
        const pendingActivities = await response.json();
        document.getElementById("pendingActivities").innerText = pendingActivities.length;
    } catch (error) {
        console.error("Erro ao carregar atividades pendentes:", error);
    }
}

// Atualizar a quantidade de atividades pendentes ao carregar a página
document.addEventListener("DOMContentLoaded", () => {
    loadPendingActivities();
    loadActivities(); // Já existente
});


async function loadTotalActivities() {
    try {
        const response = await fetch(`${API_URL}/atividades`);
        const activities = await response.json();
        document.getElementById("totalActivities").innerText = activities.length;
    } catch (error) {
        console.error("Erro ao carregar o total de atividades:", error);
    }
}

// Atualizar o total de atividades ao carregar a página
document.addEventListener("DOMContentLoaded", () => {
    loadTotalActivities();
    loadPendingActivities(); // Já existente
    loadActivities(); // Já existente
});