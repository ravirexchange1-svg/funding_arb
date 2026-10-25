// Cloudflare Worker: relays Extended's public markets feed and adds the CORS header
// that api.starknet.extended.exchange does not send, so a browser page can read it.
const UPSTREAM = "https://api.starknet.extended.exchange/api/v1/info/markets";

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: { "access-control-allow-origin": "*", "access-control-allow-methods": "GET" } });
    }
    const res = await fetch(UPSTREAM, { cf: { cacheTtl: 5, cacheEverything: true } });
    return new Response(res.body, {
      status: res.status,
      headers: { "content-type": "application/json", "access-control-allow-origin": "*", "cache-control": "public, max-age=5" },
    });
  },
};
