const out = document.getElementById('out');
const input = document.getElementById('cmd');
const form = document.getElementById('f');
const tpl = id => document.getElementById(id).innerHTML.trim();
const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const err = s => `<span class="err">${s}</span>`;
const PROMPT = '<span class="d">~</span> <span class="p">❯</span>';
const links = {};
for (const a of document.querySelectorAll('#ls a')) links[a.textContent] = a.getAttribute('href');
const email = (links.email || '').replace('mailto:', '');
const files = {
  about: tpl('about'),
  patches: tpl('patches'),
  resume: `<a href="/resume">/resume</a>  <a href="/resume.pdf">/resume.pdf</a>`,
  keys: `<a href="/cwel.asc">/cwel.asc</a>\ngpg --locate-keys ${esc(email)}`,
};
const logo = `  .--------.
  |  >_    |
  |        |
  '--------'`;
function browser() {
  const ua = navigator.userAgent;
  for (const [n, re] of [['Edge', /Edg\/(\d+)/], ['Firefox', /Firefox\/(\d+)/], ['Chrome', /Chrome\/(\d+)/], ['Safari', /Version\/(\d+).*Safari/]]) {
    const m = re.exec(ua);
    if (m) return [n, m[1]];
  }
  return ['Browser', ''];
}
function fetch_() {
  const [n, v] = browser();
  const years = Math.floor((Date.now() - Date.UTC(1994, 0, 1)) / 31557600000);
  const rows = [
    ['<span class="p">cwel</span>@<span class="p">cwel.sh</span>'],
    ['<span class="dim">------------</span>'],
    ['OS', 'cwel.sh'], ['Host', 'Cloudflare Pages'], ['Kernel', 'static html'],
    ['Uptime', `${years} years`], ['Shell', 'sh.js'], ['Theme', 'Catppuccin Mocha'],
    ['Font', 'yours'], ['Term', `${n} ${v}`.trim()], ['Locale', navigator.language],
    ['<span class="err">●</span><span class="p">●</span><span class="y">●</span><span class="g">●</span><span class="d">●</span><span class="k">●</span>'],
  ];
  const lines = logo.split('\n');
  const w = Math.max(...lines.map(l => l.length)) + 3;
  return rows.map((r, i) =>
    `<span aria-hidden="true">${esc((lines[i] ?? '').padEnd(w))}</span>` +
    (r.length === 2 ? `<span class="y">${r[0].padEnd(8)}</span> ${esc(r[1])}` : r[0])
  ).join('\n');
}
const cmds = {
  help: () => `commands: ${Object.keys(cmds).join('  ')}\nfiles:    ${Object.keys(files).join('  ')}`,
  ls: () => tpl('ls'),
  cat: a => a.length ? a.map(f => files[f] ?? err(`cat: ${esc(f)}: No such file or directory`)).join('\n') : err('cat: missing file'),
  cd: a => { if (!a.length) return null; const u = links[a[0]]; if (!u) return err(`cd: no such file or directory: ${esc(a[0])}`); location.href = u; return null; },
  open: a => cmds.cd(a),
  man: a => !a.length ? "What manual page do you want?\nFor example, try 'man cwel'." : ['cwel', 'cwel.sh', 'man'].includes(a[0]) ? tpl('man') : err(`No manual entry for ${esc(a[0])}`),
  fastfetch: () => fetch_(),
  neofetch: () => fetch_(),
  whoami: () => 'guest',
  pwd: () => '/home/cwel',
  echo: a => esc(a.join(' ')),
  uname: () => 'Linux cwel.sh 7.2.6-1-cwel',
  clear: () => { out.innerHTML = ''; return null; },
  sudo: () => err('guest is not in the sudoers file.  This incident will be reported.'),
  rm: () => err('rm: permission denied'),
  exit: () => 'logout',
  vim: () => 'nvim',
  nvim: () => '<span class="dim">:q</span>',
  emacs: () => '<span class="dim">no.</span>',
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
  const r = cmds[c] ? cmds[c](a) : err(`zsh: command not found: ${esc(c)}`);
  if (r !== null) print(r);
  input.scrollIntoView({ block: 'end' });
});
input.addEventListener('keydown', e => {
  if (e.key === 'ArrowUp' && hi > 0) { input.value = hist[--hi]; e.preventDefault(); }
  else if (e.key === 'ArrowDown') { hi = Math.min(hi + 1, hist.length); input.value = hist[hi] ?? ''; e.preventDefault(); }
  else if (e.key === 'Tab') {
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
