
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_990441e5efcfb88b09b39f4bde9f7303_10675]
   as 
    
    
    



select revenue
from "movie_analytics_db"."dbo_dbt_fact"."fact_movies"
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
    [dbo].[testview_990441e5efcfb88b09b39f4bde9f7303_10675]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_990441e5efcfb88b09b39f4bde9f7303_10675]
  ;')