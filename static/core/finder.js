// Editable demonstration floor plan: # = wall, . = aisle, C = counter, A/B = shelving.
// Each shelf occupies one blocked tile. The route stops at a walkable tile next to it.
const layout = [
  '#############',
  '#...........#',
  '#..A.A.B.B..#',
  '#..A.A.B.B..#',
  '#...........#',
  '#..A.A.B.B..#',
  '#..A.A.B.B..#',
  '#...........#',
  '#.....C.....#',
  '#############'
];
// Match the medication.location field to one of these identifiers.
const shelves = {A1:[2,3],A2:[3,3],A3:[5,3],A4:[6,3],A5:[2,5],A6:[3,5],A7:[5,5],A8:[6,5],B1:[2,7],B2:[3,7],B3:[5,7],B4:[6,7],B5:[2,9],B6:[3,9],B7:[5,9],B8:[6,9]};
const start=[8,6];
const map=document.getElementById('pharmacy-map');
const status=document.getElementById('route-status');
const key=(r,c)=>r+','+c;
const isFloor=(r,c)=>r>=0&&r<layout.length&&c>=0&&c<layout[0].length&&layout[r][c]==='.';
const neighbors=(r,c)=>[[r-1,c],[r+1,c],[r,c-1],[r,c+1]];
function shortestPath(target){
 const [sr,sc]=shelves[target];
 const goals=new Set(neighbors(sr,sc).filter(([r,c])=>isFloor(r,c)||key(r,c)===key(...start)).map(([r,c])=>key(r,c)));
 const queue=[start],previous=new Map([[key(...start),null]]);
 for(let i=0;i<queue.length;i++){
  const [r,c]=queue[i], k=key(r,c);
  if(goals.has(k)){
   const path=[];let cur=k;
   while(cur!==null){path.push(cur);cur=previous.get(cur)}
   return path.reverse();
  }
  for(const [nr,nc] of neighbors(r,c)){
   const nk=key(nr,nc);
   if(isFloor(nr,nc)&&!previous.has(nk)){previous.set(nk,k);queue.push([nr,nc])}
  }
 }
 return null;
}
function draw(target=null,name=''){
 map.replaceChildren();
 const path=target?shortestPath(target):null;
 const route=new Set(path||[]);
 for(let r=0;r<layout.length;r++)for(let c=0;c<layout[r].length;c++){
  const cell=document.createElement('div');cell.className='map-cell';
  const id=Object.keys(shelves).find(k=>shelves[k][0]===r&&shelves[k][1]===c);
  if(layout[r][c]==='#')cell.classList.add('map-wall');
  else if(layout[r][c]==='C'){cell.classList.add('map-counter');cell.textContent='COUNTER';}
  else if(id){cell.classList.add('map-shelf');cell.textContent=id;
   cell.setAttribute('role','button');cell.tabIndex=0;cell.setAttribute('aria-label','Show route to shelf '+id);
   cell.addEventListener('click',()=>draw(id));cell.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();draw(id)}});
  }else if(route.has(key(r,c))){cell.classList.add('map-route');cell.textContent='•';}
  if(id===target)cell.classList.add('map-destination');
  map.appendChild(cell);
 }
 if(target){status.textContent=path?`Route from counter to ${name?name+' at ':''}shelf ${target}: ${path.length-1} grid steps. Follow the blue dots.`:`No accessible route to ${target} in this floor plan.`;}
 else status.textContent='Choose a medication result or select a shelf to display its route.';
}
document.querySelectorAll('.map-choice').forEach(btn=>btn.addEventListener('click',()=>{
 const loc=btn.dataset.location.trim();
 if(!Object.hasOwn(shelves,loc)){status.textContent=`Location "${loc}" is not mapped yet. Use a shelf code A1–A8 or B1–B8, or update the floor plan.`;draw();status.textContent=`Location "${loc}" is not mapped yet. Use A1–A8 or B1–B8, or update the floor plan.`;return;}
 draw(loc,btn.dataset.name);
 document.getElementById('pharmacy-map').scrollIntoView({behavior:'smooth',block:'center'});
}));
draw();
