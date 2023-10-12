-- 演示 vscode 提交代码
{% macro test_all_values_gte_zero(table, column) %}

select * from {{ ref(table) }} where {{ column }} < 0

{% endmacro %}