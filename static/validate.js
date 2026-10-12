function validateRegister(f) {
    const errors = [];
    const name = f.name.value.trim();
    const email = f.email.value.trim();
    const password = f.password.value;
    const confirm = f.confirm_password.value;

    if (!name) errors.push("Name is required");
    if (!email) errors.push("Email is required");
    if (!password) errors.push("Password is required");
    if (!confirm) errors.push("Confirm password is required");
    if (password && confirm && password !== confirm) errors.push("Passwords do not match");
    return errors;
}

function validateLogin(f) {
    const errors = [];
    if (!f.email.value.trim()) errors.push("Email is required");
    if (!f.password.value) errors.push("Password is required");
    return errors;
}

function validateTodo(f) {
    const title = f.title.value.trim();
    if (!title) return ["Title is required"];
    if (title.length > 200) return ["Title is too long (200 characters at most)"];
    return [];
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

function guard(form, validator) {
    form.addEventListener("submit", (e) => {
        const errs = validator(form);
        if (errs.length) {
            e.preventDefault();
            showErrors(errs);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const regForm = document.getElementById("register-form");
    if (regForm) guard(regForm, validateRegister);

    const loginForm = document.getElementById("login-form");
    if (loginForm) guard(loginForm, validateLogin);

    const addForm = document.getElementById("add-form");
    if (addForm) guard(addForm, validateTodo);

    document.querySelectorAll(".edit-form").forEach((f) => guard(f, validateTodo));

    // R7: ask "are you sure?" before deleting
    document.querySelectorAll(".delete-form").forEach((f) => {
        f.addEventListener("submit", (e) => {
            if (!confirm("Are you sure you want to delete this to-do?")) e.preventDefault();
        });
    });
});
