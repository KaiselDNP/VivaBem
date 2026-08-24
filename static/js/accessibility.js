(function () {
    "use strict";

    const pageRole = document.documentElement.dataset.userRole || "anonymous";
    const configuredDefault = document.documentElement.dataset.defaultFontSize || "medium";
    const fontStorageKey = `vivabem-font-size-${pageRole}`;
    const preferredFontStorageKey = "vivabem-preferred-font-size";
    const readingWelcomeStorageKey = "vivabem-reading-welcome-complete";
    const allowedFontSizes = new Set(["small", "medium", "large", "xlarge"]);
    const fontSizeLabels = {
        small: "Pequena",
        medium: "Média",
        large: "Grande",
        xlarge: "Super grande",
    };

    function safeStorageGet(key) {
        try {
            return window.localStorage.getItem(key);
        } catch {
            return null;
        }
    }

    function safeStorageSet(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch {
            // A preferência continua funcionando enquanto a página estiver aberta.
        }
    }

    function announce(message) {
        const status = document.querySelector("[data-accessibility-status]");
        if (status) status.textContent = message;
    }

    function applyFontSize(size) {
        const normalizedSize = size === "default" ? "medium" : size;
        const selectedSize = allowedFontSizes.has(normalizedSize) ? normalizedSize : configuredDefault;
        document.documentElement.dataset.fontSize = selectedSize;
        const select = document.querySelector("[data-font-size-select]");
        if (select) select.value = selectedSize;
        return selectedSize;
    }

    applyFontSize(
        safeStorageGet(fontStorageKey) ||
        safeStorageGet(preferredFontStorageKey) ||
        configuredDefault
    );

    function setupFontControls() {
        const select = document.querySelector("[data-font-size-select]");
        if (!select) return;
        select.value = document.documentElement.dataset.fontSize || configuredDefault;
        select.addEventListener("change", function () {
            const selectedSize = applyFontSize(select.value);
            safeStorageSet(fontStorageKey, selectedSize);
            safeStorageSet(preferredFontStorageKey, selectedSize);
            announce(`Tamanho da letra: ${fontSizeLabels[selectedSize]}.`);
        });
    }

    function setupReadingWelcome() {
        const welcome = document.querySelector("[data-reading-welcome]");
        if (!welcome || pageRole !== "anonymous" || safeStorageGet(readingWelcomeStorageKey)) return;

        const backgroundElements = Array.from(document.body.children).filter(function (element) {
            return element !== welcome;
        });
        const choices = Array.from(welcome.querySelectorAll("[data-reading-choice]"));

        function closeWelcome(size) {
            const selectedSize = applyFontSize(size);
            safeStorageSet(preferredFontStorageKey, selectedSize);
            ["anonymous", "senior", "family", "professional", "admin"].forEach(function (role) {
                safeStorageSet(`vivabem-font-size-${role}`, selectedSize);
            });
            safeStorageSet(readingWelcomeStorageKey, "true");
            welcome.hidden = true;
            document.documentElement.classList.remove("reading-welcome-open");
            backgroundElements.forEach(function (element) {
                element.inert = false;
            });
            announce(`Tamanho da letra escolhido: ${fontSizeLabels[selectedSize]}.`);
            const firstHeading = document.querySelector("#conteudo h1");
            if (firstHeading) {
                firstHeading.setAttribute("tabindex", "-1");
                firstHeading.focus();
            }
        }

        welcome.hidden = false;
        document.documentElement.classList.add("reading-welcome-open");
        backgroundElements.forEach(function (element) {
            element.inert = true;
        });
        choices.forEach(function (choice) {
            choice.addEventListener("click", function () {
                closeWelcome(choice.dataset.readingChoice);
            });
        });
        if (choices.length) choices[0].focus();
    }

    function setupSelectiveReading() {
        const button = document.querySelector("[data-read-aloud]");
        const prompt = document.querySelector("[data-read-selection-prompt]");
        const buttonLabel = button ? button.querySelector("[data-read-button-label]") : null;
        if (!button) return;

        if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
            button.disabled = true;
            button.title = "A leitura em voz alta não está disponível neste navegador.";
            return;
        }

        let selecting = false;

        function setSelectionMode(active) {
            selecting = active;
            document.body.classList.toggle("reading-selection-active", active);
            button.setAttribute("aria-pressed", String(active));
            button.setAttribute(
                "aria-label",
                active ? "Cancelar escolha de leitura" : "Ouvir um item da página. Atalho F2"
            );
            if (buttonLabel) {
                buttonLabel.textContent = active ? "Cancelar" : "Ouvir um item";
            }
            if (prompt) prompt.hidden = !active;
            if (active) {
                window.speechSynthesis.cancel();
                announce("Modo de leitura ativado. Clique ou toque no que deseja ouvir.");
            } else {
                announce("Modo de escolha encerrado. Os botões voltaram ao funcionamento normal.");
            }
        }

        function textForControl(control) {
            if (control.matches('input[type="password"]')) return "Campo de senha.";
            if (control.matches("input, textarea")) {
                const label = control.labels && control.labels.length ? control.labels[0] : null;
                return [label ? label.innerText : "Campo", control.value].filter(Boolean).join(": ");
            }
            if (control.matches("select")) {
                const label = control.labels && control.labels.length ? control.labels[0] : null;
                const option = control.options[control.selectedIndex];
                return [label ? label.innerText : "Opção", option ? option.text : ""]
                    .filter(Boolean)
                    .join(": ");
            }
            return control.getAttribute("aria-label") || control.innerText || control.textContent;
        }

        function readableTarget(element) {
            const selector = [
                "a",
                "button",
                "label",
                "input",
                "select",
                "textarea",
                "[role='button']",
                ".senior-action-card",
                ".record-card",
                "h1",
                "h2",
                "h3",
                "p",
                "li",
                "dt",
                "dd",
            ].join(",");
            return element.closest(selector) || element;
        }

        function speak(text) {
            const cleanText = String(text || "").replace(/\s+/g, " ").trim().slice(0, 700);
            if (!cleanText) {
                announce("Não foi possível identificar o texto escolhido.");
                return;
            }
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = "pt-BR";
            utterance.rate = 0.88;
            utterance.onend = function () {
                announce("Leitura concluída. Você já pode usar os botões normalmente.");
            };
            utterance.onerror = function () {
                announce("Não foi possível concluir a leitura.");
            };
            window.speechSynthesis.speak(utterance);
        }

        button.addEventListener("click", function () {
            setSelectionMode(!selecting);
        });

        document.addEventListener(
            "click",
            function (event) {
                if (!selecting) return;
                if (event.target.closest("[data-read-aloud], .accessibility-tools, [data-read-selection-prompt]")) {
                    return;
                }
                event.preventDefault();
                event.stopImmediatePropagation();
                const target = readableTarget(event.target);
                const text = textForControl(target);
                setSelectionMode(false);
                speak(text);
            },
            true
        );

        document.addEventListener("keydown", function (event) {
            const simpleShortcut = event.key === "F2";
            const previousShortcut = event.altKey && event.key.toLowerCase() === "o";
            if ((simpleShortcut || previousShortcut) && !event.repeat) {
                event.preventDefault();
                setSelectionMode(!selecting);
            } else if (event.key === "Escape" && selecting) {
                event.preventDefault();
                setSelectionMode(false);
            }
        });

        window.addEventListener("pagehide", function () {
            window.speechSynthesis.cancel();
        });
    }

    function setupPasswordVisibility() {
        document.querySelectorAll('input[type="password"]').forEach(function (input) {
            if (input.dataset.visibilityReady) return;
            input.dataset.visibilityReady = "true";

            const button = document.createElement("button");
            button.type = "button";
            button.className = "password-visibility-button";
            button.textContent = "Mostrar senha";
            button.setAttribute("aria-controls", input.id);
            button.addEventListener("click", function () {
                const showing = input.type === "text";
                input.type = showing ? "password" : "text";
                button.textContent = showing ? "Mostrar senha" : "Ocultar senha";
                button.setAttribute("aria-pressed", String(!showing));
            });
            input.insertAdjacentElement("afterend", button);
        });
    }

    function focusErrorSummary() {
        const summary = document.querySelector("[data-error-summary]");
        if (summary) summary.focus();
    }

    function setupConfirmations() {
        document.querySelectorAll("[data-confirm]").forEach(function (control) {
            const form = control.closest("form");
            if (!form) return;
            form.addEventListener("submit", function (event) {
                if (event.submitter !== control) return;
                if (!window.confirm(control.dataset.confirm)) event.preventDefault();
            });
        });
    }

    function setup() {
        setupFontControls();
        setupReadingWelcome();
        setupSelectiveReading();
        setupPasswordVisibility();
        focusErrorSummary();
        setupConfirmations();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setup, { once: true });
    } else {
        setup();
    }
})();
