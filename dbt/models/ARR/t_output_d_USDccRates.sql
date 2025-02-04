{{ config(
          tags=['tag_dbt_test']
         ) }}

select * from 
{{ref('t_seed_d_USDccRates')}} 

