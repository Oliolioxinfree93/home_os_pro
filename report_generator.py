# report_generator.py
# Generates a beautiful shareable monthly report as HTML

def generate_monthly_report(user_name, savings, lang='en'):
    """
    Returns an HTML string for the monthly report.
    Can be displayed in browser, downloaded, or printed as PDF.
    """

    month_label = __import__('datetime').date.today().strftime('%B %Y')
    chef_value = savings['meals_cooked'] * 35
    shopper_value = savings['shopping_trips'] * 10
    admin_value = 100.0
    total_value = chef_value + shopper_value + admin_value
    annual = total_value * 12

    if lang == 'es':
        title = "Reporte Mensual del Hogar"
        subtitle = "Tu contribución económica este mes"
        direct_savings_label = "Ahorros Directos"
        labor_value_label = "Valor del Trabajo"
        total_impact_label = "Impacto Total"
        annual_label = "Proyección Anual"
        meals_label = "comidas cocinadas"
        trips_label = "compras realizadas"
        meal_s = "Planificación de comidas"
        shop_s = "Compras inteligentes"
        waste_s = "Prevención de desperdicio"
        chef_s = "Servicios de chef"
        shopper_s = "Comprador personal"
        admin_s = "Trabajo administrativo"
        footer_text = "Generado con Home OS Pro"
        prepared_by = "Preparado por"
    else:
        title = "Monthly Household Report"
        subtitle = "Your economic contribution this month"
        direct_savings_label = "Direct Savings"
        labor_value_label = "Labor Value"
        total_impact_label = "Total Impact"
        annual_label = "Annual Projection"
        meals_label = "meals cooked"
        trips_label = "shopping trips"
        meal_s = "Meal planning"
        shop_s = "Smart shopping"
        waste_s = "Waste prevention"
        chef_s = "Chef services"
        shopper_s = "Personal shopper"
        admin_s = "Admin & budget"
        footer_text = "Generated with Home OS Pro"
        prepared_by = "Prepared by"

    first_name = user_name.split()[0] if user_name else "You"

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,600;1,300&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'DM Sans', sans-serif;
    background: #FAF7F2;
    color: #2C2C2C;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }}
  .card {{
    background: white;
    border-radius: 24px;
    max-width: 600px;
    width: 100%;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(44,44,44,0.12);
  }}
  .header {{
    background: #2D5016;
    padding: 2.5rem 2.5rem 2rem;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: rgba(200,149,42,0.15);
    border-radius: 50%;
  }}
  .header::after {{
    content: '';
    position: absolute;
    bottom: -60px; left: 40%;
    width: 150px; height: 150px;
    background: rgba(122,158,95,0.1);
    border-radius: 50%;
  }}
  .logo {{ color: #C8952A; font-size: 0.8rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem; }}
  .header h1 {{
    font-family: 'Fraunces', serif;
    color: white;
    font-size: 1.8rem;
    font-weight: 600;
    line-height: 1.2;
    position: relative; z-index: 1;
  }}
  .header .month {{
    color: rgba(250,247,242,0.7);
    font-size: 0.9rem;
    margin-top: 0.4rem;
    position: relative; z-index: 1;
  }}
  .prepared {{ color: rgba(250,247,242,0.6); font-size: 0.8rem; margin-top: 0.3rem; position: relative; z-index: 1; }}

  .hero {{
    background: linear-gradient(135deg, #f0f7eb 0%, #e8f5d8 100%);
    padding: 2rem 2.5rem;
    text-align: center;
    border-bottom: 1px solid #E8E4DE;
  }}
  .hero-amount {{
    font-family: 'Fraunces', serif;
    font-size: 3.5rem;
    color: #2D5016;
    font-weight: 600;
    line-height: 1;
  }}
  .hero-label {{
    color: #6B6B6B;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.4rem;
    font-weight: 500;
  }}
  .hero-sub {{
    color: #7A9E5F;
    font-size: 0.9rem;
    margin-top: 0.6rem;
  }}

  .body {{ padding: 2rem 2.5rem; }}

  .section-title {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6B6B6B;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #E8E4DE;
  }}

  .line-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid #F5F2EE;
  }}
  .line-item:last-child {{ border-bottom: none; }}
  .line-name {{ font-size: 0.9rem; color: #2C2C2C; }}
  .line-value {{ font-family: 'Fraunces', serif; font-size: 1rem; color: #2D5016; font-weight: 600; }}

  .section {{ margin-bottom: 1.8rem; }}

  .stats-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.8rem;
  }}
  .stat-box {{
    background: #FAF7F2;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid #E8E4DE;
  }}
  .stat-number {{
    font-family: 'Fraunces', serif;
    font-size: 1.5rem;
    color: #2D5016;
    font-weight: 600;
  }}
  .stat-label {{ font-size: 0.78rem; color: #6B6B6B; margin-top: 0.2rem; }}

  .annual-box {{
    background: #2D5016;
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.8rem;
  }}
  .annual-label {{ color: rgba(250,247,242,0.7); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }}
  .annual-value {{ font-family: 'Fraunces', serif; font-size: 2rem; color: #C8952A; font-weight: 600; }}

  .footer {{
    background: #FAF7F2;
    padding: 1.2rem 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #E8E4DE;
  }}
  .footer-brand {{ font-family: 'Fraunces', serif; color: #2D5016; font-size: 0.9rem; font-weight: 600; }}
  .footer-date {{ color: #6B6B6B; font-size: 0.78rem; }}

  @media print {{
    body {{ background: white; padding: 0; }}
    .card {{ box-shadow: none; border-radius: 0; }}
  }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="logo">🏠 Home OS Pro</div>
    <h1>{title}</h1>
    <div class="month">{month_label}</div>
    <div class="prepared">{prepared_by} {first_name}</div>
  </div>

  <div class="hero">
    <div class="hero-amount">${total_value:,.2f}</div>
    <div class="hero-label">{total_impact_label}</div>
    <div class="hero-sub">
      {savings['meals_cooked']} {meals_label} &nbsp;·&nbsp; {savings['shopping_trips']} {trips_label}
    </div>
  </div>

  <div class="body">

    <div class="stats-row">
      <div class="stat-box">
        <div class="stat-number">${savings['total_monthly_savings']:,.2f}</div>
        <div class="stat-label">{direct_savings_label}</div>
      </div>
      <div class="stat-box">
        <div class="stat-number">${chef_value + shopper_value + admin_value:,.2f}</div>
        <div class="stat-label">{labor_value_label}</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">{direct_savings_label}</div>
      <div class="line-item">
        <span class="line-name">🍳 {meal_s}</span>
        <span class="line-value">${savings['meal_planning_savings']:,.2f}</span>
      </div>
      <div class="line-item">
        <span class="line-name">🛒 {shop_s}</span>
        <span class="line-value">${savings['smart_shopping_savings']:,.2f}</span>
      </div>
      <div class="line-item">
        <span class="line-name">♻️ {waste_s}</span>
        <span class="line-value">${savings['food_waste_prevention']:,.2f}</span>
      </div>
    </div>

    <div class="section">
      <div class="section-title">{labor_value_label}</div>
      <div class="line-item">
        <span class="line-name">👨‍🍳 {chef_s}</span>
        <span class="line-value">${chef_value:,.2f}</span>
      </div>
      <div class="line-item">
        <span class="line-name">🛒 {shopper_s}</span>
        <span class="line-value">${shopper_value:,.2f}</span>
      </div>
      <div class="line-item">
        <span class="line-name">🧮 {admin_s}</span>
        <span class="line-value">${admin_value:,.2f}</span>
      </div>
    </div>

    <div class="annual-box">
      <div>
        <div class="annual-label">{annual_label}</div>
      </div>
      <div class="annual-value">${annual:,.0f}</div>
    </div>

  </div>

  <div class="footer">
    <div class="footer-brand">Home OS Pro</div>
    <div class="footer-date">{footer_text} · {month_label}</div>
  </div>
</div>
</body>
</html>"""

    return html
