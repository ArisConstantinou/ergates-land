import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve('.');
const config=JSON.parse((await readFile('project.config.json','utf8')).replace(/^\uFEFF/,''));
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.jpg':'image/jpeg','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml'};
const server=http.createServer(async(req,res)=>{try{const pathname=decodeURIComponent(new URL(req.url,'http://local').pathname);const file=path.resolve(root,'.'+(pathname.endsWith('/')?pathname+'index.html':pathname));if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}const data=await readFile(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(data);}catch{res.writeHead(404).end('Δεν βρέθηκε η σελίδα');}});
server.on('error',e=>{console.error('Η σταθερή θύρα '+config.port+' δεν είναι διαθέσιμη.',e.message);process.exit(1);});
server.listen(config.port,config.host,()=>console.log(`Ergates land: http://${config.host}:${config.port}/ (strict port)`));
