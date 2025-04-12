Glosario de Variables en df_1

1. **`user_id`**  
   - Identificador único del usuario.

2. **`age`**  
   - Edad numérica del usuario.

3. **`income_range`**  
   - Rango de ingresos declarado/estimado (p. ej. “30k-50k”, “100k-150k”).

4. **`risk_profile`**  
   - Perfil de riesgo (conservative, moderate, aggressive, etc.).

5. **`occupation`**  
   - Ocupación laboral.

6. **`age_range_sturges`**  
   - Intervalo de edad categórico calculado con la regla de Sturges.

7. **`primer_producto`**, **`fecha_primer_producto`**  
   - Nombre del primer producto financiero contratado y su fecha de contratación.

8. **`segundo_producto`**, **`fecha_segundo_producto`**  
   - Segundo producto contratado y su fecha.

9. **`dias_entre_productos`**  
   - Diferencia (en días) entre la fecha del primer y el segundo producto.

10. **`antiguedad_cliente`**  
   - Días desde la contratación del primer producto hasta 2024-01-01.

11. **`checking_account`, `savings_account`, `credit_card`, `insurance`, `investment`**  
   - Indicadores binarios (0/1) que señalan si el usuario posee cada tipo de producto.

12. **`numero_productos`**  
   - Conteo total de productos contratados.

13. **`combinacion_productos`**  
   - Categoría de combinación (hasta 8 patrones posibles + “OTRA_COMBINACION”).

14. **`entertainment_count`, `food_count`, `health_count`, `shopping_count`, `supermarket_count`, `transport_count`, `travel_count`**  
   - Conteo de transacciones en cada categoría de gasto.

15. **`total_transacciones`**  
   - Número total de transacciones del usuario.

16. **`monto_promedio_transaccion`**  
   - Promedio monetario por transacción.

17. **`mes_mas_compras`, `mes_mayor_monto`**  
   - Mes con mayor número de transacciones y mes con mayor gasto total, respectivamente.

18. **`monto_promedio_mensual`, `transacciones_promedio_mensual`**  
   - Promedios de gasto y de transacciones mensuales.

19. **`variacion_mensual_promedio`, `variacion_mensual_promedio_pct`**  
   - Promedio de la variación (absoluta y relativa) del gasto mes a mes.

20. **`n_meses_activos`**  
   - Número de meses en que el usuario tuvo al menos una transacción.

21. **`total_spend`**  
   - Suma total del gasto realizado por el usuario a lo largo del histórico disponible.

22. **`recencia_transaccion`**  
   - Días desde la última transacción registrada hasta 2024-01-01.  
   - Un valor alto sugiere posible inactividad reciente.

23. **`categoria_favorita_monto`**  
   - Categoría (o categorías, separadas por “+”) con mayor gasto total para el usuario.

24. **`share_fav`**  
   - Proporción del gasto total que representa la(s) categoría(s) favorita(s).  
   - Oscila entre 0 y 1 (0%–100%).

25. **`hhi`** *(Herfindahl-Hirschman Index)*  
   - Índice de concentración del gasto por categoría (∑(proporción²)).  
   - Va de un valor cercano a 0 (distribuido en muchas categorías) hasta 1 (totalmente concentrado).

---

## Nuevas variables

- **`recencia_transaccion`**: Indispensable para *churn prediction* y segmentar usuarios según su inactividad reciente.  
- **`hhi`**: Mide cuán concentrado está el gasto de un usuario. Quienes concentran la mayoría de su gasto en una sola categoría podrían ser candidatos a cross-selling específico (por ejemplo, si gasta todo en “food”, ofrecer beneficios de supermercado/tarjeta de débito con descuentos).  
- **`share_fav`**: Compara el gasto de la(s) categoría(s) favorita(s) vs. el gasto total. Si es alto (por ejemplo, 70%), el usuario tiene comportamiento focalizado, lo cual es relevante para una campaña de marketing focal.