
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_cc8a02c26e481cf7bbf2896b9b765220_14152]
   as 
    
    
    



select revenue
from "movie_analytics_db"."dbo_dbt_staging"."stg_movies"
where revenue is null



  ;')
  select
    
    count(*) as failures,
    case when count(*) != 0
      then 'true' else 'false' end as should_warn,
    case when count(*) != 0
      then 'true' else 'false' end as should_error
  from (
    select * from 
    [dbo].[testview_cc8a02c26e481cf7bbf2896b9b765220_14152]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_cc8a02c26e481cf7bbf2896b9b765220_14152]
  ;')