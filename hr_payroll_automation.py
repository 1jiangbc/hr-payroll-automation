import pandas as pd
import numpy as np
import os
from data_ingestion import HRDataImporter

os.makedirs('output', exist_ok=True)

# ============================================================
# 1. 使用导入模块：一键导入，自动清洗、自动映射列名
# ============================================================
importer = HRDataImporter()
df_emp = importer.import_data('input/employee_master.csv', 'employee')
df_att_raw = importer.import_data('input/attendance_raw.csv', 'attendance')

# ============================================================
# 2. 数据合并与业务汇总
# ============================================================
df_att = df_att_raw.dropna(subset=['emp_id']).copy()

att_summary = df_att.groupby('emp_id').agg(
    late_total=('late_count', 'sum'),
    absent_total=('absent_days', 'sum'),
    total_volume=('project_volume', 'sum'),
    compliance_pass=('compliance_training', 'mean')
).reset_index()

df_payroll = df_emp.merge(
    att_summary,
    left_on='emp_id',
    right_on='emp_id',
    how='left'
)

# --- 加入这行验收打印，强行看数据长什么样！ ---
print("🔥 【验收】合并后，前5行的部门、底薪、总投放额：")
print(df_payroll[['emp_id', 'name', 'department', 'base_salary', 'total_volume']].head())
print("-" * 50)
# -----------------------------------------------

att_cols = ['late_total', 'absent_total', 'total_volume', 'compliance_pass']
df_payroll[att_cols] = df_payroll[att_cols].fillna(0)

# ============================================================
# 3. 金融行业专属薪酬核算规则
# ============================================================
LATE_PENALTY = 100          # 每次迟到扣100
ABSENT_PENALTY = 500        # 每天缺勤扣500
COMMISSION_RATE = 0.0001    # 提成比例：万分之一
RISK_RESERVE_RATE = 0.10    # 风险准备金：提成的10%延期支付
COMPLIANCE_PENALTY = 500    # 合规未达标扣款

df_payroll['late_deduction'] = df_payroll['late_total'] * LATE_PENALTY
df_payroll['absent_deduction'] = df_payroll['absent_total'] * ABSENT_PENALTY

# 业务提成 = 投放金额 * 提成比例
df_payroll['commission'] = df_payroll['total_volume'] * COMMISSION_RATE

# 风险准备金
df_payroll['risk_reserve'] = df_payroll['commission'] * RISK_RESERVE_RATE
df_payroll['actual_commission'] = df_payroll['commission'] - df_payroll['risk_reserve']

# 合规扣款：合规培训完成率 < 1，扣款
df_payroll['compliance_deduction'] = np.where(
    df_payroll['compliance_pass'] < 1,
    COMPLIANCE_PENALTY,
    0
)

# 应发 = 底薪 + 实际发提成 - 迟到扣款 - 缺勤扣款 - 合规扣款
df_payroll['gross_salary'] = (
    df_payroll['base_salary']
    + df_payroll['actual_commission']
    - df_payroll['late_deduction']
    - df_payroll['absent_deduction']
    - df_payroll['compliance_deduction']
)

df_payroll['gross_salary'] = df_payroll['gross_salary'].clip(lower=0)

# ============================================================
# 4. 导出多Sheet报表
# ============================================================
output_path = 'output/HR_Monthly_Report.xlsx'

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # 4.1 薪酬核算明细
    payroll_cols = [
        'emp_id', 'name', 'department', 'base_salary',
        'total_volume', 'commission', 'risk_reserve', 'actual_commission',
        'late_deduction', 'absent_deduction',
        'compliance_pass', 'compliance_deduction', 'gross_salary'
    ]
    df_payroll[payroll_cols].to_excel(writer, sheet_name='薪酬核算明细', index=False)

    # 4.2 部门人力成本
    dept_cost = df_payroll.groupby('department').agg(
        人数=('emp_id', 'count'),
        总投放额=('total_volume', 'sum'),
        总人力成本=('gross_salary', 'sum')
    ).reset_index()
    dept_cost.to_excel(writer, sheet_name='部门人力成本', index=False)

    # 4.3 合规预警名单
    compliance_alert = df_payroll[df_payroll['compliance_pass'] < 1][
        ['emp_id', 'name', 'department', 'compliance_pass', 'compliance_deduction']
    ]
    compliance_alert.to_excel(writer, sheet_name='合规预警名单', index=False)

print(f"\n✅ 报表已导出：{output_path}")
print(f"   - 核算明细：{len(df_payroll)} 条")
print(f"   - 部门成本：{len(dept_cost)} 条")
print(f"   - 合规预警：{len(compliance_alert)} 条")