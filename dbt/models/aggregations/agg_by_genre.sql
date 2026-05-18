-- Aggregation model: műfajonkénti összesítés
WITH fact AS (
    SELECT * FROM {{ ref('fact_movies') }}
),

genres AS (
    SELECT genre_id, genre_name FROM dbo.Dim_Genre
)

SELECT
    g.genre_name,
    COUNT(DISTINCT f.movie_id)    AS total_films,
    SUM(f.revenue)                AS total_revenue,
    SUM(f.budget)                 AS total_budget,
    AVG(f.revenue)                AS avg_revenue,
    AVG(f.budget)                 AS avg_budget,
    AVG(f.roi)                    AS avg_roi,
    AVG(f.vote_average)           AS avg_rating,
    GETDATE()                     AS last_updated
FROM fact f
LEFT JOIN genres g ON g.genre_id = f.genre_id
GROUP BY g.genre_name