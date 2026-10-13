import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

os.makedirs('data', exist_ok=True)#os.makedirs('data', exist_ok=True) 这行代码的作用是：确保当前目录下有一个名为 data 的文件夹，如果没有就自动创建；如果已经有了，就什么也不做，也不会报错。
random.seed(42)
np.random.seed(42)

# 保理公司架构
departments = ['业务部', '风控部', '财务部', '综合管理部']
positions = {'业务部': '保理业务经理', '风控部': '风控专员',
             '财务部': '财务主管', '综合管理部': '人事行政专员'}

employees = []
for i in range(1, 201):
    dept = random.choice(departments)
    employees.append({
        '员工ID': f'EMP{i:04d}',#f格式，输出0001，0003
        '名字': f'员工{i}',#员工1，员工200
        '所属部门': dept,#字典是 键对值
        '岗位': positions[dept],
        '入职日期': (datetime(2022, 1, 1) + timedelta(days=random.randint(0, 1000))).strftime('%Y-%m-%d'),
        '基本工资': random.choice([6000, 8000, 10000, 12000, 15000]) # 金融行业底薪偏高
    })

df_emp = pd.DataFrame(employees)
df_emp.to_csv('data/employee_master.csv', index=False, encoding='utf-8-sig')#index就是不额外生成行号0，1，2，3之类的
print(f"✅ 员工花名册生成完毕：{len(df_emp)}条")




# ============================================================
# 2. 生成原始考勤数据（制造脏数据：部门带空格、缺卡、缺加班时长）
#for x in df_emp，它默认遍历的是 DataFrame 的列名（column names），而不是行数据！
#series的列数据emp['所属部门'] 。 random.random()：生成一个 0 到 1 之间的随机小数，比如 0.032、0.87。
#< 0.05：表示只有 5% 的概率成立（因为 0~1 之间小于 0.05 的数占 5%），就是生成的格式有些会添加一个空格作为格式错误
# ============================================================

attendance_records = []#一个月的数据呗
for _,emp in df_emp.iterrows():#_是忽略行号的意思，emp是代指df_emp的行数据，是一个列表
    for day in range(1,31):
        dept_name = emp['所属部门'] + ' ' if random.random()<0.05 else emp['所属部门']

        # 业务部才有项目投放金额，其他部门为0,这是按天生成
        project_volume = 0
        if emp['所属部门'] == '业务部':
            project_volume = random.randint(500000,3000000) if random.random()<0.3 else 0


        attendance_records.append({
            '员工编号':emp['员工ID'],
            '部门': dept_name,#脏数据
            '打卡日期': f'2026-9-{day:02d}',#用0填补，两位，整数
            '迟到':1 if random.random()<0.05 else 0,#百分之5的概率迟到
            '缺勤':1 if random.random()<0.02 else 0,#百分之2的概率缺勤
            '项目投放金额': project_volume,
            '合规培训': 1 if random.random() < 0.9 else 0,#百分之10的人没用完成培训
        })


df_att = pd.DataFrame(attendance_records)
df_att.loc[50,'员工编号'] = np.nan#50 表示第 51 行，
df_att.loc[120, '项目投放金额'] = np.nan#120 表示第 121 行。专门挖 null的坑

df_att.to_csv('data/attendance_raw.csv', index=False, encoding='utf-8-sig')
print(f"✅ 业务考勤数据生成完毕：{len(df_att)}条（含脏数据）")