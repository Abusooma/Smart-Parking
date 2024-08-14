$(document).ready(function () {
  $("#sidebarCollapse").on("click", function () {
    $("#sidebar").toggleClass("active");
  });
});

// Js pour le pop de message de success, error, ... boostrap

document.addEventListener("DOMContentLoaded", function () {
  var alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    // Ajoute une animation d'entrée
    alert.style.animation = "slideInDown 0.5s forwards";

    // Fait disparaître le message après 5 secondes
    setTimeout(function () {
      alert.style.animation = "slideOutUp 0.5s forwards";
      setTimeout(function () {
        alert.remove();
      }, 500);
    }, 5000);
  });
});
