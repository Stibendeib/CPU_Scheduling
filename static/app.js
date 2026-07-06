const processBody = document.querySelector("#processBody");
const resultBody = document.querySelector("#resultBody");
const algorithmInput = document.querySelector("#algorithm");
const quantumField = document.querySelector("#quantumField");
const quantumInput = document.querySelector("#quantum");
const errorMessage = document.querySelector("#errorMessage");
const ganttChart = document.querySelector("#ganttChart");
const ganttTimeline = document.querySelector("#ganttTimeline");
const avgWaiting = document.querySelector("#avgWaiting");
const avgTurnaround = document.querySelector("#avgTurnaround");

const colors = ["#146c63", "#2d6cdf", "#8c4fb8", "#b76a13", "#c34848", "#44743f", "#5c6670"];

function priorityVisible() {
  return algorithmInput.value === "NPP";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function makeRow(process = {}) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td><input class="pid-input" value="${escapeHtml(process.pid ?? `P${processBody.children.length + 1}`)}" aria-label="Process ID"></td>
    <td><input class="arrival-input" type="number" min="0" step="0.1" value="${process.arrival_time ?? 0}" aria-label="Arrival time"></td>
    <td><input class="burst-input" type="number" min="0.1" step="0.1" value="${process.burst_time ?? 1}" aria-label="Burst time"></td>
    <td class="priority-col"><input class="priority-input" type="number" step="1" value="${process.priority ?? 1}" aria-label="Priority"></td>
    <td><button class="remove-button" type="button" title="Remove process">x</button></td>
  `;
  row.querySelector(".remove-button").addEventListener("click", () => {
    row.remove();
    updateRemoveButtons();
  });
  processBody.appendChild(row);
  updateRemoveButtons();
  updateAlgorithmUI();
}

function updateRemoveButtons() {
  const buttons = processBody.querySelectorAll(".remove-button");
  buttons.forEach((button) => {
    button.disabled = buttons.length === 1;
  });
}

function updateAlgorithmUI() {
  quantumField.classList.toggle("hidden", algorithmInput.value !== "RR");
  document.querySelectorAll(".priority-col, .priority-result-col").forEach((cell) => {
    cell.style.display = priorityVisible() ? "" : "none";
  });
}

function readProcesses() {
  return [...processBody.querySelectorAll("tr")].map((row, index) => ({
    pid: row.querySelector(".pid-input").value.trim() || `P${index + 1}`,
    arrival_time: Number(row.querySelector(".arrival-input").value),
    burst_time: Number(row.querySelector(".burst-input").value),
    priority: Number(row.querySelector(".priority-input").value || 1),
  }));
}

function setSampleData() {
  processBody.innerHTML = "";
  [
    { pid: "P1", arrival_time: 0, burst_time: 5, priority: 2 },
    { pid: "P2", arrival_time: 1, burst_time: 3, priority: 1 },
    { pid: "P3", arrival_time: 2, burst_time: 8, priority: 4 },
    { pid: "P4", arrival_time: 3, burst_time: 6, priority: 3 },
  ].forEach(makeRow);
}

function clearResults() {
  resultBody.innerHTML = `<tr><td colspan="7" class="empty-row">Results will appear here.</td></tr>`;
  ganttChart.className = "gantt-chart empty-state";
  ganttChart.textContent = "Run a schedule to see the execution order.";
  ganttTimeline.innerHTML = "";
  avgWaiting.textContent = "0";
  avgTurnaround.textContent = "0";
}

function renderTable(rows) {
  resultBody.innerHTML = rows.map((row) => `
    <tr>
      <td><strong>${escapeHtml(row.pid)}</strong></td>
      <td>${row.arrival_time}</td>
      <td>${row.burst_time}</td>
      <td class="priority-result-col">${priorityVisible() ? row.priority : `<span class="priority-muted">-</span>`}</td>
      <td>${row.start_time}</td>
      <td>${row.waiting_time}</td>
      <td>${row.turnaround_time}</td>
    </tr>
  `).join("");
  updateAlgorithmUI();
}

function renderGantt(segments) {
  const total = Math.max(...segments.map((segment) => Number(segment.end)), 1);
  ganttChart.className = "gantt-chart";
  ganttChart.innerHTML = segments.map((segment, index) => {
    const width = Math.max((Number(segment.duration) / total) * 100, 9);
    const isIdle = segment.pid === "Idle";
    const color = isIdle ? "" : `background:${colors[index % colors.length]}`;
    return `
      <div class="gantt-block ${isIdle ? "idle" : ""}" style="flex: ${width} 0 ${width}%; ${color}">
        <div>${escapeHtml(segment.pid)}<small>${segment.duration}</small></div>
      </div>
    `;
  }).join("");

  ganttTimeline.innerHTML = segments.map((segment, index) => {
    const width = Math.max((Number(segment.duration) / total) * 100, 9);
    return `
      <div class="time-cell" style="flex: ${width} 0 ${width}%;">
        <span class="time-label time-start ${index === 0 ? "first" : ""}">${segment.start}</span>
        ${index === segments.length - 1 ? `<span class="time-label time-end">${segment.end}</span>` : ""}
      </div>
    `;
  }).join("");
}

async function calculate() {
  errorMessage.textContent = "";
  try {
    const response = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        algorithm: algorithmInput.value,
        quantum: Number(quantumInput.value),
        processes: readProcesses(),
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Unable to calculate schedule.");
    }
    renderGantt(data.gantt);
    renderTable(data.table);
    avgWaiting.textContent = data.average_waiting_time;
    avgTurnaround.textContent = data.average_turnaround_time;
  } catch (error) {
    errorMessage.textContent = error.message;
  }
}

document.querySelector("#calculateBtn").addEventListener("click", calculate);
document.querySelector("#addProcessBtn").addEventListener("click", () => makeRow());
document.querySelector("#sampleBtn").addEventListener("click", () => {
  setSampleData();
  clearResults();
});
document.querySelector("#clearBtn").addEventListener("click", () => {
  processBody.innerHTML = "";
  makeRow({ pid: "P1", arrival_time: 0, burst_time: 1, priority: 1 });
  clearResults();
});
algorithmInput.addEventListener("change", updateAlgorithmUI);

setSampleData();
updateAlgorithmUI();
