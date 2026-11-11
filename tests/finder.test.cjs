const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const element = () => ({replaceChildren(){},classList:{add(){}},setAttribute(){},addEventListener(){},appendChild(){}});
const context = vm.createContext({document:{getElementById:element,createElement:element,querySelectorAll:()=>[]}});
vm.runInContext(fs.readFileSync('static/core/finder.js','utf8'),context);
vm.runInContext(`
for(const target of Object.keys(shelves)) {
 const path=shortestPath(target);
 if(!path || path[0]!==key(...start)) throw Error('Missing route: '+target);
 const [sr,sc]=shelves[target];
 const [er,ec]=path.at(-1).split(',').map(Number);
 if(Math.abs(er-sr)+Math.abs(ec-sc)!==1) throw Error('Wrong destination: '+target);
 for(let i=1;i<path.length;i++) {
  const [r,c]=path[i].split(',').map(Number);
  const [pr,pc]=path[i-1].split(',').map(Number);
  if(!isFloor(r,c) || Math.abs(r-pr)+Math.abs(c-pc)!==1) throw Error('Blocked route: '+target);
 }
 // Independently calculate distance to every walkable cell by relaxation.
 const distance = new Map([[key(...start), 0]]);
 for(let pass=0;pass<layout.length*layout[0].length;pass++)
  for(let r=0;r<layout.length;r++) for(let c=0;c<layout[r].length;c++)
   if(isFloor(r,c)) for(const [nr,nc] of neighbors(r,c))
    if(distance.has(key(nr,nc))) distance.set(key(r,c),Math.min(distance.get(key(r,c))??Infinity,distance.get(key(nr,nc))+1));
 const optimal=Math.min(...neighbors(sr,sc).map(([r,c])=>distance.get(key(r,c))??Infinity));
 if(path.length-1!==optimal) throw Error('Not shortest: '+target);
}
if(shortestPath('UNKNOWN')!==null) throw Error('Unknown shelf must be safe');
`,context);
console.log('PASS: all 16 shelves have shortest unobstructed routes; unknown shelf handled.');
