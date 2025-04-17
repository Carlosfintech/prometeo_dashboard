# INGENIERIA DE CARACTERISTICAS- GENERACIÓN DE VARIABLES PARA EL MODELO
library(dplyr)
library(tidyr)
library(lubridate)

##Ver plan de variables en el glosario 

## 1. DATASETS

## Los datasets en este caso ya e
##   1) demographics (contiene: user_id, age, income_range, risk_profile, occupation, ...)
##   2) products     (contiene: user_id, product_type, contract_date)
##   3) transactions (contiene: transaction_id, user_id, date, amount, merchant_category, ...)


## 2. PREPARACIÓN DE PRODUCTS

### Cambiamos la variable "investment_account" a "investment" 

products_mod <- products %>%
  mutate(
    product_type = ifelse(product_type == "investment_account", "investment", product_type)
  )

### Se crean variables binarias para cada producto

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

### Extraer fechas de primer/segundo producto y calcular el tiempo transcurrido entre ellos  

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

### Join de productos
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


## 3. PREPARACIÓN DE TRANSACTIONS

### Se hace un count de las transacciones por usuario por categoría
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

#### Categoría favorita (mayor número de transacciones)
transactions_agg <- transactions_agg %>%
  rowwise() %>%
  mutate(
    categoria_favorita = names(which.max(
      c(entertainment_count, food_count, health_count, shopping_count,
        supermarket_count, transport_count, travel_count)
    ))
  ) %>%
  ungroup()

### Análisis temporal detallado
###     - calculamos mes_mas_compras, mes_mayor_monto
###     - monto_promedio_mensual, transacciones_promedio_mensual


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

### Calcular variaciones promedio o tendencia mensual
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

### Join de transacciones
transactions_final <- transactions_agg %>%
  left_join(transactions_monthly_agg, by = "user_id") %>%
  left_join(transactions_trend,        by = "user_id")


## 4. JOIN DE TODOS LOS DATASETS (DEMOGRAPHICS + PRODUCTS + TRANSACTIONS)

df_final <- demographics %>%
  left_join(products_final,     by = "user_id") %>%
  left_join(transactions_final, by = "user_id")


## 5. VALIDACIÓN FINAL


glimpse(df_final)
summary(df_final)


write.csv(df_final, "data_1.csv")


# INTERACIÓN 2 #

# Hay varios errores y se requiere realizar nuevas variables

## 1. Calcular antiguedad del cliente

df_final <- df_final %>%
  mutate(
    antiguedad_cliente = as.numeric(ymd("2024-01-01") - fecha_primer_producto)
  )


## 2. Combinaciones de productos

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

## 3. Calculos de nuevas variables: Mes con más compras, mes con mayor monto, monto_promedio_mensual, transacciones_promedio_mensual, variacion_mensual_promedio, variacion_mensual_promedio_pct


### Dataframe por usuario
transactions_monthly <- transactions %>%
  mutate(mes = floor_date(date, "month")) %>%
  group_by(user_id, mes) %>%
  summarise(
    monto_mes         = sum(amount, na.rm = TRUE),
    transacciones_mes = n(),
    .groups           = "drop"
  )

### Calculo de mes_mas_compras, mes_mayor_monto, promedios mensuales
df_monthly_summary <- transactions_monthly %>%
  group_by(user_id) %>%
  summarise(
    mes_mas_compras = mes[which.max(transacciones_mes)],
    mes_mayor_monto = mes[which.max(monto_mes)],
    monto_promedio_mensual = mean(monto_mes, na.rm = TRUE),
    transacciones_promedio_mensual = mean(transacciones_mes, na.rm = TRUE),
    .groups = "drop"
  )

### Calculo de variaciones promedio (diferencia y pct) mes a mes
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


## 4. Tambien se vab a agregar: total_spend (gasto total), n_meses_activos (# de meses con transacciones),
## recencia_transaccion (# días desde última tx a 2024-01-01), HHI (índice de concentración de gasto por categoría),
## categoría favorita por monto, share_fav (proporción del gasto total en la(s) cat favorita(s)).

#### Agregación a nivel usuario
df_user_agg <- transactions %>%
  group_by(user_id) %>%
  summarise(
    total_spend = sum(amount, na.rm = TRUE),
    n_meses_activos = n_distinct(floor_date(date, "month")),
    recencia_transaccion = as.numeric(ymd("2024-01-01") - max(date, na.rm = TRUE)),
    .groups = "drop"
  )

#### Cálculo de monto por categoria
df_cat_monto <- transactions %>%
  group_by(user_id, merchant_category) %>%
  summarise(
    total_spend_cat = sum(amount, na.rm = TRUE),
    .groups = "drop"
  )

### Gasto máximo
df_cat_max <- df_cat_monto %>%
  group_by(user_id) %>%
  summarise(max_spend_cat = max(total_spend_cat, na.rm = TRUE),
            .groups = "drop")

### Categoria favorita
df_cat_fav <- df_cat_monto %>%
  inner_join(df_cat_max, by = "user_id") %>%
  filter(total_spend_cat == max_spend_cat) %>%
  group_by(user_id) %>%
  summarise(
    categoria_favorita_monto = paste0(merchant_category, collapse = " + "),
    .groups = "drop"
  )

### Cálculo del HHI (Herfindahl-Hirschman Index)
###   Mide la concentración del gasto. A mayor HHI, más concentrado en pocas categorías.
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

#### Share de la(s) categoría(s) favorita(s) 

#### Primero, unimos df_cat_fav a df_user_agg para contar con total_spend
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


## 5. JOIN VARIABLES GENERADAS

df_enriched <- df_user_agg %>%
  left_join(df_cat_fav2 %>% 
              select(user_id, categoria_favorita_monto, total_spend_fav, share_fav),
            by = "user_id") %>%
  left_join(df_cat_concentr, by = "user_id") %>%
  left_join(df_monthly_summary, by = "user_id") %>%
  left_join(df_trend, by = "user_id")


# 6. JOIN DF FINAL Y NUEVA DATA

df_final <- df_final %>%
  left_join(df_enriched, by = "user_id")


# Puedes verificar el resultado con:
glimpse(df_final)
summary(df_final)

write.csv(df_final, "data_2.csv")

#ITERACIÓN 3

##Eliminar duplicados

df_final2 <- df_final[ , !(names(df_final) %in% c("mes_mas_compras.y", "mes_mayor_monto.y","monto_promedio_mensual.y","variacion_mensual_promedio.y", "variacion_mensual_promedio_pct.y"))]

write.csv(df_final, "data_3.csv")





