{% macro get_models(directory=None, prefix=None) %}
    {% set model_names=[] %}
    {% set models = graph.nodes.values() | selectattr('resource_type', "equalto", 'model') %}
    {% if directory and prefix %}
        {% for model in models %}
            {% set model_path = "/".join(model.path.split("/")[:-1]) %}
            {% if model_path == directory and model.name.startswith(prefix) %}
                {% do model_names.append(model.name) %}
            {% endif %} 
        {% endfor %}
    {% elif directory %}
        {% for model in models %}
            {% set model_path = "/".join(model.path.split("/")[:-1]) %}
            {% if model_path == directory %}
                {% do model_names.append(model.name) %}
            {% endif %}
        {% endfor %}
    {% elif prefix %}
        {% for model in models if model.name.startswith(prefix) %}
            {% do model_names.append(model.name) %}
        {% endfor %}
    {% else %}
        {% for model in models %}
            {% do model_names.append(model.name) %}
        {% endfor %}
    {% endif %}
    {{ return(model_names) }}
{% endmacro %}





{% macro generate_column_yaml(column, model_yaml, column_desc_dict, parent_column_name="") %}
    {% if parent_column_name %}
        {% set column_name = parent_column_name ~ "." ~ column.name %}
    {% else %}
        {% set column_name = column.name %}
    {% endif %}

    {% do model_yaml.append('      - name: ' ~ column_name  | lower ) %}
    {% do model_yaml.append('        description: "' ~ column_desc_dict.get(column.name | lower,'') ~ '"') %}
    {% do model_yaml.append('') %}

    {% if column.fields|length > 0 %}
        {% for child_column in column.fields %}
            {% set model_yaml = codegen.generate_column_yaml(child_column, model_yaml, column_desc_dict, parent_column_name=column_name) %}
        {% endfor %}
    {% endif %}
    {% do return(model_yaml) %}
{% endmacro %}


{% macro test_generate_model_yaml(model_names=[], upstream_descriptions=False) %}

    {% set models_to_generate = get_models(directory='marts/core') %}

    {% set model_yaml=[] %}



    {% set model_yaml=[] %}

    {% do model_yaml.append('version: 2') %}
    {% do model_yaml.append('') %}
    {% do model_yaml.append('models:') %}

    {% if model_names is string %}
        {{ exceptions.raise_compiler_error("The `model_names` argument must always be a list, even if there is only one model.") }}
    {% else %}
        {% for model in model_names %}
            {% do model_yaml.append('  - name: ' ~ model | lower) %}
            {% do model_yaml.append('    description: ""') %}
            {% do model_yaml.append('    columns:') %}

            {% set relation=ref(model) %}
            {%- set columns = adapter.get_columns_in_relation(relation) -%}
            {% set column_desc_dict =  codegen.build_dict_column_descriptions(model) if upstream_descriptions else {} %}

         


            {% for column in columns %}
                {% set model_yaml = codegen.generate_column_yaml(column, model_yaml, column_desc_dict) %}
              
            {% endfor %}
        {% endfor %}
    {% endif %}

{% if execute %}

    {% set joined = model_yaml | join ('\n') %}
    {{ log(joined, info=True) }}
     
    {{ log("==========", info=True) }}


    {{ log(models_to_generate, info=True) }}

    {% do return(joined) %}

{% endif %}

{% endmacro %}
