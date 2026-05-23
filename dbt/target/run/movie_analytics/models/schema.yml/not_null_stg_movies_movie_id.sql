
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_dbc332af2abe16a685c8bc84214e1bc8_16219]
   as 
    
    
    



select movie_id
from "movie_analytics_db"."dbo_dbt_staging"."stg_movies"
where movie_id is null



  ;')
  select
    
    count(*) as failures,
    case when count(*) != 0
      then 'true' else 'false' end as should_warn,
    case when count(*) != 0
      then 'true' else 'false' end as should_error
  from (
    select * from 
    [dbo].[testview_dbc332af2abe16a685c8bc84214e1bc8_16219]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_dbc332af2abe16a685c8bc84214e1bc8_16219]
  ;')