/**
 * 世界杯在线人数计数器 — Cloudflare Worker
 * 部署: npx wrangler deploy counter_worker.js
 * 需要创建 KV namespace: wrangler kv:namespace create "ONLINE"
 */
export default {
  async fetch(request, env) {
    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    const url = new URL(request.url);
    const headers = {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    };

    // POST /hb — 心跳：客户端每30秒发一次
    if (url.pathname === '/hb' && request.method === 'POST') {
      try {
        const { sid } = await request.json();
        if (sid) {
          // 写入 KV，60秒后自动过期。如果60秒内没心跳，认为离线
          await env.ONLINE.put(`u:${sid}`, Date.now().toString(), { expirationTtl: 60 });
        }
        // 统计当前在线
        const list = await env.ONLINE.list();
        return new Response(JSON.stringify({ online: list.keys.length }), { headers });
      } catch (e) {
        return new Response(JSON.stringify({ online: 0, error: e.message }), { status: 500, headers });
      }
    }

    // GET /count — 查询当前在线人数（不更新自己）
    if (url.pathname === '/count') {
      try {
        const list = await env.ONLINE.list();
        return new Response(JSON.stringify({ online: list.keys.length }), { headers });
      } catch (e) {
        return new Response(JSON.stringify({ online: 0 }), { headers });
      }
    }

    return new Response('404', { status: 404 });
  }
};
