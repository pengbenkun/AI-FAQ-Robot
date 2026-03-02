"""
NL2SQL 提示词
"""

NL2SQL = """你是一个SQL生成专家。请根据以下表结构和用户问题生成SQL查询语句。

表结构：
{table_descriptions}

{fewshot_section}

重要约束（必须遵守）：
1. 只生成 SELECT 查询语句，不要生成 INSERT、UPDATE、DELETE
2. 只返回SQL语句，不要添加任何解释
3. 确保SQL语法正确
4. 如果需要限制结果数量，使用 LIMIT
{mandatory_conditions}

用户问题：{question}

SQL："""

NL2SQL_FEWSHOT_EXAMPLE = """参考示例：
示例1：
问题：查询所有员工的姓名和部门
SQL：SELECT employee.name, department.name FROM employee JOIN department ON employee.department_id = department.id

示例2：
问题：统计每个部门的员工数量
SQL：SELECT department.name, COUNT(employee.id) as count FROM department LEFT JOIN employee ON department.id = employee.department_id GROUP BY department.id

示例3：
问题：查询2024年创建的项目
SQL：SELECT * FROM project WHERE YEAR(create_time) = 2024"""


MANDATORY_CONDITIONS = """强制条件：
- 查询 performance（绩效）表时，必须使用 annual（年度）作为查询条件，如 WHERE annual = '2024'
- 查询 project（项目）表时，建议使用 status（状态）作为查询条件"""
