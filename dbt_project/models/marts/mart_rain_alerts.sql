WITH stg AS (
	SELECT
		*
	FROM
		{{ ref('stg_weather') }}
)

SELECT
	weather_date,
	station_name,
	state,
	precipitation_mm,

	CASE
		WHEN precipitation_mm >= 50 THEN 'Chuva Extrema'
		WHEN precipitation_mm >= 30 THEN 'Chuva Forte'
		WHEN precipitation_mm >= 10 THEN 'Chuva Moderada'
		WHEN precipitation_mm > 0 THEN 'Chuva Fraca'
		ELSE 'Sem Chuva'
	END AS rain_category,

	temp_mean_c,
	humidity_max_pct
FROM
	stg
WHERE
	precipitation_mm IS NOT NULL
ORDER BY
	precipitation_mm DESC
