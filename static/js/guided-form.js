(function () {
    "use strict";

    const form = document.querySelector("[data-guided-form]");
    if (!form) return;

    const steps = Array.from(form.querySelectorAll("[data-guided-step]"));
    const backButton = form.querySelector("[data-step-back]");
    const nextButton = form.querySelector("[data-step-next]");
    const submitButton = form.querySelector("[data-step-submit]");
    const counter = form.querySelector("[data-step-counter]");
    const progress = form.querySelector("[data-step-progress]");
    const draftKey = form.dataset.draftKey;
    let currentStep = Math.max(0, steps.findIndex(function (step) {
        return step.dataset.hasError === "true";
    }));

    form.classList.add("guided-ready");

    function showStep(index, focusHeading) {
        currentStep = Math.min(Math.max(index, 0), steps.length - 1);
        steps.forEach(function (step, stepIndex) {
            const active = stepIndex === currentStep;
            step.hidden = !active;
            step.setAttribute("aria-hidden", String(!active));
        });
        backButton.hidden = currentStep === 0;
        nextButton.hidden = currentStep === steps.length - 1;
        submitButton.hidden = currentStep !== steps.length - 1;
        counter.textContent = `Etapa ${currentStep + 1} de ${steps.length}`;
        progress.style.width = `${((currentStep + 1) / steps.length) * 100}%`;
        if (focusHeading) {
            const legend = steps[currentStep].querySelector("legend");
            if (legend) {
                legend.tabIndex = -1;
                legend.focus();
            }
        }
    }

    function currentFieldsAreValid() {
        const fields = Array.from(steps[currentStep].querySelectorAll("input, select, textarea"));
        for (const field of fields) {
            if (!field.checkValidity()) {
                field.reportValidity();
                field.focus();
                return false;
            }
        }
        return true;
    }

    function saveDraft() {
        if (!draftKey) return;
        const values = {};
        form.querySelectorAll("input, select, textarea").forEach(function (field) {
            if (!field.name || field.name === "csrfmiddlewaretoken" || field.type === "file") return;
            values[field.name] = field.type === "checkbox" ? field.checked : field.value;
        });
        try {
            window.sessionStorage.setItem(draftKey, JSON.stringify(values));
        } catch {
            // O formulário continua funcionando sem salvamento temporário.
        }
    }

    function restoreDraft() {
        if (!draftKey || form.querySelector(".field-error")) return;
        try {
            const values = JSON.parse(window.sessionStorage.getItem(draftKey) || "null");
            if (!values) return;
            Object.entries(values).forEach(function ([name, value]) {
                const field = form.elements.namedItem(name);
                if (!field || field.value) return;
                if (field.type === "checkbox") field.checked = Boolean(value);
                else field.value = value;
            });
        } catch {
            // Um rascunho inválido é simplesmente ignorado.
        }
    }

    backButton.addEventListener("click", function () {
        showStep(currentStep - 1, true);
    });

    nextButton.addEventListener("click", function () {
        if (currentFieldsAreValid()) showStep(currentStep + 1, true);
    });

    form.addEventListener("input", saveDraft);
    form.addEventListener("change", saveDraft);
    form.addEventListener("submit", function (event) {
        if (!currentFieldsAreValid()) {
            event.preventDefault();
            return;
        }
        if (draftKey) window.sessionStorage.removeItem(draftKey);
    });

    restoreDraft();
    showStep(currentStep, false);
})();
