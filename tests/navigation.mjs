import assert from 'node:assert/strict';
import {EventRoom} from '../worker.js';
class Store{map=new Map();async get(k){return Array.isArray(k)?new Map(k.map(x=>[x,this.map.get(x)])):this.map.get(k)}async put(k,v){this.map.set(k,v)}async delete(k){this.map.delete(k)}async transaction(fn){return fn(this)}async setAlarm(t){this.alarm=t}async deleteAlarm(){this.alarm=null}}
const storage=new Store(),room=new EventRoom({storage,getWebSockets:()=>[]},{ADMIN_PASSWORD:'test'});
const call=(path,b)=>room.fetch(new Request('https://test/api/'+path,{method:b?'POST':'GET',headers:{Authorization:'Bearer test','Content-Type':'application/json'},...(b?{body:JSON.stringify(b)}:{})}));
async function ok(path,b){const r=await call(path,b);assert.ok(r.ok,await r.clone().text());return r.json()}
let s=await ok('control',{screens:[2,2]});const host=s.slides[2].id;
const start=()=>ok('control',{guided:'start',epoch:0,round:'1',slide:host});
const confirm=s=>({round:s.active,epoch:s.voteEpoch,slide:s.competitionSlide,phase:s.open?'voting':'countdown',timerEnd:s.timerEnd});
s=await start();assert.equal((await call('control',{screens:[0,2]})).status,409);
let c=confirm(s);s=await ok('control',{screens:[0,2],confirmRound:c});assert.equal(s.timerEnd,c.timerEnd);assert.equal(s.active,'1');
s=await ok('control',{screens:[0,1],confirmRound:c});assert.equal(s.timerEnd,0);assert.equal(s.completed.length,0);assert.equal(storage.alarm,null);
await ok('control',{screens:[2,2]});s=await start();c=confirm(s);room.state.timerEnd=Date.now()-1;await room.alarm();assert.equal((await call('control',{screens:[0,1],confirmRound:c})).status,409);
s=await ok('state');assert.equal(s.open,true);await ok('vote',{round:'1',epoch:0,participant:'test-participant-1234',rating:7});s=await ok('control',{screens:[0,1],confirmRound:confirm(s)});assert.equal(s.open,false);assert.deepEqual(s.completed,['1']);assert.equal(s.results[0].average,7);assert.equal((await call('vote',{round:'1',epoch:0,participant:'test-participant-5678',rating:7})).status,409);console.log('Confirmed navigation, cancellation, vote preservation and stale confirmation checks passed.');
