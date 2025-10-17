(function(){const s=document.createElement("link").relList;if(s&&s.supports&&s.supports("modulepreload"))return;for(const t of document.querySelectorAll('link[rel="modulepreload"]'))n(t);new MutationObserver(t=>{for(const e of t)if(e.type==="childList")for(const o of e.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&n(o)}).observe(document,{childList:!0,subtree:!0});function i(t){const e={};return t.integrity&&(e.integrity=t.integrity),t.referrerPolicy&&(e.referrerPolicy=t.referrerPolicy),t.crossOrigin==="use-credentials"?e.credentials="include":t.crossOrigin==="anonymous"?e.credentials="omit":e.credentials="same-origin",e}function n(t){if(t.ep)return;t.ep=!0;const e=i(t);fetch(t.href,e)}})();async function p(){return await(await fetch("./data.json")).json()}function f(c){const s={};return c.forEach(i=>{!i.bans||!Array.isArray(i.bans)||!i.subjects||!Array.isArray(i.subjects)||i.bans.forEach(n=>{if(!n.state||!n.district)return;const t=n.state,e=n.district;s[t]||(s[t]={districts:{},subjectCounts:{},totalBans:0}),s[t].districts[e]||(s[t].districts[e]={subjectCounts:{},totalBans:0}),i.subjects.forEach(o=>{o&&(s[t].subjectCounts[o]=(s[t].subjectCounts[o]||0)+1,s[t].districts[e].subjectCounts[o]=(s[t].districts[e].subjectCounts[o]||0)+1)}),s[t].totalBans++,s[t].districts[e].totalBans++})}),s}function u(c,s=20){return Object.entries(c).sort((i,n)=>n[1]-i[1]).slice(0,s)}function l(c,s){return`
    <div class="subject-card">
      <div class="subject-name">${c}</div>
      <div class="subject-count">${s}</div>
    </div>
  `}function v(c,s){const i=u(s.subjectCounts,20),n=`district-${c.replace(/\s+/g,"-")}`,t=i.slice(0,10),e=i.slice(10,20);return`
    <div class="district-section">
      <div class="district-header" onclick="toggleSection('${n}')">
        <span class="toggle-icon" id="${n}-icon">▶</span>
        <h3>${c}</h3>
        <div class="district-stats">
          ${s.totalBans} bans • ${i.length} top subjects
        </div>
      </div>
      <div class="subjects-grid collapsed" id="${n}">
        <div class="subjects-column">
          ${t.map(([o,d])=>l(o,d)).join("")}
        </div>
        <div class="subjects-column">
          ${e.map(([o,d])=>l(o,d)).join("")}
        </div>
      </div>
    </div>
  `}function g(c,s){const i=u(s.subjectCounts,20),n=c==="Nation"?"Department of Defense Education Activity":c,t=`state-${c.replace(/\s+/g,"-")}`,e=Object.entries(s.districts).sort((a,r)=>r[1].totalBans-a[1].totalBans),o=i.slice(0,10),d=i.slice(10,20);return`
    <div class="state-section">
      <div class="state-header" onclick="toggleSection('${t}')">
        <span class="toggle-icon" id="${t}-icon">▶</span>
        <h2>${n}</h2>
        <div class="state-stats">
          <span>📚 ${s.totalBans} total bans</span>
          <span>🏫 ${e.length} districts</span>
          <span>📊 ${i.length} top subjects</span>
        </div>
      </div>
      <div class="collapsed" id="${t}">
        <div class="subjects-grid">
          <div class="subjects-column">
            ${o.map(([a,r])=>l(a,r)).join("")}
          </div>
          <div class="subjects-column">
            ${d.map(([a,r])=>l(a,r)).join("")}
          </div>
        </div>
        ${e.map(([a,r])=>v(a,r)).join("")}
      </div>
    </div>
  `}window.toggleSection=function(c){const s=document.getElementById(c),i=document.getElementById(`${c}-icon`);s.classList.toggle("collapsed"),i.classList.toggle("open")};async function j(){const c=document.getElementById("app");c.innerHTML='<div class="loading">Loading data...</div>';try{const s=await p(),i=f(s),n=Object.entries(i).sort((t,e)=>e[1].totalBans-t[1].totalBans);c.innerHTML=`
      <div class="container">
        ${n.map(([t,e])=>g(t,e)).join("")}
      </div>
    `}catch(s){c.innerHTML=`<div class="loading">Error loading data: ${s.message}</div>`}}j();
