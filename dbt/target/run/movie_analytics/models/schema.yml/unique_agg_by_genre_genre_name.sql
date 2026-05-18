
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_aa8f7475b7ac82be6d37ad7ee709f165_11734]
   as 
    
    
    

select
    genre_name as unique_field,
    count(*) as n_records

from "movie_analytics_db"."dbo_dbt_agg"."agg_by_genre"
where genre_name is not null
group by genre_name
having count(*) > 1



  ;')
  select
    
    count(*) as failures,
    case when count(*) != 0
      then 'true' else 'false' end as should_warn,
    case when count(*) != 0
      then 'true' else 'false' end as should_error
  from (
    select * from 
    [dbo].[testview_aa8f7475b7ac82be6d37ad7ee709f165_11734]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_aa8f7475b7ac82be6d37ad7ee709f165_11734]
  ;')