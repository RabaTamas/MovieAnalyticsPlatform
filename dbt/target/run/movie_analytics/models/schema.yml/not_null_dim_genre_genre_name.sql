
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_ea5da786afb56e17e362a848c793d62a_15615]
   as 
    
    
    



select genre_name
from "movie_analytics_db"."dbo_dbt_dim"."dim_genre"
where genre_name is null



  ;')
  select
    
    count(*) as failures,
    case when count(*) != 0
      then 'true' else 'false' end as should_warn,
    case when count(*) != 0
      then 'true' else 'false' end as should_error
  from (
    select * from 
    [dbo].[testview_ea5da786afb56e17e362a848c793d62a_15615]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_ea5da786afb56e17e362a848c793d62a_15615]
  ;')