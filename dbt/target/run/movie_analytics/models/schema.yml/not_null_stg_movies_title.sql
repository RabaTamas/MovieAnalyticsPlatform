
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_551195a0daa2c4d070aeb2c5c7a09cf0_7401]
   as 
    
    
    



select title
from "movie_analytics_db"."dbo_dbt_staging"."stg_movies"
where title is null



  ;')
  select
    
    count(*) as failures,
    case when count(*) != 0
      then 'true' else 'false' end as should_warn,
    case when count(*) != 0
      then 'true' else 'false' end as should_error
  from (
    select * from 
    [dbo].[testview_551195a0daa2c4d070aeb2c5c7a09cf0_7401]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_551195a0daa2c4d070aeb2c5c7a09cf0_7401]
  ;')