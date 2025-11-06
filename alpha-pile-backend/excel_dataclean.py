import pandas as pd
import re

def read_csv_with_encoding(filename):
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936', 'latin1']
    for encoding in encodings:
        try:
            print(f"尝试使用 {encoding} 编码读取文件...")
            df = pd.read_csv(filename, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取文件！")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用 {encoding} 编码时出现其他错误: {e}")
            continue
    raise ValueError(f"无法读取文件 {filename}，尝试了所有常见编码格式")

def clean_datetime(s):
    """将各种格式的时间字符串标准化为 YYYY-MM-DD HH:MM"""
    if pd.isna(s):
        return None
    s = str(s).replace('：', ':').replace('\\n', ' ').replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r'\s+', ' ', s)
    # 先找年月日
    match = re.search(r'(20\d{2})[./-](\d{1,2})[./-](\d{1,2})\s*(\d{1,2}):(\d{1,2})', s)
    if match:
        year, month, day, hour, minute = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d} {int(hour):02d}:{int(minute):02d}"
    # 只找年月日
    match = re.search(r'(20\d{2})[./-](\d{1,2})[./-](\d{1,2})', s)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d} 00:00"
    return None

def split_time_range(s):
    """分割开孔时间与浇筑完成时间"""
    if pd.isna(s):
        return None, None
    s = str(s).replace('\\n', ' ').replace('\n', ' ').replace('\r', ' ')
    # 常见分隔符
    for sep in ['/', ' / ', '  ', ' ', '|']:
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 2:
                return clean_datetime(parts[0]), clean_datetime(parts[1])
    # 直接找两个时间
    matches = re.findall(r'(20\d{2}[./-]\d{1,2}[./-]\d{1,2}\s*\d{1,2}:\d{1,2})', s)
    if len(matches) == 2:
        return clean_datetime(matches[0]), clean_datetime(matches[1])
    return clean_datetime(s), None

def calc_hour_diff(start, end):
    if pd.isna(start) or pd.isna(end):
        return None
    try:
        t1 = pd.to_datetime(start)
        t2 = pd.to_datetime(end)
        return round((t2 - t1).total_seconds() / 3600, 2)
    except Exception:
        return None

if __name__ == "__main__":
    df = read_csv_with_encoding("D:/1AAA_HJB/MCTS/alpha-pile/cp_sat_pile/alpha-pile-backend/real_data.csv")
    # 分割开孔时间与浇筑完成时间
    df[['开孔时间', '浇筑完成时间']] = df['开孔时间与浇筑完成时间'].apply(lambda x: pd.Series(split_time_range(x)))
    # 清洗成孔时间
    df['成孔时间_清洗'] = df['成孔时间'].apply(clean_datetime)
    # 计算差值
    df['开孔-成孔_小时'] = df.apply(lambda r: calc_hour_diff(r['开孔时间'], r['成孔时间_清洗']), axis=1)
    df['开孔-浇筑完成_小时'] = df.apply(lambda r: calc_hour_diff(r['开孔时间'], r['浇筑完成时间']), axis=1)
    # 结果预览
    print(df[['开孔时间', '成孔时间_清洗', '浇筑完成时间', '开孔-成孔_小时', '开孔-浇筑完成_小时']].head(10).to_string(index=False))
    # 保存
    df.to_excel("cleaned_data.xlsx", index=False)
    print("已保存到 cleaned_data.xlsx")