{% macro icon_dish(tag) -%}
{%- if tag == "S" -%}   🍵
{%- elif tag == "H" -%} 🍔
{%- elif tag == "B" -%} 🍟
{%- elif tag == "N" -%} 🍨
{%- else -%}            ❓
{%- endif -%}
{%- endmacro %}

{% macro icons_kennz(kennz) -%}
{%- for k in kennz|sort -%}
{%- if k == 'G' -%}    🐓
{%- elif k == 'S' -%}  🐖
{%- elif k == 'R' -%}  🐄
{%- elif k == 'L' -%}  🐑
{%- elif k == 'W' -%}  🐗
{%- elif k == 'F' -%}  🐟
{%- elif k == 'A' -%}  🍷
{%- elif k == 'V' -%}  🥚
{%- elif k == 'VG' -%} 🌱
{%- elif k == 'MV' -%} 🏃
{%- elif k == 'B' -%}  🌻
{%- elif k == 'A' -%}  ⭐
{%- else -%} ({{ k }}) {%- endif -%}
{%- endfor -%}
{%- endmacro %}
