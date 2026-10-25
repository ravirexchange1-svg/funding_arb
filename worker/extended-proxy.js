// Cloudflare Worker: relays two public feeds that do not send CORS headers, so a browser page can read them.
//   /extended       -> Extended's markets list
//   /aster-funding  -> Aster's funding history (symbol, startTime, endTime, limit)
//   /extended-funding -> Extended's funding history (market, startTime, endTime, limit)
const EXTENDED = "https://api.starknet.extended.exchange/api/v1/info/markets";
const ASTER_FUNDING = "https://fapi.asterdex.com/fapi/v1/fundingRate";
const CORS = { "access-control-allow-origin": "*", "access-control-allow-methods": "GET" };

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(request.url);
    let upstream;
    if (url.pathname === "/aster-funding") {
      const q = new URLSearchParams();
      for (const k of ["symbol", "startTime", "endTime", "limit"]) if (url.searchParams.has(k)) q.set(k, url.searchParams.get(k));
      upstream = ASTER_FUNDING + "?" + q;
    } else if (url.pathname === "/extended-funding") {
      const q = new URLSearchParams();
      for (const k of ["startTime", "endTime", "limit"]) if (url.searchParams.has(k)) q.set(k, url.searchParams.get(k));
      upstream = `https://api.starknet.extended.exchange/api/v1/info/${encodeURIComponent(url.searchParams.get("market") || "")}/funding?` + q;
    } else if (url.pathname === "/extended" || url.pathname === "/") {
      upstream = EXTENDED;
    } else {
      return new Response("not found", { status: 404, headers: CORS });
    }
    const res = await fetch(upstream, { cf: { cacheTtl: 5, cacheEverything: true } });
    return new Response(res.body, { status: res.status, headers: { ...CORS, "content-type": "application/json", "cache-control": "public, max-age=5" } });
  },
};
