
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_062e40897f5e4f29c7481095bbf4d433_11156]
   as 
    
    
    

select
    genre_name as unique_field,
    count(*) as n_records

from "movie_analytics_db"."dbo_dbt_dim"."dim_genre"
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
    [dbo].[testview_062e40897f5e4f29c7481095bbf4d433_11156]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_062e40897f5e4f29c7481095bbf4d433_11156]
  ;')