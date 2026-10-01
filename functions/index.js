export async function onRequestGet({ request, env }) {
  const ua = request.headers.get('user-agent') || '';
  const cli = /^(curl|wget|httpie|xh)\b/i.test(ua);
  const url = new URL(request.url);
  if (cli) url.pathname = '/index.txt';
  const res = await env.ASSETS.fetch(new Request(url, request));
  const headers = new Headers(res.headers);
  headers.set('vary', 'User-Agent');
  if (cli) headers.set('content-type', 'text/plain; charset=utf-8');
  const colo = request.cf?.colo;
  const body = colo ? (await res.text()).replace('from localhost', `from ${colo}`) : res.body;
  return new Response(body, { status: res.status, headers });
}

export const onRequestHead = onRequestGet;
