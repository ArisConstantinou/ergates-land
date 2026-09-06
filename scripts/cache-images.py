import pathlib,json,requests,concurrent.futures,hashlib,io,time
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1];d=json.loads((root/'data/properties.json').read_text(encoding='utf8'));out=root/'images';out.mkdir(exist_ok=True);cachefile=root/'research/image-cache.json';cache=json.loads(cachefile.read_text(encoding='utf8')) if cachefile.exists() else {}
urls=list(dict.fromkeys(i['url'] for p in d['properties'] for i in p['images']))
def fetch(u):
 if u in cache:return u,cache[u]
 try:
  r=requests.get(u,timeout=22);r.raise_for_status();im=Image.open(io.BytesIO(r.content));im.verify();ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp','GIF':'.gif'}.get(im.format,'.jpg');name=hashlib.sha256(r.content).hexdigest()[:22]+ext;(out/name).write_bytes(r.content);return u,{'path':'images/'+name,'bytes':len(r.content),'width':im.width,'height':im.height}
 except Exception as e:return u,{'error':str(e)[:160]}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for i,(u,v) in enumerate(ex.map(fetch,urls)):
  cache[u]=v
  if i%50==0:print(i,'/',len(urls),flush=True)
cachefile.write_text(json.dumps(cache,indent=2),encoding='utf8');print('Images verified:',sum('path'in v for v in cache.values()),'Failed:',sum('error'in v for v in cache.values()),flush=True)
