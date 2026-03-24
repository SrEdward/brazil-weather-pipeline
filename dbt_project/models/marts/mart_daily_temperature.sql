WITH stg AS (
	SELECT
		*
	FROM
		{{ ref('stg_weather') }}
)

SELECT
	weather_date,
	state,
	station_name,

	-- Temperaturas
	temp_max_c,
	temp_min_c,
	temp_mean_c,

	-- Amplitude térmica do dia
	ROUND(temp_max_c - temp_min_c, 2) AS temp_range_c,

	-- Classificação de temperatura
	CASE
		WHEN temp_mean_c >= 30 THEN 'Muito Quente'
		WHEN temp_mean_c >= 25 THEN 'Quente'
		WHEN temp_mean_c >= 18 THEN 'Agradável'
		WHEN temp_mean_c >= 10 THEN 'Frio'
		ELSE 'Muito Frio'
	END AS temp_category,

	precipitation_mm,
	windspeed_max_kmh,
	humidity_max_pct,
	humidity_min_pct
FROM
	stg
