-- Dimension model: műfajok
WITH genres AS (
    SELECT DISTINCT
        genre_name
    FROM dbo.Dim_Genre
    WHERE genre_name IS NOT NULL
      AND genre_name != 'Unknown'
)

SELECT
    genre_name,
    GETDATE() AS dbt_updated_at
FROM genres