#!/usr/bin/env node
import { spawn } from "node:child_process";
import { existsSync, readFileSync, rmSync } from "node:fs";
import { mkdtemp } from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const DEFAULT_CHROME_PATHS = [
  process.env.CHROME_BIN,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "google-chrome",
  "chromium",
].filter(Boolean);

const appUrl = process.argv[2];
if (!appUrl) {
  console.error("usage: node resources/browser_backend_network_proof.mjs http://127.0.0.1:PORT/index.html");
  process.exit(2);
}

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

async function waitForExpression(cdp, expression, description, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const ok = await evaluate(cdp, `Boolean(${expression})`).catch(() => false);
    if (ok) return;
    await sleep(100);
  }
  throw new Error(`timed out waiting for ${description}`);
}

function requestPath(url) {
  try {
    return new URL(url).pathname;
  } catch {
    return "";
  }
}

async function waitForRequestCount(requests, pathname, minCount, description, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const count = requests.filter(item => item.path === pathname).length;
    if (count >= minCount) return;
    await sleep(100);
  }
  throw new Error(`timed out waiting for ${description} (${pathname})`);
}

async function waitForNetworkIdle(inFlight, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  let idleSince = null;
  while (Date.now() < deadline) {
    if (inFlight.size === 0) {
      idleSince ??= Date.now();
      if (Date.now() - idleSince >= 400) return;
    } else {
      idleSince = null;
    }
    await sleep(100);
  }
}

async function runStep(cdp, requests, inFlight, label, waitPath, expression, waitAfterExpression = "true") {
  const before = requests.filter(item => item.path === waitPath).length;
  await evaluate(cdp, expression, { awaitPromise: true });
  await waitForRequestCount(requests, waitPath, before + 1, label);
  await waitForNetworkIdle(inFlight);
  if (waitAfterExpression !== "true") {
    await waitForExpression(cdp, waitAfterExpression, `${label} completion`);
  }
}

function findChromePath() {
  for (const candidate of DEFAULT_CHROME_PATHS) {
    if (candidate.includes("/") && existsSync(candidate)) return candidate;
    if (!candidate.includes("/")) return candidate;
  }
  throw new Error("could not find Chrome; set CHROME_BIN");
}

async function main() {
  const chromePath = findChromePath();
  const userDataDir = await mkdtemp(path.join(os.tmpdir(), "nahuatl-backend-proof-"));
  const chrome = spawn(chromePath, [
    "--headless=new",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-debugging-port=0",
    `--user-data-dir=${userDataDir}`,
    "about:blank",
  ], {
    stdio: ["ignore", "ignore", "pipe"],
  });

  let stderr = "";
  chrome.stderr.setEncoding("utf8");
  chrome.stderr.on("data", chunk => {
    stderr += chunk;
  });

  let cdp = null;
  const requests = [];
  const inFlight = new Set();
  try {
    const port = await waitForDevToolsPort(userDataDir, chrome);
    const wsUrl = await findPageWebSocket(port);
    cdp = new CdpClient(wsUrl);
    await cdp.connect();

    cdp.onEvent(message => {
      if (message.method === "Network.requestWillBeSent") {
        const request = message.params?.request || {};
        const pathname = requestPath(request.url || "");
        requests.push({
          id: message.params?.requestId,
          method: request.method || "",
          url: request.url || "",
          path: pathname,
          type: message.params?.type || "",
        });
        if (message.params?.requestId && pathname.startsWith("/api/")) inFlight.add(message.params.requestId);
      } else if (message.method === "Network.loadingFinished" || message.method === "Network.loadingFailed") {
        if (message.params?.requestId) inFlight.delete(message.params.requestId);
      }
    });

    await cdp.send("Network.enable");
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Page.navigate", { url: appUrl });

    await waitForExpression(cdp, "document.readyState === 'complete'", "document load");
    await waitForRequestCount(requests, "/api/sources", 1, "source metadata");
    await waitForRequestCount(requests, "/api/search", 1, "initial search");
    await waitForNetworkIdle(inFlight);
    await waitForExpression(cdp, "typeof getSearchApiEndpoint === 'function' && getSearchApiEndpoint() === '/api/search'", "advertised search API");

    await runStep(
      cdp,
      requests,
      inFlight,
      "filtered table search",
      "/api/search",
      `(() => {
        activeFilters = [];
        displayOffset = 0;
        maxDisplayRows = 25;
        const pageSize = document.getElementById("pageSizeSelect");
        if (pageSize) pageSize.value = "25";
        appendFilter("Editado", "any", "nemi", "AND", false, "word");
        applyFilters();
        return true;
      })()`,
      "typeof searchApiQueryPromise === 'undefined' || searchApiQueryPromise === null"
    );
    await waitForExpression(cdp, "lastRenderTotal > maxDisplayRows && !document.getElementById('pageNext')?.disabled", "a second result page");

    await runStep(
      cdp,
      requests,
      inFlight,
      "pagination",
      "/api/search",
      `(() => {
        document.getElementById("pageNext").click();
        return true;
      })()`,
      "displayOffset > 0 && (typeof searchApiQueryPromise === 'undefined' || searchApiQueryPromise === null)"
    );

    await runStep(
      cdp,
      requests,
      inFlight,
      "lemma page search",
      "/api/search",
      `(() => {
        setViewMode("lemmas");
        return true;
      })()`,
      "document.querySelector('.lemma-toggle') && Array.isArray(lastLemmaItems) && lastLemmaItems.length > 0"
    );

    await runStep(
      cdp,
      requests,
      inFlight,
      "lemma detail expansion",
      "/api/lemma",
      `(() => {
        document.querySelector(".lemma-toggle").click();
        return true;
      })()`,
      "document.querySelector('.lemma-detail-row')"
    );

    await runStep(
      cdp,
      requests,
      inFlight,
      "pair finder",
      "/api/pairs",
      `(() => {
        document.getElementById("tab-pairsPanel").click();
        document.getElementById("pairFindBtn").click();
        return true;
      })()`,
      "document.getElementById('pairResults')?.textContent?.trim().length > 0"
    );

    await runStep(
      cdp,
      requests,
      inFlight,
      "study deck",
      "/api/study",
      `(() => {
        document.getElementById("tab-studyPanel").click();
        const useFilters = document.getElementById("studyUseFilters");
        if (useFilters) useFilters.checked = true;
        const limit = document.getElementById("studyLimit");
        if (limit) limit.value = "5";
        document.getElementById("studyBuildBtn").click();
        return true;
      })()`,
      "document.getElementById('studyCardCount')?.textContent !== '0/0' || document.getElementById('studyFront')?.textContent?.length > 0"
    );

    await runStep(
      cdp,
      requests,
      inFlight,
      "CSV export",
      "/api/export",
      `(async () => {
        window.__backendProofCsv = await queryExportApi(getExportApiPayload());
        return true;
      })()`,
      "window.__backendProofCsv && window.__backendProofCsv.length > 20"
    );

    const requiredBackend = ["/api/sources", "/api/search", "/api/lemma", "/api/pairs", "/api/study", "/api/export"];
    const missingBackend = requiredBackend.filter(pathname => !requests.some(item => item.path === pathname));
    if (missingBackend.length) {
      throw new Error(`missing required backend requests: ${missingBackend.join(", ")}`);
    }

    const requiredShell = ["/index.html", "/script.js", "/style.css"];
    const missingShell = requiredShell.filter(pathname => !requests.some(item => item.path === pathname));
    if (missingShell.length) {
      throw new Error(`missing required app shell requests: ${missingShell.join(", ")}`);
    }

    const forbidden = requests.filter(item => (
      item.path === "/data/bootstrap.js"
      || item.path === "/data/data.jsonl.gz"
      || item.path.startsWith("/data/lazy/")
      || item.path === "/search-worker.js"
    ));
    if (forbidden.length) {
      const seen = [...new Set(forbidden.map(item => item.path))].join(", ");
      throw new Error(`browser requested forbidden static search assets: ${seen}`);
    }

    console.log(`ok - browser backend proof requested ${requiredBackend.join(", ")}`);
    console.log(`ok - browser backend proof requested normal app shell assets ${requiredShell.join(", ")}`);
    console.log("ok - browser backend proof did not request data/bootstrap.js, data/data.jsonl.gz, data/lazy/*, or search-worker.js");
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
    if (process.env.NAHUATL_PROOF_CHROME_LOG === "1" && stderr.trim()) {
      console.error(stderr.trim());
    }
  }
}

main().catch(err => {
  console.error(`error - ${err.message}`);
  process.exit(1);
});
