"""名片 HTML 模板（两套）：暖色手作风 / 暗色科技风。{{field}} 占位符替换。"""

WARM = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft YaHei","PingFang SC",sans-serif}
body{width:750px;height:1334px;background:linear-gradient(160deg,#FFF6EC 0%,#FFE8D6 100%);position:relative;overflow:hidden}
.deco{position:absolute;border-radius:50%;opacity:.35}
.d1{width:420px;height:420px;background:#FFD8B0;top:-140px;right:-120px}
.d2{width:260px;height:260px;background:#FFE3C8;bottom:-80px;left:-60px}
.wrap{position:relative;padding:72px 60px;height:100%;display:flex;flex-direction:column}
.emoji{font-size:64px}
.name{font-size:76px;font-weight:800;color:#3D2B1F;margin-top:18px;letter-spacing:2px}
.tagline{font-size:34px;color:#8A6A4F;margin-top:14px;line-height:1.5}
.divider{width:96px;height:8px;border-radius:4px;background:linear-gradient(90deg,#FF6B35,#F7B32B);margin:38px 0 34px}
.sec{font-size:26px;color:#B08558;letter-spacing:6px;margin-bottom:16px;font-weight:700}
.tags{display:flex;flex-wrap:wrap;gap:14px}
.tag{background:#fff;border:2px solid #F3C99A;color:#7A5230;font-size:28px;padding:10px 26px;border-radius:999px}
.svc{background:rgba(255,255,255,.75);border-radius:18px;padding:20px 26px;margin-bottom:16px}
.svc .t{font-size:30px;font-weight:700;color:#4A3320}
.svc .d{font-size:24px;color:#9B7B5E;margin-top:6px}
.spacer{flex:1}
.contact{background:#3D2B1F;border-radius:20px;padding:26px 30px;color:#F7E3CC}
.contact .row{font-size:27px;margin:6px 0;display:flex;align-items:center;gap:12px}
.footer{text-align:center;color:#C9A583;font-size:22px;margin-top:26px;letter-spacing:2px}
</style></head><body>
<div class="deco d1"></div><div class="deco d2"></div>
<div class="wrap">
  <div class="emoji">{{emoji}}</div>
  <div class="name">{{name}}</div>
  <div class="tagline">{{tagline}}</div>
  <div class="divider"></div>
  <div class="sec">我 擅 长</div>
  <div class="tags">{{strength_tags}}</div>
  <div style="height:30px"></div>
  <div class="sec">我 提 供</div>
  {{service_cards}}
  <div class="spacer"></div>
  <div class="contact">{{contact_rows}}</div>
  <div class="footer">🏪 由「托摆」生成 · 一人公司工作台</div>
</div></body></html>"""

DARK = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft YaHei","PingFang SC",sans-serif}
body{width:750px;height:1334px;background:linear-gradient(165deg,#0F1222 0%,#1A1F3A 60%,#232A4D 100%);position:relative;overflow:hidden}
.glow{position:absolute;width:520px;height:520px;border-radius:50%;filter:blur(90px);opacity:.4}
.g1{background:#5B6CFF;top:-160px;right:-100px}
.g2{background:#00C9A7;bottom:-140px;left:-120px;opacity:.25}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:52px 52px}
.wrap{position:relative;padding:72px 60px;height:100%;display:flex;flex-direction:column}
.emoji{font-size:64px}
.name{font-size:76px;font-weight:800;color:#F2F5FF;margin-top:18px;letter-spacing:2px}
.tagline{font-size:34px;color:#9AA5D1;margin-top:14px;line-height:1.5}
.divider{width:96px;height:8px;border-radius:4px;background:linear-gradient(90deg,#5B6CFF,#00C9A7);margin:38px 0 34px}
.sec{font-size:26px;color:#6B77A8;letter-spacing:6px;margin-bottom:16px;font-weight:700}
.tags{display:flex;flex-wrap:wrap;gap:14px}
.tag{background:rgba(91,108,255,.14);border:2px solid rgba(91,108,255,.45);color:#B9C3FF;font-size:28px;padding:10px 26px;border-radius:999px}
.svc{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:20px 26px;margin-bottom:16px}
.svc .t{font-size:30px;font-weight:700;color:#EAF0FF}
.svc .d{font-size:24px;color:#8E99C7;margin-top:6px}
.spacer{flex:1}
.contact{background:linear-gradient(90deg,rgba(91,108,255,.2),rgba(0,201,167,.2));border:1px solid rgba(91,108,255,.4);border-radius:20px;padding:26px 30px}
.contact .row{font-size:27px;margin:6px 0;color:#D9DFFF;display:flex;align-items:center;gap:12px}
.footer{text-align:center;color:#5B6491;font-size:22px;margin-top:26px;letter-spacing:2px}
</style></head><body>
<div class="glow g1"></div><div class="glow g2"></div><div class="grid"></div>
<div class="wrap">
  <div class="emoji">{{emoji}}</div>
  <div class="name">{{name}}</div>
  <div class="tagline">{{tagline}}</div>
  <div class="divider"></div>
  <div class="sec">我 擅 长</div>
  <div class="tags">{{strength_tags}}</div>
  <div style="height:30px"></div>
  <div class="sec">我 提 供</div>
  {{service_cards}}
  <div class="spacer"></div>
  <div class="contact">{{contact_rows}}</div>
  <div class="footer">🏪 由「托摆」生成 · 一人公司工作台</div>
</div></body></html>"""

TEMPLATES = {"warm": WARM, "dark": DARK}


def fill(tpl: str, *, emoji: str, name: str, tagline: str,
         strengths: list[str], services: list[dict], contacts: list[str]) -> str:
    strength_tags = "".join(f'<span class="tag">{s}</span>' for s in strengths[:6])
    service_cards = "".join(
        f'<div class="svc"><div class="t">▸ {s.get("name","")}</div>'
        f'<div class="d">{s.get("desc","")}</div></div>'
        for s in services[:4])
    contact_rows = "".join(f'<div class="row">{c}</div>' for c in contacts)
    return (tpl.replace("{{emoji}}", emoji).replace("{{name}}", name)
            .replace("{{tagline}}", tagline)
            .replace("{{strength_tags}}", strength_tags)
            .replace("{{service_cards}}", service_cards)
            .replace("{{contact_rows}}", contact_rows))
