const json=(x,status=200)=>Response.json(x,{status});
const defaults=()=>({title:'JKS Christmas',slides:[['Willkommen','Herzlich willkommen!'],['Apéro','Viel Spass!'],['Weihnachtsgeschichten in 60 Sekunden','Bühne frei für eure Kreativität!'],['Hauptgang','En Guete!'],['Frohe Weihnachten','Vielen Dank für diesen besonderen Abend!']].map(([title,subtitle],i)=>({id:crypto.randomUUID(),title,subtitle,bg:'',logo:'',color:'#f5d69a',background:'#39291e',size:64,align:'center',type:i===2?'competition':'standard'})),screens:[0,1],rounds:Array.from({length:7},(_,i)=>({id:String(i+1),name:`Gruppe ${i+1}`})),active:null,open:false,showResults:false,timerEnd:0,transition:0,votes:{},voteEpoch:0,completed:[],revision:0});
export default {async fetch(req,env){const u=new URL(req.url);if(!u.pathname.startsWith('/api/'))return env.ASSETS.fetch(req);const id=u.pathname.startsWith('/api/library')?'main':(u.searchParams.get('p')||'main');if(id!=='main'&&!/^[0-9a-f-]{36}$/.test(id))return json({error:'Invalid presentation'},400);return env.EVENTS.get(env.EVENTS.idFromName(id)).fetch(req);}};
export class EventRoom {
 constructor(ctx,env){this.ctx=ctx;this.env=env;this.state=null;this.clients=new Set();this.queue=Promise.resolve();}
 async load(){if(!this.state){const count=await this.ctx.storage.get('parts');if(count){const keys=Array.from({length:count},(_,i)=>'part:'+i);const parts=await this.ctx.storage.get(keys);this.state=JSON.parse(keys.map(k=>parts.get(k)).join(''));}else this.state=defaults();for(const slide of this.state.slides){if(!slide.type)slide.type=/60 Sekunden/i.test(slide.title)?'competition':'standard';}if(!this.state.competitionSlide&& (this.state.timerEnd||this.state.open||this.state.showResults)){this.state.competitionSlide=this.state.screens.map(i=>this.state.slides[i]).find(s=>s?.type==='competition')?.id||null; if(!this.state.competitionSlide){this.state.timerEnd=0;this.state.open=false;this.state.autoVote=false;this.state.showResults=false;}}if(!Array.isArray(this.state.completed))this.state.completed=this.state.rounds.filter(r=>Object.keys(this.state.votes[r.id]||{}).length&&(!(this.state.open||this.state.timerEnd)||r.id!==this.state.active)).map(r=>r.id);}return this.state;}
 authorized(req){return !!this.env.ADMIN_PASSWORD && req.headers.get('Authorization')===`Bearer ${this.env.ADMIN_PASSWORD}`;}
 results(){return this.state.rounds.map(r=>{const a=Object.values(this.state.votes[r.id]||{});return {...r,count:a.length,average:a.length?a.reduce((x,y)=>x+y,0)/a.length:0};});}
 snapshot(admin=false){const {votes,...s}=this.state;return {...s,results:admin||s.showResults?this.results():[],serverTime:Date.now()};}
 async save(){this.state.revision++;const raw=JSON.stringify(this.state);const parts=raw.match(/[\s\S]{1,40000}/g);await this.ctx.storage.transaction(async tx=>{const old=await tx.get('parts')||0;for(let i=0;i<parts.length;i++)await tx.put('part:'+i,parts[i]);for(let i=parts.length;i<old;i++)await tx.delete('part:'+i);await tx.put('parts',parts.length);});for(const ws of this.ctx.getWebSockets()){try{ws.send(JSON.stringify(this.snapshot()));}catch{}}}
 liveCompetition(id){return !!id&&this.state.screens.some(i=>{const s=this.state.slides[i];return s?.id===id&&s.type==='competition';});}
 async stopCompetition(){Object.assign(this.state,{competitionSlide:null,active:null,open:false,timerEnd:0,autoVote:false,showResults:false});await this.ctx.storage.deleteAlarm();}
 async finishTimer(){if(this.state.competitionSlide&&!this.liveCompetition(this.state.competitionSlide)){await this.stopCompetition();await this.save();return;}if(this.state.autoVote && this.state.timerEnd && Date.now()>=this.state.timerEnd){this.state.timerEnd=0;this.state.autoVote=false;this.state.open=!!this.state.active;await this.save();}}
 serial(fn){const p=this.queue.then(fn);this.queue=p.catch(()=>{});return p;}
 async alarm(){return this.serial(()=>this.runAlarm());}
 async runAlarm(){await this.load();if(this.state.autoVote&&this.state.timerEnd>Date.now()){await this.ctx.storage.setAlarm(this.state.timerEnd);return;}await this.finishTimer();}
 async fetch(req){return this.serial(()=>this.handle(req));}
 async handle(req){await this.load();await this.finishTimer();const p=new URL(req.url).pathname;const admin=this.authorized(req);if(p==='/api/auth')return admin?json({ok:true}):json({error:'Invalid admin password'},401);
 if(p==='/api/meta')return admin?json({title:this.state.title,slides:this.state.slides.length}):json({error:'Unauthorized'},401);
 if(p==='/api/init'){if(!admin||req.method!=='POST')return json({error:'Unauthorized'},401);if(await this.ctx.storage.get('parts'))return json({error:'Already initialized'},409);const b=await req.json();this.state=defaults();this.state.title=String(b.title||'Untitled presentation').slice(0,150);this.state.slides=[{...this.state.slides[0],title:'Welcome',subtitle:'',background:'#ffffff',color:'#202630',font:'System'}];this.state.screens=[0,0];await this.save();return json({ok:true});}
 if(p==='/api/library'){if(!admin)return json({error:'Invalid admin password'},401);const ids=await this.ctx.storage.get('library')||[];if(req.method==='POST'){const b=await req.json();const title=String(b.title||'').trim().slice(0,150);if(!title)return json({error:'Enter a presentation name'},400);if(ids.length>=100)return json({error:'Library limit reached'},409);const id=crypto.randomUUID();const r=await this.env.EVENTS.get(this.env.EVENTS.idFromName(id)).fetch(new Request('https://internal/api/init',{method:'POST',headers:{Authorization:req.headers.get('Authorization'),'Content-Type':'application/json'},body:JSON.stringify({title})}));if(!r.ok)return json({error:'Could not create presentation'},500);await this.ctx.storage.put('library',[...ids,id]);return json({id});}const items=await Promise.all(ids.map(async id=>{try{const r=await this.env.EVENTS.get(this.env.EVENTS.idFromName(id)).fetch(new Request('https://internal/api/meta',{headers:{Authorization:req.headers.get('Authorization')}}));if(!r.ok)throw Error();return {id,...await r.json()};}catch{return {id,title:'Unavailable presentation',slides:0};}}));return json([{id:'main',title:this.state.title,slides:this.state.slides.length},...items]);}
 if(p==='/api/socket'){const pair=new WebSocketPair();this.ctx.acceptWebSocket(pair[1]);pair[1].send(JSON.stringify(this.snapshot()));return new Response(null,{status:101,webSocket:pair[0]});}if(p==='/api/state')return json(this.snapshot(admin));if(req.method!=='POST')return json({error:'Not found'},404);let b;try{b=await req.json();}catch{return json({error:'Invalid JSON'},400);}
 if(p==='/api/vote'){if(!this.state.open||b.round!==this.state.active||b.epoch!==this.state.voteEpoch)return json({error:'Voting is closed'},409);if(typeof b.participant!=='string'||!/^[a-zA-Z0-9-]{16,80}$/.test(b.participant)||!Number.isInteger(b.rating)||b.rating<1||b.rating>7)return json({error:'Invalid vote'},400);const v=this.state.votes[b.round]??={};if(Object.hasOwn(v,b.participant))return json({error:'Already voted'},409);v[b.participant]=b.rating;await this.save();return json({ok:true});}
 if(!admin)return json({error:'Invalid admin password'},401);
 if(p==='/api/edit'){if(this.state.timerEnd||this.state.open)return json({error:'Finish the active round before editing'},409);if(!Array.isArray(b.slides)||!b.slides.length||b.slides.length>100||!Array.isArray(b.rounds)||!b.rounds.length||b.rounds.length>100)return json({error:'Invalid presentation'},400);if(JSON.stringify(b).length>12_000_000)return json({error:'Presentation too large'},413);this.state.title=String(b.title).slice(0,150);const liveIds=this.state.screens.map(i=>this.state.slides[i]?.id);this.state.slides=b.slides.map(s=>({...s,type:['competition','join'].includes(s.type)?s.type:'standard'}));this.state.screens=liveIds.map((id,i)=>{const j=this.state.slides.findIndex(s=>s.id===id);return j>=0?j:Math.min(this.state.screens[i],this.state.slides.length-1);});if(this.state.competitionSlide&&!this.liveCompetition(this.state.competitionSlide))await this.stopCompetition();this.state.rounds=b.rounds;this.state.completed=this.state.completed.filter(id=>b.rounds.some(r=>r.id===id));this.state.screens=this.state.screens.map(i=>Math.min(i,b.slides.length-1));if(!b.rounds.some(r=>r.id===this.state.active)){this.state.active=null;this.state.open=false;this.state.timerEnd=0;this.state.autoVote=false;await this.ctx.storage.deleteAlarm();}}
 else if(p==='/api/control'){
  const st=this.state, busy=!!(st.timerEnd||st.open), next=st.rounds.find(r=>!st.completed.includes(r.id));
  const fail=m=>json({error:m},409);
  if(b.guided){
   if(b.epoch!==st.voteEpoch)return fail('Competition was reset. Refresh and try again.');
   if(b.guided==='start'){
    if(busy||!next||b.round!==next.id||!this.liveCompetition(b.slide))return fail('Start is no longer available for this group.');
    Object.assign(st,{competitionSlide:b.slide,active:next.id,open:false,timerEnd:Date.now()+60000,autoVote:true,showResults:false});await this.ctx.storage.setAlarm(st.timerEnd);
   }else if(b.guided==='close'){
    if(!st.open||b.round!==st.active||b.slide!==st.competitionSlide)return fail('This voting round is no longer active.');
    st.open=false;st.completed.push(st.active);st.active=null;st.timerEnd=0;st.autoVote=false;
   }else if(b.guided==='restart'){
    if(!st.timerEnd||st.open||b.round!==st.active||b.slide!==st.competitionSlide)return fail('Only a running countdown can be restarted.');
    st.timerEnd=Date.now()+60000;await this.ctx.storage.setAlarm(st.timerEnd);
   }else if(b.guided==='abort'){
    if(!st.timerEnd||st.open||b.round!==st.active||b.slide!==st.competitionSlide)return fail('Only a running countdown can be cancelled.');await this.stopCompetition();
   }else if(b.guided==='reveal'){
    if(busy||next||!this.liveCompetition(b.slide))return fail('Finish every group and display a competition slide first.');st.competitionSlide=b.slide;st.showResults=!st.showResults;
   }else return fail('Unknown competition action.');
  }else if(b.resetVotes===true){if(busy)return fail('Finish or cancel the current round before resetting.');st.votes={};st.completed=[];st.voteEpoch=(st.voteEpoch||0)+1;await this.stopCompetition();}
  else if(Array.isArray(b.screens)&&b.screens.length===2&&b.screens.every(i=>Number.isInteger(i)&&i>=0&&i<st.slides.length)){
   const changed=b.screens.some((v,i)=>v!==st.screens[i]);
   if(changed&&busy){
    const confirmation=b.confirmRound;
    if(!confirmation||confirmation.round!==st.active||confirmation.epoch!==st.voteEpoch||confirmation.slide!==st.competitionSlide||confirmation.phase!==(st.open?'voting':'countdown')||confirmation.timerEnd!==st.timerEnd)return fail('The round is active or has changed. Confirm the screen change again.');
    const keepsHost=b.screens.some(i=>st.slides[i]?.id===st.competitionSlide);
    if(!keepsHost){if(st.open&&!st.completed.includes(st.active))st.completed.push(st.active);await this.stopCompetition();}
   }
   st.screens=b.screens;if(changed)st.transition=Date.now()+650;if(st.competitionSlide&&!this.liveCompetition(st.competitionSlide))await this.stopCompetition();
  }else if(Object.keys(b).length)return fail('Use the guided competition controls.');
 }
 else return json({error:'Not found'},404);await this.save();return json(this.snapshot(true));}
 webSocketMessage(){} webSocketClose(ws){try{ws.close();}catch{}} webSocketError(ws){try{ws.close();}catch{}}
}
