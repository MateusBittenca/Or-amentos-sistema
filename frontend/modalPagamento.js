// Adicionar evento ao botão "Pagar" no modal de informações
document.getElementById("pagamento").addEventListener("click", () => {
    // Fechar o modal de informações
    const infoModal = document.getElementById("infoModal");
    infoModal.classList.add("hidden");
    infoModal.style.display = "none";

    // Abrir o modal de pagamento
    const paymentModal = document.getElementById("paymentModal");
    paymentModal.classList.remove("hidden");
    paymentModal.style.display = "flex";

    // Preencher informações no modal de pagamento (opcional)
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
}
);
