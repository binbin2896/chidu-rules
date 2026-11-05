#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从卡片 JSON 生成 markdown 与单文件检索页。"""
import json, html, pathlib, sys

BASE = pathlib.Path(__file__).resolve().parent
src = BASE / (sys.argv[1] if len(sys.argv) > 1 else "vol1-001-010.json")
data = json.loads(src.read_text("utf-8"))
cards = data["cards"]
meta = data["meta"]

# ---------- markdown ----------
md = [f"# {meta['book']} · 规则卡（{meta['range']}）", "",
      f"> {meta['vol_title']}｜{meta['count']} 张｜生成 {meta['generated']}", "",
      meta["note"], "", "---", ""]
for c in cards:
    md += [f"## {c['no']}　{c['title']}", "",
           f"**争点**　{c['question']}", "",
           f"**规则**　{c['rule']}", "",
           f"**判例坐标**　{c['case_main']['name']}｜{c['case_main']['court']}｜{c['case_main']['no']}", "",
           f"**反向坐标**　{c['case_ref']}", "",
           f"**翻转条件**　{c['flip']}", "",
           f"**动作**　{c['action']}", "",
           f"`{'` `'.join(c['tags']['identity'])}`　`{'` `'.join(c['tags']['target'])}`　`{'` `'.join(c['tags']['hinge'])}`　`{c['tags']['newrule']}`", "",
           f"<sub>{c['source_mix']}</sub>", "", "---", ""]
(BASE / f"{src.stem}.md").write_text("\n".join(md), "utf-8")

# ---------- html ----------
def esc(s): return html.escape(str(s))

def card_vals(c, key):
    if key == "vol":
        return [c.get("volume", "")]
    raw = c["tags"][key]
    return raw if isinstance(raw, list) else [raw]

tag_groups = []
for label, key, _ in [
    ("卷次", "vol", None),
    ("身份", "identity", None),
    ("相对方", "target", None),
    ("胜负手", "hinge", None),
    ("新规", "newrule", None),
]:
    seen = []
    for v in meta["tags"].get(key, []):
        if v not in seen:
            seen.append(v)
    for c in cards:
        for v in card_vals(c, key):
            if v and v not in seen:
                seen.append(v)
    tag_groups.append((label, key, seen))

MAXCHIP = 10
filters = []
for label, key, vals in tag_groups:
    def chip(v):
        return f'<button class="chip" data-key="{key}" data-val="{esc(v)}">{esc(v)}</button>'
    head, tail = vals[:MAXCHIP], vals[MAXCHIP:]
    btns = "".join(chip(v) for v in head)
    if tail:
        btns += '<span class="rest" hidden>' + "".join(chip(v) for v in tail) + '</span>'
        btns += f'<button class="chip more" type="button">＋{len(tail)}</button>'
    filters.append(f'<div class="fgroup"><span class="flabel">{label}</span>{btns}</div>')

if not meta.get("subtitle"):
    CN = "一二三四五"
    vols = meta.get("volumes") or [{"vol": meta.get("vol", 1), "title": meta.get("vol_title",""), "range": meta.get("range","")}]
    parts = [f"卷{CN[v['vol']-1]} {v['title']}" for v in vols]
    meta["subtitle"] = "｜".join(parts)
js_cards = json.dumps(cards, ensure_ascii=False)

tpl = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['book'])} · 规则卡</title>
<meta name="description" content="{esc(meta.get('desc',''))}">
<meta property="og:title" content="{esc(meta['book'])} · 规则卡">
<meta property="og:description" content="{esc(meta.get('desc',''))}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(meta.get('url',''))}">
<link rel="canonical" href="{esc(meta.get('url',''))}">
<style>
:root{{--paper:#FAF8F3;--ink:#1C2331;--sub:#6B6A66;--red:#B23A2E;--line:#E2DDD2;--navy:#16233A}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
 font-family:-apple-system,"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif;
 line-height:1.75;-webkit-font-smoothing:antialiased}}
header{{padding:44px 24px 20px;max-width:1080px;margin:0 auto}}
.kicker{{font-size:12px;letter-spacing:.22em;color:var(--red);margin-bottom:14px}}
h1{{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:34px;font-weight:600;margin:0 0 10px;letter-spacing:.02em}}
.sub{{color:var(--sub);font-size:14px}}
.rule{{height:2px;background:var(--red);width:64px;margin:22px 0 0}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px 80px}}
.searchbar{{position:sticky;top:0;background:var(--paper);padding:18px 0 10px;z-index:9;border-bottom:1px solid transparent}}
.searchbar.stuck{{border-bottom-color:var(--line)}}
input[type=search]{{width:100%;padding:13px 16px;font-size:15px;border:1px solid var(--line);
 border-radius:6px;background:#fff;color:var(--ink);outline:none}}
input[type=search]:focus{{border-color:var(--navy)}}
.fgroup{{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-top:10px}}
.flabel{{font-size:12px;color:var(--sub);letter-spacing:.08em;min-width:56px}}
.chip{{font-size:12px;padding:4px 11px;border:1px solid var(--line);border-radius:999px;
 background:#fff;color:var(--sub);cursor:pointer;transition:.15s}}
.chip:hover{{border-color:var(--navy);color:var(--navy)}}
.chip.on{{background:var(--navy);border-color:var(--navy);color:#fff}}
.chip.more{{color:var(--red);border-style:dashed}}
#count{{font-size:12px;color:var(--sub);margin:16px 0 6px;letter-spacing:.06em}}
.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:26px 28px;margin:16px 0;
 box-shadow:0 1px 0 rgba(22,35,58,.03)}}
.chead{{display:flex;align-items:baseline;gap:14px;margin-bottom:4px}}
.no{{font-family:"Songti SC",serif;font-size:13px;color:var(--red);letter-spacing:.1em;min-width:34px}}
.vtag{{font-size:11px;color:var(--sub);border:1px solid var(--line);border-radius:3px;padding:1px 6px;margin-left:auto;white-space:nowrap}}
.card h2{{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:21px;font-weight:600;margin:0;line-height:1.5}}
.q{{color:var(--sub);font-size:14px;margin:6px 0 16px;padding-left:48px}}
.row{{display:flex;gap:12px;margin:10px 0}}
.k{{flex:0 0 68px;font-size:12px;color:var(--red);letter-spacing:.08em;padding-top:3px}}
.v{{font-size:14.5px;flex:1}}
.cite{{font-size:13px;color:var(--sub);font-family:ui-monospace,"SF Mono",Menlo,monospace;line-height:1.7}}
details{{margin:10px 0}}
summary{{cursor:pointer;font-size:12px;color:var(--sub);letter-spacing:.08em;list-style:none}}
summary::-webkit-details-marker{{display:none}}
summary:before{{content:"＋ ";color:var(--red)}}
details[open] summary:before{{content:"－ "}}
details .v{{margin-top:8px;padding-left:0}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin-top:18px;padding-top:14px;border-top:1px dashed var(--line)}}
.t{{font-size:11.5px;color:var(--navy);background:#F1F3F7;padding:2px 9px;border-radius:3px}}
.t.new{{background:#FBF0EE;color:var(--red)}}
.src{{font-size:11.5px;color:#9A988F;margin-top:8px}}
.empty{{text-align:center;color:var(--sub);padding:60px 0;font-size:14px}}
footer{{max-width:1080px;margin:0 auto;padding:32px 24px 60px;border-top:1px solid var(--line);
 font-size:12px;color:var(--sub);line-height:2}}
.fsum{{display:none}}
#fb{{margin:0}}
@media(max-width:640px){{
  .fsum{{display:block;font-size:12.5px;color:var(--sub);padding:10px 0 2px;cursor:pointer;letter-spacing:.04em}}
  .fsum::-webkit-details-marker{{display:none}}
  .fsum:before{{content:"▾ ";color:var(--red)}}
  details[open]>.fsum:before{{content:"▴ "}}
}}
@media(max-width:640px){{h1{{font-size:26px}}.card{{padding:20px 18px}}.q{{padding-left:0}}.row{{flex-direction:column;gap:2px}}.k{{padding-top:0}}}}
@media print{{.searchbar,.tags{{display:none}}.card{{break-inside:avoid;box-shadow:none}}}}
</style></head><body>
<header>
  <div class="kicker">{esc(meta.get('kicker','规 则 卡'))}</div>
  <h1>{esc(meta['book'])}</h1>
  <div class="sub">{esc(meta.get('subtitle') or meta.get('vol_title',''))}｜共 {meta['count']} 张</div>
  <div class="rule"></div>
</header>
<div class="wrap">
  <div class="searchbar" id="sb">
    <input type="search" id="q" placeholder="搜标题、争点、规则、案号、当事人…">
    <details open id="fb"><summary class="fsum">筛选：身份 · 对象 · 胜负手 · 新规</summary>
    {''.join(filters)}
    </details>
  </div>
  <div id="count"></div>
  <div id="list"></div>
</div>
<footer>
  {esc(meta['note'])}<br>
  裁判文书属《著作权法》第五条所称具有司法性质的文件；案例评析出自编写人，本卡片不转录评析原文。<br>
  本作品采用 <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans">{esc(meta.get('license','CC BY-NC-SA 4.0'))}</a> 许可，署名 BINBIN；不构成法律意见，个案请咨询执业律师。<br>
  <a href="{esc(meta.get('repo','#'))}">仓库与更新说明</a>
</footer>
<script>
const DATA = {js_cards};
const on = {{}};
const list = document.getElementById('list');
const q = document.getElementById('q');
const cnt = document.getElementById('count');
function tagsOf(c){{return [c.volume, ...c.tags.identity, ...c.tags.target, ...c.tags.hinge, c.tags.newrule];}}
function render(){{
  const kw = q.value.trim().toLowerCase();
  const active = Object.entries(on).filter(([,v])=>v.size).map(([k,v])=>[k,[...v]]);
  const rows = DATA.filter(c=>{{
    if(active.length){{
      for(const [k,vals] of active){{
        const own = k==='vol'? [c.volume] : (k==='hinge'? c.tags.hinge : (k==='newrule'? [c.tags.newrule] : c.tags[k]));
        if(!vals.some(v=>own.includes(v))) return false;
      }}
    }}
    if(!kw) return true;
    const hay = [c.no,c.title,c.question,c.rule,c.flip,c.action,c.case_main.name,c.case_main.court,c.case_main.no,c.case_ref,...tagsOf(c)].join(' ').toLowerCase();
    return hay.includes(kw);
  }});
  cnt.textContent = `显示 ${{rows.length}} / ${{DATA.length}} 张`;
  if(!rows.length){{list.innerHTML='<div class="empty">没有匹配的卡片。换个关键词，或清掉筛选。</div>';return;}}
  list.innerHTML = rows.map(c=>`
    <article class="card">
      <div class="chead"><span class="no">${{c.no}}</span><h2>${{c.title}}</h2><span class="vtag">${{c.volume}}</span></div>
      <div class="q">${{c.question}}</div>
      <div class="row"><div class="k">规则</div><div class="v">${{c.rule}}</div></div>
      <div class="row"><div class="k">判例</div><div class="v cite">${{c.case_main.name}}<br>${{c.case_main.court}} · ${{c.case_main.no}}</div></div>
      <div class="row"><div class="k">反向</div><div class="v cite">${{c.case_ref}}</div></div>
      <details><summary>翻转条件</summary><div class="v">${{c.flip}}</div></details>
      <details><summary>可以立即去做的事</summary><div class="v">${{c.action}}</div></details>
      <div class="tags">
        ${{c.tags.identity.map(t=>`<span class="t">${{t}}</span>`).join('')}}
        ${{c.tags.target.map(t=>`<span class="t">告：${{t}}</span>`).join('')}}
        <span class="t">胜负手：${{c.tags.hinge.join(' · ')}}</span>
        <span class="t new">${{c.tags.newrule}}</span>
      </div>
      <div class="src">${{c.source_mix}}</div>
    </article>`).join('');
}}
document.addEventListener('click', e=>{{
  const chip = e.target.closest('.chip');
  if(!chip) return;
  if(chip.classList.contains('more')){{
    const box = chip.closest('.fgroup');
    const rest = box.querySelector('.rest');
    if(rest) rest.hidden = false;
    chip.remove();
    return;
  }}
  const k = chip.dataset.key, v = chip.dataset.val;
  if(!k || v === undefined) return;
  on[k] = on[k] || new Set();
  if(on[k].has(v)){{ on[k].delete(v); chip.classList.remove('on'); }}
  else {{ on[k].add(v); chip.classList.add('on'); }}
  render();
}});
q.addEventListener('input',render);
addEventListener('scroll',()=>document.getElementById('sb').classList.toggle('stuck',scrollY>40));
if(matchMedia('(max-width:640px)').matches) document.getElementById('fb').open=false;
render();
</script></body></html>"""
(BASE / "index.html").write_text(tpl, "utf-8")
print("ok", len(cards), "cards ->", BASE / "index.html")
