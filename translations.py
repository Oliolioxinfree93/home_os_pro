# translations.py
# All UI text in English and Spanish
# To add more languages, copy the Spanish block and translate

TRANSLATIONS = {
    "en": {
        # App general
        "app_title": "Home OS Pro",
        "app_tagline": "See the real value you bring to your family",
        "sign_in_google": "Continue with Google",
        "sign_out": "🚪 Sign Out",
        "dev_mode": "🛠️ Dev Mode",
        "welcome": "Welcome",
        "built_with_love": "Home OS Pro | Built with ❤️ for stay-at-home parents",

        # Login screen
        "login_track": "**What you'll track:**",
        "login_savings": "💰 Money saved through smart shopping",
        "login_meals": "🍳 Meals cooked vs. eating out",
        "login_waste": "♻️ Food waste prevented",
        "login_impact": "💼 Your monthly household impact",
        "login_private": "Your data is private. Only you can see your fridge.",

        # Sidebar
        "monthly_impact": "💪 Monthly Impact",
        "saved_this_month": "🎉 Saved",
        "add_groceries_prompt": "💡 Add groceries to see your impact!",
        "quick_add": "➕ Quick Add / Scan",

        # Quick add tabs
        "tab_type": "⌨️ Type",
        "tab_barcode": "📱 Barcode",
        "tab_receipt": "📸 Receipt",
        "item_name": "Item Name",
        "quantity": "Quantity",
        "price": "Price ($)",
        "store": "Store (optional)",
        "add_to": "Add to:",
        "fridge": "Fridge",
        "shopping_list": "Shopping List",
        "add_item": "Add Item",
        "added_to_fridge": "✅ Added",
        "added_to_list": "✅ Added to list!",
        "enter_barcode": "Enter UPC/EAN",
        "lookup": "🔍 Lookup",
        "scanning": "Scanning...",
        "found": "Found",
        "not_found": "Not found",
        "add_to_fridge": "Add to Fridge",
        "take_photo": "Take Photo",
        "or_upload": "Or Upload",
        "process_receipt": "🚀 Process Receipt",
        "reading_receipt": "AI reading receipt...",
        "found_items": "Found {} items!",
        "save_selected": "✅ Save Selected",
        "store_name": "Store",

        # Main tabs
        "tab_impact": "💪 My Impact",
        "tab_fridge": "🧊 Fridge",
        "tab_shopping": "🛒 Shopping List",
        "tab_meals": "📅 Meal Planner",
        "tab_recipes": "👨‍🍳 Recipe Rescue",
        "tab_analytics": "📊 Analytics",

        # My Impact tab
        "impact_title": "'s Household Impact",
        "impact_subtitle": "The real economic value you bring to your family every month",
        "this_month_saved": "💰 This Month Saved",
        "direct_cash_retained": "Direct cash retained",
        "meals_cooked": "🍳 Meals Cooked",
        "vs_eating_out": "vs. eating out",
        "annual_projection": "📈 Annual Projection",
        "direct_savings": "**💸 Direct Savings**",
        "meal_planning": "🍳 Meal planning:",
        "smart_shopping": "🛒 Smart shopping:",
        "waste_prevention": "♻️ Waste prevention:",
        "cooked_vs_restaurant": "Cooked meals vs. $35/meal restaurant average",
        "saved_delivery": "Saved on delivery fees",
        "food_saved_expiring": "Value of food saved from expiring",
        "labor_value": "**💼 Labor Value**",
        "chef_services": "👨‍🍳 Chef services:",
        "personal_shopper": "🛒 Personal shopper:",
        "admin_work": "🧮 Admin work:",
        "bottom_line": "🌟 You added ${} in value this month.\n\n📈 Annual projection: ${}",
        "achievements": "🏆 Achievements",
        "waste_warrior": "Waste Warrior",
        "waste_warrior_desc": "Prevented ${} in food waste!",
        "deal_hunter": "Deal Hunter",
        "deal_hunter_desc": "Saved ${} shopping smart!",
        "meal_prep_master": "Meal Prep Master",
        "meal_prep_master_desc": "{} meals cooked!",
        "budget_hero": "Budget Hero",
        "budget_hero_desc": "${} saved!",

        # Fridge tab
        "your_fridge": "🧊 Your Fridge",
        "in_stock": "In Stock",
        "expiring_soon": "Expiring Soon",
        "total_value": "Total Value",
        "frozen": "Frozen",
        "expired_ago": "🔴 Expired {}d ago",
        "expires_in": "🟠 Expires in {}d",
        "good": "🟢 Good ({}d)",
        "fridge_empty": "Your fridge is empty! Add items using the sidebar.",

        # Shopping list tab
        "shopping_list_title": "🛒 Shopping List",
        "items_to_buy": "Items to Buy",
        "got_it": "✅",
        "bought": "✅ Bought",
        "shopping_list_empty": "✅ Shopping list is empty!",

        # Meal planner tab
        "meal_planner_title": "📅 Weekly Meal Planner",
        "week_starting": "Week Starting",
        "add_meal": "➕ Add meal",
        "meal_type": "Type",
        "meal_name": "Meal Name",
        "save": "Save",
        "meal_added": "Meal added!",
        "breakfast": "breakfast",
        "lunch": "lunch",
        "dinner": "dinner",
        "snack": "snack",

        # Recipe rescue tab
        "recipe_rescue_title": "👨‍🍳 Recipe Rescue",
        "recipe_subtitle": "Finds recipes using ingredients expiring soon",
        "find_recipes": "🆘 Find Recipes Using Expiring Food",
        "no_expiring": "No food expiring soon! 🎉",
        "uses": "✨ Uses:",
        "needs": "🛒 Needs:",
        "add_missing": "Add Missing",
        "cook_this": "🔥 Cook This",
        "no_recipes": "No recipes found.",

        # Analytics tab
        "analytics_title": "📊 Analytics",
        "budget_title": "💰 Budget",
        "monthly_budget": "Monthly Budget",
        "spent_this_month": "Spent This Month",
        "remaining": "remaining",
        "update_budget": "⚙️ Update Budget",
        "new_budget": "New Budget ($)",
        "update": "Update",
        "updated": "Updated!",
        "spending_by_category": "📈 Spending by Category",
        "add_purchases": "Add purchases to see breakdown.",
    },

    "es": {
        # App general
        "app_title": "Home OS Pro",
        "app_tagline": "Ve el valor real que aportas a tu familia",
        "sign_in_google": "Continuar con Google",
        "sign_out": "🚪 Cerrar Sesión",
        "dev_mode": "🛠️ Modo Dev",
        "welcome": "Bienvenida",
        "built_with_love": "Home OS Pro | Hecho con ❤️ para padres en casa",

        # Login screen
        "login_track": "**Lo que podrás registrar:**",
        "login_savings": "💰 Dinero ahorrado con compras inteligentes",
        "login_meals": "🍳 Comidas cocinadas vs. comer fuera",
        "login_waste": "♻️ Desperdicio de comida evitado",
        "login_impact": "💼 Tu impacto económico mensual en el hogar",
        "login_private": "Tus datos son privados. Solo tú puedes ver tu refrigerador.",

        # Sidebar
        "monthly_impact": "💪 Impacto Mensual",
        "saved_this_month": "🎉 Ahorrado",
        "add_groceries_prompt": "💡 ¡Agrega víveres para ver tu impacto!",
        "quick_add": "➕ Agregar / Escanear",

        # Quick add tabs
        "tab_type": "⌨️ Escribir",
        "tab_barcode": "📱 Código",
        "tab_receipt": "📸 Recibo",
        "item_name": "Nombre del Producto",
        "quantity": "Cantidad",
        "price": "Precio ($)",
        "store": "Tienda (opcional)",
        "add_to": "Agregar a:",
        "fridge": "Refrigerador",
        "shopping_list": "Lista de Compras",
        "add_item": "Agregar",
        "added_to_fridge": "✅ Agregado",
        "added_to_list": "✅ ¡Agregado a la lista!",
        "enter_barcode": "Ingresar código UPC/EAN",
        "lookup": "🔍 Buscar",
        "scanning": "Buscando...",
        "found": "Encontrado",
        "not_found": "No encontrado",
        "add_to_fridge": "Agregar al Refrigerador",
        "take_photo": "Tomar Foto",
        "or_upload": "O subir imagen",
        "process_receipt": "🚀 Procesar Recibo",
        "reading_receipt": "IA leyendo recibo...",
        "found_items": "¡Se encontraron {} productos!",
        "save_selected": "✅ Guardar Seleccionados",
        "store_name": "Tienda",

        # Main tabs
        "tab_impact": "💪 Mi Impacto",
        "tab_fridge": "🧊 Refrigerador",
        "tab_shopping": "🛒 Lista de Compras",
        "tab_meals": "📅 Plan de Comidas",
        "tab_recipes": "👨‍🍳 Rescate de Recetas",
        "tab_analytics": "📊 Estadísticas",

        # My Impact tab
        "impact_title": " - Impacto en el Hogar",
        "impact_subtitle": "El valor económico real que aportas a tu familia cada mes",
        "this_month_saved": "💰 Ahorrado Este Mes",
        "direct_cash_retained": "Dinero real conservado",
        "meals_cooked": "🍳 Comidas Cocinadas",
        "vs_eating_out": "vs. comer fuera",
        "annual_projection": "📈 Proyección Anual",
        "direct_savings": "**💸 Ahorros Directos**",
        "meal_planning": "🍳 Planificación de comidas:",
        "smart_shopping": "🛒 Compras inteligentes:",
        "waste_prevention": "♻️ Prevención de desperdicio:",
        "cooked_vs_restaurant": "Comidas cocinadas vs. promedio restaurante $35/comida",
        "saved_delivery": "Ahorrado en tarifas de entrega",
        "food_saved_expiring": "Valor de comida salvada de expirar",
        "labor_value": "**💼 Valor del Trabajo**",
        "chef_services": "👨‍🍳 Servicios de chef:",
        "personal_shopper": "🛒 Comprador personal:",
        "admin_work": "🧮 Trabajo administrativo:",
        "bottom_line": "🌟 Aportaste ${} en valor este mes.\n\n📈 Proyección anual: ${}",
        "achievements": "🏆 Logros",
        "waste_warrior": "Guerrera del Ahorro",
        "waste_warrior_desc": "¡Evitaste ${} en desperdicio!",
        "deal_hunter": "Cazadora de Ofertas",
        "deal_hunter_desc": "¡Ahorraste ${} comprando inteligente!",
        "meal_prep_master": "Maestra de Cocina",
        "meal_prep_master_desc": "¡{} comidas cocinadas!",
        "budget_hero": "Heroína del Presupuesto",
        "budget_hero_desc": "¡${} ahorrados!",

        # Fridge tab
        "your_fridge": "🧊 Tu Refrigerador",
        "in_stock": "En Stock",
        "expiring_soon": "Por Vencer",
        "total_value": "Valor Total",
        "frozen": "Congelados",
        "expired_ago": "🔴 Venció hace {}d",
        "expires_in": "🟠 Vence en {}d",
        "good": "🟢 Bien ({}d)",
        "fridge_empty": "¡Tu refrigerador está vacío! Agrega productos desde el menú.",

        # Shopping list tab
        "shopping_list_title": "🛒 Lista de Compras",
        "items_to_buy": "Productos a Comprar",
        "got_it": "✅",
        "bought": "✅ Comprado",
        "shopping_list_empty": "✅ ¡La lista de compras está vacía!",

        # Meal planner tab
        "meal_planner_title": "📅 Plan Semanal de Comidas",
        "week_starting": "Semana que Inicia",
        "add_meal": "➕ Agregar comida",
        "meal_type": "Tipo",
        "meal_name": "Nombre de la Comida",
        "save": "Guardar",
        "meal_added": "¡Comida agregada!",
        "breakfast": "desayuno",
        "lunch": "almuerzo",
        "dinner": "cena",
        "snack": "merienda",

        # Recipe rescue tab
        "recipe_rescue_title": "👨‍🍳 Rescate de Recetas",
        "recipe_subtitle": "Encuentra recetas con ingredientes por vencer",
        "find_recipes": "🆘 Buscar Recetas con Comida por Vencer",
        "no_expiring": "¡No hay comida por vencer pronto! 🎉",
        "uses": "✨ Usa:",
        "needs": "🛒 Necesita:",
        "add_missing": "Agregar Faltantes",
        "cook_this": "🔥 Cocinar Esto",
        "no_recipes": "No se encontraron recetas.",

        # Analytics tab
        "analytics_title": "📊 Estadísticas",
        "budget_title": "💰 Presupuesto",
        "monthly_budget": "Presupuesto Mensual",
        "spent_this_month": "Gastado Este Mes",
        "remaining": "restante",
        "update_budget": "⚙️ Actualizar Presupuesto",
        "new_budget": "Nuevo Presupuesto ($)",
        "update": "Actualizar",
        "updated": "¡Actualizado!",
        "spending_by_category": "📈 Gastos por Categoría",
        "add_purchases": "Agrega compras para ver el desglose.",
    }
}

def get_text(lang, key, *args):
    """Get translated text. Falls back to English if key not found."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if args:
        return text.format(*args)
    return text
