# Establecer el directorio de trabajo (ajusta si estás en otra subcarpeta dentro del proyecto)
setwd("/Users/carloslandaverdealquicirez/Documents/Prometeo_reto/Prometeo_project")

# Cargar librerías necesarias
library(tidyverse)
library(lubridate)
library(ggplot2)

# Cargar archivos desde la ruta correcta
transactions <- read_csv("03.Modelo/data/transactions.csv")
demographics <- read_csv("03.Modelo/data/demographics.csv")
products <- read_csv("03.Modelo/data/products.csv")

#Verificar limpieza de los datos

##Demógraficos

### Ver valores nulos
colSums(is.na(demographics))

### Revisar valores únicos en income_range y risk_profile
unique(demographics$income_range)
unique(demographics$risk_profile)

### Revisar tipos de datos
str(demographics)

##Productos

### Ver valores nulos
colSums(is.na(products))

### Revisar valores únicos en product_type
unique(products$product_type)

### Revisar tipos
str(products)

##Transacciones
### Ver valores nulos
colSums(is.na(transactions))

### Revisar valores únicos en merchant_category
unique(transactions$merchant_category)

### Revisar tipos de datos
str(transactions)

#Analisis univariado

##Demógraficos

### Estadísticas de edad
cat("Media:", mean(demographics$age), "\n")
cat("Mediana:", median(demographics$age), "\n")
cat("Moda:", as.numeric(names(sort(table(demographics$age), decreasing = TRUE)[1])), "\n")
cat("Rango:", range(demographics$age), "\n")
cat("Varianza:", var(demographics$age), "\n")
cat("Desviación estándar:", sd(demographics$age), "\n")

### Grafica de barras de edad
ggplot(demographics, aes(x = factor(age))) +  # convertir edad a factor para barras discretas
  geom_bar(fill = "steelblue") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5, size = 3.5) +
  labs(
    title = "Conteo de Usuarios por Edad",
    x = "Edad",
    y = "Cantidad de Usuarios"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1)  # rota etiquetas si hay muchas edades
  )
### Histograma edad
#### Crear cortes con base en Sturges
breaks <- seq(18, 70, length.out = 9)  # 8 segmentos = 9 puntos de corte
labels <- c("18–24", "25–31", "32–38", "39–45", "46–52", "53–59", "60–66", "67–70")

#### Crear variable de rango de edad
demographics <- demographics %>%
  mutate(age_range_sturges = cut(age, breaks = breaks, labels = labels, right = TRUE, include.lowest = TRUE))

#### Graficar
ggplot(demographics, aes(x = age_range_sturges)) +
  geom_bar(fill = "steelblue") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5, size = 4) +
  labs(
    title = "Distribución de Edad por Rangos (Regla de Sturges)",
    x = "Rango de Edad",
    y = "Cantidad de Usuarios"
  ) +
  theme_minimal()

### income_range
demographics %>%
  count(income_range) %>%
  ggplot(aes(x = income_range, y = n, fill = income_range)) +
  geom_col() +
  geom_text(aes(label = n), vjust = -0.5, size = 4) +  # ← Aquí agregamos las etiquetas
  labs(
    title = "Distribución por Rango de Ingresos",
    x = "Rango de Ingreso",
    y = "Frecuencia"
  ) +
  theme_minimal()

### risk_profile
demographics %>%
  count(risk_profile) %>%
  ggplot(aes(x = risk_profile, y = n, fill = risk_profile)) +
  geom_col() +
  geom_text(aes(label = n), vjust = -0.5, size = 4) +  # ← Etiquetas de conteo
  labs(
    title = "Distribución por Perfil de Riesgo",
    x = "Perfil de Riesgo",
    y = "Frecuencia"
  ) +
  theme_minimal()


###Ocupaciones

ocupaciones_completas <- demographics %>%
  count(occupation, sort = TRUE)

ocupaciones_completas

### Conclusiones: Edad- La media es de 43,39 y moda de 37 años. Se puede observar en el histograma que el mayor número de clientes se encuentra entre los 46 y 59 años. También se agrupa antes de los 38 años un grupo y hay una disminución de clientes entre los 39-5 años. Esto puede significar bimodalidad, aunque no es marcada. El rango de ingreso se concentra en segmentos bajos de 30k a 50k que equivale al 35%, pero si se suman los ingresos de más de 100k representa el 46% lo que quiere decir que hay unsegmento de ingresos altos, mientras los medios no son tan relevantes. Riesgo- En cuanto al riesgo la mayoria tiene un riesgo moderado con 41%, después de riesgo conservador 35% y finalmente de riesgo agresivo el 24%. Esto quiere decir que un segmento alto va por productos más conservadores y seguros. Hay que cruzar estos datos con la edad e ingresos para saber el comportamiento.

## Productos

###verificar si hay productos duplicados por cliente resultado: no hay duplicadoa
products %>%
  group_by(user_id, product_type) %>%
  summarise(n = n()) %>%
  filter(n > 1)

### Número de productos por usuario
productos_por_usuario <- products %>%
  count(user_id, name = "total_productos")

head(productos_por_usuario)

mean(productos_por_usuario$total_productos)

ggplot(productos_por_usuario, aes(x = total_productos)) +
  geom_bar(fill = "steelblue") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5) +
  labs(
    title = "Número de Productos Contratados por Usuario",
    x = "Total de Productos",
    y = "Cantidad de Usuarios"
  ) +
  theme_minimal()

###Grafica productos
products %>%
  count(product_type) %>%
  ggplot(aes(x = reorder(product_type, n), y = n, fill = product_type)) +
  geom_col() +
  geom_text(aes(label = n), vjust = -0.5, size = 4) +
  labs(
    title = "Distribución por Tipo de Producto Contratado",
    x = "Tipo de Producto",
    y = "Frecuencia"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(size = 10),
    plot.title = element_text(face = "bold", size = 14),
    axis.title = element_text(size = 12)
  )

###Linea de tiempo de contratación

products %>%
  mutate(month = floor_date(contract_date, "month")) %>%
  count(month) %>%
  ggplot(aes(x = month, y = n)) +
  geom_line(color = "#00703C", size = 1.2) +
  geom_point(color = "#00703C", size = 2) +
  geom_text(aes(label = n), vjust = -1, size = 3.5) +
  labs(
    title = "Tendencia Mensual de Contratación de Productos",
    x = "Mes",
    y = "Número de Contrataciones"
  ) +
  theme_minimal() +
  scale_x_date(date_labels = "%b %Y", date_breaks = "1 month") +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    plot.title = element_text(face = "bold", size = 14)
  )

###Ventas por año
products %>%
  mutate(anio = year(contract_date)) %>%
  count(anio, name = "ventas_por_anio")

products %>%
  mutate(anio = year(contract_date),
         trimestre = quarter(contract_date)) %>%
  count(anio, trimestre, name = "ventas_por_trimestre") %>%
  arrange(anio, trimestre)

products %>%
  mutate(anio = year(contract_date),
         trimestre = quarter(contract_date),
         periodo_num = anio + (trimestre - 1) / 4,
         periodo = paste0("T", trimestre, " ", anio)) %>%
  count(periodo, periodo_num) %>%
  arrange(periodo_num) %>%
  mutate(periodo = factor(periodo, levels = unique(periodo))) %>%
  ggplot(aes(x = periodo, y = n)) +
  geom_col(fill = "steelblue") +
  geom_text(aes(label = n), vjust = -0.5, size = 4) +
  labs(
    title = "Contrataciones por Trimestre",
    x = "Trimestre",
    y = "Número de Contrataciones"
  ) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

###Conclusiones: -Productos:  El 55% de los clientes tiene contratado 2 productos y 45% con un producto. Esto quiere decir que no hay clientes con más de 3 productos contratados. Algo que cabe señalar que el producto más ocntratado es la cuenta de ahorro(55), posteriormente la cuenta corriente(45). La mayoria de las personas empiezan con una cuenta corriente por lo que es importante mencionarlo. Una hipotesis puede ser que hayan empezado con la cuenta corriente y por lo atractivo o por venta cruzada la mayoria decide contratar una cuenta de ahorros. La otra hipotesis es que la cuenta de ahorro es demásiado atractiva o bien que esta relacionada la cuenta de ahorros con la cuenta corriente. Tambien se puede observar que la tarjeta de crédito es el tercer producto en número de contraciones con 24. Finalmente, los seguros quedan al final con 20 y 11 respectivamente. Es probable que por el nivel de riesgo que hay la balanza este inclinada hacia la cuenta de ahorro, pero cabe destacar que los jovenes que teinen necesidad de un mayor número de créditos por la tepa de su vida es posible que no esten accediendo a ellos pro alguna razón. En cuanto a las contrataciones a lo largo del tiempo se puede ver que hay una alta variabilidad y se contraran entre 1 a 9 productos por mes. Tambien se puede observar que que hubo una tendencia a la alza en 2021 y empezo a disminuir en el 2022. Así mismo se puede observar que el mes de menos venta es diciembre. No se puede aseverar que algun trimestre del año tiene las mejores ventas, ha sido variable.


##Transacciones

###Monto

cat("Media:", mean(transactions$amount), "\n")
cat("Mediana:", median(transactions$amount), "\n")
cat("Moda:", as.numeric(names(sort(table(transactions$amount), decreasing = TRUE)[1])), "\n")
cat("Rango:", range(transactions$amount), "\n")
cat("Varianza:", var(transactions$amount), "\n")
cat("Desviación estándar:", sd(transactions$amount), "\n")

###Histograma monto

breaks <- seq(5.17, 1989.25, length.out = 12)  # 11 rangos = 12 puntos de corte

#### Crear etiquetas
labels <- paste0(
  round(breaks[-length(breaks)]),
  "–",
  round(breaks[-1])
)

#### Crear variable categórica con rangos
transactions <- transactions %>%
  mutate(amount_range = cut(amount, breaks = breaks, labels = labels, include.lowest = TRUE, right = TRUE))

#### Graficar
ggplot(transactions, aes(x = amount_range)) +
  geom_bar(fill = "orange") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5, size = 3.5) +
  labs(
    title = "Distribución de Monto de Transacciones por Rangos",
    x = "Rango de Monto",
    y = "Frecuencia"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    plot.title = element_text(face = "bold", size = 14)
  )


###Grafica gauss monto

media_amount <- mean(transactions$amount)
sd_amount <- sd(transactions$amount)

ggplot(transactions, aes(x = amount)) +
  geom_histogram(aes(y = ..density..), bins = 30, fill = "orange", color = "white", alpha = 0.6) +
  stat_function(fun = dnorm, args = list(mean = media_amount, sd = sd_amount), color = "blue", size = 1.2) +
  labs(
    title = "Distribución Real vs. Curva Normal (Gauss)",
    x = "Monto de Transacción",
    y = "Densidad"
  ) +
  theme_minimal()

##Merchants

transactions %>%
  count(merchant_category) %>%
  ggplot(aes(x = reorder(merchant_category, n), y = n, fill = merchant_category)) +
  geom_col() +
  geom_text(aes(label = n), vjust = -0.5, size = 4) +
  labs(
    title = "Distribución por Categoría de Comercio",
    x = "Categoría",
    y = "Número de Transacciones"
  ) +
  theme_minimal() +
  coord_flip()

## Transacciones

transactions %>%
  mutate(month = floor_date(date, "month")) %>%
  count(month) %>%
  ggplot(aes(x = month, y = n)) +
  geom_line(color = "darkblue", size = 1.2) +
  geom_point(color = "darkblue", size = 2) +
  geom_text(aes(label = n), vjust = -0.8, size = 3.5) +
  labs(
    title = "Tendencia Mensual de Transacciones",
    x = "Mes",
    y = "Número de Transacciones"
  ) +
  theme_minimal() +
  scale_x_date(date_labels = "%b %Y", date_breaks = "2 months") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

transactions %>%
  mutate(anio = lubridate::year(date)) %>%
  count(anio, name = "n_transacciones_anio")

transactions %>%
  mutate(anio = lubridate::year(date),
         trimestre = lubridate::quarter(date)) %>%
  count(anio, trimestre, name = "n_transacciones_trimestre") %>%
  arrange(anio, trimestre)

###Conclusiones: Transacciones - El promedio de las transacciones ed de 15.2 mientras que la mediana es de 95.49. El mayor número de transacciones se da entre los 5 y 186 que representa el 85%. A partir de estos se distribuyen a la derecha y casi no se cuentan con transacciones superiores a los 500. Las categorias que tienen mayor cantidad de transacciones es el supermercado, comida, compras y transporte, en menor. medida entretenimiento, salud y viajes. las 4 primeras representan el 70% del total de las transacciones.El dataset solo contiene transacciones de 2023, en cuanto a estacionalidad la mayoria se da a mitad de año en julio y a final de año en diciembre. El mes que menos hay es agosto. en grandes rasgos se observa que marzo hay un repunte despues cae hasta junio, se recupera en julio y vuelve a carer de agosto a noviembre. Esto puede ser por las temporadas de vacaciones. Habria que hacer el analisis mas detallado.

#Analisis bivariado por dataset

##Demograficos

### Edad vs Ingreso
stats <- demographics %>%
  group_by(income_range) %>%
  summarise(
    mediana_edad = median(age),
    n = n()
  )

ggplot(demographics, aes(x = income_range, y = age)) +
  geom_boxplot(fill = "#87CEFA") +
  geom_text(data = stats, aes(x = income_range, y = mediana_edad, label = paste0("Mediana=", mediana_edad)),
            vjust = -1.5, size = 4.2, fontface = "bold", color = "black") +
  geom_text(data = stats, aes(x = income_range, y = mediana_edad, label = paste0("n=", n)),
            vjust = 1.8, size = 3.8, color = "gray30") +
  labs(
    title = "Edad por Rango de Ingreso",
    x = "Rango de Ingreso",
    y = "Edad"
  ) +
  theme_minimal()

### edad vs ingreso en rangos

tabla_edad_ingreso <- demographics %>%
  count(age_range_sturges, income_range) %>%
  pivot_wider(
    names_from = income_range,
    values_from = n,
    values_fill = 0  # rellena con ceros donde no haya valores
  )

tabla_edad_ingreso

tabla_con_totales <- demographics %>%
  count(age_range_sturges, income_range) %>%
  pivot_wider(
    names_from = income_range,
    values_from = n,
    values_fill = 0
  ) %>%
  mutate(Total = rowSums(select(., where(is.numeric))))

fila_totales <- tabla_con_totales %>%
  select(-age_range_sturges) %>%
  summarise(across(everything(), sum)) %>%
  mutate(age_range_sturges = "Total") %>%
  select(age_range_sturges, everything())

tabla_completa <- bind_rows(tabla_con_totales, fila_totales)

tabla_completa

### Edad vs Perfil de riesgo
stats_risk <- demographics %>%
  group_by(risk_profile) %>%
  summarise(
    mediana_edad = median(age),
    n = n()
  )

ggplot(demographics, aes(x = risk_profile, y = age)) +
  geom_boxplot(fill = "#FFB6C1") +
  geom_text(data = stats_risk, aes(x = risk_profile, y = mediana_edad, label = paste0("Mediana=", mediana_edad)),
            vjust = -1.5, size = 4.2, fontface = "bold", color = "black") +
  geom_text(data = stats_risk, aes(x = risk_profile, y = mediana_edad, label = paste0("n=", n)),
            vjust = 1.8, size = 3.8, color = "gray30") +
  labs(
    title = "Edad por Perfil de Riesgo",
    x = "Perfil de Riesgo",
    y = "Edad"
  ) +
  theme_minimal()

### Edad vs perfil de riesgo en rangos

tabla_edad_riesgo <- demographics %>%
  count(age_range_sturges, risk_profile) %>%
  pivot_wider(
    names_from = risk_profile,
    values_from = n,
    values_fill = 0
  )

tabla_edad_riesgo

tabla_con_totales_riesgo <- demographics %>%
  count(age_range_sturges, risk_profile) %>%
  pivot_wider(
    names_from = risk_profile,
    values_from = n,
    values_fill = 0
  ) %>%
  mutate(Total = rowSums(select(., where(is.numeric))))


fila_totales_riesgo <- tabla_con_totales_riesgo %>%
  select(-age_range_sturges) %>%
  summarise(across(everything(), sum)) %>%
  mutate(age_range_sturges = "Total") %>%
  select(age_range_sturges, everything())


tabla_completa_riesgo <- bind_rows(tabla_con_totales_riesgo, fila_totales_riesgo)


tabla_completa_riesgo

### Ingreso vs Perfil de riesgo
tabla_ingreso_riesgo <- demographics %>%
  count(income_range, risk_profile) %>%
  pivot_wider(
    names_from = risk_profile,
    values_from = n,
    values_fill = 0
  )

tabla_ingreso_riesgo

tabla_con_totales_ingreso_riesgo <- demographics %>%
  count(income_range, risk_profile) %>%
  pivot_wider(
    names_from = risk_profile,
    values_from = n,
    values_fill = 0
  ) %>%
  mutate(Total = rowSums(select(., where(is.numeric))))

fila_totales_ingreso_riesgo <- tabla_con_totales_ingreso_riesgo %>%
  select(-income_range) %>%
  summarise(across(everything(), sum)) %>%
  mutate(income_range = "Total") %>%
  select(income_range, everything())

tabla_completa_ingreso_riesgo <- bind_rows(tabla_con_totales_ingreso_riesgo, fila_totales_ingreso_riesgo)

tabla_completa_ingreso_riesgo


###Conclusiones: Edad-ingreso: Se puede observar en la grafica de caja que los ingresos medios de 50k-100k estan diversificados. Los ingresos más bajos de 30k-50k igual esta ampliamente diversificado por edad, aunque no hay jovenes de menos de 30 años que tengan este ingreso ¿es posible que no esten bancarizados?. Entre estos dos rangos lo que sorprende es que la media de los bajos esta en 48 años y el de medios en 35. Por otro lado los ingresos más altos de más de 150k lo tienen los de edades entre 35 y 50 años principalmente. Cuando se ve la tabla de frecuencias se puede decir que los ingresos no crecen de forma lineal o no hay patrones a simple vista. Se observa que los de mayor ingreo estan entre los 32 y 59 años. También se observa que hay una mayor cantidad de adultos mayores en los ingresos más bajos. mientras los que estan en una edad entre los 52 y 66 tienen una tendencia a tener un ingreso medio alto o alto.

###En cuanto a productos y cross selling las personas jóvenes en el rango de 150k+ podrían estar abiertas a inversiones o tarjetas premium. Usuarios mayores con ingresos bajos pueden requerir productos de bajo riesgo como seguros o ahorro.

### Edad vs riesgo: Se observa que la mayoria tiene un riesgo moderado sin distinción en la edad, es homogeneo con excepción de los 38-45 años, posiblemente la edad donde las personas empiezan a pensar en el retiro en donde deciden tomar una actitud agresiva o pasiva si ya tienen un monto ahorrado. Tambien se puede ver que los de mayor riesgo no son mayores de 60 años. Finalmente los conservadores de igual forma estan distribuidos homogeneamente, pero hay tambien un grupo grande en los ultimos escaños de edad.


### Ingreso vs riesgo: Se puede observar que a mayor ingreso del cliente tiene un perfil de riesgo. Todos los usuarios con ingresos de 150k+ tienen un perfil agresivo.Los de ingresos 30k–50k son 100% conservadores.Quienes ganan entre 100k–150k o 50k–100k son moderados.

##En cuanto a productos a los de más ingresos se les puede vender productos de inversión y a los de bajos ingresos productos más moderados. Inclusive se podria segmentar entre los de más ingresos inversiones.A los jovenes tarjeta de crédito y los de los ultimos escaños ahorro. A los de mediana edad de forma más individualizada y enfoque en los seguros.

###Ocupación vs otras: al ser multiples ocupaciones y tener poca frecuencia decidimos omitir el analisis multivariable con esta variable.


##Producto

### Productos de acuerdo al número de prodcutos contratados
productos_usuario <- products %>%
  count(user_id, name = "total_productos")

products %>%
  left_join(productos_usuario, by = "user_id") %>%
  count(product_type, total_productos) %>%
  ggplot(aes(x = factor(total_productos), y = n, fill = product_type)) +
  geom_col(position = "dodge") +
  geom_text(aes(label = n), position = position_dodge(0.9), vjust = -0.5) +
  labs(
    title = "Tipo de Producto por Número de Productos Contratados",
    x = "Total de Productos del Usuario",
    y = "Cantidad de Usuarios"
  ) +
  theme_minimal()

### productovs año

products %>%
  mutate(year = year(contract_date)) %>%
  count(product_type, year) %>%
  pivot_wider(names_from = year, values_from = n, values_fill = 0)

products %>%
  mutate(year = year(contract_date), q = paste0("T", quarter(contract_date))) %>%
  count(product_type, q) %>%
  pivot_wider(names_from = q, values_from = n, values_fill = 0)


### Conclusiones: Productos de acuerdo al número de prodcutos contratados-se puede observar que los que tienen un solo producto es la cuenta de ahorro o la cuenta corriente 21 y 24 respectivamente. Mientras que los que tienen dos productos en su mayoria tienen cuenta de ahorro y los demás productos. Temporalidad. en cuanto a la temporalidad se puede observar que en 2020 se contrataron solamente cuentas corrientes y cuentas de ahorro. Las cuentas corrientes crecieron en 2021 y disminuyeron drasticamente en 2022. Mientras que las cuentas de ahorro tuvieron un comportamiento similar pero no disminuyeron tanto. Es importante seguir con las cuentas corrientes ya que son el paso para otros productos, especialmente enfocandose en nuevos clientes. Por otro lado las tarjetas de crédito se mantuvieron con 12 contrataciones en 2021 y 2022. Seguros e inversiones se mantienen con un ligero retroseso. 


##Transacciones

### Transacción vs categoria

stats_monto_categoria <- transactions %>%
  group_by(merchant_category) %>%
  summarise(
    mediana_monto = median(amount),
    n = n()
  )

# Boxplot con anotaciones de mediana y tamaño de muestra
ggplot(transactions, aes(x = merchant_category, y = amount)) +
  geom_boxplot(fill = "#FFD700") +
  geom_text(data = stats_monto_categoria, aes(x = merchant_category, y = mediana_monto, label = paste0("Mediana=", round(mediana_monto, 1))),
            vjust = -1.5, size = 4.2, fontface = "bold", color = "black") +
  geom_text(data = stats_monto_categoria, aes(x = merchant_category, y = mediana_monto, label = paste0("n=", n)),
            vjust = 1.8, size = 3.8, color = "gray30") +
  labs(
    title = "Monto de Transacción por Categoría de Comercio",
    x = "Categoría de Comercio",
    y = "Monto"
  ) +
  theme_minimal()

### Tabla de categoria vs monto (rangos)
tabla_monto_categoria <- transactions %>%
  count(amount_range, merchant_category) %>%
  pivot_wider(
    names_from = merchant_category,
    values_from = n,
    values_fill = 0
  )

tabla_monto_categoria <- tabla_monto_categoria %>%
  mutate(Total = rowSums(select(., where(is.numeric))))

fila_total <- tabla_monto_categoria %>%
  select(-amount_range) %>%
  summarise(across(everything(), sum)) %>%
  mutate(amount_range = "Total") %>%
  select(amount_range, everything())

tabla_completa_monto_categoria <- bind_rows(tabla_monto_categoria, fila_total)


tabla_completa_monto_categoria


#Categoria vs mes

transactions %>%
  mutate(month = lubridate::floor_date(date, "month")) %>%
  count(merchant_category, month) %>%
  ggplot(aes(x = month, y = n, color = merchant_category)) +
  geom_line(size = 1.1) +
  geom_point(size = 2) +
  labs(
    title = "Evolución Mensual por Categoría de Comercio",
    x = "Mes",
    y = "Número de Transacciones"
  ) +
  theme_minimal() +
  scale_x_date(date_labels = "%b %Y", date_breaks = "1 month") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))


#promedio categoria

transactions %>%
  group_by(merchant_category) %>%
  summarise(promedio_monto = mean(amount)) %>%
  arrange(desc(promedio_monto))

promedio_mes <- transactions %>%
  mutate(month = floor_date(date, "month")) %>%
  group_by(month, merchant_category) %>%
  summarise(promedio_monto = mean(amount, na.rm = TRUE))


print(promedio_mes)

ggplot(promedio_mes, aes(x = month, y = promedio_monto, color = merchant_category)) +
  geom_line(size = 1) +
  geom_point() +
  labs(
    title = "Promedio Mensual del Monto de Transacción por Categoría",
    x = "Mes",
    y = "Monto Promedio",
    color = "Categoría de Comercio"
  ) +
  scale_x_date(date_labels = "%b %Y", date_breaks = "1 month") +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    plot.title = element_text(face = "bold", size = 14)
  )


###Conclusiones: Monto vs categoria- se observa que los mayores montos de transacciones son de viajes con una mediana de 1034.8, son transacciones de más de 546 pesos la mayoria donde las otras categorias no llegan en cuanto al monto. La de health es otra categoria que se encuentra por encima de las demas con transacciones hasta 546 persos. En cuanto a temporalidad los viajes se disparan en marzo y noviembre seguramente por las vacaciones.No onstante si se ve desde el monto promedio para viajes el mayor es en junio por las vacaciones de verano con transacciones promedio de 1500. Los gastos de shopping tienen alta variabilidad, mientras los de entretenimiento se encuentran constantes. En cuanto al promedio del monto de los gastos todos se mantienen estables con excepción de de los viajes.


# Bivariado joins

##productos vs demograficos

demo_productos <- products %>%
  left_join(demographics, by = "user_id")

### ¿Qué tipo de usuarios contratan inversiones?

inversionistas <- demo_productos %>%
  filter(product_type == "investment_account")

inversionistas %>%
  count(age_range_sturges) %>%
  ggplot(aes(x = age_range_sturges, y = n)) +
  geom_col(fill = "#1f77b4") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Edad de quienes Contratan Inversiones", x = "Rango de Edad", y = "Frecuencia") +
  theme_minimal()

inversionistas %>%
  count(risk_profile) %>%
  ggplot(aes(x = risk_profile, y = n)) +
  geom_col(fill = "#2ca02c") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Perfil de Riesgo en Inversiones", x = "Perfil de Riesgo", y = "Frecuencia") +
  theme_minimal()

inversionistas %>%
  count(income_range) %>%
  ggplot(aes(x = income_range, y = n)) +
  geom_col(fill = "#ff7f0e") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Rango de Ingreso en Inversiones", x = "Rango de Ingreso", y = "Frecuencia") +
  theme_minimal()

###  ¿Qué perfiles prefieren tarjetas de crédito?

creditos <- demo_productos %>%
  filter(product_type == "credit_card")

creditos %>%
  count(age_range_sturges, risk_profile) %>%
  pivot_wider(names_from = risk_profile, values_from = n, values_fill = 0)

creditos %>%
  count(age_range_sturges, income_range) %>%
  pivot_wider(names_from = income_range, values_from = n, values_fill = 0)

ggplot(creditos, aes(x = risk_profile)) +
  geom_bar(fill = "#5DADE2") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5) +
  labs(title = "Perfil de Riesgo que Contratan Tarjeta de Crédito", x = "Perfil", y = "Frecuencia") +
  theme_minimal()

ggplot(creditos, aes(x = age_range_sturges)) +
  geom_bar(fill = "#AED6F1") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5) +
  labs(title = "Edad de los que Contratan Tarjeta de Crédito", x = "Rango de Edad", y = "Frecuencia") +
  theme_minimal()

ggplot(creditos, aes(x = income_range)) +
  geom_bar(fill = "#D6EAF8") +
  geom_text(stat = "count", aes(label = ..count..), vjust = -0.5) +
  labs(title = "Ingreso de los que Contratan Tarjeta de Crédito", x = "Rango de Ingreso", y = "Frecuencia") +
  theme_minimal()

### ¿Qué tipo de perfiles contratan seguros?

asegurados <- demo_productos %>%
  filter(product_type == "insurance")

asegurados %>%
  count(age_range_sturges) %>%
  ggplot(aes(x = age_range_sturges, y = n)) +
  geom_col(fill = "#f39c12") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Edad de Usuarios con Seguro", x = "Rango de Edad", y = "Frecuencia") +
  theme_minimal()

asegurados %>%
  count(risk_profile) %>%
  ggplot(aes(x = risk_profile, y = n)) +
  geom_col(fill = "#c0392b") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Perfil de Riesgo en Seguros", x = "Perfil de Riesgo", y = "Frecuencia") +
  theme_minimal()

asegurados %>%
  count(income_range) %>%
  ggplot(aes(x = income_range, y = n)) +
  geom_col(fill = "#7f8c8d") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Ingreso de Usuarios con Seguro", x = "Rango de Ingreso", y = "Frecuencia") +
  theme_minimal()

### ¿Que perfil de usuario contrata cuenta de ahorro?

ahorradores <- demo_productos %>%
  filter(product_type == "savings_account")

ahorradores %>%
  count(age_range_sturges) %>%
  ggplot(aes(x = age_range_sturges, y = n)) +
  geom_col(fill = "#17becf") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Edad de Usuarios con Cuenta de Ahorro", x = "Rango de Edad", y = "Frecuencia") +
  theme_minimal()

ahorradores %>%
  count(risk_profile) %>%
  ggplot(aes(x = risk_profile, y = n)) +
  geom_col(fill = "#bcbd22") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Perfil de Riesgo en Cuentas de Ahorro", x = "Perfil de Riesgo", y = "Frecuencia") +
  theme_minimal()

ahorradores %>%
  count(income_range) %>%
  ggplot(aes(x = income_range, y = n)) +
  geom_col(fill = "#e377c2") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Ingreso de Usuarios con Cuenta de Ahorro", x = "Rango de Ingreso", y = "Frecuencia") +
  theme_minimal()

###¿Qué perfil de usuario contrata cuenta corriente?

corrientes <- demo_productos %>%
  filter(product_type == "checking_account")

corrientes %>%
  count(age_range_sturges) %>%
  ggplot(aes(x = age_range_sturges, y = n)) +
  geom_col(fill = "#795548") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Edad de Usuarios con Cuenta Corriente", x = "Rango de Edad", y = "Frecuencia") +
  theme_minimal()

corrientes %>%
  count(risk_profile) %>%
  ggplot(aes(x = risk_profile, y = n)) +
  geom_col(fill = "#607d8b") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Perfil de Riesgo en Cuentas Corrientes", x = "Perfil de Riesgo", y = "Frecuencia") +
  theme_minimal()

corrientes %>%
  count(income_range) %>%
  ggplot(aes(x = income_range, y = n)) +
  geom_col(fill = "#9e9e9e") +
  geom_text(aes(label = n), vjust = -0.5) +
  labs(title = "Ingreso de Usuarios con Cuenta Corriente", x = "Rango de Ingreso", y = "Frecuencia") +
  theme_minimal()

###Matriz de procutos por usuario

combinaciones_productos <- products %>%
  group_by(user_id) %>%
  summarise(combinacion = paste(sort(unique(product_type)), collapse = " + ")) %>%
  ungroup()

combinaciones_productos %>%
  count(combinacion, sort = TRUE) %>%
  ggplot(aes(x = reorder(combinacion, n), y = n)) +
  geom_col(fill = "#4CAF50") +
  geom_text(aes(label = n), hjust = -0.1, size = 4) +
  coord_flip() +
  labs(
    title = "Combinación de Productos Contratados por Usuario",
    x = "Combinación de Productos",
    y = "Número de Usuarios"
  ) +
  theme_minimal()

combinaciones_productos %>%
  count(combinacion, sort = TRUE)

###Conclusiones: tarjeta de credito- Los que contratan tarjeta crédito en su mayoria son personas mayores de 46 años. Los menores de 38 contratan menos créditos. En su mayoria los que contratan crédito tienen riesgo moderado. Y a cuanto a ingresos se ve homogeneo. Inversiones- los que contratan inversiones en su mayoria esta de los 46 a 52 años, tiene un perfil agresivo y gana más de 100k. Seguros: Los más jovenes contratan seguro de los 18 hasta los 38 años, tienen un riesgo moderado y algunos con riesgo agresivo, tienen un ingreso mayor a 50k. En otras paabras los del estrato más bajo no contratan seguro. Cuenta de ahorro- Se ve relativamente homogeneo, hay un outlier en el rango de 39-45 años ya que solo 1 persona tiene cuenta de ahorro. Disminuye el número mientras la edad avanza despues de los 52 años.El perfil de riesgo es homogeneo, ligeramente mayor en moderado y conservador.En cuanto a ingresos los de ingresos mas bajos y altos tienen cuenta de ahorro pero no es significativo con respecto a los otros niveles de ingreso.Cuenta corriente- muy similar y homogeneo como la cuenta de ahorro. La mayor parte de lso que tienen cuenta corriente se encuentran entre los 30k y 50k. Combinaciones de productos- la mayores combinaciones de productos es cuenta de ahorro con tarjeta de credito (17) y cuenta de ahorro con seguro (12). Posteriormente, la misma combinación pero con cuenta corriente (8 y 7 respectivamente). Esto quiere decir que despues de contratar uno de los productos principales el cliente va por un crédito o seguro principalmente. Las otras dos combinaciones son inversiones con cuneta corriente e inversiones con cuenta de ahorro con 6 y 5 respectivamente, en tercer lugar se podria decir que el cliente busca invertir.

# ------------------------------------------------------------
# Análisis de usuarios por tipo de producto (Créditos, Inversiones, Seguros)
# ------------------------------------------------------------

# 💳 Tarjetas de Crédito
# - Edad: Más comunes entre 46–66 años, aunque hay usuarios desde los 18.
# - Ingreso: Distribuidos entre 30k–150k; más frecuentes en 100k–150k.
# - Hipótesis: Producto transversal, más relevante en mediana edad con ingresos estables. Útil como entrada para cross selling.

# 📈 Inversiones
# - Edad: Pico en 46–52 años; también presentes desde los 25 hasta los 70.
# - Ingreso: Mayoría en 150k+, seguido de 100k–150k.
# - Riesgo: Predominan perfiles agresivos.
# - Hipótesis: Producto contratado por usuarios maduros, con alto ingreso y tolerancia al riesgo. Ideal para diversificación o retiro.

# 🛡️ Seguros
# - Edad: Distribuidos entre jóvenes (18–38) y adultos (39–66), con ligera concentración en jóvenes.
# - Ingreso: Frecuentes en 100k–150k y 50k–100k.
# - Riesgo: Mayoría con perfil moderado, algunos agresivos.
# - Hipótesis: Producto atractivo para perfiles conscientes del riesgo. Buen complemento para usuarios con tarjeta o ahorro.

# 🧩 Recomendaciones de Cross Selling
# - Créditos + Seguros: Usuarios en mediana edad con crédito pueden buscar protección financiera.
# - Ahorro + Inversiones: Usuarios de ingresos altos pueden interesarse en metas + inversión.
# - Jóvenes con Seguros: Potencial para productos combinados de ahorro y protección.

# -----------------------------------------------------------

##Demograficos vs transacciones

demo_transacciones <- transactions %>%
  left_join(demographics, by = "user_id")


### ingresos vs categoria

demo_transacciones %>%
  count(income_range, merchant_category) %>%
  pivot_wider(names_from = merchant_category, values_from = n, values_fill = 0)

ggplot(demo_transacciones, aes(x = income_range)) +
  geom_bar(aes(fill = merchant_category), position = "dodge") +
  labs(title = "Ingreso vs Categoría de Comercio",
       x = "Rango de Ingreso",
       y = "Frecuencia") +
  theme_minimal()

### edad vs categoria

demo_transacciones %>%
  count(age_range_sturges, merchant_category) %>%
  pivot_wider(names_from = merchant_category, values_from = n, values_fill = 0)

ggplot(demo_transacciones, aes(x = age_range_sturges)) +
  geom_bar(aes(fill = merchant_category), position = "dodge") +
  labs(title = "Edad vs Categoría de Comercio",
       x = "Rango de Edad",
       y = "Frecuencia") +
  theme_minimal()

### Riesgo vs categoria

demo_transacciones %>%
  count(risk_profile, merchant_category) %>%
  pivot_wider(names_from = merchant_category, values_from = n, values_fill = 0)

ggplot(demo_transacciones, aes(x = risk_profile)) +
  geom_bar(aes(fill = merchant_category), position = "dodge") +
  labs(title = "Perfil de Riesgo vs Categoría de Comercio",
       x = "Perfil de Riesgo",
       y = "Frecuencia") +
  theme_minimal()

### Conclusión:

# Ingreso vs Categoría de Comercio
# Los usuarios con ingresos bajos (30k-50k) concentran la mayor cantidad de transacciones, especialmente en supermercados, alimentos y salud.
# A mayor ingreso, se mantiene la importancia del supermercado, pero también aumentan levemente las categorías como transportes y entretenimiento.
# El segmento 150k+ muestra mayor equilibrio entre categorías, aunque siguen dominando supermercado, shopping y transporte.

# Edad vs Categoría de Comercio
# Las edades entre 18 y 45 años gastan más en alimentos, supermercado, transporte y entretenimiento.
# El grupo de 46-52 años tiene un pico importante en supermercado, shopping y salud, lo cual podría reflejar responsabilidades familiares.
# Adultos mayores (60+) mantienen un patrón fuerte en supermercado y salud, con un uso constante del transporte, posiblemente reflejando independencia.

# Perfil de riesgo vs Categoría de Comercio
# Los perfiles moderados y conservadores son quienes más transaccionan, especialmente en supermercado, comida, transporte y shopping.
# Los usuarios con perfil agresivo también tienen comportamiento relevante en shopping y transporte, pero en menor cantidad.
# No se observa una preferencia drástica por categorías de alto gasto (como travel) en perfiles agresivos, lo que podría indicar que el perfil de riesgo no está directamente ligado al consumo impulsivo.

# Implicaciones para estrategias comerciales:
# - Supermercado es transversal a todos los segmentos, ideal para alianzas o recompensas de fidelidad.
# - Jóvenes y usuarios con perfil conservador muestran fuerte interés en transporte y comida: campañas enfocadas en movilidad y delivery pueden funcionar.
# - Perfiles con mayores ingresos podrían recibir promociones más diversificadas (viajes, shopping).
# - Es relevante cruzar con frecuencia de compra y ticket promedio para confirmar el nivel de valor por segmento.


#Categora fav vs insurance

table_insurance_categoria <- table(df_final2$insurance, df_final2$categoria_favorita_monto)
prop_table <- prop.table(table_insurance_categoria, margin = 1)
print(table_insurance_categoria)
print(round(prop_table * 100, 2))  # Porcentajes

df_plot <- df_final2 %>%
  group_by(insurance, categoria_favorita_monto) %>%
  summarise(count = n(), .groups = "drop") %>%
  group_by(insurance) %>%
  mutate(percentage = count / sum(count) * 100)

ggplot(df_plot, aes(x = insurance, y = percentage, fill = categoria_favorita_monto)) +
  geom_bar(stat = "identity", position = "fill") +
  labs(title = "Distribución de categoría favorita según Insurance",
       x = "Tiene seguro",
       y = "Proporción (%)",
       fill = "Categoría favorita") +
  scale_y_continuous(labels = scales::percent_format()) +
  theme_minimal()

#Monto vs Insurance

df_final2 %>%
  group_by(insurance) %>%
  summarise(
    media = mean(monto_promedio_mensual.x, na.rm = TRUE),
    mediana = median(monto_promedio_mensual.x, na.rm = TRUE),
    sd = sd(monto_promedio_mensual.x, na.rm = TRUE),
    n = n()
  )

ggplot(df_final2, aes(x = monto_promedio_mensual.x)) +
  geom_histogram(bins = 30, fill = "skyblue") +
  facet_wrap(~insurance, scales = "free") +
  theme_minimal()

#Porximopasos Feature engineering 


