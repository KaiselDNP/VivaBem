(function () {
    "use strict";

    function storageKey(dialog) {
        return "vivabem-tutorial-v1-user-" + dialog.dataset.onboardingUser;
    }

    function remember(dialog) {
        try {
            window.localStorage.setItem(storageKey(dialog), "done");
        } catch (error) {
            // O tutorial continua funcionando mesmo se o navegador bloquear o armazenamento.
        }
    }

    function wasSeen(dialog) {
        try {
            return window.localStorage.getItem(storageKey(dialog)) === "done";
        } catch (error) {
            return false;
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var dialog = document.querySelector("[data-onboarding-tutorial]");
        if (!dialog) return;

        var card = dialog.querySelector("[role='dialog']");
        var closeButton = dialog.querySelector("[data-onboarding-close]");
        var helpLink = dialog.querySelector("[data-onboarding-help]");
        var openButtons = document.querySelectorAll("[data-onboarding-open]");
        var previousFocus = null;

        function focusableItems() {
            return Array.from(card.querySelectorAll("a[href], button:not([disabled])"));
        }

        function openTutorial() {
            previousFocus = document.activeElement;
            dialog.hidden = false;
            document.body.classList.add("onboarding-open");
            closeButton.focus();
        }

        function closeTutorial(saveChoice) {
            if (saveChoice) remember(dialog);
            dialog.hidden = true;
            document.body.classList.remove("onboarding-open");
            if (previousFocus && typeof previousFocus.focus === "function") previousFocus.focus();
        }

        closeButton.addEventListener("click", function () { closeTutorial(true); });
        helpLink.addEventListener("click", function () { remember(dialog); });
        openButtons.forEach(function (button) {
            button.addEventListener("click", openTutorial);
        });

        dialog.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                event.preventDefault();
                closeTutorial(true);
                return;
            }
            if (event.key !== "Tab") return;
            var items = focusableItems();
            if (!items.length) return;
            var first = items[0];
            var last = items[items.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });

        if (!wasSeen(dialog) && document.querySelector(".dashboard-page")) openTutorial();
    });
}());
