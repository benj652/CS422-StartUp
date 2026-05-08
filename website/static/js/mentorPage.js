(function () {
    const input = document.getElementById("mentor-input");
    const sendBtn = document.getElementById("mentor-send-btn");
    const container = document.getElementById("chat-container");
  
    // Read endpoint from HTML data attribute
    const chatUrl = document.body.dataset.mentorChatUrl;
  
    if (!input || !sendBtn || !container || !chatUrl) return;
  
    const history = [];
  
    function appendMessage(role, text) {
      const wrap = document.createElement("div");
      wrap.className =
        role === "user" ? "chat-msg chat-msg-user" : "chat-msg chat-msg-assistant";
      wrap.textContent = text;
      container.appendChild(wrap);
      container.scrollTop = container.scrollHeight;
    }
  
    async function sendMessage() {
      const message = (input.value || "").trim();
      if (!message) return;
  
      input.value = "";
      appendMessage("user", message);
      history.push({ role: "user", content: message });
  
      try {
        const res = await fetch(chatUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, history }),
        });
  
        const data = await res.json();
        if (!res.ok || data.status !== "success") {
          appendMessage("assistant", "Sorry - I hit an issue. Please try again.");
          return;
        }
  
        appendMessage("assistant", data.reply);
        history.push({ role: "assistant", content: data.reply });
      } catch (_err) {
        appendMessage("assistant", "Network error. Please try again.");
      }
    }
  
    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") sendMessage();
    });
  })();