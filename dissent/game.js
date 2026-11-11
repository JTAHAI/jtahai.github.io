/*
 * DISSENT: Carpooling to Hell — Seven Circles / Absurdity Director build.
 * Original dependency-free WebGL2 arcade roguelite for procedural4.JTforME.com.
 * No accounts, analytics, external assets, or runtime network requests.
 */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const DG = window.DissentGenerator;
  if (!DG) throw new Error('DissentGenerator must load before game.js');

  const canvas = $('game'), fxCanvas = $('fx');
  const gl = canvas.getContext('webgl2', {antialias:true,alpha:false,powerPreference:'high-performance'});
  if (!gl) {
    const status=$('status');status.style.display='block';
    status.textContent='DISSENT requires WebGL2. Try a current desktop Chrome, Firefox, or Edge browser.';
    $('start').disabled=true;return;
  }

  const TAU=Math.PI*2;
  const v=(x=0,y=0,z=0)=>[x,y,z];
  const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
  const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
  const scale=(a,s)=>[a[0]*s,a[1]*s,a[2]*s];
  const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const len=(a)=>Math.hypot(a[0],a[1],a[2]);
  const norm=(a)=>{const l=len(a)||1;return scale(a,1/l);};
  const dist=(a,b)=>len(sub(a,b));
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
  const mix=(a,b,t)=>a+(b-a)*t;
  const mix3=(a,b,t)=>[mix(a[0],b[0],t),mix(a[1],b[1],t),mix(a[2],b[2],t)];
  const qMul=(a,b)=>[a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1],a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0],a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3],a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]];
  const qAxis=(axis,angle)=>{const s=Math.sin(angle/2);return [axis[0]*s,axis[1]*s,axis[2]*s,Math.cos(angle/2)];};
  const qNorm=(q)=>{const l=Math.hypot(...q)||1;return q.map(x=>x/l);};
  const rotate=(a,q)=>{const u=q.slice(0,3),t=scale(cross(u,a),2);return add(a,add(scale(t,q[3]),cross(u,t)));};
  const projMat=(fovy,aspect,near,far)=>{const f=1/Math.tan(fovy/2),nf=1/(near-far);return [f/aspect,0,0,0,0,f,0,0,0,0,(far+near)*nf,-1,0,0,2*far*near*nf,0];};
  const viewMat=(p,q)=>{const r=rotate([1,0,0],q),u=rotate([0,1,0],q),b=rotate([0,0,1],q);return [r[0],u[0],b[0],0,r[1],u[1],b[1],0,r[2],u[2],b[2],0,-dot(r,p),-dot(u,p),-dot(b,p),1];};
  const lookView=(eye,target)=>{const f=norm(sub(target,eye)),r=norm(cross(f,[0,1,0])),u=cross(r,f),b=scale(f,-1);return [r[0],u[0],b[0],0,r[1],u[1],b[1],0,r[2],u[2],b[2],0,-dot(r,eye),-dot(u,eye),-dot(b,eye),1];};
  function mulMat(a,b){const c=Array(16).fill(0);for(let col=0;col<4;col++)for(let row=0;row<4;row++)for(let k=0;k<4;k++)c[col*4+row]+=a[k*4+row]*b[col*4+k];return c;}
  const pad=(n)=>String(Math.max(0,Math.floor(n))).padStart(2,'0');
  const tint=(c,k)=>c.map(x=>x*k);
  const inRange=(p,c,r)=>Math.abs(p[0]-c[0])<r&&Math.abs(p[1]-c[1])<r&&Math.abs(p[2]-c[2])<r;

  const colors={wall:[.105,.122,.143],floor:[.067,.081,.092],ceil:[.072,.092,.111],rail:[.32,.27,.22],grid:[.20,.18,.14],cyan:[.20,.94,.76],cyanDim:[.10,.37,.34],amber:[1,.60,.26],red:[1,.19,.24],white:[.94,.91,.79],core:[.87,.13,.18],bot:[.44,.55,.58],botTough:[.84,.33,.24],dark:[.026,.041,.051],pickup:[.19,.91,.66],shield:[.50,.63,.91],violet:[.58,.36,.87],paper:[.94,.87,.60],green:[.25,1,.55],orange:[1,.35,.08],magenta:[.94,.20,1]};

  function compileShader(type,source){const shader=gl.createShader(type);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(shader));return shader;}
  const vShader=`#version 300 es
  precision highp float;
  layout(location=0) in vec3 a_pos;
  layout(location=1) in vec3 a_col;
  uniform mat4 u_mvp;
  uniform vec3 u_eye;
  out vec3 v_color;
  out float v_dist;
  void main(){gl_Position=u_mvp*vec4(a_pos,1.0);v_color=a_col;v_dist=distance(a_pos,u_eye);}`;
  const fShader=`#version 300 es
  precision highp float;
  in vec3 v_color;
  in float v_dist;
  uniform float u_time;
  uniform vec3 u_fogColor;
  uniform float u_fogNear;
  uniform float u_fogFar;
  out vec4 outColor;
  void main(){
    float fog=clamp((v_dist-u_fogNear)/max(1.0,u_fogFar-u_fogNear),0.0,0.88);
    vec3 base=mix(v_color,u_fogColor,fog);
    float pulse=0.985+sin(u_time*.43+v_dist*.028)*.015;
    vec3 color=pow(max(base*pulse,vec3(0.0)),vec3(0.87));
    outColor=vec4(color,1.0);
  }`;
  const program=gl.createProgram();gl.attachShader(program,compileShader(gl.VERTEX_SHADER,vShader));gl.attachShader(program,compileShader(gl.FRAGMENT_SHADER,fShader));gl.linkProgram(program);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
  const uMvp=gl.getUniformLocation(program,'u_mvp'),uEye=gl.getUniformLocation(program,'u_eye'),uTime=gl.getUniformLocation(program,'u_time'),uFogColor=gl.getUniformLocation(program,'u_fogColor'),uFogNear=gl.getUniformLocation(program,'u_fogNear'),uFogFar=gl.getUniformLocation(program,'u_fogFar');
  const vertexArray=gl.createVertexArray(),staticBuffer=gl.createBuffer(),dynamicBuffer=gl.createBuffer();
  gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.disable(gl.CULL_FACE);gl.clearColor(.005,.016,.027,1);

  class Mesh{
    constructor(){this.data=[];}
    tri(a,b,c,color){for(const p of [a,b,c])this.data.push(p[0],p[1],p[2],color[0],color[1],color[2]);}
    quad(a,b,c,d,color){this.tri(a,b,c,color);this.tri(a,c,d,color);}
    box(x0,y0,z0,x1,y1,z1,color){
      const A=[x0,y0,z0],B=[x1,y0,z0],C=[x1,y1,z0],D=[x0,y1,z0],E=[x0,y0,z1],F=[x1,y0,z1],G=[x1,y1,z1],H=[x0,y1,z1];
      this.quad(A,B,C,D,tint(color,.85));this.quad(F,E,H,G,tint(color,.98));this.quad(E,A,D,H,tint(color,.76));this.quad(B,F,G,C,tint(color,.78));this.quad(D,C,G,H,tint(color,.66));this.quad(E,F,B,A,tint(color,1.04));
    }
    rect(axis,coord,u0,u1,v0,v1,col,center){const p=(u,v)=>axis==='x'?[coord,center[1]+v,center[2]+u]:axis==='z'?[center[0]+u,center[1]+v,coord]:[center[0]+u,coord,center[2]+v];this.quad(p(u0,v0),p(u1,v0),p(u1,v1),p(u0,v1),col);}
    wall(axis,coord,rangeU,rangeV,hole,col,center){const [u0,u1]=rangeU,[v0,v1]=rangeV;if(!hole){this.rect(axis,coord,u0,u1,v0,v1,col,center);return;}const s=6;this.rect(axis,coord,u0,-s,v0,v1,col,center);this.rect(axis,coord,s,u1,v0,v1,col,center);this.rect(axis,coord,-s,s,v0,-s,col,center);this.rect(axis,coord,-s,s,s,v1,col,center);}
    octa(center,r,color,rotation=0){const [x,y,z]=center,c=Math.cos(rotation),s=Math.sin(rotation),rot=(a)=>[x+a[0]*c-a[2]*s,y+a[1],z+a[0]*s+a[2]*c],t=rot([0,r,0]),b=rot([0,-r,0]),e=[rot([r,0,0]),rot([0,0,r]),rot([-r,0,0]),rot([0,0,-r])];for(let i=0;i<4;i++){this.tri(t,e[i],e[(i+1)%4],tint(color,i%2?.72:1.03));this.tri(b,e[(i+1)%4],e[i],tint(color,i%2?.51:.77));}}
    rod(a,b,color,thickness=.14){const direction=norm(sub(b,a));let sideways=norm(cross(direction,[0,1,0]));if(len(sideways)<.05)sideways=norm(cross(direction,[1,0,0]));const other=norm(cross(direction,sideways));for(const dir of [sideways,other]){const p=scale(dir,thickness);this.quad(add(a,p),add(b,p),sub(b,p),sub(a,p),color);}}
    ring(center,axis,radius,color,thickness=.18,rotation=0,segments=14){let previous;for(let i=0;i<=segments;i++){const t=i/segments*TAU+rotation,p=axis==='x'?[center[0],center[1]+radius*Math.cos(t),center[2]+radius*Math.sin(t)]:axis==='z'?[center[0]+radius*Math.cos(t),center[1]+radius*Math.sin(t),center[2]]:[center[0]+radius*Math.cos(t),center[1],center[2]+radius*Math.sin(t)];if(previous)this.rod(previous,p,color,thickness);previous=p;}}
    lineBox(a,b,width,color){const min=a.map((n,i)=>Math.min(n,b[i])-width),max=a.map((n,i)=>Math.max(n,b[i])+width);this.box(min[0],min[1],min[2],max[0],max[1],max[2],color);}
  }
  function upload(buffer,mesh,usage){gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(mesh.data),usage);return mesh.data.length/6;}
  function draw(buffer,count){if(!count)return;gl.bindVertexArray(vertexArray);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,3,gl.FLOAT,false,24,12);gl.drawArrays(gl.TRIANGLES,0,count);}

  const VERSION='1.0.0-rc1';
  const BEST_KEY='dissent-local-best-v10';
  const CONFIG_KEY='dissent-config-v10';
  const HISTORY_KEY='dissent-run-history-v10';
  const MODULE_KEY='dissent-modules-v10';
  const CHECKPOINT_KEY='dissent-checkpoint-v10';
  const TUTORIAL_KEY='dissent-tutorial-v10';
  const LEGACY={best:'dissent-local-best-v8',config:'dissent-config-v8',history:'dissent-run-history-v8'};
  const CAMERA_MODES=['chase','hood','cockpit'];
  const WHISPERS=[
    'ADMIN NOTICE: THE RECORD HAS BEEN MISPLACED.','PROCEEDING POSTPONED. TIME CONTINUES.','TRANSCRIPT ACCESS: PAYMENT REQUIRED.','REQUEST ACCEPTED. RELIEF NOT GUARANTEED.','SILENCE HAS BEEN ENTERED AS COMPLIANCE.','YOUR OBJECTION WAS FOUND TO BE INCONVENIENT.','CASE STATUS: PRESENT, BUT NOT HEARD.','ALL PROCEDURAL EXITS LEAD TO ANOTHER PROCEDURE.','THE FLOOR BELOW HAS BEEN DESIGNATED THE FLOOR ABOVE.','PLEASE ATTACH THE ATTACHMENT THAT EXPLAINS THE ATTACHMENT.','YOUR SERVICE CONTACT HAS BEEN SERVED WITH A CONTACT SERVICE ERROR.','THIS HALLWAY IS CLOSED IN THE ORDINARY COURSE.'
  ];
  const INCIDENTS={
    floorRecused:{title:'THE FLOOR HAS RECUSED ITSELF',detail:'ROLL DRIFT ACTIVE · KEEP THE JETTA LEVEL OR SCAN TO STABILIZE',duration:13},
    serviceUnavailable:{title:'SERVICE CONTACT UNAVAILABLE',detail:'SONAR SCRAMBLED · PRESS Z TO FORCE SERVICE',duration:12},
    motionDenied:{title:'MOTION DENIED FOR LACK OF MOTION',detail:'DESTROY THE MECHANICAL BASIS OF DENIAL',duration:22},
    exhibitExhibit:{title:'YOUR EXHIBIT REQUIRES AN EXHIBIT',detail:'RECOVER THE TEMPORARY SUPPLEMENT BEFORE IT EXPIRES',duration:20},
    emergencyContinuance:{title:'EMERGENCY CONTINUANCE',detail:'CONTINUANCE LEECHES HAVE ENTERED THE CALENDAR',duration:24},
    doorForm:{title:'THE DOOR IS TEMPORARILY A FORM',detail:'DESTROY THE FORM OR USE THE PROCEDURAL SHOEHORN',duration:22}
  };
  const ENEMY_DEFS={
    clerk:{name:'CLERK SWARM',hp:2.4,speed:10.5,damage:7,cool:[1.4,2.3],color:colors.bot,score:90},
    redactor:{name:'REDACTOR',hp:3,speed:9.4,damage:6,cool:[1.0,1.8],color:colors.violet,score:125},
    bailiff:{name:'BAILIFF DRONE',hp:7.5,speed:7.0,damage:15,cool:[1.9,2.7],color:colors.botTough,score:190},
    continuance:{name:'CONTINUANCE LEECH',hp:3.4,speed:8.2,damage:5,cool:[1.5,2.2],color:[.60,.35,.92],score:140},
    feeCollector:{name:'FEE COLLECTOR',hp:4.2,speed:7.8,damage:4,cool:[1.2,1.9],color:colors.amber,score:155},
    mimic:{name:'DOCKET MIMIC',hp:4.6,speed:11.4,damage:11,cool:[1.2,2.0],color:colors.paper,score:170},
    wraith:{name:'CITATION WRAITH',hp:3.8,speed:12.2,damage:10,cool:[1.1,1.8],color:colors.magenta,score:180}
  };
  const MODULES={
    shoehorn:{name:'PROCEDURAL SHOEHORN',short:'Z breaks incident forms and reveals secrets',key:'Z'},
    compel:{name:'MOTION TO COMPEL',short:'C emits a room-clearing EMP',key:'C'},
    exhibitA:{name:'EXHIBIT A',short:'Cannons pierce multiple targets',key:'AUTO'},
    writ:{name:'WRIT OF TURBO',short:'Stronger, cheaper afterburner',key:'SHIFT'},
    shield:{name:'OBJECTION OVERRULED',short:'Automatic emergency shield once per descent',key:'AUTO'},
    amend:{name:'LEAVE TO AMEND',short:'X restores energy and rerolls one hazard',key:'X'}
  };
  const BOSS_NAMES={rejection:'THE REJECTION ENGINE',grandSeal:'THE GRAND SEAL',gatekeeper:'THE GATEKEEPER',nullTribunal:'THE NULL TRIBUNAL',erasure:'THE ERASURE ENGINE'};

  const defaultConfig={mode:'grand',assist:'arcade',sensitivity:1,invertY:false,quality:'high',reducedMotion:false,reducedFlash:false,highContrast:false,camera:'chase',skin:'black',music:.30,sfx:.72,uiScale:1,modules:['shoehorn','writ']};
  function readStoredConfig(){try{const raw=localStorage.getItem(CONFIG_KEY)||localStorage.getItem(LEGACY.config)||'{}';return {...defaultConfig,...JSON.parse(raw)};}catch{return {...defaultConfig};}}
  let config=readStoredConfig();
  function persistConfig(){try{localStorage.setItem(CONFIG_KEY,JSON.stringify(config));localStorage.setItem(MODULE_KEY,JSON.stringify(config.modules));}catch{}}
  function bestScore(){try{return Math.max(0,Number(localStorage.getItem(BEST_KEY)||0)||0,Number(localStorage.getItem(LEGACY.best)||0)||0);}catch{return 0;}}
  function storeBest(score){try{if(score>bestScore())localStorage.setItem(BEST_KEY,String(score));}catch{}}
  function runHistory(){try{return JSON.parse(localStorage.getItem(HISTORY_KEY)||localStorage.getItem(LEGACY.history)||'[]');}catch{return [];}}
  function recordRun(entry){try{const h=runHistory();h.unshift(entry);h.length=Math.min(20,h.length);localStorage.setItem(HISTORY_KEY,JSON.stringify(h));}catch{}}
  function displayBest(){const el=$('best');if(el)el.textContent='LOCAL BEST '+String(bestScore()).padStart(7,'0')+' PTS';}


  function checkpointAvailable(){
    try{const data=JSON.parse(localStorage.getItem(CHECKPOINT_KEY)||'null');return !!(data&&data.version===VERSION&&data.generator===DG.VERSION&&data.seed&&data.player&&data.game);}
    catch{return false;}
  }
  function updateResumeButton(){const button=$('resumeRun');if(!button)return;const available=checkpointAvailable();button.hidden=!available;button.disabled=!available;}
  function checkpointSnapshot(){
    if(!game||!facility||!player)return null;
    const safeGame={};for(const key of ['seed','sector','mode','time','score','kills','shotsFired','relaysDown','recordsRecovered','countdown','lastRoom','elapsed','integrity','ledger','redaction','radarScramble','scanPulse','abilityFlash','bossActivated','bossEnrage','bossSecondShield','falseVictory','lastPageTriggered','setpieces','routeHistory','runStartedAt','daily'])safeGame[key]=structuredClone(game[key]);
    return {version:VERSION,generator:DG.VERSION,savedAt:Date.now(),seed:game.seed,sector:game.sector,config:{...config,modules:[...game.modules]},game:safeGame,player:structuredClone(player),records:facility.records.map(r=>({recovered:r.recovered,choice:r.choice,pending:false})),relays:facility.relays.map(r=>({active:r.active,hp:r.hp})),hazards:facility.hazards.map(h=>({active:h.active,disabled:h.disabled,hp:h.hp,paid:h.paid,cooldown:h.cooldown,phase:h.phase})),boss:{active:facility.boss.active,unlocked:facility.boss.unlocked,hp:facility.boss.hp,maxHp:facility.boss.maxHp,cooldown:facility.boss.cooldown,teleport:facility.boss.teleport,phase:facility.boss.phase,position:facility.boss.position.slice(),weakpoints:structuredClone(facility.boss.weakpoints||[])},enemies:structuredClone(enemies),pickups:structuredClone(pickups),incidentNodes:structuredClone(incidentNodes)};
  }
  function saveCheckpoint(force=false){
    if(!game||!player||!facility||!['playing','paused','ledger'].includes(game.phase)||game.pendingRecord)return false;
    if(!force&&game.time-(game.lastCheckpoint||0)<10)return false;
    try{const snap=checkpointSnapshot();if(!snap)return false;localStorage.setItem(CHECKPOINT_KEY,JSON.stringify(snap));game.lastCheckpoint=game.time;updateResumeButton();return true;}catch{return false;}
  }
  function clearCheckpoint(){try{localStorage.removeItem(CHECKPOINT_KEY);}catch{}updateResumeButton();}
  function restoreCheckpoint(data){
    if(!data||data.version!==VERSION||data.generator!==DG.VERSION)return false;
    config={...defaultConfig,...data.config,modules:Array.isArray(data.config?.modules)?data.config.modules:['shoehorn','writ']};applyConfigToUI();
    createWorld(data.seed,data.sector||1);Object.assign(game,data.game||{});game.modules=new Set(config.modules);game.phase='paused';game.pendingRecord=null;game.cinematic=null;game.lastCheckpoint=game.time||0;
    Object.assign(player,data.player||{});player.position=(data.player?.position||facility.rooms[0].position).slice();player.previous=player.position.slice();player.velocity=(data.player?.velocity||[0,0,0]).slice();player.rotation=(data.player?.rotation||[0,0,0,1]).slice();
    (data.records||[]).forEach((x,i)=>{if(facility.records[i])Object.assign(facility.records[i],x,{pending:false});});
    (data.relays||[]).forEach((x,i)=>{if(facility.relays[i])Object.assign(facility.relays[i],x);});
    (data.hazards||[]).forEach((x,i)=>{if(facility.hazards[i])Object.assign(facility.hazards[i],x);});
    if(data.boss){Object.assign(facility.boss,data.boss);facility.boss.position=data.boss.position.slice();facility.boss.weakpoints=structuredClone(data.boss.weakpoints||[]);}
    if(Array.isArray(data.enemies))enemies=structuredClone(data.enemies);if(Array.isArray(data.pickups))pickups=structuredClone(data.pickups);if(Array.isArray(data.incidentNodes))incidentNodes=structuredClone(data.incidentNodes);
    buildArchitecture(roomAt(player.position));updateHUD(true);return true;
  }
  function resumeSavedRun(){
    try{const data=JSON.parse(localStorage.getItem(CHECKPOINT_KEY)||'null');if(!restoreCheckpoint(data)){clearCheckpoint();return false;}audioReady();game.phase='playing';hideScreen();showCinematic('RECORD RESTORED','THE CARPOOL RESUMES.','LOCAL CHECKPOINT VERIFIED. NO CLOUD ACCOUNT WAS REQUIRED.',2.8,'resume',false);canvas.requestPointerLock?.();return true;}catch{clearCheckpoint();return false;}
  }
  function progressBundle(){return {kind:'DISSENT_LOCAL_PROGRESS',version:VERSION,exportedAt:new Date().toISOString(),config,history:runHistory(),best:bestScore(),checkpoint:(()=>{try{return JSON.parse(localStorage.getItem(CHECKPOINT_KEY)||'null');}catch{return null;}})()};}
  function downloadBlob(name,blob){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function exportProgress(){downloadBlob(`DISSENT-progress-${new Date().toISOString().slice(0,10)}.json`,new Blob([JSON.stringify(progressBundle(),null,2)],{type:'application/json'}));}
  async function importProgressFile(file){if(!file)return false;try{const data=JSON.parse(await file.text());if(data.kind!=='DISSENT_LOCAL_PROGRESS')throw new Error('Not a DISSENT progress file');if(data.config)localStorage.setItem(CONFIG_KEY,JSON.stringify({...defaultConfig,...data.config}));if(Array.isArray(data.history))localStorage.setItem(HISTORY_KEY,JSON.stringify(data.history.slice(0,20)));if(Number.isFinite(Number(data.best)))localStorage.setItem(BEST_KEY,String(Math.max(0,Number(data.best))));if(data.checkpoint)localStorage.setItem(CHECKPOINT_KEY,JSON.stringify(data.checkpoint));config=readStoredConfig();applyConfigToUI();displayBest();updateRunHistoryPanel();updateResumeButton();showToast('LOCAL PROGRESS IMPORTED',2);return true;}catch(error){alert(`Import failed: ${error.message||error}`);return false;}}
  function encodeRunCode(payload){try{return btoa(unescape(encodeURIComponent(JSON.stringify(payload)))).replaceAll('=','').slice(0,240);}catch{return '';}}
  function currentResultPayload(){return game?.lastResult||{version:VERSION,seed:game?.seed||'',mode:game?.mode||'',sector:game?.sector||1,score:Math.floor(game?.score||0),integrity:Math.round(game?.integrity||0),elapsed:Math.round(game?.elapsed||0),won:game?.phase==='won'};}
  function resultShareText(){const r=currentResultPayload(),status=r.won?'RECORD EXTRACTED':'CASE BURIED';return `DISSENT: Carpooling to Hell — ${status}\n${String(r.score).padStart(7,'0')} points · ${r.mode} · sector ${r.sector} · integrity ${r.integrity}%\nSeed: ${r.seed}\nRun code: ${encodeRunCode(r)}\nhttps://procedural4.jtforme.com/`;}
  async function copyResult(){const text=resultShareText();try{await navigator.clipboard.writeText(text);showToast('RUN RECORD COPIED',1.8);}catch{prompt('Copy your run record:',text);}}
  function drawResultCard(){const c=$('resultCard');if(!c)return;const ctx=c.getContext('2d'),r=currentResultPayload(),g=ctx.createLinearGradient(0,0,1200,630);g.addColorStop(0,'#071018');g.addColorStop(.55,'#151018');g.addColorStop(1,'#3a090d');ctx.fillStyle=g;ctx.fillRect(0,0,1200,630);ctx.strokeStyle='#71ebbe';ctx.lineWidth=3;ctx.strokeRect(34,34,1132,562);ctx.fillStyle='#f46b73';ctx.font='900 34px system-ui';ctx.fillText('DISSENT.',70,105);ctx.fillStyle='#ecebe2';ctx.font='900 68px system-ui';ctx.fillText(r.won?'RECORD EXTRACTED':'CASE BURIED',70,205);ctx.fillStyle='#efba74';ctx.font='900 78px ui-monospace,monospace';ctx.fillText(String(r.score).padStart(7,'0')+' PTS',70,315);ctx.fillStyle='#a1aeaa';ctx.font='600 25px system-ui';ctx.fillText(`${String(r.mode).toUpperCase()} · SECTOR ${r.sector} · INTEGRITY ${r.integrity}% · ${Math.floor(r.elapsed/60)}m ${pad(r.elapsed%60)}s`,70,375);ctx.fillStyle='#ecebe2';ctx.font='700 24px system-ui';ctx.fillText(`SEED: ${r.seed}`,70,435);ctx.fillStyle='#71ebbe';ctx.font='700 22px system-ui';ctx.fillText('THE COURTS HAVE BASEMENTS. THE JETTA HAS WINGS.',70,520);ctx.fillStyle='#a1aeaa';ctx.font='500 20px system-ui';ctx.fillText('procedural4.JTforME.com',70,558);}
  function downloadResultCard(){drawResultCard();const c=$('resultCard');c?.toBlob(blob=>blob&&downloadBlob(`DISSENT-${game?.seed||'run'}-${Date.now()}.png`,blob),'image/png');}
  function showCinematic(kicker,title,detail,duration=3.5,kind='generic',block=false){if(!game)return;game.cinematic={kicker,title,detail,remaining:duration,duration,kind,block};const el=$('cinematic');if(el){$('cinematicKicker').textContent=kicker;$('cinematicTitle').textContent=title;$('cinematicDetail').textContent=detail;el.classList.add('open');el.setAttribute('aria-hidden','false');}}
  function updateCinematic(dt){if(!game?.cinematic)return;game.cinematic.remaining-=dt;if(game.cinematic.remaining<=0){game.cinematic=null;const el=$('cinematic');if(el){el.classList.remove('open');el.setAttribute('aria-hidden','true');}}}
  const TUTORIAL_STEPS=[
    ['01 · MAKE THE JETTA MOVE','WASD thrusts and strafes. SPACE rises. CTRL descends. Q and E roll. The car can fly in every direction because procedure has already abandoned ordinary geometry.'],
    ['02 · BREAK THE MACHINES','LEFT CLICK fires the wing cannons. F launches a homing missile. Destroy suppression seals, hazards, hostile abstractions, and the mechanical clauses protecting the final machine.'],
    ['03 · RECOVER THE RECORD','Fly into glowing exhibits. EXPOSE weakens the boss, PROTECT repairs the record, and ARCHIVE reveals side evidence. TAB opens the full undercourt map.'],
    ['04 · SURVIVE PROCEDURE','Z scans and applies the Procedural Shoehorn. Other garage modules add EMP, piercing shots, turbo, emergency shielding, or amendment. After the boss falls, race the surviving record back to the surface.']
  ];
  let tutorialStep=0;
  function renderTutorial(){const step=TUTORIAL_STEPS[tutorialStep];if(!step)return;$('tutorialCount').textContent=`${tutorialStep+1} / ${TUTORIAL_STEPS.length}`;$('tutorialTitle').textContent=step[0];$('tutorialText').textContent=step[1];$('tutorialPrev').disabled=tutorialStep===0;$('tutorialNext').textContent=tutorialStep===TUTORIAL_STEPS.length-1?'START THE CARPOOL ▸':'NEXT ▸';}
  function openTutorial(force=false){tutorialStep=0;renderTutorial();const el=$('tutorial');if(el){el.classList.add('open');el.setAttribute('aria-hidden','false');}if(force)el?.setAttribute('data-forced','1');}
  function closeTutorial(start=false){const el=$('tutorial');if(el){el.classList.remove('open');el.setAttribute('aria-hidden','true');el.removeAttribute('data-forced');}try{localStorage.setItem(TUTORIAL_KEY,'seen');}catch{}if(start)startGame(false,false);}
  function requestLaunch(){let seen=false;try{seen=localStorage.getItem(TUTORIAL_KEY)==='seen';}catch{}if(!seen)openTutorial(false);else startGame(false,game?.phase==='paused');}

  let facility=null,player=null,shots=[],enemies=[],pickups=[],sparks=[],incidentNodes=[],game=null;
  let staticCount=0,staticCenterRoom=-1,frameCount=0,lastTime=performance.now(),accumulator=0,shownToastUntil=0,hitFlash=0,viewportW=1,viewportH=1;
  let sound=null,music=null;
  const keys=new Set(),buttons={fire:false};
  const mouseDelta={x:0,y:0};
  const gamepadEdges={};
  let directorRng=Math.random,visualRng=Math.random;
  const FIXED_STEP=1/120;
  const MAX_STEPS=8;

  const shipMesh=new Mesh();
  const JETTA_CREDIT={title:'Volkswagen Bora/Jetta MK4 2005',author:'szymonpasterczyk734',license:'CC BY 4.0'};
  let jettaModelState={loaded:false,source:'PROCEDURAL FALLBACK',triangles:0,error:null};
  const hexColor=(hex)=>{const clean=String(hex||'#ffffff').replace('#','');const n=parseInt(clean.length===3?clean.split('').map(x=>x+x).join(''):clean,16);return [((n>>16)&255)/255,((n>>8)&255)/255,(n&255)/255];};
  function addAuthenticJettaBody(m,patriot){
    const source=window.DISSENT_JETTA_DATA;if(!source?.base64||!source?.lod?.parts)return false;
    try{
      const text=atob(source.base64),bytes=new Uint8Array(text.length);for(let i=0;i<text.length;i++)bytes[i]=text.charCodeAt(i);
      if(bytes.byteLength!==source.lod.bytes)throw new Error(`Mk IV byte count ${bytes.byteLength}/${source.lod.bytes}`);
      const raw=new Float32Array(bytes.buffer),scaleFactor=1.46,yOffset=-1.04;
      for(const part of source.lod.parts){
        const start=part.offset/4,end=start+part.floats;let color=hexColor(part.color);
        if(part.mat===1)color=patriot?[.075,.15,.34]:[.018,.026,.037];
        else if(patriot&&part.mat===2&&part.em>.05)color=[.72,.065,.055];
        for(let i=start;i<end;i+=6)m.data.push(raw[i]*scaleFactor,raw[i+1]*scaleFactor+yOffset,raw[i+2]*scaleFactor,color[0],color[1],color[2]);
      }
      jettaModelState={loaded:true,source:'GRAND PRIX MK IV LOD2',triangles:source.lod.triangles,error:null};return true;
    }catch(error){jettaModelState={loaded:false,source:'PROCEDURAL FALLBACK',triangles:0,error:String(error)};return false;}
  }
  function addProceduralJettaBody(m,patriot){
    const ink=patriot?[.11,.19,.38]:[.052,.063,.076],black=[.023,.029,.038],trim=[.58,.64,.67],glass=[.075,.20,.27],white=[.9,.91,.75],red=[.92,.03,.05];
    m.box(-1.62,-.76,-3.27,1.62,.00,-1.07,ink);m.box(-1.69,-.79,-3.14,1.69,-.38,2.70,black);m.box(-1.49,-.43,1.77,1.49,.13,3.08,ink);m.box(-1.27,-.29,-1.23,1.27,.90,1.52,ink);
    m.box(-1.21,.13,-1.28,1.21,.71,-.99,glass);m.box(-1.23,.12,1.26,1.23,.72,1.48,glass);
    for(const side of [-1,1]){const a=side<0?-1.35:1.14,b=side<0?-1.14:1.35;m.box(a,.06,-.83,b,.62,.05,glass);m.box(a,.06,.25,b,.62,1.13,glass);m.box(a,-.55,-3.03,b,-.27,2.83,tint(trim,.30));m.box(a,-.58,-2.20,b,-.36,-1.63,white);m.box(a,-.48,2.77,b,-.23,3.02,red);for(const z of [-1.94,1.97]){m.box(side*1.64-.31,-1.07,z-.56,side*1.64+.31,-.09,z+.56,black);m.box(side*1.69-.21,-.97,z-.39,side*1.69+.21,-.18,z+.39,tint(trim,.55));}}
    m.box(-.96,-.55,-3.35,.96,-.23,-3.22,black);for(let x=-.74;x<=.74;x+=.2)m.box(x,-.54,-3.42,x+.055,-.24,-3.37,trim);m.box(-.69,.72,.15,.69,.80,1.14,black);
    jettaModelState={loaded:false,source:'PROCEDURAL FALLBACK',triangles:Math.floor(m.data.length/18),error:jettaModelState.error};
  }
  function addDissentWingKit(m,patriot){
    const black=[.023,.029,.038],trim=[.58,.64,.67],wing=patriot?[.46,.055,.06]:[.24,.29,.35],neon=patriot?[1,.72,.12]:[.16,.78,1],red=[.92,.03,.05],gold=[.95,.60,.09];
    for(const side of [-1,1]){const root=[side*1.44,-.22,.38],tip=[side*5.8,-.04,2.15],front=[side*2.52,-.16,-1.48];m.tri(root,tip,front,wing);m.tri(add(root,[0,-.18,0]),add(front,[0,-.18,0]),add(tip,[0,-.18,0]),black);m.rod(front,tip,neon,.10);m.rod(root,tip,trim,.11);m.box(side*4.38-.37,-.43,.77,side*4.38+.37,.03,2.40,black);m.box(side*4.38-.25,-.20,.14,side*4.38+.25,.15,.73,patriot?gold:trim);m.rod([side*4.38,-.18,-.3],[side*4.38,-.18,-2.25],patriot?red:trim,.23);if(patriot)m.rod([side*1.75,.02,-1.0],[side*5.1,.08,1.6],gold,.09);}
    m.box(-1.50,.07,2.81,1.50,.20,3.07,wing);for(const x of [-.85,.85]){m.ring([x,-.36,3.28],'z',.54,trim,.16,0,12);m.ring([x,-.36,3.36],'z',.39,neon,.17,0,12);}m.rod([-1.63,-.88,-2.56],[-1.63,-.88,2.63],neon,.045);m.rod([1.63,-.88,-2.56],[1.63,-.88,2.63],neon,.045);
  }
  function rebuildJetta(){shipMesh.data.length=0;const patriot=config.skin==='patriot';if(!addAuthenticJettaBody(shipMesh,patriot))addProceduralJettaBody(shipMesh,patriot);addDissentWingKit(shipMesh,patriot);const status=$('modelStatus');if(status)status.textContent=`SHIP MESH: ${jettaModelState.source} · ${Math.floor(shipMesh.data.length/18).toLocaleString()} TRIANGLES`;}
  rebuildJetta();

  function appendTransformed(m,raw,pos,rotation){for(let i=0;i<raw.length;i+=6){const p=rotate([raw[i],raw[i+1],raw[i+2]],rotation);m.data.push(p[0]+pos[0],p[1]+pos[1],p[2]+pos[2],raw[i+3],raw[i+4],raw[i+5]);}}
  function appendJetta(m){
    if(config.camera==='cockpit')return;
    appendTransformed(m,shipMesh.data,player.position,player.rotation);
    const spin=player.rotation,pos=player.position,boost=player.boosting,thrust=boost?4.4:1.25+len(player.velocity)*.025,flicker=config.reducedMotion?0:Math.sin(game.time*25)*.22;
    for(const side of [-.85,.85]){const a=add(pos,rotate([side,-.36,3.55],spin)),b=add(pos,rotate([side,-.36,3.55+thrust+flicker],spin));m.rod(a,b,config.skin==='patriot'?[1,.58,.09]:[.09,.67,1],boost?.32:.23);}
    // Moving roll fins and cannon recoil make the absurd conversion feel mechanical.
    const flap=clamp(player.rollInput*1.2,-.8,.8),recoil=player.recoil||0;
    for(const side of [-1,1]){
      const root=add(pos,rotate([side*5.0,.0,1.65],spin)),tip=add(pos,rotate([side*6.2,.4+flap*side,2.1],spin));m.rod(root,tip,colors.cyan,.09);
      const gunA=add(pos,rotate([side*4.38,-.18,-2.2+recoil],spin)),gunB=add(pos,rotate([side*4.38,-.18,-3.5+recoil],spin));m.rod(gunA,gunB,colors.white,.20);
    }
    if(player.hull<45&&visualRng()<.18){const p=add(pos,rotate([visualRng()>.5?1.5:-1.5,-.4,visualRng()*4-1],spin));m.octa(p,.12,colors.orange,game.time);}
  }

  const roomSize=[16,12,16],spacing=DG.SPACING;
  const stratumDef=(index)=>DG.STRATA[clamp(index,0,DG.STRATA.length-1)];
  const directionFrom=(a,b)=>b.cell.map((x,k)=>x-a.cell[k]);
  const hasLinkDirection=(room,dir)=>room.links.some(n=>directionFrom(room,facility.rooms[n]).every((x,i)=>x===dir[i]));

  function addScaleSculpture(m,p,accent){const [x,y,z]=p;m.rod([x,y+10,z],[x,y+4,z],accent,.10);m.rod([x-5,y+5,z],[x+5,y+3,z],tint(accent,.75),.20);m.rod([x-4.3,y+4.7,z],[x-4.3,y+.6,z],tint(accent,.55),.08);m.rod([x+4.3,y+3.4,z],[x+4.3,y-3.8,z],tint(accent,.55),.08);m.box(x-6.2,y+.15,z-1.25,x-2.4,y+.45,z+1.25,tint(accent,.45));m.box(x+2.4,y-4.2,z-1.25,x+6.2,y-3.9,z+1.25,tint(accent,.45));}
  function addClockwork(m,p,accent,seed){const [x,y,z]=p;m.ring([x,y+1,z],'z',5.6,tint(accent,.65),.24,seed,22);m.ring([x,y+1,z],'z',3.8,tint(accent,.42),.16,-seed,18);m.rod([x,y+1,z-.2],[x+Math.sin(seed)*3.6,y+1+Math.cos(seed)*3.6,z-.2],accent,.17);m.rod([x,y+1,z-.15],[x-Math.cos(seed)*2.4,y+1+Math.sin(seed)*2.4,z-.15],tint(accent,.7),.12);}
  function addArchiveRacks(m,p,accent){const [x,y,z]=p;for(const side of [-1,1])for(let row=-1;row<=1;row++){const xx=x+side*12.7,zz=z+row*7.2;m.box(xx-1.5,y-10.8,zz-3,xx+1.5,y+7.8,zz+3,[.07,.08,.075]);for(let h=0;h<7;h++){const yy=y-8.8+h*2.35;m.box(xx-1.7,yy,zz-3.15,xx+1.7,yy+.18,zz+3.15,tint(accent,.35));for(let f=0;f<5;f++)m.box(xx-1.4,yy+.3,zz-2.7+f*1.05,xx+1.4,yy+1.75,zz-1.86+f*1.05,tint(colors.paper,.15+(f%2)*.07));}}}
  function addPaywall(m,p,accent){const [x,y,z]=p;for(const side of [-1,1]){const xx=x+side*11.8;m.box(xx-2.2,y-10.8,z-6,xx+2.2,y+6.8,z+6,[.12,.085,.03]);for(let h=0;h<6;h++)m.ring([xx,y-7+h*2.5,z],'z',1.1,tint(accent,.42),.10,h*.5,12);}m.rod([x-7,y+8,z],[x+7,y+8,z],accent,.3);}
  function addFurnace(m,p,accent,deep=false){const [x,y,z]=p;for(const side of [-1,1]){const xx=x+side*12.5;m.box(xx-2.4,y-10.5,z-6,xx+2.4,y+7,z+6,[.18,.035,.02]);m.box(xx-2.45,y-7.5,z-4.3,xx+2.45,y+2.5,z+4.3,[.55,.055,.018]);for(let h=0;h<4;h++)m.rod([xx,y-6+h*2.1,z-3.8],[xx,y-6+h*2.1,z+3.8],tint(accent,.8),.15);}if(deep){for(let k=-2;k<=2;k++)m.rod([x+k*4.6-2,y-11.68,z-5+Math.sin(k)*6],[x+k*4.6+2,y-11.66,z+4+Math.cos(k)*5],k%2?colors.orange:colors.red,.22);}}
  function addGavel(m,p,accent){const [x,y,z]=p;m.rod([x-6,y+4,z],[x+4,y-5,z],tint(accent,.8),.55);m.box(x+2.2,y-7,z-2.6,x+8,y-2.3,z+2.6,accent);m.box(x-8,y-10.9,z-6,x+8,y-10.2,z+6,tint(accent,.22));}
  function addVoidTribunal(m,p,accent){const [x,y,z]=p;for(let i=0;i<6;i++){const a=i*TAU/6;m.rod([x+Math.sin(a)*10,y-10,z+Math.cos(a)*10],[x+Math.sin(a+.6)*5,y+9,z+Math.cos(a+.6)*5],tint(accent,.5+i*.05),.18);m.octa([x+Math.sin(a)*11,y+Math.sin(a*2)*4,z+Math.cos(a)*11],1.1,accent,a);}m.ring([x,y,z],'y',10.5,tint(accent,.5),.22,.2,20);}

  function architectureNeighborhood(centerId,hops=2){
    const seen=new Set([centerId]),queue=[[centerId,0]];
    while(queue.length){const [id,depth]=queue.shift();if(depth>=hops)continue;for(const next of facility.rooms[id].links)if(!seen.has(next)){seen.add(next);queue.push([next,depth+1]);}}
    return seen;
  }
  function buildArchitecture(centerId=0){
    staticCenterRoom=centerId;const visible=architectureNeighborhood(centerId,config.quality==='low'?1:2),m=new Mesh();
    for(const room of facility.rooms){
      if(!visible.has(room.id))continue;
      const p=room.position,[x,y,z]=p,def=stratumDef(room.stratum),pal=def.palette,shimmer=.82+((room.id*31)%17)/100;
      const wall=room.secret?tint(pal.wall,.45):tint(pal.wall,shimmer),floor=tint(pal.floor,room.secret?.55:1),ceil=tint(pal.ceil,room.secret?.55:1),accent=pal.accent;
      m.wall('x',x-16,[-16,16],[-12,12],hasLinkDirection(room,[-1,0,0]),tint(wall,.88),p);m.wall('x',x+16,[-16,16],[-12,12],hasLinkDirection(room,[1,0,0]),tint(wall,.95),p);
      m.wall('y',y-12,[-16,16],[-16,16],hasLinkDirection(room,[0,-1,0]),floor,p);m.wall('y',y+12,[-16,16],[-16,16],hasLinkDirection(room,[0,1,0]),ceil,p);
      m.wall('z',z-16,[-16,16],[-12,12],hasLinkDirection(room,[0,0,-1]),wall,p);m.wall('z',z+16,[-16,16],[-12,12],hasLinkDirection(room,[0,0,1]),tint(wall,.82),p);
      // Chamber skeleton and floor grid.
      for(const sx of [-1,1])for(const sz of [-1,1]){m.box(x+sx*15.65-.25,y-11.7,z+sz*15.65-.25,x+sx*15.65+.25,y+11.7,z+sz*15.65+.25,tint(accent,.30));for(const sy of [-1,1])m.box(x+sx*15.7-.12,y+sy*11.6-.12,z-16,x+sx*15.7+.12,y+sy*11.6+.12,z+16,tint(accent,.18));}
      for(let k=-12;k<=12;k+=8){m.box(x+k-.065,y-11.91,z-15.5,x+k+.065,y-11.82,z+15.5,tint(accent,.22));m.box(x-15.5,y-11.91,z+k-.065,x+15.5,y-11.82,z+k+.065,tint(accent,.22));}
      for(const sx of [-1,1])m.box(x+sx*12-.42,y+11.58,z-7,x+sx*12+.42,y+11.83,z+7,tint(accent,.42));
      if(room.stratum===0){for(const sx of [-1,1])for(const sz of [-1,1]){const cx=x+sx*11.8,cz=z+sz*11.8;m.box(cx-1.1,y-11.5,cz-1.1,cx+1.1,y-10.2,cz+1.1,tint(colors.white,.45));m.box(cx-.7,y-10.2,cz-.7,cx+.7,y+8,cz+.7,tint(colors.white,.22));m.box(cx-1.25,y+8,cz-1.25,cx+1.25,y+9.1,cz+1.25,tint(accent,.45));}if(room.id%3===1)addScaleSculpture(m,p,accent);}
      else if(room.stratum===1)addClockwork(m,p,accent,room.id*.71);
      else if(room.stratum===2)addArchiveRacks(m,p,accent);
      else if(room.stratum===3)addPaywall(m,p,accent);
      else if(room.stratum===4)addFurnace(m,p,accent,false);
      else if(room.stratum===5){addFurnace(m,p,accent,true);if(room.id%2)addGavel(m,p,accent);for(const sx of [-1,1])for(const sz of [-1,1]){const xx=x+sx*11,zz=z+sz*11;m.rod([xx,y+11,zz],[xx,y+2.5,zz],[.32,.17,.12],.22);for(let h=0;h<3;h++)m.ring([xx,y+7-h*2.5,zz],'y',.72,[.54,.27,.18],.08,0,8);}}
      else addVoidTribunal(m,p,accent);
      if(room.role==='entry')m.box(x-5,y-11.8,z+12.8,x+5,y-11.54,z+15.3,tint(colors.cyanDim,.75));
      if(room.role==='boss'){m.ring(p,'y',11.7,tint(accent,.35),.25,0,28);m.ring(p,'x',10.8,tint(accent,.22),.19,.3,26);}
      if(room.secret){for(let i=0;i<4;i++)m.rod([x-8+i*5.3,y-10.5,z-12],[x-6+i*5.3,y+8,z+12],tint(accent,.18),.12);}
    }

    for(const c of facility.connectors){
      if(!visible.has(c.a)&&!visible.has(c.b))continue;
      const axis=c.axis,[x,y,z]=c.center,a=c.min,b=c.max,sa=facility.rooms[c.a].stratum,sb=facility.rooms[c.b].stratum,accent=mix3(stratumDef(sa).palette.accent,stratumDef(sb).palette.accent,.5),wall=tint(mix3(stratumDef(sa).palette.wall,stratumDef(sb).palette.wall,.5),.85);
      if(axis===0){m.quad([a[0],y-6,z-6],[b[0],y-6,z-6],[b[0],y-6,z+6],[a[0],y-6,z+6],tint(wall,.8));m.quad([a[0],y+6,z-6],[b[0],y+6,z-6],[b[0],y+6,z+6],[a[0],y+6,z+6],wall);for(const s of [-1,1]){const zz=z+s*6;m.quad([a[0],y-6,zz],[b[0],y-6,zz],[b[0],y+6,zz],[a[0],y+6,zz],wall);m.box(a[0],y-5.84,zz-.09,b[0],y-5.57,zz+.09,tint(accent,.55));}}
      else if(axis===2){m.quad([x-6,y-6,a[2]],[x+6,y-6,a[2]],[x+6,y-6,b[2]],[x-6,y-6,b[2]],tint(wall,.75));m.quad([x-6,y+6,a[2]],[x+6,y+6,a[2]],[x+6,y+6,b[2]],[x-6,y+6,b[2]],wall);for(const s of [-1,1]){const xx=x+s*6;m.quad([xx,y-6,a[2]],[xx,y+6,a[2]],[xx,y+6,b[2]],[xx,y-6,b[2]],wall);m.box(xx-.1,y-5.84,a[2],xx+.1,y-5.57,b[2],tint(accent,.55));}}
      else {for(const sx of [-1,1])for(const sz of [-1,1]){const xx=x+sx*5.8,zz=z+sz*5.8;m.rod([xx,a[1],zz],[xx,b[1],zz],wall,.28);m.rod([xx,a[1],zz],[x-sx*5.8,a[1],zz],tint(accent,.35),.10);m.rod([xx,b[1],zz],[x-sx*5.8,b[1],zz],tint(accent,.35),.10);}for(let h=Math.ceil(a[1]/5)*5;h<b[1];h+=5)m.ring([x,h,z],'y',5.1,tint(accent,.23),.10,h*.03,16);}
    }
    staticCount=upload(staticBuffer,m,gl.STATIC_DRAW);
  }

  function pointInside(point,radius=0){for(const volume of facility.volumes){const a=volume.min,b=volume.max;if(point[0]>=a[0]+radius&&point[0]<=b[0]-radius&&point[1]>=a[1]+radius&&point[1]<=b[1]-radius&&point[2]>=a[2]+radius&&point[2]<=b[2]-radius)return true;}return false;}
  function roomAt(point){let best=-1,bestD=Infinity;for(const room of facility.rooms){const p=room.position,d=dist(point,p);if(Math.abs(point[0]-p[0])<17&&Math.abs(point[1]-p[1])<13&&Math.abs(point[2]-p[2])<17)return room.id;if(d<bestD){bestD=d;best=room.id;}}return best;}
  function hasSight(a,b){const d=dist(a,b),steps=Math.ceil(d/2.8);for(let i=1;i<steps;i++)if(!pointInside(add(a,scale(sub(b,a),i/steps)),.15))return false;return true;}
  function relocate(oldPos,newPos,radius){if(pointInside(newPos,radius))return newPos;let result=oldPos.slice();for(const axis of [0,1,2]){const t=result.slice();t[axis]=newPos[axis];if(pointInside(t,radius))result=t;else if(player)player.velocity[axis]*=-.18;}return result;}
  function nearestRoomOnPath(fromRoom,toRoom){if(fromRoom===toRoom)return toRoom;const path=DG.shortestPath(facility.rooms,fromRoom,toRoom);return path.length>1?path[1]:toRoom;}

  let gameRng=Math.random;
  const rand=(a=0,b=1)=>a+(b-a)*gameRng();
  const canOpenArchive=()=>game&&facility&&!facility.records.some(r=>!r.recovered)&&!facility.relays.some(r=>r.active);
  const currentRoom=()=>facility.rooms[roomAt(player.position)]||facility.rooms[0];

  function spawnEnemy(type,position,room,extras={}){
    const d=ENEMY_DEFS[type]||ENEMY_DEFS.clerk;
    const enemy={type,name:d.name,position:position.slice(),origin:position.slice(),velocity:[0,0,0],hp:d.hp,maxHp:d.hp,speed:d.speed,damage:d.damage,cooldown:rand(.5,2.4),room,alive:true,phase:rand(0,TAU),teleport:rand(2.8,5.5),hidden:type==='mimic',revealed:type!=='mimic',tag:extras.tag||null,charge:0};
    enemies.push(enemy);return enemy;
  }
  function enemyTypeForStratum(s){
    const tables=[['clerk','clerk','redactor'],['clerk','redactor','continuance'],['redactor','mimic','clerk'],['feeCollector','clerk','mimic'],['bailiff','continuance','feeCollector'],['bailiff','wraith','continuance'],['wraith','bailiff','redactor']];
    const t=tables[clamp(s,0,tables.length-1)];return t[Math.floor(rand(0,t.length))];
  }

  function createWorld(seed,sector=1){
    gameRng=DG.randomGenerator(`${seed}#${sector}#gameplay#${DG.VERSION}`);directorRng=DG.randomGenerator(`${seed}#${sector}#director#${DG.VERSION}`);visualRng=DG.randomGenerator(`${seed}#${sector}#visual#${DG.VERSION}`);
    facility=DG.generateFacility(seed,sector,{mode:config.mode});
    buildArchitecture(0);
    enemies=[];shots=[];sparks=[];pickups=[];incidentNodes=[];
    const start=facility.rooms[0].position;
    player={position:start.slice(),previous:start.slice(),velocity:[0,0,0],rotation:[0,0,0,1],hull:100,energy:100,missiles:8,lastLaser:-9,lastMissile:-9,hitCooldown:0,rollInput:0,recoil:0,boosting:false,shieldTime:0,emergencyShieldUsed:false,scanCooldown:0,empCooldown:0,amendCharge:1};
    game={seed:String(seed),sector,mode:config.mode,phase:'menu',time:0,score:0,kills:0,shotsFired:0,relaysDown:0,recordsRecovered:0,countdown:0,lastRoom:0,elapsed:0,mapOpen:false,ledgerOpen:false,feed:[],routeHistory:[0],integrity:100,ledger:[],pendingRecord:null,redaction:0,radarScramble:0,scanPulse:0,abilityFlash:0,bossActivated:false,bossEnrage:false,bossSecondShield:false,falseVictory:false,lastPageTriggered:false,cinematic:null,lastCheckpoint:0,setpieces:{continuance:false,furnace:false,bench:false,null:false},incident:null,director:{nextAt:28+directorRng()*18,last:null,history:[],serial:0},modules:new Set(config.modules),cameraLabel:'',runStartedAt:Date.now(),eventLog:[],daily:$('dailySeed')?.dataset.active==='1'};
    facility.rooms[0].visited=true;
    facility.hazards.forEach(h=>{h.hp=h.type==='filingFee'?8:5;h.active=true;h.disabled=false;h.cooldown=0;h.paid=false;h.lastHit=-9;h.position=h.position.slice();});
    facility.boss.maxHp=facility.boss.hp;facility.boss.weakpoints=[];facility.boss.cooldown=3.8;facility.boss.teleport=6;facility.boss.phase=0;facility.boss.unlocked=false;

    for(const room of facility.rooms){
      if(room.id===0||room.id===facility.bossRoom)continue;
      const base=room.stratum>=4?2:1;
      const count=base+(rand()<.42?1:0)+(sector>=3&&rand()<.26?1:0);
      for(let i=0;i<count;i++){const type=enemyTypeForStratum(room.stratum),position=add(room.position,[rand(-7,7),rand(-5,5),rand(-7,7)]);spawnEnemy(type,position,room.id);}
      if(rand()<.48){const roll=rand(),type=roll<.46?'energy':roll<.70?'hull':roll<.90?'missiles':'upgrade';pickups.push({position:add(room.position,[rand(-7,7),rand(-5,4),rand(-7,7)]),type,alive:true,phase:rand(0,TAU),secret:false});}
    }
    addDispatch(`${DG.MODES[config.mode].name} // SECTOR ${pad(sector)}`);
    addDispatch(`${facility.strataCount} CIRCLES BELOW. RECOVER THE RECORD.`);
    showCameraLabel();drawRadar();updateHUD(true);updateRunHistoryPanel();
  }

  function addDispatch(text){if(!game)return;game.feed.unshift(text);game.feed.length=Math.min(5,game.feed.length);const feed=$('dispatchMessages');if(feed)feed.replaceChildren(...game.feed.map((message,index)=>{const li=document.createElement('li');li.textContent=message;li.className=index===0?'fresh':'';return li;}));}
  function showToast(text,seconds=2.5){if(!game)return;shownToastUntil=performance.now()+seconds*1000;const el=$('toast');if(el){el.textContent=text;el.style.opacity='1';}addDispatch(text);updateHUD(true);}
  function showCameraLabel(){if(!game)return;const label={chase:'EXTERIOR CAM // WINGED MK IV',hood:'HOOD CAM // ALL JETTA',cockpit:'COCKPIT CAM // 1999½ VW'}[config.camera];game.cameraLabel=label;const el=$('cameraMode');if(el)el.textContent=label;}

  function audioReady(){
    try{
      if(!sound){sound=new (window.AudioContext||window.webkitAudioContext)();const master=sound.createGain(),sfxGain=sound.createGain(),musicGain=sound.createGain();master.gain.value=.72;master.connect(sound.destination);sfxGain.gain.value=config.sfx;sfxGain.connect(master);musicGain.gain.value=config.music;musicGain.connect(master);sound._master=master;sound._sfx=sfxGain;sound._music=musicGain;}
      if(sound.state==='suspended')sound.resume();
      if(!music)startMusic();
    }catch{sound=null;music=null;}
  }
  function startMusic(){if(!sound||music)return;const nodes=[];for(const spec of [{type:'sine',freq:43,gain:.045},{type:'triangle',freq:64,gain:.024},{type:'sawtooth',freq:86,gain:.008}]){const osc=sound.createOscillator(),g=sound.createGain(),filter=sound.createBiquadFilter();osc.type=spec.type;osc.frequency.value=spec.freq;filter.type='lowpass';filter.frequency.value=320;g.gain.value=spec.gain;osc.connect(filter);filter.connect(g);g.connect(sound._music);osc.start();nodes.push({osc,g,filter,base:spec.freq});}const engine=sound.createOscillator(),engineGain=sound.createGain(),engineFilter=sound.createBiquadFilter();engine.type='sawtooth';engine.frequency.value=48;engineGain.gain.value=.0001;engineFilter.type='lowpass';engineFilter.frequency.value=260;engine.connect(engineFilter);engineFilter.connect(engineGain);engineGain.connect(sound._music);engine.start();music={nodes,engine,engineGain,engineFilter,lastStratum:-1,nextPulse:0,pulseStep:0};}
  function musicPulse(now,s,combat,boss){const scaleSet=[0,3,5,7,10,12],step=music.pulseStep++%scaleSet.length,base=55*Math.pow(2,(scaleSet[(step+s)%scaleSet.length]+s*.5)/12),osc=sound.createOscillator(),g=sound.createGain(),filter=sound.createBiquadFilter();osc.type=boss?'sawtooth':combat?'square':'triangle';osc.frequency.setValueAtTime(base*(boss?.5:1),now);filter.type='bandpass';filter.frequency.value=320+s*90+combat*220;g.gain.setValueAtTime(.0001,now);g.gain.exponentialRampToValueAtTime((boss?.035:combat?.022:.010)*config.music,now+.012);g.gain.exponentialRampToValueAtTime(.0001,now+.20+(boss?.18:0));osc.connect(filter);filter.connect(g);g.connect(sound._music);osc.start(now);osc.stop(now+.45);}
  function updateMusic(){if(!music||!player||!game)return;const s=currentRoom().stratum,combat=enemies.some(e=>e.alive&&dist(e.position,player.position)<24)?1:0,boss=facility.boss.unlocked&&facility.boss.active?1:0,now=sound.currentTime;for(let i=0;i<music.nodes.length;i++){const n=music.nodes[i],ratio=1+s*.065+boss*.14+i*.01;n.osc.frequency.setTargetAtTime(n.base*ratio,now,.45);n.filter.frequency.setTargetAtTime(260+s*55+combat*180+boss*220,now,.5);n.g.gain.setTargetAtTime((i===0?.045:i===1?.024:.008)*(1+combat*.65+boss*.95),now,.3);}const speed=len(player.velocity),engineHz=40+speed*2.5+(player.boosting?55:0);music.engine.frequency.setTargetAtTime(engineHz,now,.05);music.engineFilter.frequency.setTargetAtTime(190+speed*15,now,.08);music.engineGain.gain.setTargetAtTime((.005+speed*.0005+(player.boosting?.018:0))*config.music,now,.08);if(now>=music.nextPulse){musicPulse(now,s,combat,boss);music.nextPulse=now+(boss?.28:combat?.42:.75-s*.025);}sound._music.gain.setTargetAtTime(config.music,now,.2);sound._sfx.gain.setTargetAtTime(config.sfx,now,.2);}
  function sfx(type,pitch=1){if(!sound)return;const now=sound.currentTime,osc=sound.createOscillator(),g=sound.createGain(),filter=sound.createBiquadFilter();osc.connect(filter);filter.connect(g);g.connect(sound._sfx);const settings={laser:[690,250,.075,.048,'sawtooth'],missile:[180,48,.30,.13,'square'],hurt:[110,36,.25,.17,'sawtooth'],enemy:[170,90,.08,.025,'triangle'],relay:[770,135,.46,.16,'sawtooth'],core:[105,22,.78,.22,'sawtooth'],pickup:[350,860,.16,.07,'sine'],ui:[540,620,.09,.04,'sine'],win:[280,980,.85,.14,'sine'],scan:[180,1100,.55,.09,'sine'],emp:[95,760,.42,.16,'square'],choice:[430,720,.26,.08,'triangle'],boss:[70,27,.65,.18,'sawtooth'],stamp:[120,42,.31,.2,'square']}[type]||[320,150,.15,.05,'sine'];osc.type=settings[4];osc.frequency.setValueAtTime(settings[0]*pitch,now);osc.frequency.exponentialRampToValueAtTime(Math.max(20,settings[1]*pitch),now+settings[2]);filter.type='lowpass';filter.frequency.value=type==='laser'?1800:900;g.gain.setValueAtTime(.0001,now);g.gain.exponentialRampToValueAtTime(settings[3],now+.009);g.gain.exponentialRampToValueAtTime(.0001,now+settings[2]);osc.start(now);osc.stop(now+settings[2]+.03);}

  function burst(position,color,count=12,power=11){const amount=config.quality==='low'?Math.ceil(count*.45):config.quality==='medium'?Math.ceil(count*.72):count;for(let i=0;i<amount;i++){const d=norm([visualRng()*2-1,visualRng()*2-1,visualRng()*2-1]);sparks.push({p:position.slice(),velocity:scale(d,(power*.2+visualRng()*power*.8)),life:.3+visualRng()*.65,maxLife:1,color});}}
  function damagePlayer(amount,effect=null){
    if(game.phase!=='playing'||player.hitCooldown>0)return;
    let actual=amount;if(player.shieldTime>0)actual*=.18;
    player.hull=clamp(player.hull-actual,0,100);player.hitCooldown=.28;hitFlash=config.reducedFlash?.18:.62;sfx('hurt');burst(player.position,colors.red,13,6);
    if(effect==='energy')player.energy=Math.max(0,player.energy-14);
    if(effect==='time'&&!facility.boss.active)game.countdown=Math.max(0,game.countdown-5);
    if(effect==='redact')game.redaction=Math.max(game.redaction,3.5);
    if(game.modules.has('shield')&&!player.emergencyShieldUsed&&player.hull<=28){player.emergencyShieldUsed=true;player.shieldTime=5;showToast('OBJECTION OVERRULED // EMERGENCY SHIELD',3);sfx('scan');}
    if(player.hull<=0)finish(false,'THE RECORD WAS BURIED WITH THE JETTA');
  }

  function launchLaser(){
    if(game.phase!=='playing'||game.mapOpen||player.energy<.75||game.time-player.lastLaser<.125)return;
    player.lastLaser=game.time;player.energy-=.75;game.shotsFired++;player.recoil=.42;
    const f=rotate([0,0,-1],player.rotation),r=rotate([1,0,0],player.rotation),u=rotate([0,1,0],player.rotation),side=game.shotsFired%2?-.58:.58;
    const start=add(add(add(player.position,scale(f,2.4)),scale(r,side)),scale(u,-.2));
    shots.push({position:start,velocity:add(scale(f,86),scale(player.velocity,.32)),life:1.55,from:'player',kind:'laser',damage:1,pierce:game.modules.has('exhibitA')?2:0});sfx('laser',1+(game.shotsFired%2)*.04);
  }
  function targetInFront(){
    const f=rotate([0,0,-1],player.rotation),targets=[];
    for(const e of enemies)if(e.alive&&e.revealed)targets.push(e.position);
    for(const r of facility.relays)if(r.active)targets.push(r.position);
    for(const h of facility.hazards)if(h.active&&!h.disabled)targets.push(h.position);
    for(const n of incidentNodes)if(n.active)targets.push(n.position);
    for(const w of facility.boss.weakpoints||[])if(w.active)targets.push(w.position);
    if(facility.boss.active&&facility.boss.unlocked&&!(facility.boss.weakpoints||[]).some(w=>w.active))targets.push(facility.boss.position);
    let best=null,bestVal=-Infinity;for(const p of targets){const delta=sub(p,player.position),d=len(delta),alignment=dot(norm(delta),f),val=alignment-d*.0015;if(alignment>.69&&d<95&&val>bestVal&&hasSight(player.position,p)){best=p;bestVal=val;}}
    return best;
  }
  function launchMissile(){if(game.phase!=='playing'||game.mapOpen||player.missiles<=0||game.time-player.lastMissile<.48)return;player.lastMissile=game.time;player.missiles--;const f=rotate([0,0,-1],player.rotation),p=add(player.position,scale(f,2.4));shots.push({position:p,velocity:add(scale(f,48),scale(player.velocity,.3)),life:4.1,from:'player',kind:'missile',damage:5,target:targetInFront(),pierce:0});sfx('missile');}
  function enemyProjectile(enemy,aim,effect=null){shots.push({position:add(enemy.position,scale(aim,2)),velocity:scale(aim,28+game.sector*1.4),life:2.8,from:'enemy',kind:'bolt',damage:enemy.damage,effect,pierce:0});sfx('enemy',.9+visualRng()*.2);}

  function destroyEnemy(enemy){if(!enemy.alive)return;enemy.alive=false;game.kills++;const def=ENEMY_DEFS[enemy.type]||ENEMY_DEFS.clerk;game.score+=def.score+Math.floor(currentRoom().stratum*12);burst(enemy.position,def.color,19,17);sfx('relay',.72);if(gameRng()<.16)pickups.push({position:enemy.position.slice(),type:gameRng()<.48?'energy':gameRng()<.75?'hull':'missiles',alive:true,phase:rand(0,TAU),secret:false});}
  function disableHazard(h){if(!h||h.disabled)return;h.disabled=true;h.active=false;game.score+=240;burst(h.position,stratumDef(facility.rooms[h.room].stratum).palette.accent,26,13);showToast(`${hazardName(h.type)} DISABLED`,2.2);sfx('relay');}
  function hazardName(type){return {redTape:'RED TAPE GRID',continuanceLoop:'CONTINUANCE CLOCK',shredder:'RECORD SHREDDER',filingFee:'FILING FEE GATE',stampPress:'STAMP PRESS',rejectionChute:'REJECTION CHUTE',missingDocket:'MISSING DOCKET FIELD'}[type]||'PROCEDURAL HAZARD';}
  function destroyIncidentNode(node){if(!node.active)return;node.active=false;game.score+=300;burst(node.position,colors.green,30,15);sfx('scan');if(game.incident&&(game.incident.nodeId===node.id||game.incident.type==='doorForm'))endIncident('BASIS DESTROYED');}

  function hitObject(position,damage,missile=false,shot=null){
    for(const node of incidentNodes){if(!node.active||dist(position,node.position)>(missile?7:3.0))continue;node.hp-=damage;if(node.hp<=0)destroyIncidentNode(node);else burst(position,colors.green,5,6);return true;}
    for(const weak of facility.boss.weakpoints||[]){if(!weak.active||dist(position,weak.position)>(missile?7:3.2))continue;weak.hp-=damage;if(weak.hp<=0){weak.active=false;game.score+=260;burst(weak.position,colors.magenta,28,18);sfx('relay');if(!facility.boss.weakpoints.some(w=>w.active))showToast(`${facility.boss.name} EXPOSED // STRIKE THE CORE`,3);}return true;}
    for(const enemy of enemies){if(!enemy.alive||!enemy.revealed||dist(position,enemy.position)>(missile?6.5:2.9))continue;enemy.hp-=damage*(missile?.9:1);burst(position,ENEMY_DEFS[enemy.type].color,5,7);if(enemy.hp<=0)destroyEnemy(enemy);return true;}
    for(const relay of facility.relays){if(!relay.active||dist(position,relay.position)>(missile?6.5:3.1))continue;relay.hp-=damage;burst(position,colors.amber,8,8);if(relay.hp<=0){relay.active=false;game.relaysDown++;game.score+=360;burst(relay.position,colors.amber,36,19);sfx('relay');showToast(game.relaysDown===facility.relays.length?'ALL SUPPRESSION SEALS BROKEN':'SUPPRESSION SEAL BROKEN // '+(facility.relays.length-game.relaysDown)+' REMAIN',2.8);activateBossIfReady();}return true;}
    for(const h of facility.hazards){if(h.disabled||!h.active||dist(position,h.position)>(missile?7:3.6))continue;h.hp-=damage;if(h.hp<=0)disableHazard(h);else burst(position,colors.orange,6,7);return true;}
    const boss=facility.boss;
    if(boss.active&&boss.unlocked&&!boss.weakpoints.some(w=>w.active)&&dist(position,boss.position)<(missile?9:5.7)){
      boss.hp-=damage;burst(position,colors.red,10,10);if(!game.bossEnrage&&boss.hp<=boss.maxHp*.5){game.bossEnrage=true;boss.phase=2;showToast(`${boss.name} // PHASE TWO`,3);spawnBossReinforcements();sfx('boss');}
      if(boss.hp<=0)defeatBoss();return true;
    }
    return false;
  }
  function explodeMissile(position){burst(position,colors.amber,28,18);hitObject(position,5,true);for(const enemy of enemies)if(enemy.alive&&enemy.revealed&&dist(position,enemy.position)<8){enemy.hp-=2.5;if(enemy.hp<=0)destroyEnemy(enemy);}for(const h of facility.hazards)if(!h.disabled&&dist(position,h.position)<8){h.hp-=2.5;if(h.hp<=0)disableHazard(h);}}
  function updateShots(dt){
    for(const shot of shots){if(shot.dead)continue;const old=shot.position.slice();if(shot.kind==='missile'&&shot.target){const desired=norm(sub(shot.target,shot.position));if(len(desired)>.001){const heading=norm(shot.velocity);shot.velocity=scale(norm(add(scale(heading,.88),scale(desired,.12))),58);}}
      shot.position=add(shot.position,scale(shot.velocity,dt));shot.life-=dt;
      if(shot.life<=0||!pointInside(shot.position,.12)){shot.dead=true;if(shot.kind==='missile')explodeMissile(old);else if(visualRng()<.35)burst(old,shot.from==='player'?colors.cyan:colors.red,3,4);continue;}
      if(shot.from==='player'){
        const increments=Math.max(1,Math.ceil(dist(old,shot.position)/1.35));for(let k=1;k<=increments;k++){const p=add(old,scale(sub(shot.position,old),k/increments));if(hitObject(p,shot.damage,shot.kind==='missile',shot)){if(shot.pierce>0&&shot.kind==='laser'){shot.pierce--;shot.damage*=.82;}else{shot.dead=true;if(shot.kind==='missile')explodeMissile(p);break;}}}
      }else if(dist(shot.position,player.position)<2.1){damagePlayer(shot.damage,shot.effect);shot.dead=true;}
    }
    shots=shots.filter(s=>!s.dead);
  }

  function beginEvidenceChoice(record){if(game.pendingRecord||record.recovered||record.pending)return;record.pending=true;game.pendingRecord=record;game.phase='choice';if(document.pointerLockElement===canvas)document.exitPointerLock();const panel=$('evidenceChoice');if(panel){$('evidenceClass').textContent=record.class;$('evidenceTitle').textContent=record.title;$('evidenceBlurb').textContent=record.blurb;panel.classList.add('open');panel.setAttribute('aria-hidden','false');}showToast('EVIDENCE RECOVERED // CHOOSE ITS DISPOSITION',2);sfx('choice');}
  function chooseEvidence(choice){const record=game?.pendingRecord;if(!record)return;record.pending=false;record.recovered=true;record.choice=choice;game.pendingRecord=null;game.recordsRecovered++;const entry={class:record.class,title:record.title,choice,stratum:facility.rooms[record.room].stratum};game.ledger.push(entry);if(choice==='expose'){game.score+=650;facility.boss.maxHp=Math.max(12,facility.boss.maxHp-2);facility.boss.hp=Math.min(facility.boss.hp,facility.boss.maxHp);showToast('EXPOSED // BOSS ARMOR WEAKENED',2.6);}else if(choice==='protect'){game.score+=450;game.integrity=clamp(game.integrity+18,0,100);player.hull=clamp(player.hull+12,0,100);showToast('PROTECTED // RECORD INTEGRITY RESTORED',2.6);}else{game.score+=520;revealNearestSecret();showToast('ARCHIVED // A SEALED SIDE RECORD IS REVEALED',2.8);}burst(record.position,colors.paper,38,11);sfx('pickup');const panel=$('evidenceChoice');if(panel){panel.classList.remove('open');panel.setAttribute('aria-hidden','true');}game.phase='playing';canvas.requestPointerLock?.();activateBossIfReady();updateHUD(true);}
  function revealNearestSecret(){const options=facility.secrets.filter(s=>!s.revealed);if(!options.length)return;options.sort((a,b)=>dist(facility.rooms[a.room].position,player.position)-dist(facility.rooms[b.room].position,player.position));const secret=options[0];secret.revealed=true;facility.rooms[secret.room].secret=false;pickups.push({position:secret.position.slice(),type:secret.reward==='upgrade'?'upgrade':'evidenceCache',alive:true,phase:rand(0,TAU),secret:true});}

  function activateBossIfReady(){
    if(!canOpenArchive()||game.bossActivated||!facility.boss.active)return;
    game.bossActivated=true;facility.boss.unlocked=true;facility.boss.phase=1;
    const exposed=game.ledger.filter(x=>x.choice==='expose').length,count=Math.max(2,facility.boss.weakpointCount-exposed);
    facility.boss.weakpoints=[];for(let i=0;i<count;i++){const a=i*TAU/count;facility.boss.weakpoints.push({id:i,position:add(facility.boss.position,[Math.sin(a)*7,Math.sin(a*2)*2.4,Math.cos(a)*7]),hp:3+Math.floor(game.sector/3),active:true,phase:a});}
    spawnBossReinforcements();showToast(`${facility.boss.name} AWAKENS // DESTROY ${count} CLAUSES`,4);addDispatch('THE FINAL MACHINE HAS ENTERED THE RECORD.');sfx('boss');
  }
  function spawnBossReinforcements(){const room=facility.rooms[facility.bossRoom];for(let i=0;i<(game.bossEnrage?3:2);i++){const type=game.bossEnrage?(i%2?'wraith':'bailiff'):(i?'bailiff':'redactor'),p=add(room.position,[i?8:-8,i*2-2,i%2?-7:7]);spawnEnemy(type,p,room.id,{tag:'boss'});}}
  function triggerFalseVictory(){const b=facility.boss;game.falseVictory=true;game.bossEnrage=true;b.phase=3;b.hp=Math.max(14,Math.round(b.maxHp*.34));const count=Math.min(5,Math.max(3,b.weakpointCount));b.weakpoints=[];for(let i=0;i<count;i++){const a=i*TAU/count;b.weakpoints.push({id:i,position:add(b.position,[Math.sin(a)*8,Math.sin(a*3)*3,Math.cos(a)*8]),hp:4+Math.floor(game.sector/3),active:true,phase:a});}spawnBossReinforcements();showCinematic('ORDER GRANTED','RELIEF HAS BEEN GRANTED.','THE ORDER GRANTING RELIEF HAS BEEN VACATED BY A LOWER LEVEL OF THE SAME COURT.',5.2,'falseVictory',false);showToast('FALSE VICTORY // THE FLOOR OPENS AGAIN',4);addDispatch('THE WORD GRANTED WAS USED IN A NONBINDING SENSE.');sfx('boss');burst(b.position,colors.magenta,80,24);}
  function spawnExtractionPursuit(){const room=currentRoom(),ids=[room.id,...room.links];for(let i=0;i<Math.min(6,2+game.sector);i++){const r=facility.rooms[ids[i%ids.length]],type=i%3===0?'wraith':i%2?'continuance':'bailiff',p=add(r.position,[rand(-7,7),rand(-4,4),rand(-7,7)]);spawnEnemy(type,p,r.id,{tag:'last-page'});}addDispatch('THE LAST PAGE HAS BEEN LOCATED. THE MACHINE IS TRYING TO ERASE THE ROUTE HOME.');}
  function defeatBoss(){const b=facility.boss;if(!b.active)return;if(!game.falseVictory&&game.mode!=='quick'){triggerFalseVictory();return;}b.active=false;b.hp=0;game.score+=2400+facility.strataCount*180;game.countdown=facility.extractionTime+game.ledger.filter(x=>x.choice==='protect').length*8;sfx('core');burst(b.position,colors.red,95,30);showCinematic('FINAL ORDER','THE MACHINE IS DISABLED.','CARRY THE LAST PAGE THROUGH THE COLLAPSING UNDERCOURT.',4.2,'bossDefeated',false);showToast(`${b.name} DISABLED // EXTRACT THE RECORD`,4);addDispatch('THE VAULT IS COLLAPSING. DRIVE UP.');saveCheckpoint(true);}

  function updateEnemies(dt){
    const pRoom=roomAt(player.position);
    for(const e of enemies){if(!e.alive)continue;
      const toPlayer=sub(player.position,e.position),d=len(toPlayer),see=d<43&&hasSight(e.position,player.position);
      if(e.type==='mimic'&&!e.revealed){if(d<8.5){e.revealed=true;e.hidden=false;showToast('DOCKET MIMIC // THE PICKUP OBJECTS',1.8);sfx('enemy');}else continue;}
      if(e.type==='wraith'){e.teleport-=dt;if(e.teleport<=0&&d<55){const room=facility.rooms[pRoom];const candidates=[room.id,...room.links];const targetRoom=facility.rooms[candidates[Math.floor(rand(0,candidates.length))]];const candidate=add(targetRoom.position,[rand(-7,7),rand(-5,5),rand(-7,7)]);if(pointInside(candidate,2)){burst(e.position,colors.magenta,12,6);e.position=candidate;e.origin=candidate.slice();burst(e.position,colors.magenta,12,6);}e.teleport=rand(3.5,6);}}
      let target;
      if(see){
        if(e.type==='redactor'||e.type==='continuance'||e.type==='feeCollector')target=d>15?player.position:add(e.position,scale(norm(toPlayer),-9));
        else target=d>7?player.position:add(e.position,scale(norm(toPlayer),-5));
      }else{
        const eRoom=roomAt(e.position),next=nearestRoomOnPath(eRoom,pRoom);target=next!==eRoom?facility.rooms[next].position:add(e.origin,[Math.sin(game.time*.7+e.phase)*5,Math.sin(game.time*.9+e.phase)*3,Math.cos(game.time*.6+e.phase)*5]);
      }
      let speed=e.speed;if(e.type==='bailiff'&&d<13&&see){e.charge=Math.max(0,e.charge-dt);if(e.charge<=0){speed*=2.25;e.charge=4.7;}}
      const desired=scale(norm(sub(target,e.position)),see?speed:speed*.58),response=1-Math.exp(-dt*2.4);e.velocity=add(scale(e.velocity,1-response),scale(desired,response));
      const moved=add(e.position,scale(e.velocity,dt));if(pointInside(moved,e.type==='bailiff'?2.3:1.7))e.position=moved;
      e.cooldown-=dt;
      if(e.type==='redactor'&&see&&d<18)game.redaction=Math.max(game.redaction,.25);
      if(e.cooldown<=0&&see&&game.phase==='playing'){
        const def=ENEMY_DEFS[e.type],range=def.cool;e.cooldown=rand(range[0],range[1])/(1+.045*(game.sector-1));const aim=norm(add(toPlayer,[rand(-1.5,1.5),rand(-1.5,1.5),rand(-1.5,1.5)]));
        if(e.type==='feeCollector')enemyProjectile(e,aim,'energy');else if(e.type==='continuance')enemyProjectile(e,aim,'time');else if(e.type==='redactor')enemyProjectile(e,aim,'redact');else enemyProjectile(e,aim,null);
      }
      if(d<2.4&&e.type==='bailiff')damagePlayer(12);
    }
  }

  function updateHazards(dt){
    const roomId=roomAt(player.position),room=facility.rooms[roomId];
    for(const h of facility.hazards){if(h.disabled||!h.active)continue;h.cooldown=Math.max(0,h.cooldown-dt);const nearRoom=roomId===h.room,d=dist(player.position,h.position),t=game.time+h.phase;
      if(h.type==='redTape'&&nearRoom){const active=Math.sin(t*2.1)>.12;if(active){const axis=h.id%2,delta=axis===0?Math.abs(player.position[0]-h.position[0]):Math.abs(player.position[2]-h.position[2]);if(delta<.75&&Math.abs(player.position[1]-h.position[1])<8&&h.cooldown<=0){damagePlayer(11);h.cooldown=.75;}}}
      else if(h.type==='continuanceLoop'&&nearRoom&&d<7){player.velocity=scale(player.velocity,Math.exp(-dt*2.1));game.abilityFlash=Math.max(game.abilityFlash,.15);}
      else if(h.type==='shredder'&&nearRoom&&d<6&&h.cooldown<=0){game.integrity=Math.max(0,game.integrity-4);damagePlayer(4);h.cooldown=.65;if(game.integrity<=0)finish(false,'THE RECORD WAS SHREDDED INTO PROCEDURALLY CORRECT PIECES');}
      else if(h.type==='filingFee'&&nearRoom&&d<7&&!h.paid){player.velocity=scale(player.velocity,Math.exp(-dt*3));player.energy=Math.max(0,player.energy-dt*8);if(player.energy<=18){h.paid=true;showToast('FILING FEE PAID // ENERGY ACCOUNT DEPLETED',2.4);}}
      else if(h.type==='stampPress'&&nearRoom){const active=Math.sin(t*1.65)>.58;if(active&&d<5.5&&h.cooldown<=0){damagePlayer(18);h.cooldown=1.0;sfx('stamp');}}
      else if(h.type==='rejectionChute'&&nearRoom&&d<3.5&&h.cooldown<=0){const target=facility.rooms[h.targetRoom]?.position;if(target){player.position=add(target,[0,4,0]);player.velocity=[0,-4,0];damagePlayer(8);showToast('REJECTED // RETURNED TO A LOWER DIVISION',2.8);h.cooldown=9;}}
      else if(h.type==='missingDocket'&&nearRoom&&d<8){game.radarScramble=Math.max(game.radarScramble,.18);if(Math.sin(t*.8)>.94&&h.cooldown<=0){const candidates=[room.id,...room.links],target=facility.rooms[candidates[Math.floor(rand(0,candidates.length))]];player.position=add(target.position,[rand(-3,3),rand(-2,2),rand(-3,3)]);h.cooldown=8;showToast('DOCKET TILE PHASED // LOCATION AMENDED',2);}}
    }
  }

  function startIncident(type){
    if(!INCIDENTS[type]||game.incident)return;const def=INCIDENTS[type],room=currentRoom(),incident={type,title:def.title,detail:def.detail,remaining:def.duration,nodeId:null,tag:`incident-${++game.director.serial}`};game.incident=incident;game.director.last=type;game.director.history.push({type,time:game.time,room:room.id});game.eventLog.push(`INCIDENT ${type} @ ${game.time.toFixed(1)}`);
    if(type==='motionDenied'||type==='doorForm'){
      const node={id:incidentNodes.length,type,position:add(room.position,[rand(-5,5),rand(-3,3),rand(-5,5)]),hp:type==='doorForm'?8:6,active:true,room:room.id,phase:rand(0,TAU)};incidentNodes.push(node);incident.nodeId=node.id;
    }else if(type==='exhibitExhibit')pickups.push({position:add(room.position,[rand(-5,5),rand(-3,3),rand(-5,5)]),type:'supplement',alive:true,phase:rand(0,TAU),secret:false,incidentTag:incident.tag});
    else if(type==='emergencyContinuance'){for(let i=0;i<3;i++)spawnEnemy('continuance',add(room.position,[i*5-5,rand(-4,4),i%2?6:-6]),room.id,{tag:incident.tag});if(!facility.boss.active)game.countdown+=12;}
    const banner=$('incidentBanner');if(banner){$('incidentTitle').textContent=def.title;$('incidentDetail').textContent=def.detail;banner.classList.add('open');}
    showToast(def.title,3.5);sfx('stamp');
  }
  function endIncident(reason='PROCEDURE SURVIVED'){if(!game.incident)return;addDispatch(`${game.incident.title} // ${reason}`);const banner=$('incidentBanner');if(banner)banner.classList.remove('open');game.incident=null;game.director.nextAt=game.time+30+directorRng()*26;}
  function updateDirector(dt){
    const incident=game.incident;
    if(incident){incident.remaining-=dt;if(incident.type==='floorRecused'){const drift=Math.sin(game.time*1.9)*.42;player.rotation=qNorm(qMul(player.rotation,qAxis([0,0,1],drift*dt)));}if(incident.type==='serviceUnavailable')game.radarScramble=Math.max(game.radarScramble,.35);if(incident.type==='doorForm')player.velocity=scale(player.velocity,Math.exp(-dt*.45));if(incident.type==='emergencyContinuance'&&!enemies.some(e=>e.alive&&e.tag===incident.tag))endIncident('CALENDAR CLEARED');else if(incident.type==='exhibitExhibit'&&!pickups.some(p=>p.alive&&p.incidentTag===incident.tag))endIncident('SUPPLEMENT FILED');else if(incident.remaining<=0)endIncident('TIME EXPIRED WITHOUT FURTHER ORDER');return;}
    if(game.time<game.director.nextAt||game.phase!=='playing'||game.elapsed<18)return;
    const progress=(game.recordsRecovered/facility.records.length+game.relaysDown/facility.relays.length)*.5,tension=clamp((100-player.hull)/100+enemies.filter(e=>e.alive&&dist(e.position,player.position)<24).length*.11+progress*.35,0,1);
    if(directorRng()>.45+tension*.35){game.director.nextAt+=8;return;}
    const choices=['floorRecused','serviceUnavailable','motionDenied','exhibitExhibit','emergencyContinuance','doorForm'].filter(x=>x!==game.director.last);startIncident(choices[Math.floor(directorRng()*choices.length)]);
  }

  function useScan(){if(player.scanCooldown>0)return;player.scanCooldown=game.modules.has('shoehorn')?7:14;game.scanPulse=1;let affected=0;for(const secret of facility.secrets)if(!secret.revealed&&dist(facility.rooms[secret.room].position,player.position)<70){secret.revealed=true;facility.rooms[secret.room].secret=false;pickups.push({position:secret.position.slice(),type:secret.reward==='upgrade'?'upgrade':'evidenceCache',alive:true,phase:rand(0,TAU),secret:true});affected++;}
    for(const node of incidentNodes)if(node.active&&dist(node.position,player.position)<22){node.hp-=game.modules.has('shoehorn')?99:2;if(node.hp<=0)destroyIncidentNode(node);affected++;}
    if(game.incident&&['floorRecused','serviceUnavailable'].includes(game.incident.type)){endIncident('PROCEDURAL SHOEHORN APPLIED');affected++;}
    for(const h of facility.hazards)if(!h.disabled&&dist(h.position,player.position)<16){h.hp-=game.modules.has('shoehorn')?2:1;if(h.hp<=0)disableHazard(h);affected++;}
    showToast(affected?`SCAN PULSE // ${affected} PROCEDURAL DEFECTS FOUND`:'SCAN PULSE // NO NEW DEFECTS',2.3);sfx('scan');}
  function useEMP(){if(!game.modules.has('compel')){showToast('MOTION TO COMPEL MODULE NOT INSTALLED',1.8);return;}if(player.empCooldown>0)return;player.empCooldown=18;let hits=0;for(const e of enemies)if(e.alive&&e.revealed&&dist(e.position,player.position)<18){e.hp-=3.5;hits++;if(e.hp<=0)destroyEnemy(e);}for(const h of facility.hazards)if(!h.disabled&&dist(h.position,player.position)<18){h.hp-=3;hits++;if(h.hp<=0)disableHazard(h);}burst(player.position,colors.cyan,45,22);showToast(`MOTION TO COMPEL // ${hits} TARGETS COMPELLED`,2.5);sfx('emp');}
  function useAmend(){if(!game.modules.has('amend')){showToast('LEAVE TO AMEND MODULE NOT INSTALLED',1.8);return;}if(player.amendCharge<=0)return;player.amendCharge--;player.energy=clamp(player.energy+42,0,100);player.hull=clamp(player.hull+12,0,100);const h=facility.hazards.filter(x=>!x.disabled).sort((a,b)=>dist(a.position,player.position)-dist(b.position,player.position))[0];if(h){h.phase+=Math.PI;h.cooldown=4;}showToast('LEAVE TO AMEND GRANTED // LOADOUT CORRECTED',2.8);sfx('choice');}

  function updatePickups(){
    for(const p of pickups){if(!p.alive||dist(p.position,player.position)>=3.1)continue;p.alive=false;let label='';if(p.type==='energy'){player.energy=clamp(player.energy+34,0,100);label='ENERGY RESTORED';}else if(p.type==='hull'){player.hull=clamp(player.hull+28,0,100);label='HULL STABILIZED';}else if(p.type==='missiles'){player.missiles=Math.min(14,player.missiles+4);label='ORDNANCE RESTORED';}else if(p.type==='upgrade'){player.energy=100;player.missiles=Math.min(14,player.missiles+2);game.score+=180;label='SEALED GARAGE CACHE RECOVERED';}else if(p.type==='evidenceCache'){game.integrity=clamp(game.integrity+25,0,100);game.score+=300;label='SIDE RECORD PRESERVED';}else if(p.type==='supplement'){game.score+=350;label='SUPPLEMENTAL EXHIBIT FILED';}
      game.score+=25;showToast(label,1.8);sfx('pickup');burst(p.position,p.type==='hull'?colors.shield:p.type==='supplement'?colors.paper:colors.pickup,14,9);
    }
    for(const record of facility.records){if(record.recovered||record.pending||dist(record.position,player.position)>3.7)continue;beginEvidenceChoice(record);break;}
  }
  function updateSparks(dt){for(const p of sparks){p.p=add(p.p,scale(p.velocity,dt));p.velocity=scale(p.velocity,Math.exp(-dt*2.2));p.life-=dt;}sparks=sparks.filter(p=>p.life>0);}

  function updateBoss(dt){
    const b=facility.boss;if(!b.active||!b.unlocked)return;
    const t=game.time,center=b.position;
    for(const w of b.weakpoints){if(!w.active)continue;const radius=b.type==='grandSeal'?8.5:7,rate=b.type==='nullTribunal'?1.15:.55,angle=w.phase+t*rate*(game.bossEnrage?1.5:1);w.position=[center[0]+Math.sin(angle)*radius,center[1]+Math.sin(angle*2.1)*2.8,center[2]+Math.cos(angle)*radius];}
    const d=dist(player.position,center);if(d>55)return;
    b.cooldown-=dt;b.teleport-=dt;
    if(b.type==='nullTribunal'&&b.teleport<=0){const room=facility.rooms[b.room];b.position=add(room.position,[rand(-8,8),rand(-5,5),rand(-8,8)]);b.teleport=game.bossEnrage?3.5:5.5;showToast('NULL TRIBUNAL // VENUE TRANSFERRED',1.7);burst(b.position,colors.magenta,20,9);}
    if(b.cooldown<=0){
      b.cooldown=(game.bossEnrage?2.4:3.8)+rand(0,1.2);const count=game.bossEnrage?12:8;
      for(let i=0;i<count;i++){const a=i*TAU/count+t*.3,dir=norm([Math.sin(a),Math.sin(a*2)*.25,Math.cos(a)]);shots.push({position:add(b.position,scale(dir,4.6)),velocity:scale(dir,24+(game.bossEnrage?7:0)),life:3.0,from:'enemy',kind:'boss',damage:game.bossEnrage?11:8,effect:b.type==='rejection'?'redact':b.type==='grandSeal'?'energy':null});}
      if(['rejection','erasure'].includes(b.type)){const room=facility.rooms[b.room];const p=add(room.position,[rand(-7,7),rand(-4,4),rand(-7,7)]);incidentNodes.push({id:incidentNodes.length,type:'bossClause',position:p,hp:4,active:true,room:room.id,phase:rand(0,TAU)});}
      sfx('boss');
    }
    if(b.type==='gatekeeper'&&game.bossEnrage&&Math.sin(t*.7)>.985){const room=facility.rooms[b.room];spawnEnemy('bailiff',add(room.position,[rand(-9,9),rand(-4,4),rand(-9,9)]),room.id,{tag:'boss'});}
    if(b.type==='grandSeal'&&!game.bossSecondShield&&b.hp<b.maxHp*.35&&!b.weakpoints.some(w=>w.active)){game.bossSecondShield=true;for(let i=0;i<3;i++){const a=i*TAU/3;b.weakpoints.push({id:b.weakpoints.length,position:add(b.position,[Math.sin(a)*8,0,Math.cos(a)*8]),hp:3,active:true,phase:a});}showToast('THE GRAND SEAL HAS ATTACHED ANOTHER CLAUSE',3);}
    if(b.type==='erasure'&&d<20){game.integrity=Math.max(0,game.integrity-dt*(game.bossEnrage?2.2:1.1));if(game.integrity<=0){finish(false,'THE ERASURE ENGINE CONSUMED THE LAST SURVIVING PAGE');return;}}
    if(b.type==='rejection'&&d<11&&Math.sin(t*2.2)>.94&&player.hitCooldown<=0){damagePlayer(game.bossEnrage?17:11,'redact');sfx('stamp');}
  }

  function gamepadState(){
    const pads=navigator.getGamepads?.()||[];const pad=[...pads].find(Boolean);if(!pad)return null;
    const dead=(x)=>Math.abs(x)<.13?0:x;
    return {strafe:dead(pad.axes[0]||0),vertical:-dead(pad.axes[1]||0),yaw:dead(pad.axes[2]||0),pitch:dead(pad.axes[3]||0),forward:(pad.buttons[7]?.value||0)-(pad.buttons[6]?.value||0),roll:(pad.buttons[5]?.value||0)-(pad.buttons[4]?.value||0),fire:!!pad.buttons[0]?.pressed,missile:!!pad.buttons[1]?.pressed,boost:!!pad.buttons[2]?.pressed,scan:!!pad.buttons[3]?.pressed,emp:!!pad.buttons[10]?.pressed,map:!!pad.buttons[8]?.pressed,pause:!!pad.buttons[9]?.pressed};
  }
  function edge(name,value){const was=!!gamepadEdges[name];gamepadEdges[name]=!!value;return value&&!was;}

  function updatePlayer(dt){
    const gp=gamepadState();
    const sensitivity=.00225*config.sensitivity,mouseYaw=-mouseDelta.x*sensitivity,mousePitch=(config.invertY?1:-1)*mouseDelta.y*sensitivity;mouseDelta.x=0;mouseDelta.y=0;
    if(mouseYaw||mousePitch)player.rotation=qNorm(qMul(qMul(player.rotation,qAxis([0,1,0],mouseYaw)),qAxis([1,0,0],mousePitch)));
    if(gp&&(gp.yaw||gp.pitch))player.rotation=qNorm(qMul(qMul(player.rotation,qAxis([0,1,0],-gp.yaw*dt*2.2*config.sensitivity)),qAxis([1,0,0],(config.invertY?1:-1)*gp.pitch*dt*2.0*config.sensitivity)));
    const right=rotate([1,0,0],player.rotation),up=rotate([0,1,0],player.rotation),front=rotate([0,0,-1],player.rotation);
    const strafe=(+keys.has('KeyD')-+keys.has('KeyA'))+(gp?.strafe||0),forward=(+keys.has('KeyW')-+keys.has('KeyS'))+(gp?.forward||0),vertical=(+keys.has('Space')-+(keys.has('ControlLeft')||keys.has('ControlRight')))+(gp?.vertical||0);
    let input=add(add(scale(right,strafe),scale(up,vertical)),scale(front,forward)),inputLen=Math.min(1,len(input));if(inputLen>.001)input=scale(norm(input),inputLen);
    const roll=(+keys.has('KeyE')-+keys.has('KeyQ'))+(gp?.roll||0);player.rollInput=roll;if(roll)player.rotation=qNorm(qMul(player.rotation,qAxis([0,0,1],-roll*dt*2.2)));
    const wantsBoost=keys.has('ShiftLeft')||keys.has('ShiftRight')||gp?.boost,hasWrit=game.modules.has('writ');player.boosting=!!wantsBoost&&player.energy>1&&inputLen>.05;
    const baseSpeed=config.assist==='precision'?17:config.assist==='drift'?29:24,boostSpeed=hasWrit?49:41,speed=player.boosting?boostSpeed:baseSpeed;
    if(player.boosting)player.energy=Math.max(0,player.energy-dt*(hasWrit?4.4:6.7));
    if(config.assist==='drift'){
      const acceleration=player.boosting?42:28;player.velocity=add(player.velocity,scale(input,acceleration*dt));player.velocity=scale(player.velocity,Math.exp(-dt*(keys.has('KeyB')?4.6:.62)));const max=speed;if(len(player.velocity)>max)player.velocity=scale(norm(player.velocity),max);
    }else{
      const target=scale(input,speed),response=1-Math.exp(-dt*(config.assist==='precision'?7.2:4.8));player.velocity=add(scale(player.velocity,1-response),scale(target,response));if(keys.has('KeyB'))player.velocity=scale(player.velocity,Math.exp(-dt*6.5));
    }
    player.previous=player.position.slice();player.position=relocate(player.position,add(player.position,scale(player.velocity,dt)),1.3);
    if(buttons.fire||keys.has('KeyJ')||gp?.fire)launchLaser();
    if(keys.has('KeyF')||edge('missile',gp?.missile)){launchMissile();keys.delete('KeyF');}
    if(keys.has('KeyZ')||edge('scan',gp?.scan)){useScan();keys.delete('KeyZ');}
    if(keys.has('KeyC')||edge('emp',gp?.emp)){useEMP();keys.delete('KeyC');}
    if(keys.has('KeyX')){useAmend();keys.delete('KeyX');}
    player.energy=clamp(player.energy+dt*2.7,0,100);player.hitCooldown=Math.max(0,player.hitCooldown-dt);player.shieldTime=Math.max(0,player.shieldTime-dt);player.scanCooldown=Math.max(0,player.scanCooldown-dt);player.empCooldown=Math.max(0,player.empCooldown-dt);player.recoil=Math.max(0,player.recoil-dt*4.5);
    const rid=roomAt(player.position);if(rid>=0){const room=facility.rooms[rid];room.visited=true;if(rid!==game.lastRoom){game.lastRoom=rid;if(rid!==staticCenterRoom)buildArchitecture(rid);if(game.routeHistory[game.routeHistory.length-1]!==rid){game.routeHistory.push(rid);game.routeHistory.length=Math.min(40,game.routeHistory.length);}showToast(`CIRCLE ${pad(room.stratum+1)} // ${room.title}`,1.8);if((rid+game.sector)%3===0)addDispatch(WHISPERS[(rid+game.sector)%WHISPERS.length]);const moments={1:['CALENDAR CONTROL','THE CONTINUANCE LOOP','BREAK THE CLOCK OR FLY THE LONG WAY AROUND.'],4:['SUBMISSION RECEIVED','THE E-FILING FURNACE','THE SYSTEM KEPT THE FEE AND RETURNED THE DOOR.'],5:['ALL RISE','THE INFERNAL BENCH','THE HONORABLE MACHINERY IS NOW FULLY MOLTEN.'],6:['VENUE UNKNOWN','THE NULL TRIBUNAL','THE FINAL APPEAL HAS NO RECORD OF YOUR EXISTENCE.']};const moment=moments[room.stratum];if(moment&&!game.setpieces[stratumDef(room.stratum).id]){game.setpieces[stratumDef(room.stratum).id]=true;showCinematic(...moment,3.6,'depthReveal',false);}saveCheckpoint(true);}}
    if(!facility.boss.active){game.countdown-=dt;if(!game.lastPageTriggered&&game.countdown<Math.min(62,facility.extractionTime*.46)){game.lastPageTriggered=true;spawnExtractionPursuit();showCinematic('THE LAST PAGE','DO NOT LET IT BURN.','EVERY MACHINE BELOW HAS BEEN ORDERED TO ERASE THE RETURN ROUTE.',4,'lastPage',false);sfx('boss');}if(game.countdown<=0){finish(false,'THE VAULT COLLAPSED // RECORD LOST');return;}if(dist(player.position,facility.exit)<4.7){game.score+=Math.floor(game.countdown)*20+Math.floor(game.integrity)*8;finish(true,'RECORD EXTRACTED. JUSTICE STILL PENDING.');return;}}
  }

  function update(dt){
    if(!game||game.phase!=='playing'||game.mapOpen)return;
    const blocked=!!game.cinematic?.block;game.time+=dt;if(!blocked)game.elapsed+=dt;hitFlash=Math.max(0,hitFlash-dt*2.6);game.redaction=Math.max(0,game.redaction-dt);game.radarScramble=Math.max(0,game.radarScramble-dt);game.scanPulse=Math.max(0,game.scanPulse-dt*1.8);game.abilityFlash=Math.max(0,game.abilityFlash-dt);updateCinematic(dt);
    if(blocked){updateSparks(dt);updateMusic();return;}
    updatePlayer(dt);if(game.phase!=='playing')return;updateEnemies(dt);updateBoss(dt);updateHazards(dt);updateShots(dt);updatePickups();updateSparks(dt);updateDirector(dt);activateBossIfReady();updateMusic();saveCheckpoint(false);
    if(Math.floor(game.time*8)%2===0&&visualRng()<.0015)burst(facility.boss.position,colors.red,2,4);
  }

  function nearVisible(p,extra=0){const base=config.quality==='low'?115:config.quality==='medium'?165:230;return dist(p,player.position)<base+extra;}
  function worldDynamic(){
    const m=new Mesh(),t=game.time;
    for(const e of enemies){if(!e.alive||!nearVisible(e.position))continue;const def=ENEMY_DEFS[e.type],p=e.position;
      if(e.type==='mimic'&&!e.revealed){m.box(p[0]-1.2,p[1]-1.6,p[2]-.15,p[0]+1.2,p[1]+1.6,p[2]+.15,colors.paper);m.ring(p,'y',2,tint(colors.paper,.45),.08,t,12);continue;}
      const r=e.type==='bailiff'?2.35:e.type==='wraith'?1.45:e.type==='redactor'?1.3:1.65,co=def.color;m.octa(p,r,co,t*(e.type==='wraith'?2.2:.9)+e.phase);m.ring(p,'y',r*1.38,tint(co,.64),.075,t+e.phase,10);
      if(e.type==='clerk'){m.box(p[0]-r*1.65,p[1]-.23,p[2]-.35,p[0]-r*.72,p[1]+.23,p[2]+.35,tint(co,.8));m.box(p[0]+r*.72,p[1]-.23,p[2]-.35,p[0]+r*1.65,p[1]+.23,p[2]+.35,tint(co,.8));}
      if(e.type==='redactor'){m.rod(add(p,[-2,-1,-.7]),add(p,[2,1,.7]),colors.red,.22);m.rod(add(p,[2,-1,-.7]),add(p,[-2,1,.7]),colors.red,.22);}
      if(e.type==='bailiff'){m.box(p[0]-r*.8,p[1]-.45,p[2]-r-.2,p[0]+r*.8,p[1]+.45,p[2]-r+.1,tint(colors.wall,2.3));m.rod(add(p,[r,0,0]),add(p,[r+2,-2,0]),colors.paper,.26);}
      if(e.type==='continuance'){for(let i=0;i<3;i++)m.ring(p,'z',r*(1+i*.32),tint(co,.75-i*.14),.08,t*(.6+i*.2)+i,12);}
      if(e.type==='feeCollector'){m.box(p[0]-1.8,p[1]-1,p[2]-.5,p[0]+1.8,p[1]+1,p[2]+.5,tint(co,.8));for(let i=-1;i<=1;i++)m.ring([p[0]+i*1.4,p[1],p[2]],'z',.55,colors.paper,.10,t+i,10);}
      if(e.type==='wraith'){m.rod(add(p,[-1.8,-2,0]),add(p,[0,2.4,0]),tint(co,.7),.13);m.rod(add(p,[1.8,-2,0]),add(p,[0,2.4,0]),tint(co,.7),.13);}
      m.box(p[0]-.36,p[1]-.22,p[2]-r-.18,p[0]+.36,p[1]+.22,p[2]-r+.18,colors.red);
    }
    for(const relay of facility.relays){if(!relay.active||!nearVisible(relay.position,30))continue;const p=relay.position,col=colors.amber;m.octa(p,2.35,col,t*.65);m.ring(p,'x',3.2,tint(col,.8),.14,t*.7,12);m.ring(p,'z',3.4,tint(col,.7),.11,-t*.48,12);m.rod(add(p,[-1.4,-1.5,-1.5]),add(p,[1.4,1.5,1.5]),colors.red,.16);m.rod(add(p,[1.4,-1.5,-1.5]),add(p,[-1.4,1.5,1.5]),colors.red,.16);}
    for(const record of facility.records){if(record.recovered||!nearVisible(record.position,35))continue;const p=add(record.position,[0,Math.sin(t*1.7+record.id)*.33,0]);m.box(p[0]-1.25,p[1]-1.7,p[2]-.16,p[0]+1.25,p[1]+1.7,p[2]+.16,colors.paper);m.box(p[0]-.82,p[1]+.79,p[2]-.21,p[0]+.92,p[1]+1.03,p[2]+.22,colors.dark);for(let line=0;line<4;line++)m.box(p[0]-.8,p[1]+.38-line*.43,p[2]-.22,p[0]+(.3+line%2*.5),p[1]+.47-line*.43,p[2]+.22,tint(colors.rail,1.3));m.ring(p,'y',2.8,colors.cyan,.13,-t*.55,16);m.ring(p,'x',2.4,tint(colors.paper,.72),.1,t*.4,14);}
    for(const h of facility.hazards){if(h.disabled||!nearVisible(h.position,30))continue;const p=h.position,accent=stratumDef(facility.rooms[h.room].stratum).palette.accent,phase=t+h.phase;
      if(h.type==='redTape'){const active=Math.sin(phase*2.1)>.12;for(let i=-2;i<=2;i++){const off=i*2.3;if(h.id%2===0)m.rod([p[0],p[1]-7,p[2]+off],[p[0],p[1]+7,p[2]+off],active?colors.red:tint(colors.red,.18),.09);else m.rod([p[0]+off,p[1]-7,p[2]],[p[0]+off,p[1]+7,p[2]],active?colors.red:tint(colors.red,.18),.09);}}
      else if(h.type==='continuanceLoop'){m.ring(p,'z',5.5,tint(accent,.7),.26,phase*.45,22);m.ring(p,'z',3.5,tint(accent,.45),.15,-phase*.7,18);m.rod(p,add(p,[Math.sin(phase)*3.5,Math.cos(phase)*3.5,0]),accent,.17);}
      else if(h.type==='shredder'){for(let i=0;i<6;i++){const a=i*TAU/6+phase;m.rod(p,add(p,[Math.sin(a)*5,Math.cos(a)*5,0]),i%2?colors.red:accent,.27);}m.ring(p,'z',5.6,tint(accent,.5),.18,-phase*.6,18);}
      else if(h.type==='filingFee'){m.box(p[0]-6,p[1]-6,p[2]-.5,p[0]+6,p[1]+6,p[2]+.5,tint(accent,h.paid?.12:.55));for(let i=-2;i<=2;i++)m.ring([p[0]+i*2,p[1],p[2]],'z',.75,h.paid?tint(accent,.2):colors.paper,.12,phase+i,10);}
      else if(h.type==='stampPress'){const y=p[1]+(Math.sin(phase*1.65)>.58?-5:5);m.box(p[0]-5,y-1,p[2]-5,p[0]+5,y+1,p[2]+5,accent);m.rod([p[0],p[1]+11,p[2]],[p[0],y+1,p[2]],tint(accent,.6),.65);}
      else if(h.type==='rejectionChute'){m.ring(p,'y',4.4,colors.red,.3,phase*.6,18);m.ring(add(p,[0,-2,0]),'y',2.6,tint(colors.red,.6),.17,-phase,14);for(let i=0;i<6;i++){const a=i*TAU/6;m.rod(add(p,[Math.sin(a)*4,3,Math.cos(a)*4]),add(p,[Math.sin(a)*2,-5,Math.cos(a)*2]),tint(colors.red,.6),.12);}}
      else {m.ring(p,'x',5.2,tint(accent,.7),.22,phase*.4,19);m.ring(p,'z',5.2,tint(accent,.55),.18,-phase*.6,19);for(let i=0;i<5;i++)m.octa(add(p,[Math.sin(phase+i)*4,Math.sin(phase*1.7+i)*3,Math.cos(phase+i)*4]),.45,accent,phase);}
    }
    for(const node of incidentNodes){if(!node.active||!nearVisible(node.position,30))continue;const p=node.position,c=node.type==='bossClause'?colors.red:colors.green;m.octa(p,2.1,c,t*.9+node.phase);m.ring(p,'x',3,tint(c,.7),.15,t,13);m.ring(p,'z',3.3,tint(c,.45),.11,-t*.7,13);for(let i=0;i<3;i++)m.box(p[0]-2.2,p[1]-1+i*.8,p[2]-.2,p[0]+2.2,p[1]-.55+i*.8,p[2]+.2,tint(colors.paper,.5));}
    const b=facility.boss;if(b.active&&dist(b.position,player.position)<110){const p=b.position,open=b.unlocked,c=open?(b.type==='nullTribunal'?colors.magenta:colors.red):[.30,.34,.50],r=game.bossEnrage?5.2:4.5;
      if(b.type==='rejection'){m.box(p[0]-5,p[1]-2,p[2]-3,p[0]+5,p[1]+2,p[2]+3,tint(c,.82));m.rod(add(p,[0,2,0]),add(p,[0,10,0]),tint(c,.58),1);m.box(p[0]-7,p[1]+8,p[2]-5,p[0]+7,p[1]+11,p[2]+5,c);m.ring(p,'y',8.5,tint(c,.46),.22,t*.8,24);}
      else if(b.type==='grandSeal'){for(let i=0;i<4;i++)m.ring(p,i%2?'x':'z',4.5+i*1.55,tint(c,1-i*.13),.28,(i%2?-1:1)*t*(.18+i*.08),24);for(let i=0;i<8;i++){const a=i*TAU/8+t*.2;m.rod(p,add(p,[Math.sin(a)*9,Math.sin(a*2)*2,Math.cos(a)*9]),tint(c,.55),.18);}}
      else if(b.type==='gatekeeper'){m.box(p[0]-8,p[1]-9,p[2]-1,p[0]-5,p[1]+9,p[2]+1,c);m.box(p[0]+5,p[1]-9,p[2]-1,p[0]+8,p[1]+9,p[2]+1,c);m.box(p[0]-8,p[1]+6,p[2]-1,p[0]+8,p[1]+9,p[2]+1,tint(c,.8));m.ring(p,'z',6.3,tint(colors.violet,.72),.35,-t*.25,24);m.octa(p,3.4,tint(c,.88),t*.28);}
      else if(b.type==='nullTribunal'){for(let i=0;i<7;i++){const a=i*TAU/7+t*(i%2?.18:-.14),q=add(p,[Math.sin(a)*(5+i*.5),Math.sin(a*2.1)*3,Math.cos(a)*(5+i*.5)]);m.octa(q,1.2+i*.12,tint(c,.6+i*.05),-a);}m.ring(p,'x',10,tint(c,.42),.16,t*.13,28);m.ring(p,'y',8,tint(c,.55),.13,-t*.21,24);}
      else {m.octa(p,r,c,t*.18);for(let i=0;i<8;i++){const a=i*TAU/8-t*.45;m.rod(p,add(p,[Math.sin(a)*8,Math.sin(a*3)*4,Math.cos(a)*8]),i%2?colors.red:colors.orange,.34);}m.ring(p,'z',8.8,tint(c,.65),.24,-t*.31,24);}
      for(const w of b.weakpoints||[])if(w.active){m.octa(w.position,1.15,colors.magenta,t*1.7+w.phase);m.ring(w.position,'y',1.8,tint(colors.magenta,.6),.09,-t,12);}}
    const ex=facility.exit;if(!b.active&&dist(ex,player.position)<100){m.ring(ex,'z',3.6,colors.cyan,.26,t*.1,20);m.ring(ex,'z',4.15,tint(colors.cyan,.6),.10,-t*.24,20);m.rod(add(ex,[-3.3,-4.6,0]),add(ex,[-3.3,4.6,0]),tint(colors.rail,.8),.27);m.rod(add(ex,[3.3,-4.6,0]),add(ex,[3.3,4.6,0]),tint(colors.rail,.8),.27);}
    for(const item of pickups){if(!item.alive||!nearVisible(item.position,30))continue;const p=add(item.position,[0,Math.sin(t*2+item.phase)*.35,0]),c=item.type==='hull'?colors.shield:item.type==='missiles'?colors.amber:item.type==='supplement'||item.type==='evidenceCache'?colors.paper:colors.pickup;m.octa(p,item.type==='upgrade'?1.7:1.35,c,t*1.3);m.ring(p,'y',item.type==='upgrade'?2.3:1.85,tint(c,.5),.09,t,10);}
    for(const shot of shots){if(!nearVisible(shot.position,15))continue;const c=shot.from==='player'?(shot.kind==='missile'?colors.amber:colors.cyan):shot.kind==='boss'?colors.magenta:colors.red,heading=norm(shot.velocity),back=add(shot.position,scale(heading,-(shot.kind==='missile'?3.2:2)));m.rod(shot.position,back,c,shot.kind==='missile'?.42:.23);if(shot.kind==='missile')m.octa(shot.position,.62,c,t*5);}
    for(const s of sparks){if(!nearVisible(s.p,15))continue;const end=add(s.p,scale(s.velocity,-.028));m.rod(s.p,end,tint(s.color,clamp(s.life/s.maxLife,.2,1)),.075);}
    const cr=currentRoom(),def=stratumDef(cr.stratum),particleCount=config.quality==='low'?8:config.quality==='medium'?16:28;if(cr.stratum>=4||def.id==='null'){for(let i=0;i<particleCount;i++){const a=i*2.39996+Math.floor(t*2.5)*.71,x=cr.position[0]+Math.sin(a)*13,z=cr.position[2]+Math.cos(a)*13,y=cr.position[1]-10+((t*(cr.stratum>=5?2.4:1.4)+i*1.7)%19);m.octa([x,y,z],.12+(i%4)*.06,cr.stratum===6?(i%2?colors.magenta:colors.violet):(i%3?colors.amber:colors.red),t);}}
    if(game.scanPulse>0){m.ring(player.position,'y',2+(1-game.scanPulse)*25,tint(colors.cyan,game.scanPulse),.15,t,24);}
    appendJetta(m);return m;
  }

  function resize(){const q=config.quality==='low'?1.05:config.quality==='medium'?1.45:1.9,dpr=Math.min(window.devicePixelRatio||1,q),w=Math.max(1,Math.floor(innerWidth*dpr)),h=Math.max(1,Math.floor(innerHeight*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;fxCanvas.width=w;fxCanvas.height=h;fxCanvas.style.width='100%';fxCanvas.style.height='100%';}viewportW=w;viewportH=h;gl.viewport(0,0,w,h);}
  function safeCameraEye(origin,wanted){let best=origin.slice();for(let i=1;i<=18;i++){const p=add(origin,scale(sub(wanted,origin),i/18));if(pointInside(p,.35))best=p;else break;}return best;}
  function render(alpha=1){
    if(!game||!player)return;resize();gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(program);
    const interp=player.previous?mix3(player.previous,player.position,clamp(alpha,0,1)):player.position,spin=player.rotation;let eye=interp,view;
    if(game.cinematic?.kind==='launch'){const a=-1.2+game.cinematic.elapsed*.62;eye=safeCameraEye(interp,add(interp,[Math.sin(a)*14,4.3,Math.cos(a)*14]));view=lookView(eye,add(interp,[0,-.1,0]));}
    else if(game.cinematic?.kind==='falseVictory'){const a=game.cinematic.elapsed*.9;eye=safeCameraEye(interp,add(interp,[Math.sin(a)*10,2.2,Math.cos(a)*10]));view=lookView(eye,facility.boss.position);}
    else{if(config.camera==='chase')eye=safeCameraEye(interp,add(interp,rotate([0,3.05,11.8],spin)));else if(config.camera==='hood')eye=add(interp,rotate([0,.18,-2.15],spin));else eye=add(interp,rotate([0,.55,-.45],spin));view=viewMat(eye,spin);}
    const def=stratumDef(currentRoom().stratum),far=config.quality==='low'?330:520,mvp=mulMat(projMat(79*Math.PI/180,viewportW/viewportH,.12,far),view);
    gl.uniformMatrix4fv(uMvp,false,new Float32Array(mvp));gl.uniform3fv(uEye,new Float32Array(eye));gl.uniform1f(uTime,game.time);gl.uniform3fv(uFogColor,new Float32Array(def.palette.fog));gl.uniform1f(uFogNear,config.quality==='low'?18:25);gl.uniform1f(uFogFar,config.quality==='low'?125:185);
    draw(staticBuffer,staticCount);const dynamicMesh=worldDynamic(),n=upload(dynamicBuffer,dynamicMesh,gl.DYNAMIC_DRAW);draw(dynamicBuffer,n);drawReticleEffects();
  }
  function objectivePosition(){
    const incident=incidentNodes.filter(n=>n.active).sort((a,b)=>dist(a.position,player.position)-dist(b.position,player.position))[0];if(incident)return incident.position;
    const options=[...facility.records.filter(r=>!r.recovered).map(r=>r.position),...facility.relays.filter(r=>r.active).map(r=>r.position)];if(options.length){options.sort((a,b)=>dist(a,player.position)-dist(b,player.position));return options[0];}
    const weak=(facility.boss.weakpoints||[]).filter(w=>w.active).sort((a,b)=>dist(a.position,player.position)-dist(b.position,player.position))[0];if(weak)return weak.position;return facility.boss.active?facility.boss.position:facility.exit;
  }
  function drawReticleEffects(){
    const ctx=fxCanvas.getContext('2d');if(!ctx)return;const w=viewportW,h=viewportH;ctx.clearRect(0,0,w,h);if(game.phase!=='playing'||game.mapOpen||game.cinematic?.block)return;
    const f=rotate([0,0,-1],player.rotation),r=rotate([1,0,0],player.rotation),up=rotate([0,1,0],player.rotation),towards=sub(objectivePosition(),player.position),forward=dot(towards,f),right=dot(towards,r),upper=dot(towards,up);
    if(forward>1){const pX=w*.5+(right/forward)*h*.62,pY=h*.5-(upper/forward)*h*.62,x=clamp(pX,28,w-28),y=clamp(pY,28,h-28);ctx.save();ctx.translate(x,y);ctx.rotate(Math.PI*.25);ctx.lineWidth=Math.max(1,viewportW/1500);ctx.strokeStyle='rgba(255,151,90,.82)';ctx.strokeRect(-8,-8,16,16);ctx.restore();ctx.fillStyle='rgba(255,171,123,.78)';ctx.font=`${Math.max(11,Math.floor(w/125))}px monospace`;ctx.textAlign='center';ctx.fillText(`${Math.floor(len(towards))}m`,x,y+29);}
    const target=targetInFront();if(target){ctx.strokeStyle='rgba(255,220,126,.92)';ctx.lineWidth=2;ctx.beginPath();ctx.arc(w/2,h/2,24+Math.sin(game.time*6)*3,0,TAU);ctx.stroke();ctx.fillStyle='rgba(255,220,126,.9)';ctx.font=`${Math.max(10,Math.floor(w/145))}px monospace`;ctx.fillText('LOCK',w/2,h/2+43);}
    if(hitFlash>0&&!config.reducedFlash){ctx.fillStyle=`rgba(255,63,65,${hitFlash*.24})`;ctx.fillRect(0,0,w,h);}
    if(game.redaction>0){const alpha=clamp(game.redaction/3.5,0,.68);ctx.fillStyle=`rgba(2,2,4,${alpha*.58})`;for(let i=0;i<6;i++){const yy=h*(.13+i*.14)+Math.sin(game.time*2+i)*18;ctx.fillRect(0,yy,w,Math.max(14,h*.05));}ctx.fillStyle=`rgba(255,255,255,${alpha*.65})`;ctx.font=`bold ${Math.max(14,Math.floor(w/75))}px monospace`;ctx.fillText('REDACTED PENDING REVIEW',w/2,h*.13);}
    const speed=len(player.velocity);if(speed>17&&!config.reducedMotion){ctx.strokeStyle=`rgba(94,249,223,${clamp((speed-16)/65,.02,.16)})`;ctx.lineWidth=1;for(let i=0;i<16;i++){const a=i*TAU/16,radius=Math.min(w,h)*(.29+Math.sin(i*2.34+game.time)*.017);ctx.beginPath();ctx.moveTo(w*.5+Math.cos(a)*radius,h*.5+Math.sin(a)*radius);ctx.lineTo(w*.5+Math.cos(a)*radius*1.22,h*.5+Math.sin(a)*radius*1.22);ctx.stroke();}}
    // Velocity vector shows drift separately from nose direction.
    const vel=player.velocity;if(len(vel)>1){const vf=dot(vel,f),vr=dot(vel,r),vu=dot(vel,up);if(vf>1){const x=clamp(w*.5+(vr/vf)*h*.35,18,w-18),y=clamp(h*.5-(vu/vf)*h*.35,18,h-18);ctx.strokeStyle='rgba(110,255,224,.72)';ctx.beginPath();ctx.arc(x,y,7,0,TAU);ctx.stroke();ctx.beginPath();ctx.moveTo(x-10,y);ctx.lineTo(x+10,y);ctx.moveTo(x,y-10);ctx.lineTo(x,y+10);ctx.stroke();}}
  }

  function floorBounds(floor){const rooms=facility.rooms.filter(r=>r.stratum===floor&&!r.secret);const xs=rooms.map(r=>r.cell[0]),zs=rooms.map(r=>r.cell[2]);return {minX:Math.min(...xs),maxX:Math.max(...xs),minZ:Math.min(...zs),maxZ:Math.max(...zs)};}
  function drawRadar(){
    if(!facility||!player)return;const radar=$('radar'),ctx=radar.getContext('2d'),w=radar.width,h=radar.height;ctx.clearRect(0,0,w,h);ctx.fillStyle='#04121f';ctx.fillRect(0,0,w,h);
    ctx.strokeStyle='rgba(80,218,218,.10)';for(let x=0;x<w;x+=31){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}for(let y=0;y<h;y+=31){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
    if(game.radarScramble>0){for(let i=0;i<25;i++){ctx.strokeStyle=`rgba(${100+Math.floor(visualRng()*155)},${40+Math.floor(visualRng()*100)},${180+Math.floor(visualRng()*75)},.38)`;ctx.beginPath();ctx.moveTo(visualRng()*w,visualRng()*h);ctx.lineTo(visualRng()*w,visualRng()*h);ctx.stroke();}ctx.fillStyle='#ff8eff';ctx.font='bold 15px monospace';ctx.fillText('SERVICE CONTACT UNAVAILABLE',20,h/2);return;}
    const room=currentRoom(),floor=room.stratum,bounds=floorBounds(floor),rangeX=Math.max(1,bounds.maxX-bounds.minX),rangeZ=Math.max(1,bounds.maxZ-bounds.minZ),padPx=38,mapP=(r)=>[padPx+(r.cell[0]-bounds.minX)/rangeX*(w-padPx*2),padPx+(r.cell[2]-bounds.minZ)/rangeZ*(h-padPx*2)];
    for(const c of facility.connectors){const a=facility.rooms[c.a],b=facility.rooms[c.b];if(a.stratum!==floor||b.stratum!==floor||a.secret||b.secret)continue;const A=mapP(a),B=mapP(b);ctx.beginPath();ctx.moveTo(...A);ctx.lineTo(...B);ctx.lineWidth=7;ctx.strokeStyle=a.visited||b.visited?'rgba(64,219,198,.28)':'rgba(38,89,104,.18)';ctx.stroke();}
    for(const r of facility.rooms){if(r.stratum!==floor||r.secret)continue;const [x,y]=mapP(r),visited=r.visited;ctx.fillStyle=visited?'rgba(64,219,198,.35)':'rgba(34,68,84,.35)';ctx.fillRect(x-18,y-14,36,28);ctx.strokeStyle=visited?'rgba(96,242,213,.72)':'rgba(80,119,130,.28)';ctx.strokeRect(x-18,y-14,36,28);if(r.links.some(n=>facility.rooms[n].stratum!==floor)){ctx.strokeStyle='#a68bff';ctx.strokeRect(x-12,y-9,24,18);}if(r.id===facility.bossRoom&&facility.boss.active){ctx.fillStyle='#ff5e72';ctx.fillRect(x-5,y-5,10,10);}for(const relay of facility.relays)if(relay.room===r.id&&relay.active){ctx.fillStyle='#ff985a';ctx.fillRect(x-5,y-5,10,10);}for(const rec of facility.records)if(rec.room===r.id&&!rec.recovered){ctx.fillStyle='#f8e4a1';ctx.fillRect(x-6,y-12,12,4);}}
    const [px,py]=mapP(room),dx=(player.position[0]-room.position[0])/spacing[0]*(w-padPx*2)/rangeX,dz=(player.position[2]-room.position[2])/spacing[2]*(h-padPx*2)/rangeZ,fwd=rotate([0,0,-1],player.rotation);ctx.save();ctx.translate(px+dx,py+dz);ctx.rotate(Math.atan2(fwd[0],-fwd[2]));ctx.fillStyle='#fff';ctx.shadowBlur=13;ctx.shadowColor='#fff';ctx.beginPath();ctx.moveTo(0,-12);ctx.lineTo(-7,8);ctx.lineTo(0,4);ctx.lineTo(7,8);ctx.closePath();ctx.fill();ctx.restore();$('radarFloor').textContent=`CIRCLE ${pad(floor+1)} / ${pad(facility.strataCount)}`;
  }

  function drawBigMap(){
    const can=$('bigMap');if(!can||!facility)return;const rect=can.getBoundingClientRect();if(!rect.width||!rect.height)return;const dpr=Math.min(devicePixelRatio||1,2);can.width=Math.floor(rect.width*dpr);can.height=Math.floor(rect.height*dpr);const c=can.getContext('2d');c.scale(dpr,dpr);const W=rect.width,H=rect.height,cols=Math.min(4,facility.strataCount),rows=Math.ceil(facility.strataCount/cols),panelW=W/cols,panelH=H/rows;c.fillStyle='#051421';c.fillRect(0,0,W,H);
    for(let floor=0;floor<facility.strataCount;floor++){const col=floor%cols,row=Math.floor(floor/cols),x0=col*panelW,y0=row*panelH,bounds=floorBounds(floor),rangeX=Math.max(1,bounds.maxX-bounds.minX),rangeZ=Math.max(1,bounds.maxZ-bounds.minZ),margin=30,mapP=(r)=>[x0+margin+(r.cell[0]-bounds.minX)/rangeX*(panelW-margin*2),y0+45+(r.cell[2]-bounds.minZ)/rangeZ*(panelH-75)];c.strokeStyle='rgba(90,226,224,.12)';c.strokeRect(x0+8,y0+8,panelW-16,panelH-16);const accentRgb=stratumDef(floor).palette.accent.map(x=>Math.floor(x*255));c.fillStyle=`rgb(${accentRgb.join(',')})`;c.font='bold 11px monospace';c.fillText(`${pad(floor+1)} // ${stratumDef(floor).name}`,x0+14,y0+28);
      for(const link of facility.connectors){const a=facility.rooms[link.a],b=facility.rooms[link.b];if(a.stratum!==floor||b.stratum!==floor||a.secret||b.secret)continue;const A=mapP(a),B=mapP(b);c.beginPath();c.moveTo(...A);c.lineTo(...B);c.lineWidth=8;c.strokeStyle=a.visited&&b.visited?'rgba(77,220,209,.45)':'rgba(61,113,130,.22)';c.stroke();}
      for(const r of facility.rooms){if(r.stratum!==floor||r.secret)continue;const [x,y]=mapP(r),s=Math.min(22,panelW*.09);c.fillStyle=r.visited?'rgba(16,113,113,.60)':'rgba(15,44,60,.65)';c.fillRect(x-s/2,y-s/2,s,s);c.strokeStyle=r.visited?'#4ddfd1':'#31556a';c.strokeRect(x-s/2,y-s/2,s,s);if(r.links.some(n=>facility.rooms[n].stratum!==floor)){c.strokeStyle='#ae91ff';c.strokeRect(x-s*.32,y-s*.32,s*.64,s*.64);}if(r.id===facility.bossRoom&&facility.boss.active){c.fillStyle='#f76772';c.fillRect(x-5,y-14,10,5);}for(const relay of facility.relays)if(relay.room===r.id&&relay.active){c.fillStyle='#ff9b59';c.fillRect(x-5,y+9,10,5);}for(const rec of facility.records)if(rec.room===r.id&&!rec.recovered){c.fillStyle='#f4e4af';c.fillRect(x-6,y+16,12,5);}if(r.id===0){c.fillStyle='#70ffe0';c.fillRect(x-5,y-20,10,5);}}
      if(currentRoom().stratum===floor){const r=currentRoom(),[x,y]=mapP(r),dx=(player.position[0]-r.position[0])/spacing[0]*(panelW-margin*2)/rangeX,dz=(player.position[2]-r.position[2])/spacing[2]*(panelH-75)/rangeZ;c.beginPath();c.arc(x+dx,y+dz,5,0,TAU);c.fillStyle='#fff';c.shadowBlur=15;c.shadowColor='#fff';c.fill();c.shadowBlur=0;}
    }
  }

  function updateHUD(){
    if(!game||!player)return;const room=currentRoom(),def=stratumDef(room.stratum);$('sectorLabel').textContent=`SECTOR ${pad(game.sector)} · ${DG.MODES[game.mode].name} · CIRCLE ${pad(room.stratum+1)} / ${pad(facility.strataCount)} · ${def.name}`;$('stratumLabel').textContent=`DEPTH ${pad(room.stratum+1)} / ${pad(facility.strataCount)} · ${def.name}`;
    $('scoreValue').textContent=String(Math.floor(game.score)).padStart(7,'0');$('shieldValue').textContent=Math.ceil(player.hull);$('energyValue').textContent=Math.ceil(player.energy);$('missileValue').textContent=pad(player.missiles);$('integrityValue').textContent=Math.ceil(game.integrity);$('evidenceValue').textContent=`${game.recordsRecovered}/${facility.records.length}`;
    $('shieldMeter').style.width=player.hull+'%';$('energyMeter').style.width=player.energy+'%';$('missileMeter').style.width=(100*player.missiles/14)+'%';$('integrityMeter').style.width=game.integrity+'%';$('evidenceMeter').style.width=(100*game.recordsRecovered/facility.records.length)+'%';
    const bossBar=$('bossBar');if(facility.boss.unlocked&&facility.boss.active){bossBar.classList.add('open');$('bossName').textContent=facility.boss.name+(facility.boss.weakpoints.some(w=>w.active)?' // CLAUSES ACTIVE':' // CORE EXPOSED');$('bossMeter').style.width=(100*facility.boss.hp/facility.boss.maxHp)+'%';}else bossBar.classList.remove('open');
    const ability=[];ability.push(`SCAN ${player.scanCooldown>0?player.scanCooldown.toFixed(1):'READY'}`);if(game.modules.has('compel'))ability.push(`EMP ${player.empCooldown>0?player.empCooldown.toFixed(1):'READY'}`);ability.push(`SPEED ${Math.round(len(player.velocity))}`);$('abilityStatus').textContent=ability.join(' · ');
    if(!facility.boss.active){$('missionTitle').textContent='EXTRACT THE RECORD';$('missionDetail').textContent=`RETURN TO THE PUBLIC GATES · INTEGRITY ${Math.ceil(game.integrity)}%`;$('timer').style.display='block';const seconds=Math.ceil(game.countdown);$('timer').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+pad(seconds%60);}
    else if(!canOpenArchive()){$('missionTitle').textContent='UNCOVER THE BURIED RECORD';$('missionDetail').textContent=`EXHIBITS ${game.recordsRecovered}/${facility.records.length} · SEALS ${game.relaysDown}/${facility.relays.length} · Z SCAN`;$('timer').style.display='none';}
    else{$('missionTitle').textContent=`BREAK ${facility.boss.name}`;$('missionDetail').textContent=facility.boss.weakpoints.some(w=>w.active)?'DESTROY THE ORBITING CLAUSES':'STRIKE THE EXPOSED CORE';$('timer').style.display='none';}
    if(shownToastUntil&&performance.now()>shownToastUntil){$('toast').style.opacity='0';shownToastUntil=0;}drawRadar();
  }

  function updateRunHistoryPanel(){const el=$('historyList');if(!el)return;const history=runHistory();el.replaceChildren(...history.slice(0,5).map(run=>{const li=document.createElement('li');li.textContent=`${run.won?'EXTRACTED':'BURIED'} · ${String(run.score).padStart(7,'0')} · ${run.mode.toUpperCase()} · ${run.seed}`;return li;}));if(!history.length){const li=document.createElement('li');li.textContent='NO PRIOR RUNS IN THIS BROWSER';el.append(li);}}
  function showScreen(mode){const overlay=$('screen'),menu=overlay.querySelector('.menu-content'),outcome=overlay.querySelector('.outcome');overlay.classList.remove('hidden');document.body.classList.remove('playing');if(mode==='outcome'){menu.style.display='none';outcome.style.display='block';}else{menu.style.display='block';outcome.style.display='none';}$('start').textContent=mode==='pause'?'RESUME DESCENT ▸':'START THE CARPOOL TO HELL ▸';}
  function hideScreen(){$('screen').classList.add('hidden');document.body.classList.add('playing');}
  function togglePause(){if(!game)return;if(game.phase==='playing'){game.phase='paused';showScreen('pause');if(document.pointerLockElement===canvas)document.exitPointerLock();}else if(game.phase==='paused')startGame(false,true);}
  function toggleLedger(force){if(!game)return;const open=force!==undefined?force:!game.ledgerOpen;game.ledgerOpen=open;const panel=$('ledgerOverlay');panel.classList.toggle('open',open);panel.setAttribute('aria-hidden',String(!open));if(open){const list=$('ledgerEntries');list.replaceChildren(...(game.ledger.length?game.ledger.map((entry,i)=>{const li=document.createElement('li');li.innerHTML=`<strong>${pad(i+1)} · ${entry.class}</strong><span>${entry.title}</span><em>${entry.choice.toUpperCase()}</em>`;return li;}):[Object.assign(document.createElement('li'),{textContent:'NO EVIDENCE HAS YET SURVIVED THE DESCENT.'})]));$('ledgerSummary').textContent=`EXPOSED ${game.ledger.filter(x=>x.choice==='expose').length} · PROTECTED ${game.ledger.filter(x=>x.choice==='protect').length} · ARCHIVED ${game.ledger.filter(x=>x.choice==='archive').length}`;game.phase='ledger';if(document.pointerLockElement===canvas)document.exitPointerLock();}else{if(game.phase==='ledger')game.phase='playing';canvas.requestPointerLock?.();}}

  function readMenuConfig(){
    const activeMode=document.querySelector('.mode-card.active');if(activeMode)config.mode=activeMode.dataset.mode;
    config.assist=$('assistSelect')?.value||config.assist;config.sensitivity=Number($('sensitivity')?.value||config.sensitivity);config.invertY=!!$('invertY')?.checked;config.quality=$('qualitySelect')?.value||config.quality;config.reducedMotion=!!$('reducedMotion')?.checked;config.reducedFlash=!!$('reducedFlash')?.checked;config.highContrast=!!$('highContrast')?.checked;config.skin=$('skinSelect')?.value||config.skin;config.music=Number($('musicVolume')?.value??config.music);config.sfx=Number($('sfxVolume')?.value??config.sfx);config.uiScale=Number($('uiScale')?.value||config.uiScale);config.modules=[...document.querySelectorAll('.module-card.active')].map(x=>x.dataset.module).slice(0,2);if(!config.modules.length)config.modules=['shoehorn'];persistConfig();rebuildJetta();document.body.classList.toggle('high-contrast',config.highContrast);document.documentElement.style.setProperty('--ui-scale',config.uiScale);
  }
  function applyConfigToUI(){
    document.querySelectorAll('.mode-card').forEach(card=>card.classList.toggle('active',card.dataset.mode===config.mode));if($('assistSelect'))$('assistSelect').value=config.assist;if($('sensitivity'))$('sensitivity').value=config.sensitivity;if($('invertY'))$('invertY').checked=config.invertY;if($('qualitySelect'))$('qualitySelect').value=config.quality;if($('reducedMotion'))$('reducedMotion').checked=config.reducedMotion;if($('reducedFlash'))$('reducedFlash').checked=config.reducedFlash;if($('highContrast'))$('highContrast').checked=config.highContrast;document.body.classList.toggle('high-contrast',config.highContrast);if($('skinSelect'))$('skinSelect').value=config.skin;if($('musicVolume'))$('musicVolume').value=config.music;if($('sfxVolume'))$('sfxVolume').value=config.sfx;if($('uiScale'))$('uiScale').value=config.uiScale;document.querySelectorAll('.module-card').forEach(card=>card.classList.toggle('active',config.modules.includes(card.dataset.module)));document.documentElement.style.setProperty('--ui-scale',config.uiScale);
  }

  function startGame(newSector=false,resume=false,debug=false){
    audioReady();readMenuConfig();const fresh=!resume||!game||['menu','dead','won'].includes(game.phase)||newSector;
    if(fresh){
      if(!newSector)clearCheckpoint();
      const seed=newSector?(game?.seed||$('seed').value.trim()):($('seed').value.trim()||'DISSENT-01'),sector=newSector?(game?.sector||1)+1:1,carry=newSector&&game&&player?{score:game.score,kills:game.kills,elapsed:game.elapsed,hull:player.hull,energy:player.energy,missiles:player.missiles,integrity:game.integrity,ledger:game.ledger.slice()}:null;
      createWorld(seed,sector);if(carry){game.score=carry.score;game.kills=carry.kills;game.elapsed=carry.elapsed;game.integrity=clamp(carry.integrity+10,0,100);game.ledger=carry.ledger;player.hull=clamp(carry.hull+20,0,100);player.energy=clamp(carry.energy+35,0,100);player.missiles=Math.min(14,carry.missiles+4);}
    }
    game.modules=new Set(config.modules);game.phase='playing';game.mapOpen=false;game.ledgerOpen=false;$('mapOverlay').classList.remove('open');$('ledgerOverlay').classList.remove('open');hideScreen();sfx('ui');
    if(fresh&&!debug)showCinematic(newSector?'APPEAL REFILED':'ENGINE IGNITION',newSector?`SECTOR ${pad(game.sector)} ACCEPTED`:'THE JETTA HAS WINGS.',newSector?'THE UNDERCOURT HAS GENERATED A DEEPER VERSION OF THE SAME PROBLEM.':'DESCEND. RECOVER THE RECORD. BRING IT BACK THROUGH HELL.',newSector?3.1:4.2,'opening',true);
    saveCheckpoint(true);if(!debug)canvas.requestPointerLock?.();
  }
  function finish(won,reason){
    if(!game||['won','dead'].includes(game.phase))return;game.phase=won?'won':'dead';clearCheckpoint();game.lastResult={version:VERSION,won,score:Math.floor(game.score),mode:game.mode,seed:game.seed,sector:game.sector,elapsed:Math.round(game.elapsed),integrity:Math.round(game.integrity),kills:game.kills,records:game.recordsRecovered,relays:game.relaysDown,date:new Date().toISOString()};$('outcomeLabel').textContent=won?'RECORD EXTRACTED':'CASE BURIED';$('outcomeTitle').textContent=reason;storeBest(game.score);displayBest();$('outcomeScore').textContent=String(Math.floor(game.score)).padStart(7,'0')+' PTS';$('outcomeStats').textContent=`SECTOR ${pad(game.sector)} · ${game.kills} MACHINES · EXHIBITS ${game.recordsRecovered}/${facility.records.length} · SEALS ${game.relaysDown}/${facility.relays.length} · INTEGRITY ${Math.ceil(game.integrity)}% · ${Math.floor(game.elapsed/60)}m ${pad(game.elapsed%60)}s`;$('outcomeLedger').textContent=game.ledger.map(x=>`${x.class}: ${x.choice.toUpperCase()}`).join(' · ')||'NO RECORD DISPOSITION ENTERED';$('next').style.display=won?'block':'none';$('next').textContent=game.mode==='endless'?'FILE THE NEXT ENDLESS APPEAL ▸':'DESCEND INTO THE NEXT CASE ▸';$('again').textContent=won?'REPLAY THIS SEED':'REOPEN THIS CASE';if(won)sfx('win');recordRun(game.lastResult);drawResultCard();updateRunHistoryPanel();showScreen('outcome');buttons.fire=false;keys.clear();if(document.pointerLockElement===canvas)document.exitPointerLock();
  }


  document.querySelectorAll('.mode-card').forEach(card=>card.addEventListener('click',()=>{document.querySelectorAll('.mode-card').forEach(x=>x.classList.remove('active'));card.classList.add('active');config.mode=card.dataset.mode;sfx('ui');}));
  document.querySelectorAll('.module-card').forEach(card=>card.addEventListener('click',()=>{const active=[...document.querySelectorAll('.module-card.active')];if(card.classList.contains('active'))card.classList.remove('active');else if(active.length<2)card.classList.add('active');else{active[0].classList.remove('active');card.classList.add('active');}sfx('ui');}));
  $('start').addEventListener('click',requestLaunch);$('resumeRun')?.addEventListener('click',resumeSavedRun);$('trainingBrief')?.addEventListener('click',()=>openTutorial(true));$('exportProgress')?.addEventListener('click',exportProgress);$('importProgress')?.addEventListener('click',()=>$('importProgressFile')?.click());$('importProgressFile')?.addEventListener('change',e=>{importProgressFile(e.target.files?.[0]);e.target.value='';});$('copyResult')?.addEventListener('click',copyResult);$('downloadCard')?.addEventListener('click',downloadResultCard);$('tutorialPrev')?.addEventListener('click',()=>{tutorialStep=Math.max(0,tutorialStep-1);renderTutorial();});$('tutorialSkip')?.addEventListener('click',()=>closeTutorial(false));$('tutorialNext')?.addEventListener('click',()=>{if(tutorialStep<TUTORIAL_STEPS.length-1){tutorialStep++;renderTutorial();}else closeTutorial(true);});
  $('reroll').addEventListener('click',()=>{$('seed').value='DS-'+Math.floor(Math.random()*0xfffffff).toString(36).toUpperCase();$('dailySeed').dataset.active='0';sfx('ui');});
  $('dailySeed').addEventListener('click',()=>{const d=new Date(),date=d.toISOString().slice(0,10).replaceAll('-','');$('seed').value=`DAILY-DOCKET-${date}`;$('dailySeed').dataset.active='1';showToast('DAILY DOCKET LOADED',1.5);});
  $('next').addEventListener('click',()=>startGame(true,false));$('again').addEventListener('click',()=>{createWorld(game.seed,game.sector);startGame(false,true);});$('seed').addEventListener('keydown',e=>e.stopPropagation());
  document.querySelectorAll('[data-evidence-choice]').forEach(button=>button.addEventListener('click',()=>chooseEvidence(button.dataset.evidenceChoice)));
  $('ledgerClose').addEventListener('click',()=>toggleLedger(false));

  document.addEventListener('keydown',e=>{
    if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Tab'].includes(e.code))e.preventDefault();if(document.activeElement===$('seed'))return;
    if(game?.phase==='choice'){if(e.code==='Digit1')chooseEvidence('expose');if(e.code==='Digit2')chooseEvidence('protect');if(e.code==='Digit3')chooseEvidence('archive');return;}
    if(e.code==='KeyL'&&!e.repeat&&game&&['playing','ledger'].includes(game.phase)){toggleLedger();return;}
    if(e.code==='Tab'&&!e.repeat&&game?.phase==='playing'){game.mapOpen=!game.mapOpen;$('mapOverlay').classList.toggle('open',game.mapOpen);if(game.mapOpen)drawBigMap();sfx('ui');return;}
    if((e.code==='KeyP'||e.code==='Escape')&&!e.repeat&&game&&['playing','paused'].includes(game.phase)){togglePause();return;}
    if(e.code==='Enter'&&game?.phase==='paused'){startGame(false,true);return;}
    if(e.code==='KeyR'&&game&&['dead','won'].includes(game.phase)){createWorld(game.seed,game.sector);startGame(false,true);return;}
    if(e.code==='KeyV'&&!e.repeat&&game?.phase==='playing'){const i=(CAMERA_MODES.indexOf(config.camera)+1)%CAMERA_MODES.length;config.camera=CAMERA_MODES[i];persistConfig();showCameraLabel();showToast(game.cameraLabel,1.6);return;}
    keys.add(e.code);
  });
  document.addEventListener('keyup',e=>keys.delete(e.code));
  canvas.addEventListener('mousedown',e=>{if(e.button===0)buttons.fire=true;if(e.button===2)launchMissile();});window.addEventListener('mouseup',e=>{if(e.button===0)buttons.fire=false;});canvas.addEventListener('contextmenu',e=>e.preventDefault());window.addEventListener('blur',()=>{keys.clear();buttons.fire=false;});
  document.addEventListener('mousemove',e=>{if(document.pointerLockElement!==canvas||!game||game.phase!=='playing'||game.mapOpen)return;mouseDelta.x+=e.movementX;mouseDelta.y+=e.movementY;});
  document.addEventListener('pointerlockchange',()=>{if(document.pointerLockElement!==canvas&&game?.phase==='playing'&&!game.mapOpen&&!game.pendingRecord){game.phase='paused';showScreen('pause');buttons.fire=false;keys.clear();}});document.addEventListener('pointerlockerror',()=>showToast('POINTER CAPTURE UNAVAILABLE — KEYBOARD / GAMEPAD FLIGHT REMAINS ACTIVE'));
  window.addEventListener('resize',()=>{if(game?.mapOpen)drawBigMap();});document.addEventListener('visibilitychange',()=>{if(document.hidden)saveCheckpoint(true);});window.addEventListener('beforeunload',()=>saveCheckpoint(true));

  function handleGamepadMeta(){const gp=gamepadState();if(!gp||!game)return;if(edge('map',gp.map)&&game.phase==='playing'){game.mapOpen=!game.mapOpen;$('mapOverlay').classList.toggle('open',game.mapOpen);if(game.mapOpen)drawBigMap();}if(edge('pause',gp.pause)&&['playing','paused'].includes(game.phase))togglePause();}
  function frame(time){
    const realDt=clamp((time-lastTime)/1000,0,.12);lastTime=time;handleGamepadMeta();
    if(game&&player){if(game.phase==='menu'){player.rotation=qNorm(qMul(player.rotation,qAxis([0,1,0],realDt*.12)));game.time+=realDt*.35;}else if(game.phase==='playing'&&!game.mapOpen){accumulator=Math.min(accumulator+realDt,FIXED_STEP*MAX_STEPS);let steps=0;while(accumulator>=FIXED_STEP&&steps++<MAX_STEPS){update(FIXED_STEP);accumulator-=FIXED_STEP;}}render(accumulator/FIXED_STEP);if(frameCount++%6===0)updateHUD();}
    requestAnimationFrame(frame);
  }

  applyConfigToUI();createWorld($('seed').value,1);displayBest();updateResumeButton();showScreen('menu');requestAnimationFrame(frame);
  window.DISSENT_DEBUG={
    version:VERSION,generatorVersion:DG.VERSION,
    getState:()=>({phase:game.phase,seed:game.seed,sector:game.sector,mode:game.mode,strata:facility.strataCount,rooms:facility.rooms.length,connectors:facility.connectors.length,records:facility.records.length,recordsRecovered:game.recordsRecovered,relays:facility.relays.length,relaysDown:game.relaysDown,boss:facility.boss.type,bossActive:facility.boss.active,bossUnlocked:facility.boss.unlocked,ship:player.position.slice(),camera:config.camera,shipTriangles:shipMesh.data.length/18,authenticJetta:jettaModelState.loaded,modelSource:jettaModelState.source,checkpoint:checkpointAvailable(),staticTriangles:staticCount/3,score:Math.floor(game.score),integrity:game.integrity,incidents:game.director.history.slice(),ledger:game.ledger.slice(),falseVictory:game.falseVictory,cinematic:game.cinematic?.kind||null}),
    getGraph:()=>facility.rooms.map(r=>({id:r.id,cell:r.cell.slice(),links:r.links.slice(),stratum:r.stratum,role:r.role,secret:r.secret})),
    validate:()=>DG.validateFacility(facility),
    debugRegenerate:(seed,sector=1,mode=config.mode)=>{config.mode=mode;createWorld(String(seed),sector);return DG.summarizeFacility(facility);},
    debugStart:()=>{game.phase='playing';hideScreen();return true;},
    debugMoveTo:(p)=>{if(!Array.isArray(p)||p.length!==3||p.some(x=>!Number.isFinite(x))||!pointInside(p,1.3))return false;player.position=p.slice();player.previous=p.slice();player.velocity=[0,0,0];return true;},
    debugRecoverRecord:(choice='archive')=>{const record=facility.records.find(r=>!r.recovered);if(!record)return null;beginEvidenceChoice(record);chooseEvidence(['expose','protect','archive'].includes(choice)?choice:'archive');return game.ledger.at(-1);},
    debugCycleCamera:()=>{const i=(CAMERA_MODES.indexOf(config.camera)+1)%CAMERA_MODES.length;config.camera=CAMERA_MODES[i];showCameraLabel();return config.camera;},
    debugToggleMap:()=>{game.mapOpen=!game.mapOpen;$('mapOverlay').classList.toggle('open',game.mapOpen);if(game.mapOpen)drawBigMap();return game.mapOpen;},
    debugCompleteObjectives:()=>{for(const r of facility.records){r.recovered=true;r.choice='archive';}game.recordsRecovered=facility.records.length;for(const r of facility.relays)r.active=false;game.relaysDown=facility.relays.length;activateBossIfReady();return facility.boss.unlocked;},
    debugFalseVictory:()=>{if(!facility.boss.unlocked)window.DISSENT_DEBUG.debugCompleteObjectives();game.falseVictory=false;for(const w of facility.boss.weakpoints)w.active=false;facility.boss.hp=0;defeatBoss();return game.falseVictory&&facility.boss.active;},
    debugDefeatBoss:()=>{if(!facility.boss.unlocked){for(const r of facility.records)r.recovered=true;game.recordsRecovered=facility.records.length;for(const r of facility.relays)r.active=false;game.relaysDown=facility.relays.length;activateBossIfReady();}game.falseVictory=true;for(const w of facility.boss.weakpoints)w.active=false;facility.boss.hp=0;defeatBoss();return !facility.boss.active;},
    debugWin:()=>{if(facility.boss.active)window.DISSENT_DEBUG.debugDefeatBoss();finish(true,'DEBUG EXTRACTION COMPLETE');return game.phase;},
    debugIncident:(type)=>{if(game.incident)endIncident('DEBUG CLEAR');startIncident(type);return game.incident?.type;},
    debugSaveCheckpoint:()=>saveCheckpoint(true),debugResumeCheckpoint:()=>resumeSavedRun(),debugCheckpointAvailable:()=>checkpointAvailable(),debugResultCard:()=>{drawResultCard();return !!$('resultCard')?.toDataURL('image/png').startsWith('data:image/png');},
    debugStep:(seconds=1)=>{const steps=Math.ceil(seconds/FIXED_STEP);for(let i=0;i<steps;i++)update(FIXED_STEP);return window.DISSENT_DEBUG.getState();}
  };
})();
