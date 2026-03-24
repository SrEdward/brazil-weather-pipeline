WITH source AS (
	SELECT
		*
	FROM
		{{ source('staging', 'RAW_WEATHER') }}
),
renamed AS (
	SELECT
		-- Identifiers
		STATION_ID			AS station_id,
		STATION_NAME 			AS station_name,
		STATE				AS state,

		-- Geography
		LATITUDE			AS latitude,
		LONGITUDE			AS longitude,

		-- Date
		DATE				AS weather_date,

		-- Temperature (Celsius)
		TEMP_MAX			AS temp_max_c,
		TEMP_MIN			AS temp_min_c,
		TEMP_MEAN			AS temp_mean_c,

		-- Precipitation
		PRECIPITATION_MM		AS precipitation_mm,

		-- Wind
		WINDSPEED_MAX			AS windspeed_max_kmh,

		-- Humidity
		HUMIDITY_MAX			AS humidity_max_pct,
		HUMIDITY_MIN			AS humidity_min_pct,

		-- Metadata
		EXTRACTED_AT			AS extracted_at,
		_LOADED_AT			AS loaded_at
	FROM
		source
)

SELECT
	*
FROM
	renamed
