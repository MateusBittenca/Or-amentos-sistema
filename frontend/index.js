const API_URL = "http://localhost:8000";

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
                    <td class="py-2 px-4 border-b">${activity.activity}</td>
                    <td class="py-2 px-4 border-b">${activity.sector || "-"}</td>
                    <td class="py-2 px-4 border-b">R$ ${Number(activity.valor_restante).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="py-2 px-4 border-b">R$ ${Number(activity.total_value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="py-2 px-4 border-b">${activity.date || "-"}</td>
                    <td class="py-2 px-4 border-b">
                        <button class="bg-blue-500 text-white px-2 py-1 rounded pagar-btn">Informação</button>
                    </td>
                `;

                // Add click event to the "Pagar" button
                const pagarButton = row.querySelector(".pagar-btn");
                pagarButton.addEventListener("click", (e) => {
                    e.stopPropagation(); // Prevent triggering the row click event
                    showModal(activity);
                });

                activitiesList.appendChild(row);
            });
        } else {
            console.error("Expected an array but got:", pendingActivities);
        }
    } catch (error) {
        console.error("Erro ao carregar atividades pendentes:", error);
    }
}


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

async function valorTotalPago() {
    try {
        const response = await fetch(`${API_URL}/valor-total-pago`);
        const data = await response.json();
        const totalValueElement = document.getElementById("valorPagoObra");
        totalValueElement.innerText = `R$ ${Number(data.total_pago).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    } catch (error) {
        console.error("Erro ao carregar o valor total pago:", error);
    }
}

async function valorPagoDiego() {
    try {
        const response = await fetch(`${API_URL}/valor-pago-diego`);
        const data = await response.json();
        const totalValueElement = document.getElementById("valorPagoDiego");
        totalValueElement.innerText = `R$ ${Number(data.total_pago_diego).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    } catch (error) {
        console.error("Erro ao carregar o valor pago por Diego:", error);
    }
}

async function valorPagoAlex() {
    try {
        const response = await fetch(`${API_URL}/valor-pago-alex`);
        const data = await response.json();
        const totalValueElement = document.getElementById("valorPagoAlex");
        totalValueElement.innerText = `R$ ${Number(data.total_pago_alex).toLocaleString("pt-BR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    } catch (error) {
        console.error("Erro ao carregar o valor pago por Alex:", error);
    }
}

async function loadPendingActivities() {
    try {
        const response = await fetch(`${API_URL}/atividades-pendentes`);
        const pendingActivities = await response.json();
        document.getElementById("pendingActivities").innerText = pendingActivities.length;
    } catch (error) {
        console.error("Erro ao carregar atividades pendentes:", error);
    }
}

async function loadTotalActivities() {
    try {
        const response = await fetch(`${API_URL}/atividades`);
        const activities = await response.json();
        document.getElementById("totalActivities").innerText = activities.length;
    } catch (error) {
        console.error("Erro ao carregar o total de atividades:", error);
    }
}

async function deleteAtividade(id) {
    try {
        const response = await fetch(`${API_URL}/delete-activity/${id}`, {
            method: "DELETE",
        });
        if (response.ok) {
            console.log("Atividade deletada com sucesso:", id);
            alert("Atividade deletada com sucesso!");
            loadActivities(); // Recarregar atividades após deletar
        } else {
            const result = await response.json();
            alert("Erro ao deletar atividade: " + (result.detail || "Unknown error"));
        }
    } catch (error) {
        console.error("Erro ao deletar atividade:", error);
        alert("Erro ao deletar atividade: " + error.message);
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

document.getElementById("btnDelete").addEventListener("click", async () => {
    const activityId = document.getElementById("modalId").innerText;
    if (confirm("Tem certeza que deseja deletar esta atividade?")) {
        await deleteAtividade(activityId);
        const modal = document.getElementById("infoModal");
        modal.classList.add("hidden");
        modal.style.display = "none"; // Ocultar o modal
    }
}
);

function showLoader() {
    const loader = document.getElementById("loader");
    loader.classList.remove("hidden");
}

function hideLoader() {
    const loader = document.getElementById("loader");
    loader.classList.add("hidden");
}

// Função para fechar o modal
document.getElementById("closeModal").addEventListener("click", () => {
    const modal = document.getElementById("infoModal");
    modal.classList.add("hidden");
    modal.style.display = "none"; // Ocultar o modal
});

// Função para adicionar uma nova atividade
document.getElementById("addActivityForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    // Debug log of form data
    console.log("Submitting form data:");
    for (let pair of formData.entries()) {
        console.log(pair[0] + ': ' + pair[1]);
    }

    const response = await fetch(`${API_URL}/add-activity`, {
        method: "POST",
        body: formData,
    });

    const result = await response.json();
    console.log("Response:", result);

    if (response.ok) {
        console.log("Atividade adicionada com sucesso:", result);
        alert("Atividade adicionada com sucesso!");
        loadActivities(); // Recarregar atividades após adicionar

    } else {
        alert("Erro ao adicionar atividade: " + (result.detail || "Unknown error"));
    }

});

//Sistema de busca
document.getElementById('searchBtn').addEventListener('click', function () {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const activitiesList = document.getElementById('activitiesList');
    const rows = activitiesList.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let match = false;

        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().includes(searchInput)) {
                match = true;
                break;
            }
        }

        rows[i].style.display = match ? '' : 'none';
    }
});

document.getElementById('searchInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        document.getElementById('searchBtn').click();
    }
});





// Atualizar o total de atividades ao carregar a página
document.addEventListener("DOMContentLoaded", async () => {
    showLoader(); // Mostrar o loader ao carregar a página
    try {
        await Promise.all([
            loadTotalActivities(),
            loadPendingActivities(),
            loadActivities(),
            valorTotalPago(),
            loadTotalValue(),
            valorPagoDiego(),
            valorPagoAlex(),
        ]);
    } catch (error) {
        console.error("Erro ao carregar os dados iniciais:", error);
    } finally {
        hideLoader(); // Esconder o loader após carregar todos os dados
    }
});

