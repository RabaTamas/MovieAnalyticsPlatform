
  
    USE [movie_analytics_db];
    USE [movie_analytics_db];
    
    

    

    
    USE [movie_analytics_db];
    EXEC('
        create view "dbo_dbt_fact"."fact_movies__dbt_tmp__dbt_tmp_vw" as -- Fact model: filmek ténytábla
WITH staging AS (
    SELECT * FROM "movie_analytics_db"."dbo_dbt_staging"."stg_movies"
),

genres AS (
    SELECT genre_id, genre_name FROM dbo.Dim_Genre
),

times AS (
    SELECT time_id, full_date FROM dbo.Dim_Time
),

studios AS (
    SELECT studio_id, studio_name FROM dbo.Dim_Studio
)

SELECT
    s.movie_id,
    s.title,
    g.genre_id,
    t.time_id,
    st.studio_id,
    s.budget,
    s.revenue,
    s.profit,
    s.roi,
    s.runtime,
    s.vote_average,
    s.vote_count,
    s.popularity,
    s.original_language,
    GETDATE() AS dbt_updated_at
FROM staging s
LEFT JOIN genres g
    ON g.genre_name = LEFT(s.genres, CHARINDEX(''-'', s.genres + ''-'') - 1)
LEFT JOIN times t
    ON t.full_date = CAST(s.release_date AS DATE)
LEFT JOIN studios st
    ON st.studio_name = LEFT(s.production_companies, CHARINDEX(''-'', s.production_companies + ''-'') - 1);
    ')

EXEC('
            SELECT * INTO "movie_analytics_db"."dbo_dbt_fact"."fact_movies__dbt_tmp" FROM "movie_analytics_db"."dbo_dbt_fact"."fact_movies__dbt_tmp__dbt_tmp_vw" 
    OPTION (LABEL = ''dbt-sqlserver'');

        ')

    
    EXEC('DROP VIEW IF EXISTS dbo_dbt_fact.fact_movies__dbt_tmp__dbt_tmp_vw')



    
    


  