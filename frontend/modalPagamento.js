



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

async function extrairDadosComprovante () {
    const comprovante = document.getElementById("receiptImage").files[0];

    if (!comprovante) {
        alert("Por favor, selecione um comprovante.");
        return; 
    }
    
    const formData = new FormData();
    formData.append("comprovante", comprovante);

    try {
        const response = await fetch("/process-receipt", {
            method: "POST",
            body: formData
            
        });
        if (response.ok) { 
            const result = await response.json();
            console.log("Upload bem sucedido:" , result);
        }else{
            console.error("Erro ao fazer upload do comprovante:", response.statusText);
        }
    }catch (error) {
        console.error("Erro ao enviar o arquivo :", error);
    }
}

const btnPagar = document.getElementById("confirmPayment");
btnPagar.addEventListener("click", async () => {
    extrairDadosComprovante();
})


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
