// Deterministic UI fixtures, NOT live RAG or answer-quality measurements.
// BASELINE_DIR points at the clean Review 2 checkout; build both React apps first.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const root=path.resolve(__dirname,'../..'),before=process.env.BASELINE_DIR;
if(!before) throw Error('Set BASELINE_DIR to clean Review 2 checkout');
const output=path.join(root,'research/review3/ui_screenshots');fs.mkdirSync(output,{recursive:true});
const fixtures=[
 {name:'acronym',question:'Explain CL carry forward rules',answer:'UI test fixture: consult section 5.5.1 for the carry-forward rule. This text is not a live policy answer.',source:'VIT_HR_Conditions_of_Service.pdf',outcome:'answer',evidence_status:'SUFFICIENT',acronym_entries:[{aliases:['CL'],full_form:'Casual Leave',source:'VIT_HR_Conditions_of_Service.pdf'}],trajectory:[{attempt:1,query:'Explain Casual Leave carry forward rules',score:.81,best_score:.81,score_delta:0,chunk_overlap:0,decision:'SUFFICIENT',critic_decision:'SUFFICIENT',halting_decision:'STOP',runtime_action:'STOP',stop_probability:.9}]},
 {name:'insufficient',question:'What is the policy for employee moon travel?',answer:'The retrieved policy evidence is insufficient to answer this question reliably.',source:'',outcome:'abstained',evidence_status:'INSUFFICIENT',acronym_entries:[],trajectory:[{attempt:1,query:'What is the policy for employee moon travel?',score:.32,best_score:.32,score_delta:0,chunk_overlap:0,decision:'INSUFFICIENT',critic_decision:'INSUFFICIENT',halting_decision:'STOP',runtime_action:'STOP',stop_probability:.7}]}
];
let active=fixtures[0],status=200,requestCount=0;
function server(base,react,port){return new Promise(resolve=>{const s=http.createServer((req,res)=>{let filename=decodeURIComponent(req.url.split('?')[0]);if(filename==='/static/research_metrics.json')filename=path.join(base,filename);else filename=react?path.join(base,'frontend/dist',filename):path.join(base,'static/index.html');if(react&&!fs.existsSync(filename))filename=path.join(base,'frontend/dist/index.html');if(fs.existsSync(filename)&&fs.statSync(filename).isDirectory())filename=path.join(filename,'index.html');try{res.setHeader('Content-Type',filename.endsWith('.js')?'text/javascript':filename.endsWith('.css')?'text/css':filename.endsWith('.json')?'application/json':'text/html');res.end(fs.readFileSync(filename));}catch{res.statusCode=404;res.end('Missing');}}).listen(port,'127.0.0.1',()=>resolve(s));});}
(async()=>{
 const servers=[];let browser;const results=[];
 try{
  for(const [base,react,port] of [[before,false,9111],[root,false,9112],[before,true,9113],[root,true,9114]])servers.push(await server(base,react,port));
  browser=await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE||undefined,headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']});
  for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
   for(const ui of ['static','react'])for(const version of ['before','after']){
    const context=await browser.newContext({viewport});
    await context.addInitScript(()=>localStorage.setItem('access_token','ui-test-fixture-only'));
    const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',async route=>{
     const url=new URL(route.request().url());
     if(url.pathname.endsWith('/auth/me'))return route.fulfill({json:{id:1,full_name:'UI Test User',email:'ui@example.test'}});
     if(url.pathname.endsWith('/auth/login'))return route.fulfill({json:{access_token:'ui-test-fixture-only',user:{id:1,full_name:'UI Test User',email:'ui@example.test'}}});
     if(url.pathname.endsWith('/ask')){requestCount++;if(status===0)return route.abort('failed');return route.fulfill({status,json:status===200?active:{detail:'Unavailable'}});}
     return route.continue();
    });
    const port=ui==='static'?(version==='before'?9111:9112):(version==='before'?9113:9114);
    await page.goto(`http://127.0.0.1:${port}${ui==='react'?'/chat':''}`);
    if(ui==='static'&&version==='after'){
      await page.locator('#auth-email').fill('ui@example.test');await page.locator('#auth-password').fill('ui-fixture-password');await page.locator('#login-button').click();await page.getByText('Signed in',{exact:true}).waitFor();
    }
    for(const fixture of fixtures){active=fixture;status=200;await page.locator('#question').fill(fixture.question);await page.getByRole('button',{name:'Ask Question',exact:true}).click();await page.getByText(fixture.answer,{exact:true}).waitFor();
      if(version==='after'){
       if(fixture.name==='acronym')await page.getByText(/Verified abbreviation: CL = Casual Leave/).waitFor();
       else{await page.getByText('Insufficient evidence',{exact:true}).waitFor();assert(!(await page.locator('body').innerText()).includes('HR policy handbook'));}
      }
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert(!overflow,`${ui} ${version} mobile overflow`);
      await page.screenshot({path:path.join(output,`${ui}-${version}-${viewport.width}-${fixture.name}.png`),fullPage:true});
      results.push({ui,version,width:viewport.width,scenario:fixture.name,overflow:false,fixture:true});
    }
    if(version==='after'){
      const count=requestCount;await page.locator('#question').fill('');await page.getByRole('button',{name:'Ask Question',exact:true}).click();assert.equal(requestCount,count);
      for(const code of [401,429,503,0]){status=code;await page.locator('#question').fill('How much leave?');await page.getByRole('button',{name:'Ask Question',exact:true}).click();await page.getByText(code===401?(/sign in/i):code===429?(/Too many requests/):code===0?(/fetch|network/i):(/temporarily unavailable/)).last().waitFor();results.push({ui,width:viewport.width,scenario:`http_${code}`,passed:true});}
    }
    assert.deepEqual(errors,[]);await context.close();
   }
  }
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({type:'mocked API UI tests; no answer quality measurement',browser:browser.version(),results},null,2));console.log(`${results.length} UI scenarios passed; 16 before/after screenshots generated.`);
 }finally{if(browser)await browser.close();for(const s of servers)s.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
