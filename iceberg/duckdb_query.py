import duckdb
import os

from dotenv import load_dotenv


load_dotenv(override=True)

conn = duckdb.connect()

conn.execute(f"""
    SET s3_access_key_id='{os.getenv("AWS_ACCESS_KEY_ID")}';
    SET s3_secret_access_key='{os.getenv("AWS_SECRET_ACCESS_KEY")}';
    SET s3_region='us-east-1';
""")

conn.execute("INSTALL iceberg; LOAD iceberg;")
conn.execute("SET unsafe_enable_version_guessing = true;")

bucket = os.getenv("S3_BUCKET")

# print("\n🌡️ Temperatura média por cidade: ")
# 
# result = conn.execute(f"""
#     SELECT
#         station_name,
#         state,
#         ROUND(AVG(temp_mean_c), 2) AS avg_temp,
#         ROUND(MAX(temp_max_c), 2) AS max_temp,
#         ROUND(MIN(temp_min_c), 2) AS min_temp
#     FROM
#         iceberg_scan('s3://{bucket}/iceberg/brazil_weather.db/weather_data')
#     GROUP BY
#         station_name,
#         state
#     ORDER BY
#         avg_temp DESC;
# """).fetchall()
# 
# for row in result:
#     print(f" {row[0]} ({row[1]}): avg={row[2]}°C max={row[3]}°C min={row[4]}°C")

print("\n Volume total de dados:")

result = conn.execute(f"""
    SELECT
        COUNT(*) AS total_records,
        MIN(weather_date) AS from_date,
        MAX(weather_date) AS to_date,
        COUNT(DISTINCT station_name) AS stations
    FROM
        iceberg_scan('s3://{bucket}/iceberg/brazil_weather.db/weather_data')
""").fetchall()

for row in result:
    print(f"\tTotal: {row[0]} registros | {row[1]} até {row[2]} | {row[3]} cidades")
