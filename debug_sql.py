import sys
sys.path.insert(0, '.')

import sqlparse

sql = "SELECT COUNT(*) AS project_count FROM project WHERE status = '进行中' LIMIT 1"

parsed = sqlparse.parse(sql)
print("SQL 解析结果:")
for stmt in parsed:
    print(f"Statement: {stmt}")
    print(f"Tokens:")
    for token in stmt.tokens:
        print(f"  ttype={token.ttype}, value={token.value!r}")
