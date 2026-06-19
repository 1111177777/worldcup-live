/**
 * 世界杯在线人数计数器 — Deno Deploy
 * 部署: deno deploy --entrypoint counter_deno.ts
 */
const kv = await Deno.openKv();

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  };

  // CORS
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        ...headers,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  }

  // POST /hb — 心跳
  if (url.pathname === "/hb" && req.method === "POST") {
    try {
      const { sid } = await req.json();
      if (sid) {
        await kv.set(["session", sid], Date.now(), { expireIn: 60000 });
      }
      let count = 0;
      for await (const _ of kv.list({ prefix: ["session"] })) count++;
      return new Response(JSON.stringify({ online: count }), { headers });
    } catch (_) {
      return new Response(JSON.stringify({ online: 0 }), { headers });
    }
  }

  // GET /count
  if (url.pathname === "/count") {
    try {
      let count = 0;
      for await (const _ of kv.list({ prefix: ["session"] })) count++;
      return new Response(JSON.stringify({ online: count }), { headers });
    } catch (_) {
      return new Response(JSON.stringify({ online: 0 }), { headers });
    }
  }

  return new Response("404", { status: 404, headers });
});
