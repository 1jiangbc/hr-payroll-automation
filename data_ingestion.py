import pandas as pd
import numpy as np
import os


class HRDataImporter:
    def __init__(self, config_path=None):
        # 映射规则直接写死在代码里，不需要折腾任何 JSON 文件
        self.mapping_rules = {
            "employee": {
                "emp_id": ["工号", "员工编号", "员工ID", "编号"],
                "name": ["姓名", "名字", "员工姓名"],
                "department": ["部门", "所属部门", "部门名称"],
                "base_salary": ["底薪", "基本工资", "基础薪资"]
            },
            "attendance": {
                "emp_id": ["工号", "员工编号", "员工ID"],
                "date": ["日期", "考勤日期", "打卡日期"],
                "late_count": ["迟到次数", "迟到"],
                "absent_days": ["缺勤天数", "缺勤"],
                "project_volume": ["项目投放金额", "业务量", "投放额"],
                "compliance_training": ["合规培训", "培训完成", "合规学分"]
            }
        }

    def detect_file(self, file_path):
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == '.csv':
            for encoding in ['utf-8', 'gbk', 'utf-8-sig']:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"无法读取csv文件编码：{file_path}")
        elif ext in ['.xlsx', '.xls']:  # 修复了以前的 == 错误
            return pd.read_excel(file_path, sheet_name=0)
        else:
            raise ValueError(f"不支持文件格式：{ext}")

    def standardize(self, df, data_type):
        rules = self.mapping_rules.get(data_type, {})
        rename_dict = {}

        # 把原始表头和规则打印出来，让你看看到底匹配没匹配上！
        print(f"🔍 【调试】当前 {data_type} 表的原始列名: {list(df.columns)}")

        for actual_col in df.columns:
            clean_col = str(actual_col).strip().lower()
            for standard_name, aliases in rules.items():
                alias_lower = [str(a).strip().lower() for a in aliases]
                if clean_col in alias_lower:
                    rename_dict[actual_col] = standard_name
                    break

        df = df.rename(columns=rename_dict)
        print(f"🔍 【调试】重命名后的标准列名: {list(df.columns)}")

        required_cols = list(rules.keys())
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"⚠️ 警告：数据 {data_type} 缺少关键字段 {missing_cols}，将自动填充NaN")
            for col in missing_cols:
                df[col] = np.nan

        return df

    def clean_type(self, df):
        # 文本列去空格
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True)

        # 日期转换
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # 合规培训文本映射成 1/0
        if 'compliance_training' in df.columns:
            df['compliance_training'] = df['compliance_training'].replace({
                '是': 1, '完成': 1, '已完成': 1, '已培训': 1, '通过': 1,
                '否': 0, '未完成': 0, '未培训': 0, '未通过': 0
            })

        # 数值列转换
        num_cols = ['base_salary', 'late_count', 'absent_days',
                    'project_volume', 'compliance_training', 'overtime_hours']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def import_data(self, file_path, data_type):
        print(f"📥 正在导入 {data_type} 数据: {file_path}")
        df_raw = self.detect_file(file_path)
        df_standard = self.standardize(df_raw, data_type)
        df_clean = self.clean_type(df_standard)
        print(f"✅ 导入成功，共 {len(df_clean)} 条记录\n")
        return df_clean