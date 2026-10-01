const out = document.getElementById('out');
const input = document.getElementById('cmd');
const form = document.getElementById('f');
const tpl = id => document.getElementById(id).innerHTML.trim();
const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const err = s => `<span class="err">${s}</span>`;
const go = u => { location.href = u; return null; };
const PROMPT = '<span class="d">~</span>\n<span class="p">❯</span>';
const login = document.getElementById('login');
const BOOT = Date.parse(login.dataset.built) || Date.now();
const colo = (/from (\S+)/.exec(login.textContent) || [])[1] || 'localhost';
const links = { __proto__: null };
for (const a of document.querySelectorAll('#ls a')) links[a.textContent] = a.getAttribute('href');
const email = (links.email || '').replace('mailto:', '');
const files = {
  __proto__: null,
  about: tpl('about'),
  resume: `<a href="/resume">/resume</a>  <a href="/resume.pdf">/resume.pdf</a>`,
  pgp: `<a href="/cwel.asc">/cwel.asc</a>\ngpg --locate-keys ${esc(email)}`,
};
const logo = `.----------.
| <span class="d">~</span>        |
| <span class="p">❯</span> <span class="c">▮</span>      |
'----------'`;
const ICONS = { host: '\u{f01c5}', os: '\u{f07fe}', kernel: '\uf013', uptime: '\u{f0150}', shell: '\uf489', term: '\ue795', network: '\u{f0a5f}', colors: '\u{f03d8}' };
const HUES = ['d', 'p', 'y', 'g', 'k'];
function browser() {
  const ua = navigator.userAgent;
  for (const [n, re] of [['Edge', /Edg\/(\d+)/], ['Firefox', /Firefox\/(\d+)/], ['Chrome', /Chrome\/(\d+)/], ['Safari', /Version\/(\d+).*Safari/]]) {
    const m = re.exec(ua);
    if (m) return [n, m[1]];
  }
  return ['Browser', ''];
}
function uptime() {
  let m = Math.floor((Date.now() - BOOT) / 60000);
  const d = Math.floor(m / 1440); m -= d * 1440;
  const h = Math.floor(m / 60); m -= h * 60;
  return [[d, 'day'], [h, 'hour'], [m, 'min']].filter(([n]) => n).map(([n, u]) => `${n} ${u}${n === 1 ? '' : 's'}`).join(', ') || '0 mins';
}
let server;
async function sys() {
  server ??= await fetch(location.href, { method: 'HEAD' }).then(r => r.headers.get('server') || 'unknown', () => 'unknown');
  const proto = (performance.getEntriesByType('navigation')[0]?.nextHopProtocol || 'http').replace(/^h(\d)$/, 'HTTP/$1').replace(/^http\//, 'HTTP/');
  return { server, host: location.hostname, proto };
}
async function fetch_() {
  const [n, v] = browser();
  const { server, host, proto } = await sys();
  const rows = [
    ['host', host], ['os', server], ['kernel', proto], ['uptime', uptime()],
    ['shell', 'shell.js'], ['term', `${n} ${v}`.trim()], ['network', colo],
  ].map(([k, val], i) => [k, k, esc(val), HUES[i % HUES.length]]);
  rows.push(['colors', [...'colors'].map((ch, i) => `<span class="${HUES[i % HUES.length]}">${ch}</span>`).join(''),
    '<span class="err">●</span> <span class="p">●</span> <span class="y">●</span> <span class="g">●</span> <span class="d">●</span> <span class="k">●</span>', 'd']);
  const body = [
    `<span class="p">guest</span>@<span class="p">${esc(location.hostname)}</span>`,
    '<span class="dim">-------------</span>',
    ...rows.map(([k, label, val, hue]) => `<span class="${hue}" aria-hidden="true">${ICONS[k]}</span> ${label}${' '.repeat(9 - k.length)}<span class="${hue}">${val}</span>`),
  ].join('\n');
  return `<span class="logo" aria-hidden="true">${self.logos?.[n] ?? logo}</span><span class="fetch">${body}</span>`;
}
const cmds = {
  __proto__: null,
  help: () => [
    ['help', 'this'],
    ['ls', "list what's here"],
    ['cat FILE', `read a file: ${Object.keys(files).join(', ')}`],
    ['cd NAME', `go there: ${Object.keys(links).join(', ')}`],
    ['man cwel', 'the manual'],
    ['fastfetch', 'system info'],
    ['clear', 'clear the screen, or ctrl-l'],
  ].map(([c, d]) => `<span class="c">${c.padEnd(10)}</span> ${esc(d)}`).join('\n'),
  ls: () => tpl('ls'),
  cat: a => a.length ? a.map(f => files[f] ?? err(`cat: ${esc(f)}: No such file or directory`)).join('\n') : err('cat: missing file'),
  cd: a => !a.length ? null : links[a[0]] ? go(links[a[0]]) : err(`cd: no such file or directory: ${esc(a[0])}`),
  open: a => cmds.cd(a),
  cwel: a => !a.length ? tpl('man') : a[0].startsWith('--') && links[a[0].slice(2)] ? go(links[a[0].slice(2)]) : err(`cwel: unrecognized option '${esc(a[0])}'`),
  jellyfin: () => go('https://jelly.cwel.sh'),
  plex: () => cmds.jellyfin(),
  seerr: () => go('https://req.cwel.sh'),
  requests: () => cmds.seerr(),
  man: a => !a.length ? "What manual page do you want?\nFor example, try 'man cwel'." : ['cwel', 'cwel.sh', 'man'].includes(a[0]) ? tpl('man') : err(`No manual entry for ${esc(a[0])}`),
  fastfetch: () => fetch_(),
  neofetch: () => fetch_(),
  whoami: () => 'guest',
  pwd: () => '/home/cwel',
  echo: a => esc(a.join(' ')),
  uname: async () => { const s = await sys(); return esc(`${s.server} ${s.host} ${s.proto}`); },
  clear: () => { out.innerHTML = ''; return null; },
  sudo: () => err('guest is not in the sudoers file.  This incident will be reported.'),
  rm: a => { const f = a.filter(x => !x.startsWith('-')); return err(f.length ? f.map(x => `rm: cannot remove '${esc(x)}': Permission denied`).join('\n') : "rm: missing operand\nTry 'rm --help' for more information."); },
  exit: () => { close(); for (const el of [form.previousElementSibling, form, document.getElementById('hint')]) el.remove(); return `Connection to ${esc(location.hostname)} closed.`; },
  nvim: () => go('https://github.com/cwelsys/dotfiles/tree/main/dot_config/nvim'),
  vim: () => cmds.nvim(),
  vi: () => cmds.nvim(),
};
const hist = [];
let hi = 0;
function print(html, cls = '') {
  const p = document.createElement('pre');
  if (cls) p.className = cls;
  p.innerHTML = html;
  out.append(p);
}
form.addEventListener('submit', e => {
  e.preventDefault();
  const raw = input.value;
  input.value = '';
  const [c, ...a] = raw.trim().split(/\s+/);
  if (!c) return;
  print(`${PROMPT} ${esc(raw)}`, 'cmd');
  hist.push(raw);
  hi = hist.length;
  Promise.resolve(cmds[c] ? cmds[c](a) : err(`zsh: command not found: ${esc(c)}`)).then(r => {
    if (r !== null) print(r);
    input.scrollIntoView({ block: 'end' });
  });
});
input.addEventListener('keydown', e => {
  if (e.key === 'ArrowUp' && hi > 0) { input.value = hist[--hi]; e.preventDefault(); }
  else if (e.key === 'ArrowDown') { hi = Math.min(hi + 1, hist.length); input.value = hist[hi] ?? ''; e.preventDefault(); }
  else if (e.key === 'Tab' && !e.shiftKey && input.value.trim()) {
    const parts = input.value.split(/\s+/);
    const last = parts.pop();
    const pool = parts.length ? Object.keys({ ...files, ...links }) : Object.keys(cmds);
    const m = pool.filter(x => x.startsWith(last));
    if (m.length === 1) { input.value = [...parts, m[0]].join(' ') + ' '; e.preventDefault(); }
    else if (m.length > 1) { print(m.join('  ')); e.preventDefault(); }
  } else if (e.key === 'l' && e.ctrlKey) { cmds.clear(); e.preventDefault(); }
});
document.querySelector('main').addEventListener('click', e => {
  if (e.target.closest('a') || getSelection().toString()) return;
  input.focus({ preventScroll: true });
});
