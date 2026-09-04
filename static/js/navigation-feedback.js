(function () {
    "use strict";

    var root = document.documentElement;

    function feedbackElement() {
        return document.querySelector("[data-navigation-feedback]");
    }

    function showFeedback(message) {
        var feedback = feedbackElement();
        if (!feedback || root.classList.contains("navigation-pending")) return;

        var label = feedback.querySelector("[data-navigation-message]");
        if (label) label.textContent = message || "Abrindo...";
        feedback.hidden = false;
        root.classList.add("navigation-pending");
    }

    function resetFeedback() {
        var feedback = feedbackElement();
        root.classList.remove("navigation-pending");
        if (feedback) feedback.hidden = true;
    }

    function isRegularInternalLink(event, link) {
        if (!link || event.defaultPrevented || event.button !== 0) return false;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
        if (link.target && link.target !== "_self") return false;
        if (link.hasAttribute("download") || link.dataset.noNavigationFeedback !== undefined) return false;

        var href = link.getAttribute("href");
        if (!href || href.charAt(0) === "#") return false;

        var target;
        try {
            target = new URL(link.href, window.location.href);
        } catch (error) {
            return false;
        }

        if (target.origin !== window.location.origin) return false;
        if (target.pathname === window.location.pathname &&
            target.search === window.location.search && target.hash) return false;
        return true;
    }

    document.addEventListener("click", function (event) {
        var link = event.target.closest("a[href]");
        if (!isRegularInternalLink(event, link)) return;
        showFeedback(link.dataset.loadingLabel || "Abrindo...");
    });

    document.addEventListener("submit", function (event) {
        if (event.defaultPrevented) return;
        var form = event.target;
        if (typeof form.checkValidity === "function" && !form.checkValidity()) return;
        var message = form.classList.contains("logout-form") ? "Saindo..." : "Carregando...";
        showFeedback(form.dataset.loadingLabel || message);
    });

    window.addEventListener("pageshow", resetFeedback);
}());
