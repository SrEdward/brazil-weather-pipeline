WITH stg AS (
	SELECT
		*
	FROM
		{{ ref('stg_weather') }}
)

SELECT
	state,
	weather_date,

	-- Agregações por estado
	COUNT(station_id)			AS station_count,
	ROUND(AVG(temp_mean_c), 2)		AS avg_temp_c,
	ROUND(MAX(temp_max_c), 2) 		AS max_temp_c,
	ROUND(MIN(temp_min_c), 2)		AS min_temp_c,
	ROUND(AVG(precipitation_mm), 2) 	AS avg_precipitation_mm,
	ROUND(MAX(windspeed_max_kmh), 2)	AS max_windspeed_kmh,
	ROUND(AVG(humidity_max_pct), 2)		AS avg_humidity_pct
FROM
	stg
GROUP BY
	state,
	weather_date
