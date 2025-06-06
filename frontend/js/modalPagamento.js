const URL_api = "https://or-amentos-sistema.onrender.com"; // URL do seu backend
const successMessage = document.getElementById("sucessMessage");

document.getElementById("pagamento").addEventListener("click", () => {
   
    const infoModal = document.getElementById("infoModal");
    infoModal.classList.add("hidden");
    infoModal.style.display = "none";

    const paymentModal = document.getElementById("paymentModal");
    paymentModal.classList.remove("hidden");
    paymentModal.style.display = "flex";

    const modalContent = document.querySelector("#paymentModal .modal-content");
    if (modalContent) {
        modalContent.scrollTop = 0;
    }

    const activity = document.getElementById("modalActivity").innerText;
    const sector = document.getElementById("modalSector").innerText;
    const pendingValue = document.getElementById("modalRemainingValue").innerText;


    document.getElementById("paymentModalActivity").innerText = activity;
    document.getElementById("paymentModalSector").innerText = sector;
    document.getElementById("paymentModalPending").innerText = pendingValue;
});

document.getElementById("closePaymentModal").addEventListener("click", () => {
    const paymentModal = document.getElementById("paymentModal");
    paymentModal.classList.add("hidden");
    paymentModal.style.display = "none";
});

// Função para mostrar mensagem de sucesso
function showSuccessMessage(message) {
    const messageContainer = document.createElement("div");
    messageContainer.innerText = message;
    messageContainer.className = "success-message";
    document.body.appendChild(messageContainer);

    setTimeout(() => {
        messageContainer.remove();
    }, 5000);
}

async function extrairDadosComprovante() {
    const comprovante = document.getElementById("receiptImage").files[0];

    if (!comprovante) {
        alert("Por favor, selecione um comprovante.");
        console.error("Nenhum comprovante selecionado.");
        return;
    }

    const formData = new FormData();
    formData.append("file", comprovante);

    console.log("Enviando comprovante para extração:", [...formData.entries()]);

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${URL_api}/process-receipt`, {
            method: "POST",
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData,
        });

        console.log("Resposta da extração do comprovante:", response);

        if (response.ok) {
            const result = await response.json();
            console.log("Dados extraídos do comprovante:", result);

            await registrarPagamento(result);
        } else {
            console.error("Erro ao fazer upload do comprovante:", response.status, response.statusText);
        }
    } catch (error) {
        console.error("Erro ao enviar o arquivo:", error);
    }
}

async function registrarPagamento(dadosComprovante) {
    const atividade = document.getElementById("paymentModalActivity").textContent;
    const setor = document.getElementById("paymentModalSector").textContent || null;
    const valor = dadosComprovante.value
        .replace('R$', '') // Remove o símbolo de moeda
        .replace(/\./g, '') // Remove separadores de milhar
        .replace(',', '.') // Substitui vírgula por ponto (formato numérico)
        .trim();
    const data = dadosComprovante.date || new Date().toISOString().split("T")[0];

    const payerOptions = document.querySelectorAll('input[name="payer"]');
    let pagador = "";
    payerOptions.forEach(option => {
        if (option.checked) {
            pagador = option.value;
        }
    });

    if (!pagador) {
        alert("Por favor, selecione um pagador.");
        // Restaurar o estado do botão em caso de erro
        const btnPagar = document.getElementById("confirmPayment");
        btnPagar.innerHTML = '<i class="fas fa-check-circle"></i> Confirmar Pagamento';
        btnPagar.disabled = false;
        btnPagar.classList.remove('opacity-75');
        return false;
    }

    const paymentData = {
        activity: atividade,
        sector: setor || null,
        payer: pagador,
        value: valor,
        date: data,
    };

    console.log("Dados do pagamento formatados:", paymentData);

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${URL_api}/register-payment`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(paymentData),
        });

      
        if (response.ok) {
            const result = await response.json();
            console.log("Pagamento registrado com sucesso:", result);
            
            // Alterar o texto do botão para indicar sucesso
            const btnPagar = document.getElementById("confirmPayment");
            btnPagar.innerHTML = '<i class="fas fa-check-circle"></i> Pagamento Confirmado!';
            btnPagar.classList.remove('opacity-75');
            btnPagar.classList.add('bg-green-700');
            
            // Exibir mensagem de sucesso
            showSuccessMessage("Pagamento registrado com sucesso!");
            
            // Fechar o modal de pagamento e recarregar a página após um breve delay
            setTimeout(() => {
                const paymentModal = document.getElementById("paymentModal");
                paymentModal.classList.add("hidden");
                paymentModal.style.display = "none";
                window.location.reload();
            }, 1500);
            
            return true;
        } else {
            const errorBody = await response.json();
            console.error("Erro detalhado do servidor:", errorBody);
            alert(`Erro ao registrar pagamento: ${errorBody.detail || "Erro desconhecido"}`);
            
            // Restaurar o estado do botão em caso de erro
            const btnPagar = document.getElementById("confirmPayment");
            btnPagar.innerHTML = '<i class="fas fa-check-circle"></i> Confirmar Pagamento';
            btnPagar.disabled = false;
            btnPagar.classList.remove('opacity-75');
            
            return false;
        }
    } catch (error) {
        console.error("Erro ao registrar o pagamento:", error);
        alert(`Erro na comunicação com o servidor: ${error.message}`);
        
        // Restaurar o estado do botão em caso de erro
        const btnPagar = document.getElementById("confirmPayment");
        btnPagar.innerHTML = '<i class="fas fa-check-circle"></i> Confirmar Pagamento';
        btnPagar.disabled = false;
        btnPagar.classList.remove('opacity-75');
        
        return false;
    }
}

const btnPagar = document.getElementById("confirmPayment");
btnPagar.addEventListener("click", async () => {
    // Salvar o conteúdo original do botão
    const originalContent = btnPagar.innerHTML;
    
    // Alterar o texto do botão para indicar processamento
    btnPagar.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Processando pagamento...';
    btnPagar.disabled = true;
    btnPagar.classList.add('opacity-75');
    
    try {
        // Executar a requisição de pagamento
        await extrairDadosComprovante();
    } catch (error) {
        console.error("Erro durante o processamento do pagamento:", error);
        // Em caso de erro, restaurar o botão
        btnPagar.innerHTML = originalContent;
        btnPagar.disabled = false;
        btnPagar.classList.remove('opacity-75');
    }
});

document.getElementById("receiptImage").addEventListener("change", function (event) {
    const file = event.target.files[0];
    const preview = document.getElementById("receiptPreview");
    const placeholder = document.querySelector(".image-upload-placeholder");

    if (file) {
        console.log("Arquivo selecionado:", file.name);
        const reader = new FileReader();

        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.style.display = "block";
            placeholder.style.display = "none";
        };

        reader.readAsDataURL(file);
    } else {
        console.log("Nenhum arquivo selecionado.");
        preview.src = "";
        preview.style.display = "none";
        placeholder.style.display = "flex";
    }
});