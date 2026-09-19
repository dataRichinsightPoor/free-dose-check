/** Reproducible smoke QA against a running static server.
 * npm ci && npx playwright install chromium
 * node tools/browser_qa.mjs http://localhost:3000 /tmp/free-dose-qa
 */
import {chromium} from "playwright";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";

const target=process.argv[2]||"http://localhost:3000";
const output=process.argv[3]||"/tmp/free-dose-qa";
await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
const page=await context.newPage(),errors=[];
page.on("pageerror",e=>errors.push(e.message));
const ready=p=>p.waitForFunction(()=>document.querySelector("#runtime").textContent.includes("Python ready"),null,{timeout:60000});
async function saveDownload(button,filename){
  const next=page.waitForEvent("download");
  await page.locator(button).click();
  await (await next).saveAs(path.join(output,filename));
}
try {
  await page.goto(target,{waitUntil:"domcontentloaded"});await ready(page);
  assert.equal(await page.locator("#cells").inputValue(),"");
  await page.screenshot({path:path.join(output,"desktop-initial.png")});
  for(const [key,status,label] of [
    ["low","within_tolerance","Synthetic: low depletion"],
    ["bounded","crosses_tolerance","Synthetic: bounds cross tolerance"],
    ["unsupported","exceeds_tolerance","Synthetic: unsupported internalizing bivalent ligand"],
    ["constrained","exceeds_tolerance","Synthetic: high depletion, constrained design"],
  ]){
    await page.locator("#example").selectOption(key);await page.locator("#loadExample").click();
    await page.waitForFunction(label=>window.lastReport?.inputs.label===label,label);
    const report=await page.evaluate(()=>window.lastReport);
    assert.equal(report.depletion_assessment,status);
    if(key==="unsupported"){
      assert.equal(report.model_applicability,"unsupported_model");
      assert.equal(report.recommendations.volume_option,null);
      assert.equal(report.recommendations.cell_option,null);
    }
    await fs.writeFile(path.join(output,key+"-browser.json"),JSON.stringify(report,null,2));
  }
  assert((await page.locator("#recommendations").innerText()).includes("1,371.088"));
  await saveDownload("#exportJson","browser-export.json");
  await saveDownload("#exportCsv","browser-export.csv");
  await page.screenshot({path:path.join(output,"desktop-results.png")});
  await page.locator("#cells").fill("2000");
  assert(await page.locator("#staleBadge").isVisible());
  assert(await page.locator("#exportJson").isDisabled());
  await page.locator("#run").click();
  await page.waitForFunction(()=>window.lastReport?.inputs.cell_count===2000);
  assert.equal(await page.evaluate(()=>lastReport.depletion_assessment),"within_tolerance");
  await page.locator("#kdBasis").selectOption("functional");
  await page.locator("#run").click();
  await page.waitForFunction(()=>document.querySelector("#formError").textContent.includes("Functional"));
  await page.locator("#kdBasis").selectOption("independent");
  await page.locator("#assumption_equilibrium").selectOption("uncertain");
  await page.locator("#run").click();
  await page.waitForFunction(()=>window.lastReport?.model_applicability==="assumption_check_required");
  await page.locator("#compareEnabled").evaluate(el=>el.closest("details").open=true);
  await page.locator("#compareEnabled").check();
  await page.locator("#altCells").fill("100000");await page.locator("#altVolume").fill("100");
  await page.locator("#run").click();await page.locator("#comparisonCard").waitFor({state:"visible"});
  await saveDownload("#exportAlternative","alternative-export.json");
  await page.locator("#theme").click();await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:path.join(output,"desktop-dark.png")});
  assert.equal(await page.evaluate(()=>document.documentElement.dataset.theme),"dark");
  for(const width of [375,390]){
    const mobile=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});
    const p=await mobile.newPage();await p.goto(target,{waitUntil:"domcontentloaded"});await ready(p);
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await p.locator("#loadExample").click();await p.waitForFunction(()=>window.lastReport!==null);
    await p.locator("#results").scrollIntoViewIfNeeded();
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await p.screenshot({path:path.join(output,`mobile-${width}.png`)});
    await mobile.close();
  }
  assert.deepEqual(errors,[]);
  console.log("PASS: four scenarios, gates, exports, stale state, alternative, themes, 375/390 px layouts.");
  console.log("Reports and screenshots:",output);
}finally{
  await browser.close();
}
