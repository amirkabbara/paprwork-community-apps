interface Expense {
  id: number;
  amount: number;
  category: string;
  description: string;
  created_at: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  food: "#FF6B6B",
  transport: "#4ECDC4",
  entertainment: "#A78BFA",
  shopping: "#F59E0B",
  bills: "#3B82F6",
  health: "#10B981",
  other: "#94A3B8",
};

const API_BASE = window.location.origin;

async function dbExec(sql: string): Promise<void> {
  await fetch(`${API_BASE}/api/db/exec`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql }),
  });
}

async function dbQuery(sql: string, params: unknown[] = []): Promise<Expense[]> {
  const res = await fetch(`${API_BASE}/api/db/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql, params }),
  });
  const data = (await res.json()) as { rows?: Expense[] };
  return data.rows ?? [];
}

async function dbWrite(sql: string, params: unknown[] = []): Promise<void> {
  await fetch(`${API_BASE}/api/db/write`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql, params }),
  });
}

async function initDB(): Promise<void> {
  await dbExec(`
    CREATE TABLE IF NOT EXISTS expenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      amount REAL NOT NULL,
      category TEXT NOT NULL,
      description TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now'))
    )
  `);
}

async function loadExpenses(): Promise<Expense[]> {
  return dbQuery("SELECT * FROM expenses ORDER BY created_at DESC LIMIT 50");
}

async function addExpense(amount: number, category: string, description: string): Promise<void> {
  await dbWrite(
    "INSERT INTO expenses (amount, category, description) VALUES (?, ?, ?)",
    [amount, category, description],
  );
}

async function deleteExpense(id: number): Promise<void> {
  await dbWrite("DELETE FROM expenses WHERE id = ?", [id]);
}

function renderList(expenses: Expense[]): void {
  const list = document.getElementById("expense-list") as HTMLDivElement;
  if (expenses.length === 0) {
    list.innerHTML = '<p class="empty">No expenses yet. Add one above.</p>';
    return;
  }
  list.innerHTML = expenses
    .map(
      (e) => `
    <div class="expense-item">
      <div class="expense-item__color" style="background:${CATEGORY_COLORS[e.category] ?? "#94A3B8"}"></div>
      <div class="expense-item__info">
        <span class="expense-item__category">${e.category}</span>
        <span class="expense-item__desc">${e.description || "—"}</span>
      </div>
      <span class="expense-item__amount">$${e.amount.toFixed(2)}</span>
      <button class="expense-item__delete" data-id="${e.id}">&times;</button>
    </div>`,
    )
    .join("");

  list.querySelectorAll(".expense-item__delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number((btn as HTMLElement).dataset.id);
      await deleteExpense(id);
      await refresh();
    });
  });
}

function renderChart(expenses: Expense[]): void {
  const canvas = document.getElementById("chart") as HTMLCanvasElement;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const totals: Record<string, number> = {};
  for (const e of expenses) {
    totals[e.category] = (totals[e.category] ?? 0) + e.amount;
  }

  const entries = Object.entries(totals).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const radius = Math.min(cx, cy) - 10;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (total === 0) {
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(148,163,184,0.15)";
    ctx.fill();
    ctx.fillStyle = "rgba(148,163,184,0.5)";
    ctx.font = "14px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("No data", cx, cy + 5);
    return;
  }

  let startAngle = -Math.PI / 2;
  for (const [cat, val] of entries) {
    const sliceAngle = (val / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
    ctx.closePath();
    ctx.fillStyle = CATEGORY_COLORS[cat] ?? "#94A3B8";
    ctx.fill();
    startAngle += sliceAngle;
  }

  // center hole for donut effect
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.55, 0, Math.PI * 2);
  ctx.fillStyle = getComputedStyle(document.body).getPropertyValue("--glass-bg").trim() || "rgba(255,255,255,0.85)";
  ctx.fill();

  const legend = document.getElementById("legend") as HTMLDivElement;
  legend.innerHTML = entries
    .map(
      ([cat, val]) =>
        `<div class="legend-item">
          <span class="legend-dot" style="background:${CATEGORY_COLORS[cat] ?? "#94A3B8"}"></span>
          <span class="legend-label">${cat}</span>
          <span class="legend-value">$${val.toFixed(2)}</span>
        </div>`,
    )
    .join("");
}

function updateTotal(expenses: Expense[]): void {
  const total = expenses.reduce((sum, e) => sum + e.amount, 0);
  const el = document.getElementById("total-display") as HTMLParagraphElement;
  el.textContent = `Total: $${total.toFixed(2)}`;
}

async function refresh(): Promise<void> {
  const expenses = await loadExpenses();
  renderList(expenses);
  renderChart(expenses);
  updateTotal(expenses);
}

async function main(): Promise<void> {
  await initDB();

  const addBtn = document.getElementById("add-btn") as HTMLButtonElement;
  const amountInput = document.getElementById("amount") as HTMLInputElement;
  const categorySelect = document.getElementById("category") as HTMLSelectElement;
  const descInput = document.getElementById("description") as HTMLInputElement;

  addBtn.addEventListener("click", async () => {
    const amount = parseFloat(amountInput.value);
    if (isNaN(amount) || amount <= 0) return;

    await addExpense(amount, categorySelect.value, descInput.value.trim());
    amountInput.value = "";
    descInput.value = "";
    await refresh();
  });

  // Allow Enter key to submit
  for (const input of [amountInput, descInput]) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") addBtn.click();
    });
  }

  await refresh();
}

main();
