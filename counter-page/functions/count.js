// GET /count — 查询在线人数
export async function onRequestGet({ env }) {
  try {
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
