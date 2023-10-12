{% materialization my_materialization_table, default %}

  {%- set existing_relation = load_cached_relation(this) -%}
  {%- set target_relation = this.incorporate(type='table') %}

   

  {%- set target_relation_new =  make_intermediate_relation(target_relation,'20230626') -%}


  {{ log("==============0", info=True) }}
   {%-  set partition_key= config.get('partition_key') -%}
     {{ log(partition_key, info=True) }}
 



   {{ log("==============1", info=True) }}
       {{ log(target_relation_new.name, info=True) }}




  {%- set intermediate_relation =  make_intermediate_relation(target_relation_new) -%}
  -- the intermediate_relation should not already exist in the database; get_relation
  -- will return None in that case. Otherwise, we get a relation that we can drop
  -- later, before we try to use this name for the current operation
  {%- set preexisting_intermediate_relation = load_cached_relation(intermediate_relation) -%}

       {{ log(models_to_generate, info=True) }}


  /*
      See ../view/view.sql for more information about this relation.
  */
  {%- set backup_relation_type = 'table' if existing_relation is none else existing_relation.type -%}

   {{ log("==============2", info=True) }}
       {{ log(backup_relation_type, info=True) }}



  {%- set backup_relation = make_backup_relation(target_relation_new, backup_relation_type) -%}
  -- as above, the backup_relation should not already exist
  {%- set preexisting_backup_relation = load_cached_relation(backup_relation) -%}
  -- grab current tables grants config for comparision later on
  {% set grant_config = config.get('grants') %}

  -- drop the temp relations if they exist already in the database
  {{ drop_relation_if_exists(preexisting_intermediate_relation) }}
  {{ drop_relation_if_exists(preexisting_backup_relation) }}
  

  {{ run_hooks(pre_hooks, inside_transaction=False) }}

  -- `BEGIN` happens here:
  {{ run_hooks(pre_hooks, inside_transaction=True) }}

  -- build model
  {% call statement('main') -%}
    {{ get_create_table_as_sql(False, intermediate_relation, sql) }}
       {{ log(sql, info=True) }}
       {{ log("==============", info=True) }}
       {{ log(intermediate_relation, info=True) }}
  {%- endcall %}

  -- cleanup
  {% if existing_relation is not none %}
      {{ adapter.rename_relation(existing_relation, backup_relation) }}
  {% endif %}

  {{ adapter.rename_relation(intermediate_relation, target_relation_new) }}

  {% do create_indexes(target_relation_new) %}

  {{ run_hooks(post_hooks, inside_transaction=True) }}

  {% set should_revoke = should_revoke(existing_relation, full_refresh_mode=True) %}
  {% do apply_grants(target_relation_new, grant_config, should_revoke=should_revoke) %}

  {% do persist_docs(target_relation_new, model) %}

  -- `COMMIT` happens here
  {{ adapter.commit() }}

  -- finally, drop the existing/backup relation after the commit
  {{ drop_relation_if_exists(backup_relation) }}

  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation_new]}) }}
{% endmaterialization %}