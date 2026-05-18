
  
    USE [movie_analytics_db];
    USE [movie_analytics_db];
    
    

    

    
    USE [movie_analytics_db];
    EXEC('
        create view "dbo_dbt_dim"."dim_genre__dbt_tmp__dbt_tmp_vw" as -- Dimension model: műfajok
WITH genres AS (
    SELECT DISTINCT
        genre_name
    FROM dbo.Dim_Genre
    WHERE genre_name IS NOT NULL
      AND genre_name != ''Unknown''
)

SELECT
    genre_name,
    GETDATE() AS dbt_updated_at
FROM genres;
    ')

EXEC('
            SELECT * INTO "movie_analytics_db"."dbo_dbt_dim"."dim_genre__dbt_tmp" FROM "movie_analytics_db"."dbo_dbt_dim"."dim_genre__dbt_tmp__dbt_tmp_vw" 
    OPTION (LABEL = ''dbt-sqlserver'');

        ')

    
    EXEC('DROP VIEW IF EXISTS dbo_dbt_dim.dim_genre__dbt_tmp__dbt_tmp_vw')



    
    


  