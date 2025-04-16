const API_URL = "http://localhost:8000";
console.log("API_URL:", API_URL);

// Função para carregar atividades
async function loadActivities() {
    const response = await fetch(`${API_URL}/atividades`);
    const activities = await response.json();
    console.log("Activities response:", activities); // Verifique a resposta no console
    const activitiesList = document.getElementById("activitiesList");
    activitiesList.innerHTML = "";

    if (Array.isArray(activities)) {
        activities.forEach(activity => {
            activitiesList.innerHTML += `
        <tr>
            <td class="py-2 px-4 border-b">${activity.id}</td>
            <td class="py-2 px-4 border-b">${activity.activity}</td>
            <td class="py-2 px-4 border-b">${activity.sector}</td>
            <td class="py-2 px-4 border-b">R$ ${activity.value}</td>
            <td class="py-2 px-4 border-b">
                <button class="bg-green-500 text-white px-2 py-1 rounded">Pagar</button>
            </td>
        </tr>
    `;
        });
    } else {
        console.error("Expected an array but got:", activities);
    }
}

// Função para adicionar uma nova atividade
document.getElementById("addActivityForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch(`${API_URL}/adicionar-atividade`, {
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