// 같은 Wi-Fi의 다른 기기(태블릿·폰)에서 게임을 열 수 있게 하는 작은 정적 서버.
// 실행:  node serve.js        (끄려면 Ctrl+C)
const http = require('http'), fs = require('fs'), path = require('path'), os = require('os');

const ROOT = __dirname, PORT = +(process.argv[2] || 8000);
const TYPE = { '.html':'text/html; charset=utf-8', '.png':'image/png', '.js':'text/javascript',
               '.css':'text/css', '.ico':'image/x-icon' };

http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/') p = '/chess.html';
  const file = path.join(ROOT, path.normalize(p).replace(/^([/\\])+/, ''));
  if (!file.startsWith(ROOT)) { res.writeHead(403).end('nope'); return; }   // 폴더 밖 접근 차단
  fs.readFile(file, (e, buf) => {
    if (e) { res.writeHead(404, {'content-type':'text/plain; charset=utf-8'}).end('없는 파일'); return; }
    res.writeHead(200, {'content-type': TYPE[path.extname(file).toLowerCase()] || 'application/octet-stream',
                        'cache-control':'no-cache'});
    res.end(buf);
  });
}).listen(PORT, '0.0.0.0', () => {
  const ips = Object.values(os.networkInterfaces()).flat()
    .filter(i => i.family === 'IPv4' && !i.internal).map(i => i.address);
  console.log('배틀 체스 서버가 켜졌습니다. 태블릿 브라우저에서 아래 주소를 여세요:\n');
  console.log('   이 컴퓨터:  http://localhost:' + PORT);
  ips.forEach(ip => console.log('   같은 Wi-Fi:  http://' + ip + ':' + PORT));
  console.log('\n끄려면 이 창에서 Ctrl+C');
});
