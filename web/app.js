const statusNode = document.querySelector("#status");
const poolsBody = document.querySelector("#poolsBody");
const resultNode = document.querySelector("#result");
const analysisView = document.querySelector("#analysisView");
const inferenceView = document.querySelector("#inferenceView");
const healthStats = document.querySelector("#healthStats");
const healthTag = document.querySelector("#healthTag");
const summaryLink = document.querySelector("#summaryLink");
const eventsLink = document.querySelector("#eventsLink");
const graphMeta = document.querySelector("#graphMeta");
const graphReport = document.querySelector("#graphReport");
const canvas = document.querySelector("#graphCanvas");
const ctx = canvas.getContext("2d");

let pools = [];
let selected = new Set();
let lastRun = null;
let rankingProvider = "unknown";

function money(value) {
  if (value == null || Number.isNaN(Number(value))) return "unknown";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function shortAddr(value) {
  if (!value) return "—";
  return `${value.slice(0, 8)}…${value.slice(-4)}`;
}

function showStatus(text) {
  statusNode.textContent = text;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function renderHealth(data) {
  healthTag.textContent = data.ok ? "localhost · paper-only" : "degraded";
  const items = [
    ["Chain ID", data.chain_id],
    ["Provider", data.provider],
    ["RPC host", data.rpc?.rpc_host || "unset"],
    ["Safe block", data.safe_block ?? "unknown"],
    ["Fingerprint", data.rpc?.rpc_fingerprint || "—"],
    ["Mode", "spot_long_only / paper"],
  ];
  healthStats.innerHTML = items
    .map(([label, value]) => `<div class="stat"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`)
    .join("");
}

function renderPools() {
  poolsBody.innerHTML = pools
    .map((pool) => {
      const checked = selected.has(pool.address) ? "checked" : "";
      const verified = lastRun?.pools?.find((item) => item.pool.address === pool.address)?.rpc_verified;
      const badge = verified
        ? '<span class="badge ok">rpc_verified</span>'
        : '<span class="badge muted">provider only</span>';
      const pair = pool.pair_name || `${pool.base_symbol || "?"} / ${pool.quote_symbol || "?"}`;
      return `<tr>
        <td><input type="checkbox" data-address="${esc(pool.address)}" ${checked}></td>
        <td>#${esc(pool.provider_rank)}</td>
        <td>
          <strong>${esc(pair)}</strong><br>
          <code title="pool CA">${esc(pool.address)}</code><br>
        </td>
        <td><small>base ${esc(pool.base_symbol || "?")} <code>${esc(shortAddr(pool.base_token))}</code></small><br><small>quote ${esc(pool.quote_symbol || "?")} <code>${esc(shortAddr(pool.quote_token))}</code></small></td>
        <td>${esc(money(pool.volume_24h_usd))}</td>
        <td>${esc(money(pool.liquidity_usd))}</td>
        <td>${esc(pool.transactions_24h ?? "unknown")}</td>
        <td>${esc(pool.observed_at || "unknown")}<br><small>${esc(pool.ranking_provider || rankingProvider)}</small></td>
        <td>${badge}</td>
      </tr>`;
    })
    .join("");
  poolsBody.querySelectorAll("input[type=checkbox]").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) selected.add(input.dataset.address);
      else selected.delete(input.dataset.address);
    });
  });
}

function kv(rows) {
  return `<div class="kv">${rows
    .map(([k, v]) => `<div><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`)
    .join("")}</div>`;
}

function renderAnalysis(run) {
  if (!run?.pools?.length) {
    analysisView.innerHTML = `<p class="empty">无池分析结果。quality=${esc(run?.quality || "unknown")} · ${esc((run?.reason_codes || []).join(", "))}</p>`;
    inferenceView.innerHTML = '<p class="empty">无推理结果。</p>';
    return;
  }
  analysisView.innerHTML = run.pools
    .map((item) => {
      const features = item.features || {};
      const pool = item.pool || {};
      const pair = pool.pair_name || `${pool.base_symbol || "?"} / ${pool.quote_symbol || "?"}`;
      const swaps = item.recent_swaps || [];
      const swapRows = swaps.length
        ? `<table class="mini"><thead><tr><th>block</th><th>tx/log</th><th>a0_in</th><th>a1_in</th><th>a0_out</th><th>a1_out</th></tr></thead><tbody>${swaps
            .map(
              (swap) => `<tr>
              <td>${esc(swap.block_number)}</td>
              <td>${esc(swap.transaction_index)}/${esc(swap.log_index)}</td>
              <td>${esc(swap.amount0_in)}</td>
              <td>${esc(swap.amount1_in)}</td>
              <td>${esc(swap.amount0_out)}</td>
              <td>${esc(swap.amount1_out)}</td>
            </tr>`
            )
            .join("")}</tbody></table>`
        : "<p class='empty'>lookback 内无 Swap（或 getLogs 降级）。</p>";
      return `<div style="margin-bottom:18px">
        <h3 style="font-family:var(--mono);font-size:13px;margin:0 0 10px">${esc(pair)}<br><code>${esc(pool.address)}</code></h3>
        ${kv([
          ["rpc_verified", String(Boolean(item.rpc_verified))],
          ["base / quote", `${pool.base_symbol || "?"} ${pool.base_token || "—"} / ${pool.quote_symbol || "?"} ${pool.quote_token || "—"}`],
          ["token0 / token1", `${item.verification?.token0 || "—"} / ${item.verification?.token1 || "—"}`],
          ["reserve0 / reserve1", `${features.reserve0 ?? item.verification?.reserve0 ?? "—"} / ${features.reserve1 ?? item.verification?.reserve1 ?? "—"}`],
          ["mid_price", features.mid_price ?? "—"],
          ["price_impact_proxy", features.price_impact_proxy ?? "—"],
          ["buy / sell", `${features.buy_count ?? 0} / ${features.sell_count ?? 0}`],
          ["ofi_net_flow", features.ofi_net_flow ?? "—"],
          ["swap_count / density", `${features.swap_count ?? 0} / ${features.event_density ?? "—"}`],
          ["data_cutoff", item.data_cutoff ? `${item.data_cutoff.block_number}/${item.data_cutoff.transaction_index}/${item.data_cutoff.log_index}` : "—"],
          ["reason", (item.reason_codes || []).join(", ") || "—"],
          ["error_detail", item.error_detail || "—"],
        ])}
        <h4 style="margin:12px 0 6px;font-size:12px">recent_swaps</h4>
        ${swapRows}
      </div>`;
    })
    .join("");
  inferenceView.innerHTML = run.pools
    .map((item) => {
      const prediction = item.prediction || {};
      const decision = item.decision || {};
      const pool = item.pool || {};
      const features = item.features || {};
      return `<div style="margin-bottom:18px">
        <h3 style="font-family:var(--mono);font-size:13px;margin:0 0 10px">${esc(pool.pair_name || pool.address)}</h3>
        ${kv([
          ["decision", decision.status || "—"],
          ["paper", String(decision.paper ?? true)],
          ["decision reasons", (decision.reason_codes || []).join(", ") || "—"],
          ["prediction abstain", String(prediction.abstain ?? true)],
          ["prediction reasons", (prediction.reason_codes || []).join(", ") || "—"],
          ["calibration", prediction.calibration_status || "uncalibrated"],
          ["model / feature / label", `${prediction.model_version || "none"} / ${prediction.feature_version || "none"} / ${prediction.label_version || "none"}`],
          ["decision_time", item.decision_time || "—"],
          ["horizon_end", item.horizon_end || "—"],
          ["target", item.target_definition || "—"],
          ["feature snapshot", `swaps=${features.swap_count ?? 0}, ofi=${features.ofi_net_flow ?? "—"}, mid=${features.mid_price ?? "—"}`],
          ["risk", "unknown / not_supported → no-trade"],
        ])}
      </div>`;
    })
    .join("");
}

function parseGeckoPools(document, topK, providerDexId) {
  const included = Object.fromEntries((document.included || []).map((item) => [item.id, item]));
  const rows = [];
  for (const [index, row] of (document.data || []).entries()) {
    const dex = row.relationships?.dex?.data?.id || "";
    if (dex !== providerDexId && dex !== `bsc_${providerDexId}`) continue;
    const attrs = row.attributes || {};
    const baseId = row.relationships?.base_token?.data?.id;
    const quoteId = row.relationships?.quote_token?.data?.id;
    const base = included[baseId]?.attributes || {};
    const quote = included[quoteId]?.attributes || {};
    const tx = attrs.transactions?.h24 || {};
    rows.push({
      address: (attrs.address || "").toLowerCase(),
      network: "bsc",
      dex_id: "pancakeswap_v2",
      dex_name: "PancakeSwap V2",
      pair_name: attrs.name || null,
      base_token: (base.address || (baseId || "").split("_").pop() || "").toLowerCase(),
      quote_token: (quote.address || (quoteId || "").split("_").pop() || "").toLowerCase(),
      base_symbol: base.symbol || null,
      quote_symbol: quote.symbol || null,
      provider_rank: rows.length + 1,
      volume_24h_usd: Number(attrs.volume_usd?.h24 || 0),
      liquidity_usd: attrs.reserve_in_usd == null ? null : Number(attrs.reserve_in_usd),
      transactions_24h: Number(tx.buys || 0) + Number(tx.sells || 0),
      observed_at: attrs.updated_at || new Date().toISOString(),
      display_only: true,
      ranking_provider: "geckoterminal_browser",
      ranking_metric: "h24_volume_usd",
    });
    if (rows.length >= topK) break;
  }
  return rows;
}

async function discoverViaBrowser(topK) {
  const dexUrl = "https://api.geckoterminal.com/api/v2/networks/bsc/dexes";
  const url = "https://api.geckoterminal.com/api/v2/networks/bsc/pools?include=base_token,quote_token,dex&page=1&sort=h24_volume_usd_desc";
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const [dexResponse, response] = await Promise.all([fetch(dexUrl, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    }), fetch(url, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })]);
    if (!dexResponse.ok || !response.ok) throw new Error(`browser_http_${dexResponse.status}_${response.status}`);
    const dexDocument = await dexResponse.json();
    const providerDexId = (dexDocument.data || []).map((row) => String(row.id || "").replace(/^bsc_/, "")).find((id) => id === "pancakeswap_v2");
    if (!providerDexId) throw new Error("browser_dex_unmapped");
    const document = await response.json();
    const rows = parseGeckoPools(document, topK, providerDexId);
    if (!rows.length) throw new Error("browser_empty");
    return rows;
  } finally {
    clearTimeout(timer);
  }
}

async function loadHealth() {
  const response = await fetch("/api/health");
  const data = await response.json();
  renderHealth(data);
}

async function loadPools() {
  const top_k = Number(document.querySelector("#topK").value);
  try {
    const browserPools = await discoverViaBrowser(top_k);
    pools = browserPools;
    rankingProvider = "geckoterminal_browser";
    selected = new Set(pools.map((pool) => pool.address));
    renderPools();
    showStatus(`浏览器直连发现 ${pools.length} 个 Pancake V2 候选池。`);
    return;
  } catch (browserError) {
    showStatus(`浏览器 discovery 失败（${browserError.message}），改用服务端/bootstrap…`);
  }
  const response = await fetch(`/api/bsc/pools?top_k=${top_k}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || data.error || "source_unavailable");
  pools = data.pools;
  rankingProvider = data.ranking_provider || pools[0]?.ranking_provider || "server";
  selected = new Set(pools.map((pool) => pool.address));
  renderPools();
  showStatus(`发现 ${pools.length} 个候选池（source=${rankingProvider}）。`);
}

async function analyze() {
  const body = {
    paper: true,
    mode: "spot_long_only",
    top_k: Number(document.querySelector("#topK").value),
    lookback_blocks: Number(document.querySelector("#lookback").value),
    confirmation_lag: Number(document.querySelector("#lag").value),
    pool_addresses: [...selected],
  };
  showStatus("分析中：RPC 核验 + cutoff-safe Swap + abstain/no-trade…");
  const response = await fetch("/api/bsc/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    showStatus(`分析失败：${data.detail || data.error || "unknown"}`);
    return;
  }
  lastRun = data;
  resultNode.textContent = JSON.stringify(data, null, 2);
  if (data.pools?.length) {
    const byAddr = Object.fromEntries(pools.map((pool) => [pool.address, pool]));
    pools = data.pools.map((item) => ({ ...byAddr[item.pool.address], ...item.pool }));
    selected = new Set(pools.map((pool) => pool.address));
  }
  renderPools();
  renderAnalysis(data);
  summaryLink.href = `/api/runs/${data.run_id}`;
  eventsLink.href = `/api/runs/${data.run_id}/events`;
  showStatus(`run ${data.run_id} · quality=${data.quality} · pools=${data.pools?.length || 0} · source=${data.ranking_provider || rankingProvider}`);
}

function drawGraph(graph) {
  const nodes = (graph.nodes || []).filter((node) =>
    ["file", "module", "class", "function"].includes(node.kind)
  );
  const focus = nodes.filter((node) =>
    /bsc_pipeline|geckoterminal|bsc_rpc|run_store|web\.py|domain\.py|inference\.py/i.test(
      `${node.id} ${node.name || ""} ${node.path || ""}`
    )
  );
  const chosen = (focus.length ? focus : nodes).slice(0, 36);
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const placed = chosen.map((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(chosen.length, 1);
    const radius = 180 + (index % 3) * 40;
    return {
      ...node,
      x: width / 2 + Math.cos(angle) * radius,
      y: height / 2 + Math.sin(angle) * radius,
    };
  });
  const byId = Object.fromEntries(placed.map((node) => [node.id, node]));
  const edges = (graph.edges || []).filter((edge) => byId[edge.source] && byId[edge.target]);
  ctx.strokeStyle = "rgba(28,36,48,0.18)";
  ctx.lineWidth = 1;
  edges.slice(0, 120).forEach((edge) => {
    const a = byId[edge.source];
    const b = byId[edge.target];
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  });
  placed.forEach((node) => {
    ctx.beginPath();
    ctx.fillStyle = node.kind === "file" ? "#0f766e" : node.kind === "class" ? "#9a3412" : "#1c2430";
    ctx.arc(node.x, node.y, node.kind === "file" ? 7 : 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#1c2430";
    ctx.font = "12px IBM Plex Mono";
    const label = (node.name || node.id).split("/").pop();
    ctx.fillText(label.slice(0, 28), node.x + 10, node.y + 4);
  });
  graphMeta.textContent = `nodes=${graph.nodes?.length ?? 0} · edges=${graph.edges?.length ?? 0} · rendered=${placed.length}`;
}

async function loadGraphify() {
  try {
    const [graphResponse, reportResponse] = await Promise.all([
      fetch("/graphify-out/graph.json"),
      fetch("/graphify-out/GRAPH_REPORT.md"),
    ]);
    if (!graphResponse.ok) throw new Error("graph unavailable");
    const graph = await graphResponse.json();
    drawGraph(graph);
    if (reportResponse.ok) graphReport.textContent = await reportResponse.text();
  } catch (error) {
    graphMeta.textContent = `图谱暂不可用：${error.message}`;
  }
}

document.querySelector("#load").addEventListener("click", () => {
  loadPools().catch((error) => showStatus(error.message));
});
document.querySelector("#analyze").addEventListener("click", () => {
  analyze().catch((error) => showStatus(error.message));
});
document.querySelector("#lookback").value = "40";

loadHealth().catch(() => {
  healthTag.textContent = "offline";
});
loadPools().catch(() => showStatus("请启动服务；若外网不可用将自动使用 bootstrap 候选池。"));
loadGraphify();
