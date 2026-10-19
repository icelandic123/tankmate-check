
(async function(){
 const r=await fetch((window.BASE||'')+'/compat.json');const D=await r.json();const sel=new Set();
 const chips=document.getElementById('chips'),q=document.getElementById('q'),out=document.getElementById('result');
 const by=Object.fromEntries(D.species.map(s=>[s.id,s]));const F=c=>Math.round(c*9/5+32);
 function draw(){const t=q.value.toLowerCase();chips.innerHTML='';
  D.species.filter(s=>sel.has(s.id)||!t||s.name.toLowerCase().includes(t)).sort((a,b)=>a.name.localeCompare(b.name)).forEach(s=>{
   const b=document.createElement('button');b.textContent=s.name;b.className=sel.has(s.id)?'on':'';b.onclick=()=>{sel.has(s.id)?sel.delete(s.id):sel.add(s.id);draw();calc()};chips.appendChild(b)})}
 function esc(x){return x.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
 function calc(){const ids=[...sel];if(ids.length<2){out.innerHTML='<p class="fine">Select two or more species.</p>';return}
  let worst=0,items=[];const R={yes:0,caution:1,no:2};
  for(let i=0;i<ids.length;i++)for(let j=i+1;j<ids.length;j++){const k=[ids[i],ids[j]];const key=D.pairs[k[0]+'|'+k[1]]?k[0]+'|'+k[1]:k[1]+'|'+k[0];const p=D.pairs[key];
   if(p){worst=Math.max(worst,R[p[0]]);items.push('<li><span class="badge '+(p[0]=='no'?'bad':'warn')+'">'+(p[0]=='no'?'No':'Caution')+'</span> <strong>'+esc(by[k[0]].name)+' + '+esc(by[k[1]].name)+'</strong>: '+p[1].map(esc).join(' ')+'</li>')}}
  const S=ids.map(i=>by[i]);const tl=Math.max(...S.map(s=>s.temp[0])),th=Math.min(...S.map(s=>s.temp[1])),pl=Math.max(...S.map(s=>s.ph[0])),ph=Math.min(...S.map(s=>s.ph[1]));const tk=Math.max(...S.map(s=>s.tank_l));
  const cls=['good','warn','bad'][worst],lab=['Looks compatible','Possible, with caution','Not compatible'][worst];
  let h='<div class="answer '+cls+'"><span class="badge '+cls+'">'+lab+'</span>';
  h+='<ul>'+(tl<=th?'<li>Shared temperature: '+F(tl)+'–'+F(th)+' °F ('+tl+'–'+th+' °C)</li>':'<li>No temperature suits them all.</li>')+(pl<=ph?'<li>Shared pH: '+pl+'–'+ph+'</li>':'<li>No pH suits them all.</li>')+'<li>Tank: at least '+Math.round(tk/3.785)+' gallons ('+tk+' L), more for a full stock.</li></ul></div>';
  if(items.length)h+='<ul>'+items.join('')+'</ul>';out.innerHTML=h}
 q.oninput=draw;draw()})();
