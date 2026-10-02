"""SPC v0.6.0 — SAZ Proxy Collector — THE SAZ"""
import asyncio, base64, json, os, re, time, datetime, hashlib, sys
from pathlib import Path
from urllib.parse import urlparse
import aiohttp, jdatetime

# ---------------- Config ----------------
def _int(name: str, default: int) -> int:
    try: return int(os.getenv(name, "") or default)
    except (TypeError, ValueError): return default

API_ID   = _int("TELEGRAM_API_ID", 0)
API_HASH = (os.getenv("TELEGRAM_API_HASH") or "").strip()
SESSION  = (os.getenv("TELEGRAM_SESSION") or "").strip()

CHANNELS = [
    "@v2ray_configs_pools", "@configms", "@V2RootConfigPilot",
    "@ROJproxy", "@ProxyMTProto", "@mtproxy_iran", "@socks5_proxy_iran",
]
TOP_C, TOP_P, MSG_LIMIT = 50, 30, 400
TIMEOUT = max(1, _int("SPC_TIMEOUT", 5))
CONC    = max(1, min(200, _int("SPC_CONC", 80)))

DATA = Path("docs/data")
DOCS = Path("docs")
DATA.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

# ---------------- Regex ----------------
CFG_RE = {
    "vmess":  re.compile(r"vmess://[A-Za-z0-9+/=_\-]+", re.I),
    "vless":  re.compile(r"vless://[^\s\"'<>`\\]+", re.I),
    "trojan": re.compile(r"trojan://[^\s\"'<>`\\]+", re.I),
    "ss":     re.compile(r"ss://[^\s\"'<>`\\]+", re.I),
}
PRX_RE = re.compile(
    r"(?:https?://(?:t|telegram)\.me/proxy\?|tg://proxy\?)"
    r"server=[^&\s\"'<>]+&port=\d+&secret=[A-Za-z0-9_\-]+", re.I)

# ---------------- Telegram Scraper ----------------
async def scrape() -> list[str]:
    if not (API_ID and API_HASH and SESSION):
        print("[!] Telegram credentials missing — skipping scrape.", file=sys.stderr)
        return []
    try:
        from pyrogram import Client
    except ImportError:
        print("[!] pyrogram not installed.", file=sys.stderr)
        return []
    texts: list[str] = []
    try:
        async with Client("spc", api_id=API_ID, api_hash=API_HASH,
                          session_string=SESSION, in_memory=True) as app:
            for ch in CHANNELS:
                try:
                    async for m in app.get_chat_history(ch, limit=MSG_LIMIT):
                        t = (m.text or m.caption or "").strip()
                        if t: texts.append(t)
                except Exception as e:
                    print(f"[!] {ch}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[!] Telegram: {e}", file=sys.stderr)
    return texts

# ---------------- Parsers ----------------
def _vmess_host_port(uri: str) -> tuple[str, int]:
    try:
        payload = uri.split("://", 1)[1].split("#", 1)[0].split("?", 1)[0]
        payload += "=" * (-len(payload) % 4)
        raw = base64.b64decode(payload).decode("utf-8", "ignore")
        data = json.loads(raw)
        return str(data.get("add", "")), int(data.get("port", 0) or 0)
    except Exception:
        return "", 0

def _uri_host_port(uri: str) -> tuple[str, int]:
    try:
        u = urlparse(uri)
        return u.hostname or "", u.port or 0
    except Exception:
        return "", 0

def parse_configs(texts: list[str]) -> list[dict]:
    seen, out = set(), []
    for t in texts:
        for proto, rx in CFG_RE.items():
            for m in rx.findall(t):
                uri = m.strip().rstrip(".,;!؟)]}`\"'\\")
                if not uri or uri in seen: continue
                seen.add(uri)
                h, p = (_vmess_host_port if proto == "vmess" else _uri_host_port)(uri)
                if not h or not p: continue
                out.append({"proto": proto, "raw": uri, "_h": h, "_p": p})
    return out

def parse_proxies(texts: list[str]) -> list[dict]:
    seen, out = set(), []
    for t in texts:
        for m in PRX_RE.findall(t):
            uri = m.strip()
            if not uri or uri in seen: continue
            seen.add(uri)
            s = re.search(r"server=([^&]+)", uri)
            p = re.search(r"port=(\d+)", uri)
            if not s or not p: continue
            out.append({"raw": uri, "_h": s.group(1), "_p": int(p.group(1))})
    return out

# ---------------- Validator ----------------
async def _tcp(h: str, p: int) -> float | None:
    if not h or not p or p < 1 or p > 65535: return None
    s = time.perf_counter()
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(h, p), TIMEOUT)
        lat = round((time.perf_counter() - s) * 1000, 1)
        w.close()
        try: await w.wait_closed()
        except Exception: pass
        return lat
    except Exception:
        return None

async def validate(items: list[dict]) -> list[dict]:
    if not items: return []
    sem = asyncio.Semaphore(CONC)
    async def task(it):
        async with sem:
            it["lat"] = await _tcp(it["_h"], it["_p"])
            return it
    return await asyncio.gather(*[task(i) for i in items])

def rank(items: list[dict], top: int) -> list[dict]:
    alive = [i for i in items if i.get("lat") is not None]
    alive.sort(key=lambda x: x["lat"])
    seen, out = set(), []
    for i in alive:
        k = (i["_h"], i["_p"])
        if k in seen: continue
        seen.add(k); out.append(i)
        if len(out) >= top: break
    return out

# ---------------- GeoIP ----------------
async def geo_lookup(hosts: list[str]) -> dict[str, str]:
    ips = sorted({h for h in hosts if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", h or "")})
    if not ips: return {}
    out: dict[str, str] = {}
    async with aiohttp.ClientSession() as s:
        for i in range(0, len(ips), 100):
            batch = ips[i:i+100]
            try:
                async with s.post(
                    "http://ip-api.com/batch?fields=countryCode,query",
                    json=batch, timeout=aiohttp.ClientTimeout(total=12)
                ) as r:
                    if r.status == 200:
                        for it in await r.json():
                            out[it.get("query", "")] = (it.get("countryCode") or "").upper()
            except Exception as e:
                print(f"[!] GeoIP batch: {e}", file=sys.stderr)
    return out

# ---------------- History ----------------
def update_history(keys: list[str]) -> dict[str, int]:
    f = DATA / "history.json"
    hist: dict = {}
    if f.exists():
        try: hist = json.loads(f.read_text("utf-8")) or {}
        except Exception: hist = {}
    now = int(time.time())
    for k in keys:
        rec = hist.get(k) or {"n": 0, "first": now}
        rec["n"] = int(rec.get("n", 0)) + 1
        rec["last"] = now
        hist[k] = rec
    cutoff = now - 30 * 86400
    hist = {k: v for k, v in hist.items() if v.get("last", 0) > cutoff}
    f.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), "utf-8")
    return {k: v["n"] for k, v in hist.items()}

# ---------------- Live Data ----------------
async def prices() -> dict:
    out = {"usd": None, "eur": None}
    urls = [
        ("usd", "https://api.priceto.day/v1/latest/irr/usd"),
        ("eur", "https://api.priceto.day/v1/latest/irr/euro"),
        ("usd", "https://api.priceto.day/v1/latest/irr/dollar"),
        ("eur", "https://api.priceto.day/v1/latest/irr/eur"),
        ("usd", "https://api.priceto.day/v1/latest/irr/USD"),
        ("eur", "https://api.priceto.day/v1/latest/irr/EUR"),
    ]
    to = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=to) as s:
        for k, u in urls:
            if out[k] is not None: continue
            try:
                async with s.get(u) as r:
                    if r.status == 200:
                        d = await r.json()
                        v = d.get("value") or d.get("price") or 0
                        if v and float(v) > 0:
                            out[k] = round(float(v) / 10)
            except Exception: pass
    # Partial cache save
    f = DATA / "prices_cache.json"
    if out["usd"] or out["eur"]:
        try:
            cached = json.loads(f.read_text("utf-8")) if f.exists() else {}
        except Exception: cached = {}
        cached.update({k: v for k, v in out.items() if v})
        f.write_text(json.dumps(cached), "utf-8")
        for k in ("usd", "eur"):
            if out[k] is None and cached.get(k): out[k] = cached[k]
    return out

async def tehran() -> dict:
    to = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=to) as s:
            async with s.get("https://worldtimeapi.org/api/timezone/Asia/Tehran") as r:
                if r.status == 200:
                    d = await r.json()
                    dt = datetime.datetime.fromisoformat(d["datetime"])
                    j = jdatetime.date.fromgregorian(date=dt.date())
                    return {"j": j.strftime("%Y/%m/%d"), "w": j.strftime("%A"),
                            "t": dt.strftime("%H:%M")}
    except Exception: pass
    n = datetime.datetime.now()
    j = jdatetime.date.fromgregorian(date=n.date())
    return {"j": j.strftime("%Y/%m/%d"), "w": j.strftime("%A"), "t": n.strftime("%H:%M")}

# ---------------- Subscription ----------------
def write_subscription(configs: list[dict]):
    text = "\n".join(c["raw"] for c in configs if c.get("raw"))
    (DOCS / "sub.txt").write_text(text, "utf-8")
    (DOCS / "sub64.txt").write_text(base64.b64encode(text.encode()).decode(), "utf-8")

# ---------------- Build ----------------
async def main():
    print("[*] Telegram scrape...")
    texts = await scrape()
    print(f"    {len(texts)} messages")

    cfgs = await validate(parse_configs(texts))
    prxs = await validate(parse_proxies(texts))
    top_c, top_p = rank(cfgs, TOP_C), rank(prxs, TOP_P)
    print(f"[✓] alive: {len(top_c)} configs, {len(top_p)} proxies")

    print("[*] GeoIP...")
    geo = await geo_lookup([c["_h"] for c in top_c] + [p["_h"] for p in top_p])

    print("[*] History...")
    keys = [hashlib.sha1(c["raw"].encode()).hexdigest()[:12] for c in top_c + top_p]
    stab = update_history(keys)

    print("[*] Live data...")
    p = await prices()
    t = await tehran()

    def pack(item, is_cfg):
        k = hashlib.sha1(item["raw"].encode()).hexdigest()[:12]
        d = {"raw": item["raw"], "lat": item["lat"],
             "cc": geo.get(item["_h"], ""), "stab": stab.get(k, 1)}
        if is_cfg: d["proto"] = item["proto"]
        else: d.update({"s": item["_h"], "port": item["_p"]})
        return d

    _w("configs.json", [pack(c, True) for c in top_c])
    _w("proxies.json", [pack(x, False) for x in top_p])
    _w("meta.json", {
        "version": "0.6.0",
        "usd": p["usd"], "eur": p["eur"], "date": t,
        "updated": int(time.time()),
        "next": int(time.time()) + 12 * 3600,
        "counts": {"c": len(top_c), "p": len(top_p)},
        "avg_c": round(sum(c["lat"] for c in top_c) / max(len(top_c), 1), 1),
        "avg_p": round(sum(c["lat"] for c in top_p) / max(len(top_p), 1), 1),
        "best_c": min((c["lat"] for c in top_c), default=None),
        "best_p": min((c["lat"] for c in top_p), default=None),
    })
    write_subscription(top_c)
    print("[✓] v0.6.0 done.")

def _w(name: str, data):
    (DATA / name).write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")

if __name__ == "__main__":
    asyncio.run(main())
