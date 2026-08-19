const API = "http://127.0.0.1:8000";
let sessionId = "";
let accessToken = "";
const messages = document.querySelector("#messages");
const approval = document.querySelector("#approval");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");

function addMessage(text, role = "agent") {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function showApproval(action) {
  approval.hidden = false;
  approval.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = "Approval required";
  const summary = document.createElement("div");
  summary.textContent = action.summary;
  const controls = document.createElement("div");
  controls.className = "approval-actions";
  for (const [label, message] of [["Approve simulation", "approve"], ["Cancel", "cancel"]]) {
    const button = document.createElement("button");
    button.textContent = label;
    button.addEventListener("click", () => send(message));
    controls.appendChild(button);
  }
  approval.append(title, summary, controls);
}

async function start() {
  messages.replaceChildren();
  approval.hidden = true;
  try {
    const response = await fetch(`${API}/api/chat/start`, { method: "POST", headers: {"Content-Type":"application/json"}, body: "{}" });
    const data = await response.json();
    sessionId = data.session_id;
    accessToken = data.access_token;
    addMessage(data.reply);
  } catch {
    addMessage("Start the local API with: python -m app.api, then refresh this demo.");
  }
}

async function send(text) {
  if (!text.trim() || !sessionId) return;
  addMessage(text, "user");
  input.value = "";
  approval.hidden = true;
  try {
    const response = await fetch(`${API}/api/chat/message`, {
      method: "POST",
      headers: {"Content-Type":"application/json", "X-Demo-Session-Token":accessToken},
      body: JSON.stringify({session_id:sessionId, message:text}),
    });
    const data = await response.json();
    addMessage(data.reply || "The request could not be completed.");
    if (data.approval) showApproval(data.approval);
  } catch {
    addMessage("The local API is unavailable.");
  }
}

form.addEventListener("submit", (event) => { event.preventDefault(); send(input.value); });
document.querySelector("#reset").addEventListener("click", start);
document.querySelectorAll("[data-message]").forEach((button) => button.addEventListener("click", () => send(button.dataset.message)));
start();

