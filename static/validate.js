function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateRegister(f) {
    const errors = [];
    const name = f.name.value.trim();
    const email = f.email.value.trim();
    const password = f.password.value;
    const confirm = f.confirm_password.value;

    if (!name) errors.push("Name is required");
    if (!email) {
        errors.push("Email is required");
    } else if (!isValidEmail(email)) {
        errors.push("Email is not valid");
    }
    if (!password) errors.push("Password is required");
    if (!confirm) errors.push("Confirm password is required");
    if (password && confirm && password !== confirm) errors.push("Passwords do not match");

    return errors;
}

function validateLogin(f) {
    const errors = [];
    const email = f.email.value.trim();
    const password = f.password.value;

    if (!email) {
        errors.push("Email is required");
    } else if (!isValidEmail(email)) {
        errors.push("Email is not valid");
    }
    if (!password) errors.push("Password is required");

    return errors;
}

function showErrors(errors) {
    const box = document.getElementById("errors");
    if (!box) return;
    box.innerHTML = "";
    for (const message of errors) {
        const li = document.createElement("li");
        li.textContent = message;
        box.appendChild(li);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const regForm = document.getElementById("register-form");
    if (regForm) {
        regForm.addEventListener("submit", (e) => {
            const errs = validateRegister(regForm);
            if (errs.length) {
                e.preventDefault();
                showErrors(errs);
            }
        });
    }

    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", (e) => {
            const errs = validateLogin(loginForm);
            if (errs.length) {
                e.preventDefault();
                showErrors(errs);
            }
        });
    }
});