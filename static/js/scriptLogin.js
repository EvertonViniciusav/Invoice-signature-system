document.getElementById("loginForm").addEventListener("submit", function (event) {
    let valid = true;

    const errorMessages = document.querySelectorAll(".error-message");
    errorMessages.forEach((msg) => (msg.style.display = "none"));
    const inputs = document.querySelectorAll("input");
    inputs.forEach((input) => input.classList.remove("error"));

    const username = document.getElementById("name");
    if (username.value.trim() === "") {
        valid = false;
        username.classList.add("error");
        document.getElementById("usernameError").style.display = "block";
    }

    const password = document.getElementById("senha");
    if (password.value.trim() === "") {
        valid = false;
        password.classList.add("error");
        document.getElementById("passwordError").style.display = "block";
    }

    if (!valid) {
        event.preventDefault();
    }
});
