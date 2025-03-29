document.addEventListener("DOMContentLoaded", function () {
    fetch("/dados_dashboard")
        .then(response => response.json())
        .then(data => {
            document.getElementById("notas-assinar").innerText = data.notas_assinar;
            document.getElementById("notas-assinadas").innerText = data.notas_assinadas;
            document.getElementById("total-dia").innerText = data.total_dia;
            document.getElementById("total-geral").innerText = data.total_geral;
        })
        .catch(error => console.error("Erro ao carregar os dados:", error));
});