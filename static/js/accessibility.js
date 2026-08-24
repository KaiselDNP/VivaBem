(function () {
    "use strict";

    const pageRole = document.documentElement.dataset.userRole || "anonymous";
    const configuredDefault = document.documentElement.dataset.defaultFontSize || "default";
    const fontStorageKey = `vivabem-font-size-${pageRole}`;
    const allowedFontSizes = new Set(["default", "large", "xlarge"]);

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
        const selectedSize = allowedFontSizes.has(size) ? size : configuredDefault;
        document.documentElement.dataset.fontSize = selectedSize;
        document.querySelectorAll("[data-font-size]").forEach(function (button) {
            const active = button.dataset.fontSize === selectedSize;
            button.setAttribute("aria-pressed", String(active));
        });
        return selectedSize;
    }

    applyFontSize(safeStorageGet(fontStorageKey) || configuredDefault);

    function setupFontControls() {
        document.querySelectorAll("[data-font-size]").forEach(function (button) {
            button.addEventListener("click", function () {
                const selectedSize = applyFontSize(button.dataset.fontSize);
                safeStorageSet(fontStorageKey, selectedSize);
                announce(selectedSize === "default" ? "Tamanho normal ativado." : "Texto aumentado.");
            });
        });
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
                active ? "Cancelar escolha de leitura" : "Escolher uma parte da página para ouvir"
            );
            if (buttonLabel) {
                buttonLabel.textContent = active ? "Cancelar leitura" : "Escolher o que ouvir";
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
            if (event.altKey && event.key.toLowerCase() === "o" && !event.repeat) {
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
