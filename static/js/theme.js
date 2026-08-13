(function () {
    "use strict";

    const storageKey = "vivabem-theme";
    const darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");

    function readStoredTheme() {
        try {
            const storedTheme = window.localStorage.getItem(storageKey);
            return storedTheme === "dark" || storedTheme === "light" ? storedTheme : null;
        } catch {
            return null;
        }
    }

    function rememberTheme(theme) {
        try {
            window.localStorage.setItem(storageKey, theme);
        } catch {
            // O tema ainda funciona durante a sessão quando o armazenamento está indisponível.
        }
    }

    function preferredTheme() {
        return readStoredTheme() || (darkModeQuery.matches ? "dark" : "light");
    }

    function updateToggle(theme) {
        const toggle = document.querySelector("[data-theme-toggle]");
        if (!toggle) return;

        const isDark = theme === "dark";
        const actionLabel = isDark ? "Ativar modo claro" : "Ativar modo escuro";
        const icon = toggle.querySelector("[data-theme-icon]");
        const label = toggle.querySelector("[data-theme-label]");

        toggle.setAttribute("aria-pressed", String(isDark));
        toggle.setAttribute("aria-label", actionLabel);
        toggle.setAttribute("title", actionLabel);
        if (icon) icon.textContent = isDark ? "☀" : "☾";
        if (label) label.textContent = actionLabel;
    }

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        document.documentElement.style.colorScheme = theme;
        updateToggle(theme);
    }

    applyTheme(preferredTheme());

    function setupToggle() {
        const toggle = document.querySelector("[data-theme-toggle]");
        if (!toggle) return;

        updateToggle(document.documentElement.dataset.theme);
        toggle.addEventListener("click", function () {
            const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            rememberTheme(nextTheme);
            applyTheme(nextTheme);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupToggle, { once: true });
    } else {
        setupToggle();
    }

    darkModeQuery.addEventListener("change", function (event) {
        if (!readStoredTheme()) applyTheme(event.matches ? "dark" : "light");
    });
})();
