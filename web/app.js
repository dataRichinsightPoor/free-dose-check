"use strict";
const $ = id => document.getElementById(id);
const assumptionLabels = {
  equilibrium:"Equilibrium reached during incubation",
  independent_sites:"One ligand per independent site; no avidity",
  closed_system:"No relevant sinks, internalization, or turnover",
  well_mixed:"Well mixed; one accessible affinity class"
};
const escapeHtml = value => String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const human = value => value.replaceAll("_"," ");
const fmt = value => {
  if (value === null || value === undefined) return "—";
  if (value === 0) return "0";
  if (Math.abs(value) < .001 || Math.abs(value) >= 1e6) return value.toExponential(3);
  return Number(value.toPrecision(4)).toLocaleString("en-US",{maximumFractionDigits:8});
};
const range = (v,multiplier=1) => v === null ? "N/A" : v.low === v.high ? fmt(v.low*multiplier) : `${fmt(v.low*multiplier)} to ${fmt(v.high*multiplier)}`;
let worker, ready=false, sequence=0, pending=new Map(), report=null, alternativeReport=null, stale=false, working=false, inputRevision=0;
let exampleData=null;
window.lastReport=null;
$("assumptionInputs").innerHTML=Object.entries(assumptionLabels).map(([key,label])=>`
  <div class="assumption-field"><label for="assumption_${key}">${label}</label>
  <select id="assumption_${key}"><option value="uncertain">Uncertain / not established</option><option value="supported">Supported under declared conditions</option><option value="unsupported">Unsupported / violated</option></select>
  <textarea id="note_${key}" rows="1" aria-label="${label}: evidence note" placeholder="Evidence or qualification (optional)"></textarea></div>`).join("");

function updateButtons(){
  $("run").disabled=!ready||working;
  $("loadExample").disabled=!ready||working||!exampleData;
  for(const id of ["exportJson","exportCsv","exportAlternative"]) $(id).disabled=!report||stale||working;
}
async function startWorker(){
  if(worker) worker.terminate();
  for(const promise of pending.values()) promise.reject(new Error("Runtime restarted."));
  pending.clear();
  ready=false; updateButtons();
  $("runtimeError").hidden=true;
  $("runtime").innerHTML='<span class="pulse"></span>Loading local Python…';
  try {
    const source=await fetch("worker.js");
    if(!source.ok)throw new Error("Worker asset unavailable");
    const prefix="const PACKAGE_URL = "+JSON.stringify(new URL("free_dose_check.zip",document.baseURI).href)+";\n";
    const blob=URL.createObjectURL(new Blob([prefix,await source.text()],{type:"text/javascript"}));
    worker=new Worker(blob);
    URL.revokeObjectURL(blob);
  } catch(error) {
    $("runtimeError").hidden=false;$("runtime").textContent="Runtime unavailable";return;
  }
  const timer=setTimeout(()=>{if(!ready){$("runtimeError").hidden=false;$("runtime").textContent="Runtime loading slowly. Retry available.";}},45000);
  worker.onmessage=event=>{
    const message=event.data;
    if(message.type==="ready"){
      clearTimeout(timer);ready=true;
      $("runtime").innerHTML='<span class="pulse"></span>Python ready · calculations stay local';
      $("runtimeError").hidden=true;updateButtons();return;
    }
    if(message.type==="boot_error"){clearTimeout(timer);$("runtimeError").hidden=false;$("runtime").textContent="Runtime unavailable";return;}
    const p=pending.get(message.id);
    if(!p)return;
    pending.delete(message.id);
    message.type==="error"?p.reject(new Error(message.message)):p.resolve(message);
  };
  worker.onerror=()=>{clearTimeout(timer);ready=false;$("runtimeError").hidden=false;$("runtime").textContent="Runtime unavailable";for(const p of pending.values())p.reject(new Error("Browser runtime failed."));pending.clear();updateButtons();};
}
function request(message){return new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});worker.postMessage({...message,id});});}
function value(id,optional=false){
  const raw=$(id).value.trim();
  if(!raw&&optional)return null;
  if(!raw)throw new Error(`${$(id).labels?.[0]?.textContent||id}: enter a value.`);
  const n=Number(raw);if(!Number.isFinite(n))throw new Error(`${id}: enter a finite number.`);return n;
}
function getConfig(){
  const raw=$("doses").value.trim();
  if(!raw)throw new Error("Added ligand concentrations: enter at least one positive dose.");
  const config={
    label:$("label").value,cell_count:value("cells"),volume_uL:value("volume"),
    sites_per_cell:$("sitesBound").checked?{low:value("sites"),high:value("sitesHigh")}:value("sites"),
    kd_nM:$("kdBound").checked?{low:value("kd"),high:value("kdHigh")}:value("kd"),
    ligand_total_nM:raw.split(/[\s,;]+/).map(s=>{const n=Number(s);if(!Number.isFinite(n))throw new Error("Dose list contains a nonnumeric value.");return n;}),
    depletion_tolerance:value("tolerance")/100,max_volume_uL:value("maxVolume",true),min_cells:value("minCells",true),
    ligand_format:$("ligandFormat").value,effective_1to1_justification:$("justification").value,
    provenance:{sites_per_cell:{kind:$("sitesKind").value,note:$("sitesNote").value},
      kd_nM:{kind:$("kdKind").value,note:$("kdNote").value,basis:$("kdBasis").value}},
    assumptions:Object.fromEntries(Object.keys(assumptionLabels).map(k=>[k,{status:$("assumption_"+k).value,note:$("note_"+k).value}]))
  };
  return config;
}
function setConfig(c){
  const pairs={label:c.label,cells:c.cell_count,volume:c.volume_uL,doses:c.ligand_total_nM.join(", "),tolerance:c.depletion_tolerance*100,maxVolume:c.max_volume_uL??"",minCells:c.min_cells??"",ligandFormat:c.ligand_format,kdBasis:c.provenance.kd_nM.basis,
    sitesKind:c.provenance.sites_per_cell.kind,sitesNote:c.provenance.sites_per_cell.note,kdKind:c.provenance.kd_nM.kind,kdNote:c.provenance.kd_nM.note,justification:c.effective_1to1_justification||""};
  for(const [key,v] of Object.entries(pairs))$(key).value=v;
  for(const [key,source] of [["sites","sites_per_cell"],["kd","kd_nM"]]){
    const bounded=typeof c[source]==="object";
    $(key+"Bound").checked=bounded;$(key).value=bounded?c[source].low:c[source];
    $(key+"High").value=bounded?c[source].high:"";$(key+"High").hidden=!bounded;
  }
  for(const [key,v] of Object.entries(c.assumptions)){$("assumption_"+key).value=v.status;$("note_"+key).value=v.note||"";}
  $("justificationWrap").hidden=c.ligand_format!=="effective_1to1";
  $("compareEnabled").checked=false;$("altCells").value="";$("altVolume").value="";
  markStale();
}
function markStale(){
  inputRevision++;
  if(report){stale=true;$("staleBadge").hidden=false;updateButtons();}
}
async function runAnalysis(scroll=false){
  if(!ready||working)return;
  $("formError").hidden=true;
  try{
    const config=getConfig();
    const submittedRevision=inputRevision;
    const alternative=$("compareEnabled").checked?{...config,label:(config.label||"Condition")+" / alternative",cell_count:value("altCells"),volume_uL:value("altVolume")}:null;
    working=true;updateButtons();$("run").textContent="Calculating…";
    const result=await request({type:"analyze",config,alternative});
    report=result.report;alternativeReport=result.alternative;window.lastReport=report;
    stale=inputRevision!==submittedRevision;$("staleBadge").hidden=!stale;render();
    if(scroll&&window.innerWidth<701)$("results").scrollIntoView({behavior:"smooth",block:"start"});
  }catch(error){
    $("formError").textContent=error.message;$("formError").hidden=false;
    if(report){stale=true;$("staleBadge").hidden=false;}
    $("formError").scrollIntoView({behavior:"smooth",block:"center"});
  }finally{working=false;$("run").innerHTML='Run depletion check <span aria-hidden="true">↗</span>';updateButtons();}
}
function render(){
  $("empty").hidden=true;$("results").hidden=false;
  $("resultLabel").textContent=report.inputs.label||"Untitled binding condition";
  const unsupported=report.model_applicability==="unsupported_model", uncertain=report.model_applicability==="assumption_check_required";
  const assessment=report.depletion_assessment, positive=report.doses.filter(d=>d.ligand_total_nM>0);
  const worst={low:Math.max(...positive.map(d=>d.depletion.low)),high:Math.max(...positive.map(d=>d.depletion.high))};
  const titles={exceeds_tolerance:"Depletion exceeds your tolerance.",crosses_tolerance:"Input bounds cross your tolerance.",within_tolerance:"Depletion is within your tolerance."};
  const title=unsupported?"This biology is outside the model.":uncertain?"Check the assumptions before acting.":titles[assessment];
  const desc=unsupported?"The numbers below are illustrative mathematical outputs only. Actionable design recommendations are suppressed.":uncertain?"This is a conditional calculation, not an assurance about your assay. Resolve uncertain assumptions before using the design alternatives.":"This checks the free-equals-added approximation, not assay validity. The "+fmt(report.inputs.depletion_tolerance*100)+"% threshold is your planning choice.";
  $("decision").className="decision "+(unsupported?"unsupported":uncertain||assessment!=="within_tolerance"?"warn":"");
  $("decision").innerHTML=`<div class="status-line">${escapeHtml(human(report.model_applicability))}</div><h3>${title}</h3>${(unsupported||uncertain)?`<p class="secondary-assessment">Illustrative depletion assessment: ${escapeHtml(human(assessment))}.</p>`:""}<p>${desc}</p>`;
  $("metrics").innerHTML=[
    ["Worst-dose depletion",range(worst,100),"%","Across every positive dose; no low doses omitted."],
    ["Accessible-site concentration",range(report.site_concentration_nM),"nM","Calculated from cells, accessible sites, and volume."],
    ["Model-implied half occupancy",range(report.model_implied_half_occupancy_nM),"nM","Total ligand at 50% occupancy. Not a fitted EC50."]
  ].map(([label,v,unit,note])=>`<div class="metric"><label>${label}</label><strong>${v}<span class="unit">${unit}</span></strong><small>${note}</small></div>`).join("");
  renderRecommendations();
  $("doseRows").innerHTML=report.doses.map(d=>`<tr><td>${fmt(d.ligand_total_nM)}</td><td>${range(d.free_nM)}</td><td>${range(d.bound_nM)}</td><td>${range(d.depletion,100)}</td><td>${range(d.occupancy,100)}</td><td>${range(d.naive_occupancy,100)}</td><td>${range(d.occupancy_error_pp)}</td><td>${human(d.assessment)}</td></tr>`).join("");
  $("record").innerHTML='<div class="record-grid">'+Object.entries(report.inputs.assumptions).map(([k,v])=>`<div class="record-item"><strong>${assumptionLabels[k]}</strong><span class="badge ${v.status==="supported"?"":"warning"}">${v.status}</span><p>${escapeHtml(v.note||"No evidence note supplied.")}</p></div>`).join("")+
    Object.entries(report.inputs.provenance).map(([k,v])=>`<div class="record-item"><strong>${k==="kd_nM"?"Affinity":"Accessible sites"} · ${v.kind}</strong><p>${escapeHtml(v.note)}</p>${v.basis?`<p>Basis: ${human(v.basis)}</p>`:""}</div>`).join("")+
    `<div class="record-item"><strong>Ligand format</strong><p>${human(report.inputs.ligand_format)}</p><p>${escapeHtml(report.inputs.effective_1to1_justification)}</p></div></div>`;
  $("warnings").innerHTML=report.warnings.map(w=>`<li>${escapeHtml(w)}</li>`).join("");
  $("comparisonCard").hidden=!alternativeReport;
  if(alternativeReport){
    const alt=alternativeReport, aWorst={low:Math.max(...alt.doses.filter(d=>d.depletion).map(d=>d.depletion.low)),high:Math.max(...alt.doses.filter(d=>d.depletion).map(d=>d.depletion.high))};
    $("comparison").innerHTML=`<div class="comparison-grid"><div><strong>BASELINE</strong>${fmt(report.inputs.cell_count)} cells / ${fmt(report.inputs.volume_uL)} µL<br>Worst depletion: ${range(worst,100)}%</div><div><strong>ALTERNATIVE</strong>${fmt(alt.inputs.cell_count)} cells / ${fmt(alt.inputs.volume_uL)} µL<br>Worst depletion: ${range(aWorst,100)}%</div></div><p class="comparison-status">Alternative: ${human(alt.depletion_assessment)}. Model: ${human(alt.model_applicability)}. Design feasibility: ${human(alt.design_feasibility)}.</p><p class="rec-footer">Ligand concentrations remain fixed. Relative ligand amount: ${fmt(alt.inputs.volume_uL/report.inputs.volume_uL)}×. Alternative JSON contains all per-dose values.</p>`;
  }
  drawCharts();
}
function renderRecommendations(){
  const rec=report.recommendations;
  if(rec.status==="suppressed"){
    $("recommendations").innerHTML='<p class="rec-note">No actionable recommendations. The declared assay violates this model. An appropriate multivalent, kinetic, or additional-sink model is needed before design advice can be given.</p>';return;
  }
  if(!rec.volume_option){$("recommendations").textContent=rec.message;return;}
  function option(v,type){
    const verified=v.forward_verified, feasible=v.feasible_with_supplied_constraints;
    const status=!verified?"Not forward-verified":feasible===false?"Outside supplied constraints":feasible===true?"Meets supplied constraints":"Operational feasibility not assessed";
    const amount=type==="volume"?`${v.volume_uL.toLocaleString("en-US",{maximumFractionDigits:3})} µL`:`${v.cell_count.toLocaleString("en-US")} cells`;
    const note=type==="volume"?`Hold ${fmt(v.cell_count)} cells and every added concentration fixed. Ligand amount: ${fmt(v.reagent_multiplier)}× current.`:`Hold ${fmt(v.volume_uL)} µL and every added concentration fixed. Sufficient detection signal is not established.`;
    return `<div class="rec-option"><h4>${type==="volume"?"Volume at fixed cell count":"Cell count at fixed volume"}</h4><strong>${amount}</strong><p>${note}</p><p class="status ${!verified||feasible===false?"bad":feasible===true?"ok":""}">${status}</p><p>${escapeHtml(v.error||v.constraint_failures.join("; ")||"Rounded option checked through the equilibrium model.")}</p></div>`;
  }
  const noChange=report.depletion_assessment==="within_tolerance"?"No depletion-driven change is required under the declared model. ":"";
  $("recommendations").innerHTML=`<p class="rec-note">${rec.conditional?"Conditional options only: assumptions need review. ":""}${noChange}${escapeHtml(rec.message)}</p><div class="rec-options">${option(rec.volume_option,"volume")}${option(rec.cell_option,"cells")}</div><p class="rec-footer">Approximate mathematical limits: minimum volume ${fmt(rec.minimum_volume_uL)} µL; maximum cells ${fmt(rec.maximum_cells)}. Full precision is retained in JSON. Limiting dose: ${fmt(rec.limiting_dose_nM)} nM. Actionable options above round volume up to 0.001 µL and cells down; each changes only one variable.</p>`;
}
function drawCharts(){
  if(!report)return;
  drawPlot($("depletionChart"),[{key:"depletion",color:"--chart"}],report.inputs.depletion_tolerance);
  drawPlot($("occupancyChart"),[{key:"occupancy",color:"--chart"},{key:"naive_occupancy",color:"--naive"}],null);
}
function drawPlot(canvas,series,threshold){
  const css=getComputedStyle(document.documentElement), color=key=>css.getPropertyValue(key).trim();
  const rect=canvas.getBoundingClientRect(), w=rect.width,h=rect.height,dpr=window.devicePixelRatio||1;
  if(!w)return;
  canvas.width=w*dpr;canvas.height=h*dpr;
  const ctx=canvas.getContext("2d");ctx.scale(dpr,dpr);
  const p={l:39,r:11,t:14,b:42},W=w-p.l-p.r,H=h-p.t-p.b;
  const rows=report.doses.filter(d=>d.ligand_total_nM>0);
  let min=Math.log10(rows[0].ligand_total_nM),max=Math.log10(rows.at(-1).ligand_total_nM);
  if(min===max){min-=.5;max+=.5;}
  const x=v=>p.l+(Math.log10(v)-min)/(max-min)*W,y=v=>p.t+H*(1-v);
  ctx.font='9px "IBM Plex Mono", monospace';ctx.textAlign="right";
  for(let t=0;t<=1.001;t+=.25){
    ctx.strokeStyle=color("--line");ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(p.l,y(t));ctx.lineTo(w-p.r,y(t));ctx.stroke();
    ctx.fillStyle=color("--muted");ctx.fillText(Math.round(t*100)+"%",p.l-7,y(t)+3);
  }
  const ticks=rows.length<=5?rows:rows.filter((_,i)=>i===0||i===rows.length-1||i%Math.ceil(rows.length/4)===0);
  ctx.textAlign="center";for(const row of ticks){ctx.fillText(fmt(row.ligand_total_nM),x(row.ligand_total_nM),h-23);}
  ctx.fillText("Added ligand (nM) · log scale",p.l+W/2,h-5);
  if(threshold!==null){ctx.strokeStyle=color("--naive");ctx.lineWidth=1.5;ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(p.l,y(threshold));ctx.lineTo(w-p.r,y(threshold));ctx.stroke();ctx.setLineDash([]);}
  for(const s of series){
    ctx.beginPath();rows.forEach((r,i)=>{const xx=x(r.ligand_total_nM),yy=y(r[s.key].low);i?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy);});
    [...rows].reverse().forEach(r=>ctx.lineTo(x(r.ligand_total_nM),y(r[s.key].high)));ctx.closePath();ctx.fillStyle=color(s.color);ctx.globalAlpha=.13;ctx.fill();ctx.globalAlpha=1;
    for(const bound of ["low","high"]){
      ctx.strokeStyle=color(s.color);ctx.lineWidth=1.7;ctx.beginPath();
      rows.forEach((r,i)=>{const xx=x(r.ligand_total_nM),yy=y(r[s.key][bound]);i?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy);});ctx.stroke();
      rows.forEach(r=>{ctx.beginPath();ctx.arc(x(r.ligand_total_nM),y(r[s.key][bound]),2.6,0,2*Math.PI);ctx.fillStyle=color(s.color);ctx.fill();});
    }
  }
}
function download(text,name,type){
  const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement("a");
  a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$("analysisForm").addEventListener("submit",event=>{event.preventDefault();runAnalysis(true);});
$("analysisForm").addEventListener("input",markStale);
$("analysisForm").addEventListener("change",markStale);
for(const prefix of ["sites","kd"])$(prefix+"Bound").addEventListener("change",()=>{$(prefix+"High").hidden=!$(prefix+"Bound").checked;});
$("ligandFormat").addEventListener("change",()=>{$("justificationWrap").hidden=$("ligandFormat").value!=="effective_1to1";});
$("loadExample").addEventListener("click",()=>{setConfig(exampleData[$("example").value]);runAnalysis(true);});
$("retry").addEventListener("click",startWorker);
$("exportJson").addEventListener("click",()=>{if(!stale)download(JSON.stringify(report,null,2)+"\n","free-dose-check-report.json","application/json");});
$("exportAlternative").addEventListener("click",()=>{if(!stale)download(JSON.stringify(alternativeReport,null,2)+"\n","free-dose-check-alternative.json","application/json");});
$("exportCsv").addEventListener("click",async()=>{
  try{const response=await request({type:"csv",report});download(response.csv,"free-dose-check-doses.csv","text/csv");}
  catch(e){$("formError").textContent=e.message;$("formError").hidden=false;}
});
function setTheme(dark){document.documentElement.dataset.theme=dark?"dark":"light";$("theme").textContent=dark?"Light":"Dark";drawCharts();}
setTheme(window.matchMedia("(prefers-color-scheme: dark)").matches);
$("theme").addEventListener("click",()=>setTheme(document.documentElement.dataset.theme!=="dark"));
new ResizeObserver(()=>drawCharts()).observe($("output-panel")||document.querySelector(".output-panel"));
fetch("examples.json").then(r=>{if(!r.ok)throw new Error("Examples unavailable");return r.json();}).then(data=>{exampleData=data;updateButtons();}).catch(()=>{$("loadExample").textContent="Examples unavailable";});
startWorker();
