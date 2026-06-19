// POST /hb — 心跳
export async function onRequestPost({ env, request }) {
  try {
    const { sid } = await request.json();
    if (sid) {
      await env.ONLINE.put(`u:${sid}`, String(Date.now()), { expirationTtl: 60 });
    }
    const list = await env.ONLINE.list();
    return new Response(JSON.stringify({ online: list.keys.length }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  } catch (e) {
    return new Response(JSON.stringify({ online: 0 }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }
}
