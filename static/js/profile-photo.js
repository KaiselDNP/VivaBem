(function () {
    "use strict";

    const input = document.querySelector("[data-photo-input]");
    const preview = document.querySelector("[data-photo-preview]");
    const fallback = document.querySelector("[data-photo-fallback]");
    if (!input || !preview) return;

    let previewUrl = null;
    input.addEventListener("change", function () {
        const file = input.files && input.files[0];
        if (!file || !file.type.startsWith("image/")) return;

        if (previewUrl) URL.revokeObjectURL(previewUrl);
        previewUrl = URL.createObjectURL(file);
        preview.src = previewUrl;
        preview.hidden = false;
        if (fallback) fallback.hidden = true;
    });

    window.addEventListener("pagehide", function () {
        if (previewUrl) URL.revokeObjectURL(previewUrl);
    });
})();
