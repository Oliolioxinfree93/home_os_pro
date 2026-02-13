# fridge_animation.py
# Animated fridge and pantry visuals rendered as HTML components

def get_fridge_animation(items_data, lang='en'):
    """
    Returns HTML for an animated fridge door that opens to reveal contents.
    items_data: list of dicts with item_name, days_left, category
    """
    empty_msg = "Your fridge is empty!" if lang == 'en' else "¡Tu refrigerador está vacío!"
    
    # Build item pills grouped by expiry status
    urgent, good, frozen = [], [], []
    for item in items_data[:20]:  # cap at 20 for visual
        name = item.get('item_name', '').title()[:18]
        days = item.get('days_left', 99)
        storage = item.get('storage', 'fresh')
        if storage == 'frozen':
            frozen.append(f'<span class="item-pill frozen">❄️ {name}</span>')
        elif days < 0:
            urgent.append(f'<span class="item-pill expired">⚠️ {name}</span>')
        elif days < 4:
            urgent.append(f'<span class="item-pill expiring">🟠 {name}</span>')
        else:
            good.append(f'<span class="item-pill fresh">✓ {name}</span>')

    all_items_html = ''.join(urgent + good + frozen) if items_data else f'<span class="empty-msg">{empty_msg}</span>'

    shelf_label_1 = "Expiring Soon" if lang == 'en' else "Por Vencer"
    shelf_label_2 = "Fresh" if lang == 'en' else "Frescos"
    shelf_label_3 = "Frozen" if lang == 'en' else "Congelados"

    urgent_html = ''.join(urgent) if urgent else '<span class="empty-shelf">—</span>'
    good_html = ''.join(good) if good else '<span class="empty-shelf">—</span>'
    frozen_html = ''.join(frozen) if frozen else '<span class="empty-shelf">—</span>'

    return f"""<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    display: flex;
    justify-content: center;
    padding: 10px;
  }}

  .scene {{
    position: relative;
    width: 380px;
    height: 320px;
    perspective: 800px;
  }}

  /* ── FRIDGE BODY ── */
  .fridge-body {{
    position: absolute;
    width: 100%;
    height: 100%;
    background: linear-gradient(160deg, #e8e8e8 0%, #d0d0d0 100%);
    border-radius: 16px;
    border: 3px solid #b8b8b8;
    box-shadow: 4px 4px 20px rgba(0,0,0,0.2), inset 2px 2px 6px rgba(255,255,255,0.5);
    overflow: hidden;
  }}

  /* ── FRIDGE INTERIOR ── */
  .fridge-interior {{
    position: absolute;
    inset: 8px;
    background: linear-gradient(180deg, #f0f8f0 0%, #e8f4e8 100%);
    border-radius: 10px;
    padding: 10px;
    opacity: 0;
    animation: fadeInInterior 0.5s ease 0.6s forwards;
  }}

  .shelf {{
    margin-bottom: 8px;
    border-bottom: 2px solid rgba(0,0,0,0.08);
    padding-bottom: 6px;
  }}
  .shelf:last-child {{ border-bottom: none; }}
  .shelf-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #888;
    font-weight: 600;
    margin-bottom: 4px;
  }}
  .shelf-items {{ display: flex; flex-wrap: wrap; gap: 3px; min-height: 22px; }}

  /* ── ITEM PILLS ── */
  .item-pill {{
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 20px;
    font-weight: 500;
    white-space: nowrap;
  }}
  .item-pill.fresh    {{ background: #e8f5e9; color: #2D5016; border: 1px solid #c8e6c9; }}
  .item-pill.expiring {{ background: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; }}
  .item-pill.expired  {{ background: #ffeaea; color: #c62828; border: 1px solid #ffcdd2; }}
  .item-pill.frozen   {{ background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }}
  .empty-shelf        {{ font-size: 10px; color: #bbb; font-style: italic; }}
  .empty-msg          {{ font-size: 12px; color: #aaa; font-style: italic; }}

  /* ── DOOR ── */
  .door-container {{
    position: absolute;
    width: 100%;
    height: 100%;
    transform-origin: left center;
    transform-style: preserve-3d;
    animation: openDoor 1s cubic-bezier(0.4, 0, 0.2, 1) 0.2s forwards;
  }}

  .door-front {{
    position: absolute;
    width: 100%;
    height: 100%;
    background: linear-gradient(160deg, #f5f5f5 0%, #e0e0e0 50%, #d5d5d5 100%);
    border-radius: 14px;
    border: 3px solid #c0c0c0;
    box-shadow: 3px 0 15px rgba(0,0,0,0.15);
    backface-visibility: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 12px;
  }}

  .door-handle {{
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    width: 10px;
    height: 60px;
    background: linear-gradient(90deg, #c8952a, #e0a830, #c8952a);
    border-radius: 5px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.3);
  }}

  .door-brand {{
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #555;
    letter-spacing: 0.05em;
    text-align: center;
  }}
  .door-icon {{ font-size: 36px; }}

  /* ── ANIMATIONS ── */
  @keyframes openDoor {{
    0%   {{ transform: rotateY(0deg); }}
    80% {{ transform: rotateY(-92deg); }}
    100% {{ transform: rotateY(-88deg); }}
  }}

  @keyframes fadeInInterior {{
    0%   {{ opacity: 0; }}
    100% {{ opacity: 1; }}
  }}
</style>
</head>
<body>
<div class="scene">
  <!-- Interior revealed when door opens -->
  <div class="fridge-body">
    <div class="fridge-interior">
      <div class="shelf">
        <div class="shelf-label">⚠️ {shelf_label_1}</div>
        <div class="shelf-items">{urgent_html}</div>
      </div>
      <div class="shelf">
        <div class="shelf-label">✓ {shelf_label_2}</div>
        <div class="shelf-items">{good_html}</div>
      </div>
      <div class="shelf">
        <div class="shelf-label">❄️ {shelf_label_3}</div>
        <div class="shelf-items">{frozen_html}</div>
      </div>
    </div>
  </div>

  <!-- Door swings open -->
  <div class="door-container">
    <div class="door-front">
      <div class="door-icon">🏠</div>
      <div class="door-brand">Home OS Pro</div>
      <div class="door-handle"></div>
    </div>
  </div>
</div>
</body>
</html>"""


def get_pantry_animation(items_data, lang='en'):
    """
    Returns HTML showing a pantry shelf visualization.
    """
    empty_msg = "Your pantry is empty!" if lang == 'en' else "¡Tu despensa está vacía!"
    add_msg = "Add items with storage type 'pantry'" if lang == 'en' else "Agrega productos con tipo de almacenamiento 'despensa'"

    # Group pantry items by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for item in items_data:
        cat = item.get('category', 'Other')
        name = item.get('item_name', '').title()[:16]
        days = item.get('days_left', 999)
        by_category[cat].append((name, days))

    if not by_category:
        shelves_html = f'<div class="empty-pantry"><div class="empty-icon">🏺</div><div>{empty_msg}</div><div class="empty-sub">{add_msg}</div></div>'
    else:
        shelves_html = ''
        shelf_colors = ['#8B4513','#6B3410','#7A3D12','#5C2E0A','#9B5523']
        for i, (category, items) in enumerate(by_category.items()):
            color = shelf_colors[i % len(shelf_colors)]
            items_html = ''
            for name, days in items[:8]:
                if days < 0:
                    icon, style = '⚠️', 'border: 2px solid #ff6b6b;'
                elif days < 14:
                    icon, style = '🟡', 'border: 2px solid #ffa94d;'
                else:
                    icon, style = '', ''
                items_html += f'''
                <div class="pantry-item" style="{style}">
                    <div class="item-icon">{icon or "📦"}</div>
                    <div class="item-name">{name}</div>
                </div>'''
            shelves_html += f'''
            <div class="shelf-unit">
                <div class="shelf-board" style="background: linear-gradient(180deg, {color}dd, {color}99);">
                    <span class="cat-label">{category}</span>
                </div>
                <div class="shelf-contents">{items_html}</div>
                <div class="shelf-shadow"></div>
            </div>'''

    return f"""<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'DM Sans', sans-serif;
    background: transparent;
    padding: 10px;
  }}

  .pantry-scene {{
    background: linear-gradient(180deg, #f5efe6 0%, #ede4d8 100%);
    border-radius: 16px;
    border: 2px solid #d4c4b0;
    padding: 16px;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.06);
    animation: pantryReveal 0.5s ease forwards;
  }}

  .pantry-header {{
    text-align: center;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #8B7355;
    font-weight: 600;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #d4c4b0;
  }}

  /* ── SHELF UNITS ── */
  .shelf-unit {{
    margin-bottom: 16px;
    animation: slideInShelf 0.4s ease backwards;
  }}
  .shelf-unit:nth-child(1) {{ animation-delay: 0.1s; }}
  .shelf-unit:nth-child(2) {{ animation-delay: 0.2s; }}
  .shelf-unit:nth-child(3) {{ animation-delay: 0.3s; }}
  .shelf-unit:nth-child(4) {{ animation-delay: 0.4s; }}

  .shelf-board {{
    border-radius: 6px 6px 0 0;
    padding: 5px 10px;
    display: flex;
    align-items: center;
  }}
  .cat-label {{
    font-size: 10px;
    font-weight: 600;
    color: rgba(255,255,255,0.9);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}

  .shelf-contents {{
    background: rgba(255,255,255,0.5);
    border: 1px solid rgba(0,0,0,0.06);
    border-top: none;
    padding: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    min-height: 52px;
  }}

  .shelf-shadow {{
    height: 5px;
    background: linear-gradient(180deg, rgba(0,0,0,0.08), transparent);
    border-radius: 0 0 4px 4px;
  }}

  /* ── PANTRY ITEMS ── */
  .pantry-item {{
    background: white;
    border-radius: 8px;
    border: 1.5px solid #e8e0d6;
    padding: 5px 8px;
    text-align: center;
    min-width: 60px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    transition: transform 0.15s ease;
  }}
  .pantry-item:hover {{ transform: translateY(-2px); }}
  .item-icon {{ font-size: 16px; line-height: 1.3; }}
  .item-name {{ font-size: 9px; color: #555; font-weight: 500; margin-top: 2px; }}

  /* ── EMPTY STATE ── */
  .empty-pantry {{
    text-align: center;
    padding: 30px 20px;
    color: #9B8B7A;
  }}
  .empty-icon {{ font-size: 40px; margin-bottom: 10px; }}
  .empty-pantry div {{ font-size: 13px; font-weight: 500; }}
  .empty-sub {{ font-size: 11px; color: #b5a898; margin-top: 6px; }}

  /* ── ANIMATIONS ── */
  @keyframes pantryReveal {{
    from {{ opacity: 0; transform: scale(0.97); }}
    to   {{ opacity: 1; transform: scale(1); }}
  }}
  @keyframes slideInShelf {{
    from {{ opacity: 0; transform: translateX(-12px); }}
    to   {{ opacity: 1; transform: translateX(0); }}
  }}
</style>
</head>
<body>
<div class="pantry-scene">
  <div class="pantry-header">🏺 {'Pantry' if lang == 'en' else 'Despensa'}</div>
  {shelves_html}
</div>
</body>
</html>"""
