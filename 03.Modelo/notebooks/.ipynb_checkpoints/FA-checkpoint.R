###############################################################################
# LIBRERÍAS
###############################################################################
library(dplyr)
library(tidyr)
library(lubridate)

# Se asume que ya cuentas con estos data frames cargados:
#   1) demographics (contiene: user_id, age, income_range, risk_profile, occupation, ...)
#   2) products     (contiene: user_id, product_type, contract_date)
#   3) transactions (contiene: transaction_id, user_id, date, amount, merchant_category, ...)

###############################################################################
# 1. PREPARACIÓN DE DEMOGRAPHICS
###############################################################################
# Si tu dataset incluyera 'income' numérico, lo conservarías tal cual.
# Por ejemplo:
# glimpse(demographics)
#  user_id: chr
#  age    : num
#  income : num   (solo si existe)
#  income_range: chr
#  ...

# Dado que 'income_range' ya está en tu dataset, no forzamos una recodificación adicional.
# Puedes convertir 'income_range' en factor si lo deseas (opcional):
# demographics <- demographics %>%
#   mutate(income_range = factor(income_range))

###############################################################################
# 2. PREPARACIÓN DE PRODUCTS
###############################################################################
# 2.1 Convertir los tipos de producto en indicadores binarios (1/0) para cada usuario.

# 1) Normalizamos "investment_account" a "investment" si lo deseas
products_mod <- products %>%
  mutate(
    product_type = ifelse(product_type == "investment_account", "investment", product_type)
  )

# 2) Creamos una tabla ancha con indicadores 1/0 para cada producto.
#    Nota: pivot_wider expandirá filas si hay múltiples productos con diferentes fechas,
#    así que primero generamos un flag, luego en el summarise tomamos el máximo de cada.

products_wide <- products_mod %>%
  mutate(flag = 1) %>%
  pivot_wider(
    names_from  = product_type,
    values_from = flag,
    values_fill = 0
  ) %>%
  group_by(user_id) %>%
  summarise(
    checking_account = max(checking_account, na.rm = TRUE),
    savings_account  = max(savings_account, na.rm = TRUE),
    credit_card      = max(credit_card, na.rm = TRUE),
    insurance        = max(insurance, na.rm = TRUE),
    investment       = max(investment, na.rm = TRUE),
    .groups          = "drop"
  )

# 3) Extraer fechas de primer/segundo producto y calcular métricas asociadas
product_dates <- products_mod %>%
  group_by(user_id) %>%
  arrange(contract_date, .by_group = TRUE) %>%
  summarise(
    primer_producto        = first(product_type),
    fecha_primer_producto  = first(contract_date),
    segundo_producto       = ifelse(n() >= 2, nth(product_type, 2), NA),
    fecha_segundo_producto = ifelse(n() >= 2, as.character(nth(contract_date, 2)), NA),
    .groups               = "drop"
  ) %>%
  mutate(
    fecha_primer_producto  = ymd(fecha_primer_producto),
    fecha_segundo_producto = ymd(fecha_segundo_producto),
    dias_entre_productos   = as.numeric(fecha_segundo_producto - fecha_primer_producto),
    antiguedad_cliente     = as.numeric(Sys.Date() - fecha_primer_producto)
  )

# 4) Juntamos ambas tablas de productos
products_final <- product_dates %>%
  left_join(products_wide, by = "user_id") %>%
  rowwise() %>%
  mutate(
    numero_productos = sum(c_across(c(checking_account, savings_account,
                                      credit_card, insurance, investment))),
    combinacion_productos = paste0(
      paste(
        c(
          ifelse(checking_account == 1, "checking_account", NA),
          ifelse(savings_account  == 1, "savings_account", NA),
          ifelse(credit_card      == 1, "credit_card", NA),
          ifelse(insurance        == 1, "insurance", NA),
          ifelse(investment       == 1, "investment", NA)
        ),
        collapse = " + "
      )
    )
  ) %>%
  ungroup()

###############################################################################
# 3. PREPARACIÓN DE TRANSACTIONS
###############################################################################
# 3.1 Agregaciones por categoría y totales (una fila por usuario)
transactions_agg <- transactions %>%
  group_by(user_id) %>%
  summarise(
    entertainment_count = sum(merchant_category == "entertainment", na.rm = TRUE),
    food_count          = sum(merchant_category == "food", na.rm = TRUE),
    health_count        = sum(merchant_category == "health", na.rm = TRUE),
    shopping_count      = sum(merchant_category == "shopping", na.rm = TRUE),
    supermarket_count   = sum(merchant_category == "supermarket", na.rm = TRUE),
    transport_count     = sum(merchant_category == "transport", na.rm = TRUE),
    travel_count        = sum(merchant_category == "travel", na.rm = TRUE),
    total_transacciones = n(),
    monto_promedio_transaccion = mean(amount, na.rm = TRUE),
    .groups = "drop"
  )

# 3.2 Categoría favorita (mayor número de transacciones)
transactions_agg <- transactions_agg %>%
  rowwise() %>%
  mutate(
    categoria_favorita = names(which.max(
      c(entertainment_count, food_count, health_count, shopping_count,
        supermarket_count, transport_count, travel_count)
    ))
  ) %>%
  ungroup()

# 3.3 Análisis temporal detallado (mensual)
#     - calculamos mes_mas_compras, mes_mayor_monto
#     - monto_promedio_mensual, transacciones_promedio_mensual
#     - y otras métricas opcionales (variaciones mes a mes)

transactions_monthly <- transactions %>%
  mutate(mes = floor_date(date, "month")) %>%
  group_by(user_id, mes) %>%
  summarise(
    monto_mes         = sum(amount, na.rm = TRUE),
    transacciones_mes = n(),
    .groups           = "drop"
  ) %>%
  arrange(user_id, mes)

# Identificamos el mes con más compras y mayor gasto
transactions_monthly_agg <- transactions_monthly %>%
  group_by(user_id) %>%
  summarise(
    mes_mas_compras  = mes[which.max(transacciones_mes)],
    mes_mayor_monto  = mes[which.max(monto_mes)],
    monto_promedio_mensual        = mean(monto_mes, na.rm = TRUE),
    transacciones_promedio_mensual= mean(transacciones_mes, na.rm = TRUE),
    .groups = "drop"
  )

# Opcional: calcular variaciones promedio o tendencia mensual
transactions_trend <- transactions_monthly %>%
  group_by(user_id) %>%
  mutate(
    lag_monto_mes    = lag(monto_mes, 1),
    variacion_monto  = monto_mes - lag_monto_mes,
    variacion_monto_pct = (monto_mes / lag_monto_mes) - 1
  ) %>%
  summarise(
    variacion_mensual_promedio = mean(variacion_monto, na.rm = TRUE),
    variacion_mensual_promedio_pct = mean(variacion_monto_pct, na.rm = TRUE),
    .groups = "drop"
  )

# 3.4 Unión de las partes temporales
transactions_final <- transactions_agg %>%
  left_join(transactions_monthly_agg, by = "user_id") %>%
  left_join(transactions_trend,        by = "user_id")

###############################################################################
# 4. UNIÓN DE TODOS LOS DATASETS (DEMOGRAPHICS + PRODUCTS + TRANSACTIONS)
###############################################################################
df_final <- demographics %>%
  left_join(products_final,     by = "user_id") %>%
  left_join(transactions_final, by = "user_id")

###############################################################################
# 5. VALIDACIÓN FINAL
###############################################################################
# Revisa dimensiones, valores faltantes y consistencia de las variables
glimpse(df_final)
summary(df_final)

# df_final ahora contiene una observación por usuario,
# con variables demográficas, de productos, y de transacciones (incl. métricas temporales).
###############################################################################





write.csv(df_final, "data_1.csv")



### INTERACIÓN 2

###############################################################################
# Supongamos que ya cuentas con:
#  - df_final: DataFrame principal con user_id, fecha_primer_producto, 
#              y las columnas checking_account, savings_account, credit_card,
#              insurance, investment_account.
#  - df_transactions: DataFrame con user_id, date (tipo Date), amount, merchant_category
#
# La meta es: Enriquecer df_final con:
#  1) antiguedad_cliente (al 2024-01-01)
#  2) combinacion_productos forzada a las 8 combinaciones
#  3) categoria_favorita_monto (basado en gasto total)
#  4) variables temporales (mes_mas_compras, mes_mayor_monto, etc.)
#  5) nuevas métricas: recencia, n_meses_activos, HHI, share_fav
###############################################################################

###############################################################################
# 1. CALCULAR LA ANTIGÜEDAD AL 1 DE ENERO DE 2024
###############################################################################
df_final <- df_final %>%
  mutate(
    # Asegúrate de que fecha_primer_producto sea tipo Date.
    # Si no, convierte con as.Date() o ymd():
    # df_final$fecha_primer_producto <- as.Date(df_final$fecha_primer_producto)
    antiguedad_cliente = as.numeric(ymd("2024-01-01") - fecha_primer_producto)
    # antiguedad_cliente estará en días.
    # Si prefieres en meses o años, conviertele la unidad.
  )

###############################################################################
# 2. FORZAR LA COMBINACIÓN DE PRODUCTOS A LAS 8 PREDEFINIDAS
###############################################################################
# Si el usuario NO encaja exactamente en esas 8, se asigna "OTRA_COMBINACION".
# Ajusta los nombres si tus columnas son diferentes (p.ej. "investment" en vez de "investment_account")
df_final <- df_final %>%
  mutate(
    combinacion_productos = case_when(
      checking_account == 1 & savings_account == 0 & credit_card == 0 & insurance == 0 & investment == 0 ~ "checking_account",
      checking_account == 0 & savings_account == 1 & credit_card == 0 & insurance == 0 & investment == 0 ~ "savings_account",
      checking_account == 0 & savings_account == 1 & credit_card == 1 & insurance == 0 & investment == 0 ~ "credit_card + savings_account",
      checking_account == 0 & savings_account == 1 & credit_card == 0 & insurance == 1 & investment == 0 ~ "insurance + savings_account",
      checking_account == 1 & insurance == 1 & savings_account == 0 & credit_card == 0 & investment == 0 ~ "checking_account + insurance",
      checking_account == 1 & credit_card == 1 & savings_account == 0 & insurance == 0 & investment == 0 ~ "checking_account + credit_card",
      checking_account == 1 & investment == 1 & savings_account == 0 & insurance == 0 & credit_card == 0 ~ "checking_account + investment",
      investment == 1 & savings_account == 1 & checking_account == 0 & insurance == 0 & credit_card == 0 ~ "investment + savings_account",
      TRUE ~ "OTRA_COMBINACION"
    )
  )
###############################################################################
# 3. AGREGACIONES TEMPORALES BASADAS EN df_transactions
#    (a) Mes con más compras, mes con mayor monto,
#    (b) monto_promedio_mensual, transacciones_promedio_mensual
#    (c) variacion_mensual_promedio, variacion_mensual_promedio_pct
###############################################################################

# Primero, creamos un dataframe por usuario y mes
transactions_monthly <- transactions %>%
  mutate(mes = floor_date(date, "month")) %>%
  group_by(user_id, mes) %>%
  summarise(
    monto_mes         = sum(amount, na.rm = TRUE),
    transacciones_mes = n(),
    .groups           = "drop"
  )

# Calculamos: mes_mas_compras, mes_mayor_monto, promedios mensuales
df_monthly_summary <- transactions_monthly %>%
  group_by(user_id) %>%
  summarise(
    mes_mas_compras = mes[which.max(transacciones_mes)],
    mes_mayor_monto = mes[which.max(monto_mes)],
    monto_promedio_mensual = mean(monto_mes, na.rm = TRUE),
    transacciones_promedio_mensual = mean(transacciones_mes, na.rm = TRUE),
    .groups = "drop"
  )

# Calculamos variaciones promedio (diferencia y pct) mes a mes
df_trend <- transactions_monthly %>%
  arrange(user_id, mes) %>%
  group_by(user_id) %>%
  mutate(
    lag_monto_mes        = lag(monto_mes, 1),
    variacion_monto      = monto_mes - lag_monto_mes,
    variacion_monto_pct  = (monto_mes / lag_monto_mes) - 1
  ) %>%
  summarise(
    variacion_mensual_promedio     = mean(variacion_monto, na.rm = TRUE),
    variacion_mensual_promedio_pct = mean(variacion_monto_pct, na.rm = TRUE),
    .groups = "drop"
  )

###############################################################################
# 4. NUEVAS MÉTRICAS RELEVANTES:
#    (a) total_spend (gasto total),
#    (b) n_meses_activos (# de meses con transacciones),
#    (c) recencia_transaccion (# días desde última tx a 2024-01-01),
#    (d) HHI (índice de concentración de gasto por categoría),
#    (e) categoría favorita por monto,
#    (f) share_fav (proporción del gasto total en la(s) cat favorita(s)).
###############################################################################

#### 4.1 Agregación a nivel usuario ####
df_user_agg <- transactions %>%
  group_by(user_id) %>%
  summarise(
    total_spend = sum(amount, na.rm = TRUE),
    n_meses_activos = n_distinct(floor_date(date, "month")),
    recencia_transaccion = as.numeric(ymd("2024-01-01") - max(date, na.rm = TRUE)),
    .groups = "drop"
  )

#### 4.2 Cálculo de categoría(s) favorita(s) por MONTO ####
df_cat_monto <- transactions %>%
  group_by(user_id, merchant_category) %>%
  summarise(
    total_spend_cat = sum(amount, na.rm = TRUE),
    .groups = "drop"
  )

# Hallamos el gasto máximo y lo unimos para filtrar la(s) categoría(s) top
df_cat_max <- df_cat_monto %>%
  group_by(user_id) %>%
  summarise(max_spend_cat = max(total_spend_cat, na.rm = TRUE),
            .groups = "drop")

# Obtenemos la(s) categoría(s) favorita(s) (podrían ser varias si hay empate)
df_cat_fav <- df_cat_monto %>%
  inner_join(df_cat_max, by = "user_id") %>%
  filter(total_spend_cat == max_spend_cat) %>%
  group_by(user_id) %>%
  summarise(
    categoria_favorita_monto = paste0(merchant_category, collapse = " + "),
    .groups = "drop"
  )

#### 4.3 Cálculo del HHI (Herfindahl-Hirschman Index) ####
#   Mide la concentración del gasto. A mayor HHI, más concentrado en pocas categorías.
df_cat_concentr <- df_cat_monto %>%
  group_by(user_id) %>%
  mutate(
    user_spend = sum(total_spend_cat, na.rm = TRUE),
    pcat       = total_spend_cat / user_spend,  # proporción de cada categoría
    pcat_sq    = pcat^2
  ) %>%
  summarise(
    hhi = sum(pcat_sq, na.rm = TRUE),
    .groups = "drop"
  )

#### 4.4 Share de la(s) categoría(s) favorita(s) ####
#   Si hay más de una categoría favorita (por empate), sumaremos ambas y la dividimos entre el gasto total.

# Primero, unimos df_cat_fav a df_user_agg para contar con total_spend
df_cat_fav2 <- df_cat_fav %>%
  left_join(df_user_agg %>% select(user_id, total_spend), by = "user_id") 

# Necesitamos sumar el gasto de cada categoría que aparezca en categoria_favorita_monto
# (Puede contener "food + shopping" si hay empate)
compute_sum_for_cats <- function(userid, cat_string) {
  # separa las categorías
  cat_list <- strsplit(cat_string, " + ", fixed = TRUE)[[1]]
  sum(df_cat_monto$total_spend_cat[
    df_cat_monto$user_id == userid & 
      df_cat_monto$merchant_category %in% cat_list
  ], na.rm = TRUE)
}

df_cat_fav2 <- df_cat_fav2 %>%
  rowwise() %>%
  mutate(
    total_spend_fav = compute_sum_for_cats(user_id, categoria_favorita_monto),
    share_fav        = total_spend_fav / total_spend
  ) %>%
  ungroup()

###############################################################################
# 5. UNIMOS TODAS ESTAS NUEVAS MÉTRICAS EN UN SOLO DATAFRAME DE ENRIQUECIMIENTO
###############################################################################
df_enriched <- df_user_agg %>%
  left_join(df_cat_fav2 %>% 
              select(user_id, categoria_favorita_monto, total_spend_fav, share_fav),
            by = "user_id") %>%
  left_join(df_cat_concentr, by = "user_id") %>%
  left_join(df_monthly_summary, by = "user_id") %>%
  left_join(df_trend, by = "user_id")

###############################################################################
# 6. FINALMENTE, UNIMOS df_enriched A df_final
###############################################################################
# Asumimos que df_final y df_enriched comparten user_id y no hay colisiones de nombres.
# Esto agregará todas las columnas nuevas a df_final.
df_final <- df_final %>%
  left_join(df_enriched, by = "user_id")

###############################################################################
# RESULTADO
###############################################################################
# df_final ahora incluye:
#  - antiguedad_cliente (días al 2024-01-01)
#  - combinacion_productos (8 combinaciones o "OTRA_COMBINACION")
#  - métrica mes_mas_compras, mes_mayor_monto,
#    monto_promedio_mensual, transacciones_promedio_mensual,
#    variacion_mensual_promedio, variacion_mensual_promedio_pct
#  - total_spend, n_meses_activos, recencia_transaccion
#  - categoria_favorita_monto (por gasto total) y share_fav
#  - hhi (concentración de gasto)
#
# Revisa la consistencia de tipos, la posible presencia de NA, etc.
# Ajusta lo necesario a tu flujo real, y listo para usarse en modelado o dashboards.
###############################################################################

# Puedes verificar el resultado con:
glimpse(df_final)
summary(df_final)

write.csv(df_final, "data_2.csv")

#ITERACIÓN 3

#Eliminar duplicados

df_final2 <- df_final[ , !(names(df_final) %in% c("mes_mas_compras.y", "mes_mayor_monto.y","monto_promedio_mensual.y","variacion_mensual_promedio.y", "variacion_mensual_promedio_pct.y"))]

write.csv(df_final, "data_3.csv")





