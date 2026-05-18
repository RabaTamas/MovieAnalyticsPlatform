
    
    

select
    genre_name as unique_field,
    count(*) as n_records

from "movie_analytics_db"."dbo_dbt_dim"."dim_genre"
where genre_name is not null
group by genre_name
having count(*) > 1


