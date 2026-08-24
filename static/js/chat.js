(function () {
    "use strict";
    const thread = document.querySelector("[data-chat-thread]");
    if (!thread) return;
    let lastMessageId = Number(thread.dataset.lastMessageId || 0);
    let requestRunning = false;

    function scrollToLatest() { thread.scrollTop = thread.scrollHeight; }
    function appendMessage(message) {
        if (thread.querySelector(`[data-message-id="${message.id}"]`)) return;
        const emptyState = thread.querySelector("[data-empty-chat]");
        if (emptyState) emptyState.remove();
        const article = document.createElement("article");
        article.className = `chat-bubble ${message.is_own ? "chat-bubble-own" : "chat-bubble-other"}`;
        article.dataset.messageId = String(message.id);
        const sender = document.createElement("span");
        sender.className = "visually-hidden";
        sender.textContent = message.is_own ? "Você disse:" : `${message.sender} disse:`;
        const body = document.createElement("p");
        body.textContent = message.body;
        const time = document.createElement("time");
        time.textContent = message.created_at;
        article.append(sender, body, time);
        thread.append(article);
        lastMessageId = Math.max(lastMessageId, message.id);
    }
    async function updateMessages() {
        if (requestRunning || document.hidden) return;
        requestRunning = true;
        try {
            const url = new URL(thread.dataset.messagesUrl, window.location.origin);
            url.searchParams.set("after", String(lastMessageId));
            const response = await window.fetch(url, {headers: {Accept: "application/json"}, credentials: "same-origin"});
            if (!response.ok) return;
            const payload = await response.json();
            if (payload.messages.length) { payload.messages.forEach(appendMessage); scrollToLatest(); }
        } finally { requestRunning = false; }
    }
    document.querySelectorAll("[data-quick-reply]").forEach((button) => button.addEventListener("click", () => {
        const textarea = document.querySelector("[data-chat-form] textarea");
        if (!textarea) return;
        textarea.value = button.dataset.quickReply;
        textarea.focus();
    }));
    scrollToLatest();
    window.setInterval(updateMessages, 5000);
    document.addEventListener("visibilitychange", updateMessages);
})();
