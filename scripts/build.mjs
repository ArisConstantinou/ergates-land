import {mkdir,copyFile,cp,writeFile,readFile} from 'node:fs/promises';
await mkdir('dist',{recursive:true});
for(const name of ['index.html','property.html','styles.css','app.js'])await copyFile(name,'dist/'+name);
await cp('data','dist/data',{recursive:true});await cp('images','dist/images',{recursive:true});await writeFile('dist/.nojekyll','');
const data=JSON.parse(await readFile('data/properties.json','utf8'));
if(!data.properties.length)throw new Error('Empty catalogue');
console.log(`Static build ready: ${data.properties.length} properties.`);
