
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_cd74ac7d00316e28cdffd5aabc4f46c2_17723]
   as 
    
    
    



select budget
from "movie_analytics_db"."dbo_dbt_staging"."stg_movies"
where budget is null



  ;')
  select
    
    count(*) as failures,
    case when count(*) != 0
      then 'true' else 'false' end as should_warn,
    case when count(*) != 0
      then 'true' else 'false' end as should_error
  from (
    select * from 
    [dbo].[testview_cd74ac7d00316e28cdffd5aabc4f46c2_17723]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_cd74ac7d00316e28cdffd5aabc4f46c2_17723]
  ;')