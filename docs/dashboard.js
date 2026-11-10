// AGYToolkit Interactive Web Dashboard Engine
// Standalone zero-dependency runtime supporting live API polling and static JSON imports.

const DEFAULT_SNAPSHOT = {
  workspace: "~/projects/AGYToolkit",
  doctor_healthy: true,
  passed_checks: 18,
  failed_checks: 0,
  warning_checks: 0,
  toolchains: [
    { name: "Node.js", status: "PASS", details: "Node.js v20.18.0 detected" },
    { name: "npm", status: "PASS", details: "npm 10.8.2 detected" },
    { name: "Python", status: "PASS", details: "Python 3.12.10 detected" },
    { name: "Java JDK", status: "PASS", details: "OpenJDK 23 detected" },
    { name: "Apache Maven", status: "PASS", details: "Apache Maven 3.9.6 detected" },
    { name: "Git", status: "PASS", details: "git 2.47.0 detected" }
  ],
  governance: [
    { name: "GEMINI.md", status: "PASS", details: "Configured with strict non-negotiables" },
    { name: "AGENTS.md", status: "PASS", details: "Configured with Conventional Commits" },
    { name: "anti-bloat-check", status: "PASS", details: "Zero emojis & 600-line ceiling enforced" },
    { name: "enforce-branch-rule", status: "PASS", details: "Direct commits to main blocked" },
    { name: "auto-compact-memory", status: "PASS", details: "85% auto-compact PostToolUse hook active" },
    { name: "MCP Server", status: "PASS", details: "8 native tools registered over stdio" }
  ],
  memory: {
    status: "OPTIMAL",
    active_session_bytes: 342,
    active_session_cap: 1024,
    active_session_within: true,
    decisions_bytes: 1420,
    decisions_cap: 3072,
    decisions_within: true,
    session_archives_count: 3,
    adr_history_count: 12
  },
  bus: {
    active_events_count: 0,
    claimed_events_count: 0,
    recent_events: []
  },
  agents_count: 15,
  skills_count: 28
};

const AGENTS_LIST = [
  { name: "orchestrator", role: "Primary Swarm Coordinator", ws: "inherit", rw: "RW", desc: "Top-level orchestrator directing multi-agent pipelines and task handoffs." },
  { name: "planner-architect", role: "Architecture & System Design", ws: "branch", rw: "RO", desc: "Drafts implementation plans, ADRs, trade-off matrices, and specifications." },
  { name: "spring-boot-engineer", role: "Java 23 / Spring Boot Backend", ws: "branch", rw: "RW", desc: "Implements Hexagonal Architecture services, domain ports, and JPA adapters." },
  { name: "node-ts-engineer", role: "Node.js & TypeScript Systems", ws: "branch", rw: "RW", desc: "Builds MCP servers, Puppeteer automation sidecars, and Fastify endpoints." },
  { name: "python-automation-lead", role: "Python Automation & Pipelines", ws: "branch", rw: "RW", desc: "Maintains Python diagnostics, test harnesses, and computer vision harnesses." },
  { name: "frontend-ui-engineer", role: "Web & UI Components", ws: "branch", rw: "RW", desc: "Builds accessible, responsive, modern web interfaces and web dashboards." },
  { name: "database-architect", role: "Schema Design & Migrations", ws: "branch", rw: "RW", desc: "Designs relational and document schemas, indexing strategies, and Flyway/Liquibase scripts." },
  { name: "tdd-specialist", role: "Test-Driven Development Lead", ws: "share", rw: "RW", desc: "Enforces Red-Green-Refactor cycles and writes exhaustive unit and boundary tests." },
  { name: "security-auditor", role: "OWASP & Vulnerability Auditor", ws: "branch", rw: "RO", desc: "Audits for credentials leaks, CVE vulnerabilities, and permission escapes." },
  { name: "code-reviewer", role: "Production Quality Reviewer", ws: "branch", rw: "RO", desc: "Reviews git diffs against architectural cohesion and security standards." },
  { name: "anti-bloat-sentinel", role: "Code Cleanliness & Size Guard", ws: "inherit", rw: "RO", desc: "Guarantees 0 emojis, <600 lines per file, and zero conversational AI chatter." },
  { name: "git-craftsman", role: "Git Discipline & Commits", ws: "inherit", rw: "RW", desc: "Crafts atomic Conventional Commits and manages isolated feature branches." },
  { name: "docs-librarian", role: "Technical Documentation Lead", ws: "share", rw: "RW", desc: "Maintains sitemaps, manuals, API specifications, and architectural documentation." },
  { name: "context-budget-guard", role: "Memory & Token Governor", ws: "inherit", rw: "RW", desc: "Monitors memory byte caps (1 KB / 3 KB) and manages volatile payload offloading." },
  { name: "dependency-curator", role: "Toolchain & Package Auditor", ws: "branch", rw: "RW", desc: "Audits dependencies across Maven, npm, and pip for security and license compliance." }
];

function updateHUD(metrics) {
  document.getElementById("workspace-label").textContent = metrics.workspace || "Local Workspace";
  
  // Health badge
  const healthEl = document.getElementById("health-indicator");
  const healthText = document.getElementById("health-text");
  if (metrics.doctor_healthy) {
    healthEl.style.backgroundColor = "var(--accent-green)";
    healthEl.style.boxShadow = "0 0 8px var(--accent-green)";
    healthText.textContent = "SYSTEM HEALTHY";
  } else {
    healthEl.style.backgroundColor = "var(--accent-red)";
    healthEl.style.boxShadow = "0 0 8px var(--accent-red)";
    healthText.textContent = "DEGRADED (" + metrics.failed_checks + " Failures)";
  }

  // Memory gauges
  const mem = metrics.memory;
  const actRatio = Math.min(100, (mem.active_session_bytes / mem.active_session_cap) * 100);
  const decRatio = Math.min(100, (mem.decisions_bytes / mem.decisions_cap) * 100);

  document.getElementById("act-mem-bytes").textContent = `${mem.active_session_bytes} / ${mem.active_session_cap} B`;
  document.getElementById("act-mem-pct").textContent = `${actRatio.toFixed(1)}%`;
  const actBar = document.getElementById("act-mem-bar");
  actBar.style.width = `${actRatio}%`;
  actBar.className = "progress-fill" + (actRatio >= 85 ? " danger" : actRatio >= 70 ? " warning" : "");

  document.getElementById("dec-mem-bytes").textContent = `${mem.decisions_bytes} / ${mem.decisions_cap} B`;
  document.getElementById("dec-mem-pct").textContent = `${decRatio.toFixed(1)}%`;
  const decBar = document.getElementById("dec-mem-bar");
  decBar.style.width = `${decRatio}%`;
  decBar.className = "progress-fill" + (decRatio >= 85 ? " danger" : decRatio >= 70 ? " warning" : "");

  document.getElementById("session-archives-count").textContent = mem.session_archives_count;
  document.getElementById("adr-history-count").textContent = mem.adr_history_count;

  // Toolchains
  const tcContainer = document.getElementById("toolchains-list");
  tcContainer.innerHTML = "";
  metrics.toolchains.forEach(tc => {
    const row = document.createElement("div");
    row.className = "list-item-row";
    const badgeClass = tc.status === "PASS" ? "badge-pass" : "badge-fail";
    row.innerHTML = `<span><strong>${tc.name}</strong> <small style="color:var(--text-muted);margin-left:8px;">${tc.details}</small></span><span class="${badgeClass}">${tc.status}</span>`;
    tcContainer.appendChild(row);
  });

  // Governance
  const govContainer = document.getElementById("governance-list");
  govContainer.innerHTML = "";
  metrics.governance.forEach(gov => {
    const row = document.createElement("div");
    row.className = "list-item-row";
    const badgeClass = gov.status === "PASS" ? "badge-pass" : gov.status === "WARN" ? "badge-warn" : "badge-fail";
    row.innerHTML = `<span><strong>${gov.name}</strong> <small style="color:var(--text-muted);margin-left:8px;">${gov.details}</small></span><span class="${badgeClass}">${gov.status}</span>`;
    govContainer.appendChild(row);
  });

  // Bus stats
  document.getElementById("bus-active-count").textContent = metrics.bus.active_events_count;
  document.getElementById("bus-claimed-count").textContent = metrics.bus.claimed_events_count;
}

function renderAgents(agents) {
  const container = document.getElementById("agents-container");
  container.innerHTML = "";
  agents.forEach(agent => {
    const card = document.createElement("div");
    card.className = "agent-card";
    const rwBadge = agent.rw === "RW" ? "badge-warn" : "badge-pass";
    card.innerHTML = `
      <div class="agent-card-header">
        <span class="agent-name">${agent.name}</span>
        <span class="${rwBadge}">${agent.rw} | ${agent.ws}</span>
      </div>
      <div class="agent-role">${agent.role}</div>
      <div class="agent-desc">${agent.desc}</div>
    `;
    container.appendChild(card);
  });
}

function filterAgents() {
  const query = document.getElementById("agent-search").value.toLowerCase();
  const filtered = AGENTS_LIST.filter(a => 
    a.name.toLowerCase().includes(query) || 
    a.role.toLowerCase().includes(query) || 
    a.desc.toLowerCase().includes(query)
  );
  renderAgents(filtered);
}

function loadLiveDiagnostics() {
  fetch("/api/status")
    .then(res => {
      if (!res.ok) throw new Error("API not reachable");
      return res.json();
    })
    .then(data => {
      updateHUD(data);
      document.getElementById("connection-status").textContent = "Connected to Live Daemon";
    })
    .catch(() => {
      document.getElementById("connection-status").textContent = "Offline (Static Mode)";
      updateHUD(DEFAULT_SNAPSHOT);
    });
}

function parseImportedJSON() {
  const raw = document.getElementById("json-import-textarea").value;
  try {
    const parsed = JSON.parse(raw);
    if (parsed.memory && parsed.toolchains) {
      updateHUD(parsed);
      alert("Diagnostic JSON loaded successfully!");
    } else {
      alert("Invalid format: expected AGYToolkit doctor/dashboard JSON output.");
    }
  } catch (e) {
    alert("JSON parse error: " + e.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  renderAgents(AGENTS_LIST);
  loadLiveDiagnostics();
});
