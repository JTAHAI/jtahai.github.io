/*
 * DISSENT procedural facility generator.
 * Browser + Node compatible, deterministic, dependency free.
 * Generator version G7-ABSURDITY-1.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  root.DissentGenerator=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='G7-ABSURDITY-1';
  const SPACING=[46,36,46];
  const ROOM_HALF=[16,12,16];
  const DIRS=[[1,0,0],[-1,0,0],[0,0,1],[0,0,-1]];
  const STRATA=[
    {id:'facade',name:'PUBLIC FACADE',subtitle:'All doors are open. None of them lead out.',palette:{wall:[.17,.20,.22],floor:[.075,.09,.10],ceil:[.11,.14,.15],accent:[.24,.95,.79],fog:[.006,.018,.025]},hazard:'redTape',features:['marble','columns','scales']},
    {id:'continuance',name:'CONTINUANCE CATACOMBS',subtitle:'Every postponement builds another corridor.',palette:{wall:[.19,.13,.24],floor:[.075,.055,.10],ceil:[.13,.09,.17],accent:[.67,.48,1],fog:[.018,.008,.028]},hazard:'continuanceLoop',features:['clocks','catacombs','dockets']},
    {id:'registry',name:'SEALED REGISTRY',subtitle:'The archive is complete. Access is not.',palette:{wall:[.10,.20,.20],floor:[.05,.105,.10],ceil:[.07,.16,.15],accent:[.25,.95,.76],fog:[.004,.025,.022]},hazard:'shredder',features:['archives','racks','chains']},
    {id:'paywall',name:'PAYWALL PITS',subtitle:'Truth is available in the premium tier.',palette:{wall:[.22,.17,.08],floor:[.10,.075,.03],ceil:[.17,.12,.045],accent:[1,.66,.22],fog:[.028,.018,.004]},hazard:'filingFee',features:['toll','ledgers','coins']},
    {id:'efiling',name:'E-FILING FURNACE',subtitle:'Your submission was received, rejected, and retained.',palette:{wall:[.28,.085,.045],floor:[.15,.035,.02],ceil:[.22,.055,.03],accent:[1,.30,.08],fog:[.040,.006,.002]},hazard:'stampPress',features:['furnace','conveyors','stamps']},
    {id:'bench',name:'INFERNAL BENCH',subtitle:'The honorable machinery is now fully molten.',palette:{wall:[.32,.045,.035],floor:[.19,.018,.012],ceil:[.25,.035,.025],accent:[1,.10,.04],fog:[.050,.003,.002]},hazard:'rejectionChute',features:['magma','chains','gavels']},
    {id:'null',name:'NULL TRIBUNAL',subtitle:'The final appeal has no record of your existence.',palette:{wall:[.16,.055,.22],floor:[.035,.012,.055],ceil:[.10,.025,.16],accent:[.94,.20,1],fog:[.015,.001,.025]},hazard:'missingDocket',features:['void','fractures','tribunal']}
  ];

  const MODES={
    quick:{id:'quick',name:'ONE MORE FILING',strata:3,baseRooms:16,roomGrowth:1,records:3,relays:2,secrets:1,extraction:105,description:'A concentrated 5–8 minute descent.'},
    grand:{id:'grand',name:'THE GRAND DESCENT',strata:7,baseRooms:32,roomGrowth:2,records:5,relays:4,secrets:2,extraction:190,description:'The complete seven-circle procedural absurdity.'},
    endless:{id:'endless',name:'ENDLESS APPEAL',strata:7,baseRooms:35,roomGrowth:3,records:6,relays:5,secrets:3,extraction:175,description:'Escalating sectors with no final docket.'}
  };

  const CHAMBERS=[
    'CONTINUANCE HALL','DOCKET GRAVEYARD','MISSING FINDINGS','VAULT OF DELAY','REDACTION WING','CLERKLESS CORRIDOR','ORDER MILL','THE SILENT BENCH','RECORDS CEMETERY','STAMPWORKS','THE FORGOTTEN HEARING','THE CLOSED DOOR','MOTION IN LIMBO','SERVICE WINDOW 404','THE RETURNED ENVELOPE','ARCHIVE OF UNMAILED ORDERS','FEE SCHEDULE ATRIUM','THE RECURSIVE CAPTION','HALL OF CORRECTED CORRECTIONS','THE MINUTE ENTRY WITHOUT MINUTES','THE ROOM THAT DENIED ITSELF','CLERK OF THE ABYSS','THE FILE WITHIN THE FILE','CHAMBER OF ORDINARY COURSE'
  ];

  const RECORD_LIBRARY=[
    {class:'ORDER',title:'THE ORDER THAT WAS NEVER MAILED',blurb:'Stamped, entered, and sent somewhere that was not here.'},
    {class:'TESTIMONY',title:'THE MISSING SIX MINUTES',blurb:'A witness spoke. The machine retained only the silence around it.'},
    {class:'CORRESPONDENCE',title:'THE EMAIL ACKNOWLEDGED BY NOBODY',blurb:'Delivered to every recipient and accepted by none.'},
    {class:'AUDIO',title:'THE RECORDING BEHIND THE PAYWALL',blurb:'The truth exists at a price the truth-teller cannot pay.'},
    {class:'DOCKET',title:'THE ENTRY WITHOUT THE FILING',blurb:'The system remembers a result but not the request that produced it.'},
    {class:'EXHIBIT',title:'EXHIBIT A TO EXHIBIT A',blurb:'A document proving that another document required another document.'},
    {class:'NOTICE',title:'NOTICE OF NOTICE OF NOTICE',blurb:'Service was perfected by announcing that perfection remained pending.'},
    {class:'KEY',title:'THE ARCHIVE KEY MARKED DO NOT DUPLICATE',blurb:'It opens the cabinet containing the form required to request the key.'},
    {class:'TRANSCRIPT',title:'THE TRANSCRIPT OF THE UNHEARD HEARING',blurb:'Every spoken word survived except the part that mattered.'},
    {class:'AFFIDAVIT',title:'THE SWORN STATEMENT OF COMMON SENSE',blurb:'Rejected for failing to attach an affidavit proving that sense exists.'}
  ];

  const HAZARD_BY_STRATUM=['redTape','continuanceLoop','shredder','filingFee','stampPress','rejectionChute','missingDocket'];
  const FEATURE_BY_STRATUM=['marble','clock','archives','paywall','furnace','magma','void'];
  const BOSS_TYPES=['rejection','grandSeal','gatekeeper','nullTribunal','erasure'];

  function hashString(str){let h=2166136261>>>0;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
  function randomGenerator(seed){let x=(hashString(String(seed))||1234567)>>>0;return function(){x+=0x6D2B79F5;let z=x;z=Math.imul(z^(z>>>15),z|1);z^=z+Math.imul(z^(z>>>7),z|61);return ((z^(z>>>14))>>>0)/4294967296;};}
  const key=c=>c.join(',');
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
  const addLink=(rooms,a,b)=>{if(!rooms[a].links.includes(b))rooms[a].links.push(b);if(!rooms[b].links.includes(a))rooms[b].links.push(a);};
  const adjacent=(a,b)=>Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1])+Math.abs(a[2]-b[2])===1;
  const shortestPath=(rooms,start,goal)=>{
    const prev=Array(rooms.length).fill(-1),q=[start];prev[start]=start;
    for(let qi=0;qi<q.length;qi++){const id=q[qi];if(id===goal)break;for(const n of rooms[id].links)if(prev[n]===-1){prev[n]=id;q.push(n);}}
    if(prev[goal]===-1)return [];
    const path=[];for(let at=goal;;at=prev[at]){path.push(at);if(at===start)break;}return path.reverse();
  };
  const bfsDepths=(rooms,start=0)=>{const d=Array(rooms.length).fill(Infinity),q=[start];d[start]=0;for(let i=0;i<q.length;i++){const id=q[i];for(const n of rooms[id].links)if(!Number.isFinite(d[n])){d[n]=d[id]+1;q.push(n);}}return d;};

  function chooseSpread(candidates,count,rng,rooms,strataCount){
    const chosen=[];
    if(!candidates.length||count<=0)return chosen;
    for(let i=0;i<count;i++){
      const wanted=count===1?strataCount-1:Math.round(i*(strataCount-1)/(count-1));
      const pool=candidates.filter(id=>!chosen.includes(id));
      pool.sort((a,b)=>Math.abs(rooms[a].stratum-wanted)-Math.abs(rooms[b].stratum-wanted)||rooms[b].distance-rooms[a].distance||rng()-.5);
      if(pool[0]!==undefined)chosen.push(pool[0]);
    }
    return chosen;
  }

  function generateFacility(seed='DISSENT-01',sector=1,options={}){
    const mode=MODES[options.mode]||MODES.grand;
    const strataCount=clamp(Number(options.strata||mode.strata)|0,3,7);
    const rng=randomGenerator(`${seed}#${sector}#${mode.id}#${VERSION}`);
    const rooms=[],occupied=new Map();
    const addRoom=(cell,parent=null,role='branch')=>{
      const id=rooms.length;
      const room={id,cell:cell.slice(),links:[],stratum:-cell[1],role,visited:false,secret:false,title:'',feature:'',distance:0,position:cell.map((n,i)=>n*SPACING[i])};
      rooms.push(room);occupied.set(key(cell),id);if(parent!==null)addLink(rooms,id,parent);return id;
    };

    // Guaranteed vertical spine through every active circle.
    const spine=[];
    for(let s=0;s<strataCount;s++){
      const id=addRoom([0,-s,0],s?spine[s-1]:null,s===0?'entry':'spine');spine.push(id);
    }

    const target=Math.max(strataCount*3,mode.baseRooms+Math.min(10,(sector-1)*mode.roomGrowth));
    const targetPer=Array(strataCount).fill(Math.floor(target/strataCount));
    for(let i=0;i<target%strataCount;i++)targetPer[(i*3+sector)%strataCount]++;

    // Seed each stratum with an intentional branch before free expansion.
    for(let s=0;s<strataCount;s++){
      const order=DIRS.slice().sort(()=>rng()-.5);
      for(const d of order){const c=[d[0],-s,d[2]];if(!occupied.has(key(c))){addRoom(c,spine[s],s===strataCount-1?'sanctum-approach':'branch');break;}}
    }

    // Grammar-driven horizontal expansion: favor dead ends for optional content,
    // but regularly return to the spine to keep navigation readable.
    for(let s=0;s<strataCount;s++){
      let guard=0;
      while(rooms.filter(r=>r.stratum===s).length<targetPer[s]&&guard++<5000){
        const floorRooms=rooms.filter(r=>r.stratum===s);
        const source=(rng()<.32?rooms[spine[s]]:floorRooms[Math.floor(rng()*floorRooms.length)]);
        const dirs=DIRS.slice().sort(()=>rng()-.5);
        let created=false;
        for(const d of dirs){
          const c=[source.cell[0]+d[0],-s,source.cell[2]+d[2]];
          if(Math.abs(c[0])>3||Math.abs(c[2])>3||occupied.has(key(c)))continue;
          addRoom(c,source.id,'branch');created=true;break;
        }
        if(!created&&floorRooms.length>=49)break;
      }
    }

    // Horizontal loops create alternate routes; secondary shafts create real 3D loops.
    for(const room of rooms){
      for(const d of DIRS){const n=occupied.get(key([room.cell[0]+d[0],room.cell[1],room.cell[2]+d[2]]));if(n!==undefined&&n>room.id&&!room.links.includes(n)&&rng()<.34)addLink(rooms,room.id,n);}
    }
    for(let s=0;s<strataCount-1;s++){
      const upper=rooms.filter(r=>r.stratum===s&&r.id!==spine[s]);
      const candidates=upper.filter(r=>occupied.has(key([r.cell[0],-(s+1),r.cell[2]])));
      const maxExtra=Math.max(1,Math.floor(candidates.length*.24));
      let added=0;
      for(const room of candidates.sort(()=>rng()-.5)){
        if(added>=maxExtra)break;
        const below=occupied.get(key([room.cell[0],-(s+1),room.cell[2]]));
        if(!room.links.includes(below)&&rng()<.58){addLink(rooms,room.id,below);added++;}
      }
    }

    const depths=bfsDepths(rooms,0);
    for(const room of rooms){room.distance=depths[room.id];room.title=room.id===0?'GATES OF PUBLIC ACCESS':CHAMBERS[Math.floor(rng()*CHAMBERS.length)];room.feature=FEATURE_BY_STRATUM[room.stratum]||'void';}

    const lowest=rooms.filter(r=>r.stratum===strataCount-1);
    const bossRoom=lowest.slice().sort((a,b)=>b.distance-a.distance||b.links.length-a.links.length)[0].id;
    rooms[bossRoom].role='boss';rooms[bossRoom].title=sector%5===0?'THE ERASURE SANCTUM':'THE FINAL MACHINE';
    const criticalPath=shortestPath(rooms,0,bossRoom);

    const objectivePool=rooms.filter(r=>r.id!==0&&r.id!==bossRoom&&r.role!=='spine').map(r=>r.id);
    const relayRooms=chooseSpread(objectivePool,Math.min(mode.relays,objectivePool.length),rng,rooms,strataCount);
    relayRooms.forEach((id,i)=>{rooms[id].role='relay';rooms[id].title=`SUPPRESSION SEAL ${String(i+1).padStart(2,'0')}`;});
    const recordPool=objectivePool.filter(id=>!relayRooms.includes(id));
    const recordRooms=chooseSpread(recordPool,Math.min(mode.records,recordPool.length),rng,rooms,strataCount);
    const records=recordRooms.map((room,id)=>{
      const source=RECORD_LIBRARY[(Math.floor(rng()*RECORD_LIBRARY.length)+id+sector)%RECORD_LIBRARY.length];
      rooms[room].role='record';rooms[room].title=`BURIED ${source.class} ${String(id+1).padStart(2,'0')}`;
      return {id,room,class:source.class,title:source.title,blurb:source.blurb,position:offset(rooms[room].position,rng,4.5,3.2),recovered:false,choice:null};
    });

    const secretPool=rooms.filter(r=>r.id!==0&&r.id!==bossRoom&&!recordRooms.includes(r.id)&&!relayRooms.includes(r.id)&&r.links.length<=2).map(r=>r.id);
    const secrets=[];
    for(const id of secretPool.sort(()=>rng()-.5).slice(0,Math.min(mode.secrets,secretPool.length))){rooms[id].secret=true;rooms[id].role='secret';rooms[id].title='SEALED SIDE RECORD';secrets.push({room:id,revealed:false,position:offset(rooms[id].position,rng,3,2),reward:rng()<.5?'upgrade':'score'});}

    const hazardRooms=[];
    for(let s=0;s<strataCount;s++){
      const optionsOnFloor=rooms.filter(r=>r.stratum===s&&r.id!==0&&r.id!==bossRoom&&!recordRooms.includes(r.id)&&!relayRooms.includes(r.id));
      if(!optionsOnFloor.length)continue;
      optionsOnFloor.sort((a,b)=>b.distance-a.distance||rng()-.5);
      const room=optionsOnFloor[0];hazardRooms.push(room.id);
    }
    const hazards=hazardRooms.map((room,id)=>({id,room,type:HAZARD_BY_STRATUM[rooms[room].stratum]||'redTape',position:offset(rooms[room].position,rng,2.3,1.2),disabled:false,phase:rng()*Math.PI*2,targetRoom:null}));
    for(const h of hazards){
      if(h.type==='rejectionChute'){
        const from=rooms[h.room];const lower=rooms.filter(r=>r.stratum>from.stratum).sort((a,b)=>Math.abs(a.stratum-from.stratum)-Math.abs(b.stratum-from.stratum)||a.distance-b.distance)[0];
        h.targetRoom=lower?lower.id:spine[Math.min(strataCount-1,from.stratum+1)];
      }
    }

    const connectors=[],volumes=[];
    for(const room of rooms){const p=room.position;volumes.push({min:[p[0]-ROOM_HALF[0],p[1]-ROOM_HALF[1],p[2]-ROOM_HALF[2]],max:[p[0]+ROOM_HALF[0],p[1]+ROOM_HALF[1],p[2]+ROOM_HALF[2]],room:room.id});}
    for(const room of rooms)for(const n of room.links){if(n<room.id)continue;const other=rooms[n];if(!adjacent(room.cell,other.cell))throw new Error(`Non-adjacent link ${room.id}-${n}`);const axis=room.cell.findIndex((x,k)=>x!==other.cell[k]);const center=room.position.map((x,k)=>(x+other.position[k])/2);const delta=Math.abs(room.position[axis]-other.position[axis]);const min=center.map((x,k)=>x-(k===axis?delta/2-10:6));const max=center.map((x,k)=>x+(k===axis?delta/2-10:6));const cmin=center.map((x,k)=>x-(k===axis?delta/2-8:6));const cmax=center.map((x,k)=>x+(k===axis?delta/2-8:6));connectors.push({a:room.id,b:n,axis,center,min,max,cmin,cmax});volumes.push({min:cmin,max:cmax,connector:[room.id,n]});}

    let bossType=BOSS_TYPES[(sector-1)%BOSS_TYPES.length];
    if(mode.id==='grand')bossType=sector%3===0?'nullTribunal':'erasure';
    if(mode.id==='endless'&&sector%5===0)bossType='erasure';
    const bossNames={rejection:'THE REJECTION ENGINE',grandSeal:'THE GRAND SEAL',gatekeeper:'THE GATEKEEPER',nullTribunal:'THE NULL TRIBUNAL',erasure:'THE ERASURE ENGINE'};
    const boss={room:bossRoom,position:rooms[bossRoom].position.slice(),type:bossType,name:bossNames[bossType],hp:28+sector*4+(mode.id==='quick'?0:10),active:true,unlocked:false,phase:0,weakpointCount:bossType==='grandSeal'?5:bossType==='erasure'?4:3};
    const relays=relayRooms.map((room,id)=>({id,room,position:offset(rooms[room].position,rng,3.5,2.4),hp:5+Math.floor(sector/3),active:true}));
    const exit=[rooms[0].position[0],rooms[0].position[1],rooms[0].position[2]+10.2];

    const facility={version:VERSION,seed:String(seed),sector,mode:mode.id,strataCount,rooms,connectors,volumes,spine,criticalPath,records,relays,secrets,hazards,boss,bossRoom,exit,spacing:SPACING.slice(),roomHalf:ROOM_HALF.slice(),extractionTime:mode.extraction};
    const validation=validateFacility(facility);
    if(!validation.ok)throw new Error(`Generated invalid facility: ${validation.errors.join('; ')}`);
    return facility;
  }

  function offset(position,rng,horizontal=4,vertical=3){return [position[0]+(rng()*2-1)*horizontal,position[1]+(rng()*2-1)*vertical,position[2]+(rng()*2-1)*horizontal];}

  function validateFacility(f){
    const errors=[];
    if(!f||!Array.isArray(f.rooms)||!f.rooms.length)return {ok:false,errors:['No rooms']};
    const cells=new Set();
    for(const r of f.rooms){const k=key(r.cell);if(cells.has(k))errors.push(`Duplicate cell ${k}`);cells.add(k);if(r.stratum<0||r.stratum>=f.strataCount)errors.push(`Bad stratum ${r.id}`);for(const n of r.links){if(!f.rooms[n])errors.push(`Missing link target ${r.id}-${n}`);else if(!f.rooms[n].links.includes(r.id))errors.push(`Asymmetric link ${r.id}-${n}`);else if(!adjacent(r.cell,f.rooms[n].cell))errors.push(`Nonadjacent link ${r.id}-${n}`);}}
    const d=bfsDepths(f.rooms,0);if(d.some(x=>!Number.isFinite(x)))errors.push('Disconnected graph');
    for(let s=0;s<f.strataCount;s++)if(!f.rooms.some(r=>r.stratum===s))errors.push(`Empty stratum ${s}`);
    if(!f.rooms[f.bossRoom]||f.rooms[f.bossRoom].stratum!==f.strataCount-1)errors.push('Boss not on lowest stratum');
    if(!shortestPath(f.rooms,0,f.bossRoom).length)errors.push('Boss unreachable');
    for(const r of f.records||[])if(!f.rooms[r.room]||!Number.isFinite(d[r.room]))errors.push(`Record unreachable ${r.id}`);
    for(const r of f.relays||[])if(!f.rooms[r.room]||!Number.isFinite(d[r.room]))errors.push(`Relay unreachable ${r.id}`);
    for(const c of f.connectors||[])if(!adjacent(f.rooms[c.a].cell,f.rooms[c.b].cell))errors.push(`Bad connector ${c.a}-${c.b}`);
    return {ok:errors.length===0,errors,rooms:f.rooms.length,strata:f.strataCount,criticalPath:f.criticalPath?.length||0};
  }

  function summarizeFacility(f){return {version:f.version,seed:f.seed,sector:f.sector,mode:f.mode,strata:f.strataCount,rooms:f.rooms.length,connectors:f.connectors.length,records:f.records.length,relays:f.relays.length,secrets:f.secrets.length,hazards:f.hazards.length,boss:f.boss.type,criticalPath:f.criticalPath.length};}

  return {VERSION,SPACING,ROOM_HALF,STRATA,MODES,CHAMBERS,RECORD_LIBRARY,HAZARD_BY_STRATUM,BOSS_TYPES,hashString,randomGenerator,generateFacility,validateFacility,summarizeFacility,shortestPath,bfsDepths};
});
