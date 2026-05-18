
  
    USE [movie_analytics_db];
    USE [movie_analytics_db];
    
    

    

    
    USE [movie_analytics_db];
    EXEC('
        create view "dbo_dbt_agg"."agg_by_genre__dbt_tmp__dbt_tmp_vw" as -- Aggregation model: műfajonkénti összesítés
WITH fact AS (
    SELECT * FROM "movie_analytics_db"."dbo_dbt_fact"."fact_movies"
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
GROUP BY g.genre_name;
    ')

EXEC('
            SELECT * INTO "movie_analytics_db"."dbo_dbt_agg"."agg_by_genre__dbt_tmp" FROM "movie_analytics_db"."dbo_dbt_agg"."agg_by_genre__dbt_tmp__dbt_tmp_vw" 
    OPTION (LABEL = ''dbt-sqlserver'');

        ')

    
    EXEC('DROP VIEW IF EXISTS dbo_dbt_agg.agg_by_genre__dbt_tmp__dbt_tmp_vw')



    
    


  