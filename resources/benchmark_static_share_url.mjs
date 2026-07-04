#!/usr/bin/env node
import { spawn } from "node:child_process";
import { existsSync, readFileSync, rmSync } from "node:fs";
import { mkdtemp } from "node:fs/promises";
import http from "node:http";
import https from "node:https";
import os from "node:os";
import path from "node:path";

const DEFAULT_CHROME_PATHS = [
  process.env.CHROME_BIN,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "google-chrome",
  "chromium",
].filter(Boolean);

const [url, expectedTotalRaw = "", expectedIdsRaw = ""] = process.argv.slice(2);
if (!url) {
  console.error("usage: node resources/benchmark_static_share_url.mjs URL [EXPECTED_TOTAL] [EXPECTED_FIRST_IDS_CSV]");
  process.exit(2);
}

const READINESS_TIMEOUT_MS = 120000;
const MOBILE_VIEWPORT = {
  width: 390,
  height: 844,
  deviceScaleFactor: 3,
  mobile: true,
};
const expectedTotal = expectedTotalRaw === "" ? null : Number(expectedTotalRaw);
const expectedFirstIds = expectedIdsRaw ? expectedIdsRaw.split(",").map(id => id.trim()).filter(Boolean) : [];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function httpRequestJson(url, { method = "GET" } = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method }, res => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", chunk => {
        body += chunk;
      });
      res.on("end", () => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`${method} ${url} returned ${res.statusCode}: ${body.slice(0, 200)}`));
          return;
        }
        try {
          resolve(JSON.parse(body));
        } catch (err) {
          reject(new Error(`invalid JSON from ${method} ${url}: ${err.message}`));
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

function httpHeadContentLength(url) {
  return new Promise(resolve => {
    let parsed;
    try {
      parsed = new URL(url);
    } catch {
      resolve(0);
      return;
    }
    const lib = parsed.protocol === "https:" ? https : http;
    const req = lib.request(url, { method: "HEAD" }, res => {
      const length = Number(res.headers["content-length"] || 0);
      res.resume();
      resolve(Number.isFinite(length) ? length : 0);
    });
    req.on("error", () => resolve(0));
    req.end();
  });
}

async function estimateCandidateChunkBytes(pageUrl, chunks = []) {
  if (!Array.isArray(chunks) || !chunks.length) return 0;
  let origin;
  try {
    origin = new URL(pageUrl).origin;
  } catch {
    return 0;
  }
  const lengths = await Promise.all(chunks.map(chunk =>
    httpHeadContentLength(`${origin}/data/lazy/rows/${encodeURIComponent(chunk)}.jsonl.gz`)
  ));
  return lengths.reduce((sum, length) => sum + length, 0);
}

async function waitForDevToolsPort(userDataDir, chrome) {
  const marker = path.join(userDataDir, "DevToolsActivePort");
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    if (chrome.exitCode !== null) {
      throw new Error(`Chrome exited before DevTools started with code ${chrome.exitCode}`);
    }
    if (existsSync(marker)) {
      const [portLine] = readFileSync(marker, "utf8").trim().split(/\r?\n/);
      const port = Number(portLine);
      if (Number.isFinite(port) && port > 0) return port;
    }
    await sleep(100);
  }
  throw new Error("timed out waiting for Chrome DevTools port");
}

async function findPageWebSocket(port) {
  const listUrl = `http://127.0.0.1:${port}/json/list`;
  for (let attempt = 0; attempt < 50; attempt += 1) {
    const targets = await httpRequestJson(listUrl).catch(() => []);
    const page = Array.isArray(targets)
      ? targets.find(target => target.type === "page" && target.webSocketDebuggerUrl)
      : null;
    if (page) return page.webSocketDebuggerUrl;
    await sleep(100);
  }
  const created = await httpRequestJson(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" });
  if (!created.webSocketDebuggerUrl) throw new Error("could not create a Chrome page target");
  return created.webSocketDebuggerUrl;
}

class CdpClient {
  constructor(webSocketUrl) {
    this.webSocketUrl = webSocketUrl;
    this.nextId = 1;
    this.pending = new Map();
    this.eventHandlers = [];
    this.ws = null;
  }

  async connect() {
    this.ws = new WebSocket(this.webSocketUrl);
    this.ws.addEventListener("message", event => this.handleMessage(event));
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("timed out connecting to Chrome websocket")), 10000);
      this.ws.addEventListener("open", () => {
        clearTimeout(timeout);
        resolve();
      }, { once: true });
      this.ws.addEventListener("error", err => {
        clearTimeout(timeout);
        reject(err.error || err);
      }, { once: true });
    });
  }

  handleMessage(event) {
    const message = JSON.parse(event.data);
    if (message.id && this.pending.has(message.id)) {
      const { resolve, reject } = this.pending.get(message.id);
      this.pending.delete(message.id);
      if (message.error) reject(new Error(`${message.error.message || "CDP error"} ${JSON.stringify(message.error.data || "")}`));
      else resolve(message.result || {});
      return;
    }
    this.eventHandlers.forEach(handler => handler(message));
  }

  onEvent(handler) {
    this.eventHandlers.push(handler);
  }

  send(method, params = {}) {
    const id = this.nextId;
    this.nextId += 1;
    const payload = JSON.stringify({ id, method, params });
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(payload);
    });
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

async function evaluate(cdp, expression, { awaitPromise = false } = {}) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    const text = result.exceptionDetails.text || JSON.stringify(result.exceptionDetails);
    throw new Error(`browser evaluation failed: ${text}\n${expression}`);
  }
  return result.result?.value;
}

async function waitForValue(cdp, expression, description, timeoutMs = READINESS_TIMEOUT_MS) {
  const deadline = Date.now() + timeoutMs;
  let lastValue = null;
  while (Date.now() < deadline) {
    lastValue = await evaluate(cdp, expression, { awaitPromise: true }).catch(err => ({ error: err.message }));
    if (lastValue && typeof lastValue === "object" && lastValue.ok) return lastValue;
    await sleep(100);
  }
  throw new Error(`timed out waiting for ${description}; last value: ${JSON.stringify(lastValue)}`);
}

async function waitForNetworkIdle(inFlight, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  let idleSince = null;
  while (Date.now() < deadline) {
    if (inFlight.size === 0) {
      idleSince ??= Date.now();
      if (Date.now() - idleSince >= 500) return;
    } else {
      idleSince = null;
    }
    await sleep(100);
  }
}

function requestPath(url) {
  try {
    return new URL(url).pathname;
  } catch {
    return "";
  }
}

function findChromePath() {
  for (const candidate of DEFAULT_CHROME_PATHS) {
    if (candidate.includes("/") && existsSync(candidate)) return candidate;
    if (!candidate.includes("/")) return candidate;
  }
  throw new Error("could not find Chrome; set CHROME_BIN");
}

function chromeFlags(userDataDir) {
  return [
    "--headless=new",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--enable-precise-memory-info",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-debugging-port=0",
    `--user-data-dir=${userDataDir}`,
    "about:blank",
  ];
}

function summarizeRequests(requests) {
  const byPath = new Map();
  for (const request of requests) {
    const current = byPath.get(request.path) || {
      count: 0,
      bytes: 0,
      methods: new Set(),
      statuses: new Set(),
      maxDurationMs: 0,
    };
    current.count += 1;
    current.bytes += request.encodedDataLength || 0;
    if (request.method) current.methods.add(request.method);
    if (request.status) current.statuses.add(request.status);
    current.maxDurationMs = Math.max(current.maxDurationMs, request.durationMs || 0);
    byPath.set(request.path, current);
  }
  return Object.fromEntries([...byPath.entries()].map(([key, value]) => [key, {
    count: value.count,
    bytes: value.bytes,
    methods: [...value.methods],
    statuses: [...value.statuses],
    maxDurationMs: Math.round(value.maxDurationMs),
  }]));
}

function bytesForPath(requests, pathname) {
  return requests
    .filter(item => item.path === pathname)
    .reduce((sum, item) => sum + (item.encodedDataLength || 0), 0);
}

function bytesForPrefix(requests, prefix) {
  return requests
    .filter(item => item.path.startsWith(prefix))
    .reduce((sum, item) => sum + (item.encodedDataLength || 0), 0);
}

function mb(bytes) {
  return Math.round((bytes / 1024 / 1024) * 10) / 10;
}

function scoreStaticRun(result) {
  const notes = [];
  let score = 0;
  const cache = result.pageState.workerCache || {};

  const totalOk = expectedTotal == null || result.pageState.total === expectedTotal;
  const idsOk = expectedFirstIds.length === 0
    || JSON.stringify(result.pageState.firstIds.slice(0, expectedFirstIds.length)) === JSON.stringify(expectedFirstIds);
  if (totalOk && idsOk) {
    score += 3;
    notes.push("+3 share URL correctness matched");
  } else {
    score -= 5;
    notes.push("-5 share URL total or first IDs changed");
  }

  if (result.dataJsonlBytes === 0 && result.pageState.dataRowsComplete === false) {
    score += 2;
    notes.push("+2 full data file was not loaded");
  } else {
    score -= 3;
    notes.push("-3 full data path was used");
  }

  if (cache.fallbackIndexesLoaded === false && Array.isArray(cache.indexesLoaded) && cache.indexesLoaded.length === 0) {
    score += 2;
    notes.push("+2 full field indexes were avoided");
  } else {
    notes.push("+0 full field indexes were loaded or worker cache was unavailable");
  }

  if ((cache.usedNgrams || cache.usedShortTokens || cache.usedWordEdges) && Number(cache.candidateCount) <= 2500) {
    score += 1;
    notes.push("+1 compact candidates were page-hydrated");
  } else {
    notes.push("+0 compact candidate path was not clearly used");
  }

  if (result.heapUsedBytes > 0 && mb(result.heapUsedBytes) <= 45) {
    score += 1;
    notes.push("+1 heap stayed under 45 MB in headless Chrome");
  } else {
    notes.push("+0 heap exceeded the local target or was unavailable");
  }

  const lazyTransferEstimate = result.lazyBytes || result.estimatedCandidateChunkBytes || 0;
  if (lazyTransferEstimate < 2_000_000) {
    score += 1;
    notes.push("+1 lazy transfer stayed under 2 MB");
  } else {
    notes.push("+0 lazy transfer exceeded 2 MB");
  }

  return {
    score,
    band: score >= 9 ? "excellent static path"
      : score >= 7 ? "good static path"
      : score >= 4 ? "usable but needs trimming"
      : "not good enough yet",
    totalOk,
    idsOk,
    notes,
  };
}

async function benchmarkStatic(url) {
  const chromePath = findChromePath();
  const userDataDir = await mkdtemp(path.join(os.tmpdir(), "nahuatl-static-benchmark-"));
  const chrome = spawn(chromePath, chromeFlags(userDataDir), {
    stdio: ["ignore", "ignore", "pipe"],
  });
  let stderr = "";
  chrome.stderr.setEncoding("utf8");
  chrome.stderr.on("data", chunk => {
    stderr += chunk;
  });

  const requests = [];
  const requestsById = new Map();
  const inFlight = new Set();
  let cdp = null;
  const startedAt = Date.now();
  try {
    const port = await waitForDevToolsPort(userDataDir, chrome);
    const wsUrl = await findPageWebSocket(port);
    cdp = new CdpClient(wsUrl);
    await cdp.connect();
    cdp.onEvent(message => {
      if (message.method === "Network.requestWillBeSent") {
        const request = message.params?.request || {};
        const item = {
          id: message.params?.requestId,
          method: request.method || "",
          url: request.url || "",
          path: requestPath(request.url || ""),
          type: message.params?.type || "",
          startTimestamp: message.params?.timestamp || 0,
          status: 0,
          encodedDataLength: 0,
          durationMs: 0,
        };
        requests.push(item);
        if (item.id) requestsById.set(item.id, item);
        if (item.id) inFlight.add(item.id);
      } else if (message.method === "Network.responseReceived") {
        const item = requestsById.get(message.params?.requestId);
        if (item) item.status = message.params?.response?.status || 0;
      } else if (message.method === "Network.loadingFinished") {
        const item = requestsById.get(message.params?.requestId);
        if (item) {
          item.encodedDataLength = message.params?.encodedDataLength || 0;
          if (item.startTimestamp && message.params?.timestamp) {
            item.durationMs = (message.params.timestamp - item.startTimestamp) * 1000;
          }
        }
        if (message.params?.requestId) inFlight.delete(message.params.requestId);
      } else if (message.method === "Network.loadingFailed") {
        if (message.params?.requestId) inFlight.delete(message.params.requestId);
      }
    });

    await cdp.send("Network.enable");
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", MOBILE_VIEWPORT);
    await cdp.send("Emulation.setUserAgentOverride", {
      userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    });
    await cdp.send("Page.navigate", { url });

    await waitForValue(cdp, `(() => {
      const rows = Array.isArray(lastRenderRows) ? lastRenderRows : [];
      const statusText = document.getElementById("tableStatus")?.textContent?.trim() || "";
      const total = Number(lastRenderTotal || 0);
      const ready = document.readyState === "complete"
        && (rows.length > 0 || total === 0)
        && statusText
        && !/cargando|loading|servidor|required/i.test(statusText);
      return { ok: ready, rows: rows.length, total, statusText };
    })()`, "first rows");
    const firstRowsMs = Date.now() - startedAt;

    const settled = await waitForValue(cdp, `(() => {
      const rows = Array.isArray(lastRenderRows) ? lastRenderRows : [];
      const statusText = document.getElementById("tableStatus")?.textContent?.trim() || "";
      const total = Number(lastRenderTotal || 0);
      const ready = document.readyState === "complete"
        && (rows.length > 0 || total === 0)
        && (typeof fullDataLoadPromise === "undefined" || !fullDataLoadPromise)
        && (typeof lazyQueryPromise === "undefined" || !lazyQueryPromise)
        && (typeof lazyWorkerQueryPromise === "undefined" || !lazyWorkerQueryPromise)
        && (typeof lazyHydrationPromise === "undefined" || !lazyHydrationPromise)
        && !/cargando|loading|servidor|required/i.test(statusText);
      return { ok: ready, rows: rows.length, total, statusText };
    })()`, "settled rows");
    await waitForNetworkIdle(inFlight, 1000).catch(() => {});
    const settledMs = Date.now() - startedAt;

    const pageState = await evaluate(cdp, `(() => {
      const rows = Array.isArray(lastRenderRows) ? lastRenderRows : [];
      const workerResult = typeof lazyWorkerResult !== "undefined" ? lazyWorkerResult : null;
      return {
        endpoint: typeof getSearchApiEndpoint === "function" ? getSearchApiEndpoint() : "",
        staticMode: typeof isStaticFallbackMode === "function" ? isStaticFallbackMode() : null,
        dataRows: typeof dataRows !== "undefined" && Array.isArray(dataRows) ? dataRows.length : null,
        dataRowsComplete: typeof dataRowsComplete !== "undefined" ? Boolean(dataRowsComplete) : null,
        renderedRows: rows.length,
        total: Number(lastRenderTotal || 0),
        firstIds: rows.slice(0, 5).map(row => row.record_id || row.eid || row._rid || ""),
        statusText: document.getElementById("tableStatus")?.textContent?.trim() || "",
        pageSize: Number(maxDisplayRows || 0),
        workerCache: workerResult?.cache || null,
      };
    })()`, { awaitPromise: true });
    const heapUsage = await cdp.send("Runtime.getHeapUsage").catch(() => ({}));
    const totalBytes = requests.reduce((sum, item) => sum + (item.encodedDataLength || 0), 0);
    const estimatedCandidateChunkBytes = await estimateCandidateChunkBytes(
      url,
      pageState.workerCache?.candidateChunks || []
    );
    const result = {
      url,
      firstRowsMs,
      settledMs,
      settled,
      totalBytes,
      heapUsedBytes: heapUsage.usedSize || 0,
      heapTotalBytes: heapUsage.totalSize || 0,
      dataJsonlBytes: bytesForPath(requests, "/data/data.jsonl.gz"),
      lazyBytes: bytesForPrefix(requests, "/data/lazy/"),
      shortTokenBytes: bytesForPrefix(requests, "/data/lazy/short-tokens/"),
      ngramBytes: bytesForPrefix(requests, "/data/lazy/ngrams/"),
      indexBytes: bytesForPrefix(requests, "/data/lazy/indexes/"),
      rowChunkBytes: bytesForPrefix(requests, "/data/lazy/rows/"),
      estimatedCandidateChunkBytes,
      pageState,
      requests: summarizeRequests(requests),
    };
    return {
      score: scoreStaticRun(result),
      summary: {
        firstRowsMs: result.firstRowsMs,
        settledMs: result.settledMs,
        totalBytesMb: mb(result.totalBytes),
        heapUsedMb: mb(result.heapUsedBytes),
        dataJsonlBytesMb: mb(result.dataJsonlBytes),
        lazyBytesMb: mb(result.lazyBytes),
        shortTokenBytesKb: Math.round(result.shortTokenBytes / 1024),
        ngramBytesKb: Math.round(result.ngramBytes / 1024),
        indexBytesKb: Math.round(result.indexBytes / 1024),
        rowChunkBytesMb: mb(result.rowChunkBytes),
        estimatedCandidateChunkBytesMb: mb(result.estimatedCandidateChunkBytes),
        viewport: MOBILE_VIEWPORT,
        pageState: result.pageState,
      },
      requests: result.requests,
    };
  } finally {
    if (cdp) cdp.close();
    if (chrome.exitCode === null) {
      chrome.kill("SIGTERM");
      await new Promise(resolve => {
        const timeout = setTimeout(resolve, 2000);
        chrome.once("exit", () => {
          clearTimeout(timeout);
          resolve();
        });
      });
      if (chrome.exitCode === null) chrome.kill("SIGKILL");
    }
    rmSync(userDataDir, { recursive: true, force: true });
    if (process.env.NAHUATL_BENCHMARK_CHROME_LOG === "1" && stderr.trim()) {
      console.error(stderr.trim());
    }
  }
}

const report = await benchmarkStatic(url);
console.log(JSON.stringify(report, null, 2));
process.exit(report.score.totalOk && report.score.idsOk && report.score.score >= 7 ? 0 : 1);
