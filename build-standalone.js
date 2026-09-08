// chess.html + sprites.png → 그림까지 들어있는 단일 파일(deploy/index.html) 만들기
// 실행:  node build-standalone.js
const fs = require('fs'), path = require('path');

const SRC = 'chess.html', SHEET = fs.existsSync('sprites-web.png') ? 'sprites-web.png' : 'sprites.png';
let html = fs.readFileSync(SRC, 'utf8');
const uri = 'data:image/png;base64,' + fs.readFileSync(SHEET).toString('base64');

html = html.replace(':root{', `:root{--sheet:url("${uri}");\n  `);
html = html.split('background-image:url(sprites.png)').join('background-image:var(--sheet)');
html = html.replace(/\(function loadSheet\(\)\{[\s\S]*?\}\)\(\);/, 'SPR=true;   // 그림이 파일 안에 들어있다');

fs.mkdirSync('deploy', { recursive: true });
fs.writeFileSync('standalone.html', html);
fs.writeFileSync(path.join('deploy', 'index.html'), html);
fs.writeFileSync('artifact.html', html.replace(/^<!doctype html>\r?\n/i, ''));

const kb = n => Math.round(n / 1024) + 'KB';
console.log(`그림: ${SHEET} (${kb(fs.statSync(SHEET).size)}) → 단일 파일 ${kb(html.length)}`);
console.log('만들어진 파일: standalone.html · deploy/index.html · artifact.html');
console.log('CSS 데이터 URI 한도(약 2MB)를 넘지 않는지 확인:',
  (html.match(/data:image\/png;base64,[A-Za-z0-9+/=]+/) || [''])[0].length < 2000000 ? 'OK' : '초과!');
