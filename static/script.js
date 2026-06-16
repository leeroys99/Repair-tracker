//QUOTE BUTTON/FORM
document.addEventListener("DOMContentLoaded", function () {
    const quoteBtn = document.getElementById("quoteBtn");
    const quoteForm = document.getElementById("quoteForm");

    if (quoteBtn && quoteForm) {
        quoteForm.style.display = "none";

        quoteBtn.addEventListener("click", function () {

            if (quoteForm.style.display === "none") {
                quoteForm.style.display = "block";
            } else {
                quoteForm.style.display = "none";
            }
        });
    }
});