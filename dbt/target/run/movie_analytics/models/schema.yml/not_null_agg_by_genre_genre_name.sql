
    
    -- Create target schema if it does not
  USE [movie_analytics_db];
  IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
  BEGIN
    EXEC('CREATE SCHEMA [dbo]')
  END

  

  
  EXEC('create view 
    [dbo].[testview_11ac1716407836e9688097eef99249f7_18788]
   as 
    
    
    



select genre_name
from "movie_analytics_db"."dbo_dbt_agg"."agg_by_genre"
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
    [dbo].[testview_11ac1716407836e9688097eef99249f7_18788]
  
  ) dbt_internal_test;

  EXEC('drop view 
    [dbo].[testview_11ac1716407836e9688097eef99249f7_18788]
  ;')