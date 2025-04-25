const URL_api = "http://localhost:8000"; // URL do seu backend

document.getElementById("pagamento").addEventListener("click", () => {
    // Fechar o modal de informações
    const infoModal = document.getElementById("infoModal");
    infoModal.classList.add("hidden");
    infoModal.style.display = "none";

    // Abrir o modal de pagamento
    const paymentModal = document.getElementById("paymentModal");
    paymentModal.classList.remove("hidden");
    paymentModal.style.display = "flex";

    // Garantir que o modal abra no topo
    const modalContent = document.querySelector("#paymentModal .modal-content");
    if (modalContent) {
        modalContent.scrollTop = 0; // Define a rolagem para o topo
    }

    // Preencher informações no modal de pagamento (opcional)
    const activity = document.getElementById("modalActivity").innerText;
    const sector = document.getElementById("modalSector").innerText;
    const pendingValue = document.getElementById("modalRemainingValue").innerText;

    document.getElementById("paymentModalActivity").innerText = activity;
    document.getElementById("paymentModalSector").innerText = sector;
    document.getElementById("paymentModalPending").innerText = pendingValue;
    document.getElementById("summaryActivity").innerText = activity;
    document.getElementById("summaryValue").innerText = pendingValue;
});

document.getElementById("closePaymentModal").addEventListener("click", () => {
    const paymentModal = document.getElementById("paymentModal");
    paymentModal.classList.add("hidden");
    paymentModal.style.display = "none";
});

async function extrairDadosComprovante() {
    const comprovante = document.getElementById("receiptImage").files[0];

    if (!comprovante) {
        alert("Por favor, selecione um comprovante.");
        return;
    }

    const formData = new FormData();
    formData.append("file", comprovante);

    console.log([...formData.entries()]); // Verifique se o arquivo está sendo anexado corretamente

    try {
        // Extrair dados do comprovante
        const response = await fetch(`${URL_api}/process-receipt`, {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            console.log("Dados extraídos do comprovante:", result);

            // Preencher os campos do modal com os dados extraídos
            document.getElementById("summaryValue").innerText = result.value || "0,00";

            // Registrar o pagamento automaticamente
            await registrarPagamento(result);
        } else {
            console.error("Erro ao fazer upload do comprovante:", response.statusText);
        }
    } catch (error) {
        console.error("Erro ao enviar o arquivo:", error);
    }
}

async function registrarPagamento(dadosComprovante) {
    const atividade = document.getElementById("paymentModalActivity").textContent;
    const setor = document.getElementById("paymentModalSector").textContent || null;
    const valor = dadosComprovante.value;
    const pagador = "Diego-Ana"; // Ou Alex-Rute, dependendo do contexto
    const data = dadosComprovante.date || new Date().toISOString().split("T")[0]; // Data extraída ou data atual

    const paymentData = {
        activity: atividade,
        sector: setor,
        payer: pagador,
        value: valor,
        date: data,
    };

    try {
        const response = await fetch(`${URL_api}/register-payment`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(paymentData),
        });

        if (response.ok) {
            const result = await response.json();
            console.log("Pagamento registrado com sucesso:", result);
            alert("Pagamento registrado com sucesso!");
        } else {
            console.error("Erro ao registrar o pagamento:", response.statusText);
        }
    } catch (error) {
        console.error("Erro ao registrar o pagamento:", error);
    }
}

const btnPagar = document.getElementById("confirmPayment");
btnPagar.addEventListener("click", async () => {
    extrairDadosComprovante();
});


document.getElementById("receiptImage").addEventListener("change", function (event) {
    const file = event.target.files[0]; // Obtém o arquivo selecionado
    const preview = document.getElementById("receiptPreview"); // Seleciona o elemento <img>
    const placeholder = document.querySelector(".image-upload-placeholder"); // Seleciona o placeholder

    if (file) {
        const reader = new FileReader();

        // Quando o arquivo for carregado, atualiza o src da imagem
        reader.onload = function (e) {
            preview.src = e.target.result; // Define o src da imagem
            preview.style.display = "block"; // Mostra a imagem
            placeholder.style.display = "none"; // Esconde o placeholder
        };

        reader.readAsDataURL(file); // Lê o arquivo como uma URL de dados
    } else {
        // Caso nenhum arquivo seja selecionado, restaura o estado original
        preview.src = "";
        preview.style.display = "none";
        placeholder.style.display = "flex";
    }
});
