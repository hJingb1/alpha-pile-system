import pandas as pd
import re
import io


# 假设您的数据在一个名为 "data.csv" 的文件中
# 您可以使用 df = pd.read_csv("data.csv") 来读取
# 这里我们用上面的模拟数据来创建DataFrame

def read_csv_with_encoding(filename):
    """尝试不同编码读取CSV文件"""
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

try:
    df = read_csv_with_encoding("real_data.csv")
    
    print(f"数据形状: {df.shape}")
    print("可用的列名有:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1:2d}. {col}")
    
    print("\n数据前5行预览:")
    print(df.head().to_string())
    
    # 根据图片数据，自动识别时间相关的列名
    time_columns = []
    for col in df.columns:
        if any(keyword in str(col) for keyword in ['时间', '日期', 'time', 'date']) and not pd.isna(df[col]).all():
            time_columns.append(col)
    
    print(f"\n识别到的时间相关列: {time_columns}")
    
    if not time_columns:
        print("错误：未找到任何时间相关的列")
        print("请检查数据文件格式")
        exit(1)
    
except Exception as e:
    print(f"读取文件失败: {e}")
    print("请检查文件是否存在，以及列名是否正确")
    exit(1)

# --- 2. 定义核心清洗函数 ---



import pandas as pd
import re
import io

# ==============================================================================
#                      CORE DATA CLEANING FUNCTIONS
# ==============================================================================

def find_year_from_series(series: pd.Series, column_name: str) -> int:
    """从一个Series中找到第一个有效的年份，用于处理"M.D H:M"格式。"""
    for s in series.dropna():
        s = str(s)
        match = re.search(r'(20\d{2})', s)
        if match:
            year = int(match.group(1))
            print(f"在列 '{column_name}' 的字符串 '{s}' 中找到年份: {year}")
            return year
    print(f"警告: 在列 '{column_name}' 中未找到任何年份信息，将使用默认年份 2025。")
    return 2025

def clean_and_format_datetime(raw_string: str, default_year: int = None) -> str:
    """
    清洗单个时间字符串，并格式化为 'YYYY-MM-DD HH:MM:SS'。
    支持带年份的完整格式、不带年份的 "M.D H:M" 格式。
    """
    if pd.isna(raw_string):
        return None
    
    s = str(raw_string).strip().replace('：', ':').replace('；', ':')
    s = re.sub(r':00$', '', s)
    s = re.sub(r'\s+', ' ', s)

    # 1. 优先匹配带年份的完整格式
    full_patterns = [
        r'(\d{4})[.-/](\d{1,2})[.-/](\d{1,2})\s+(\d{1,2}):(\d{1,2})',
        r'(\d{4})[.-/](\d{1,2})[.-/](\d{1,2})(\d{1,2}):(\d{1,2})',
    ]
    for pattern in full_patterns:
        match = re.search(pattern, s)
        if match:
            try:
                year, month, day, hour, minute = map(int, match.groups())
                if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
            except (ValueError, IndexError):
                continue
    
    # 2. 尝试匹配无年份格式 (如 "4.1 8:00")
    if default_year:
        short_pattern = r'(\d{1,2})[.-/](\d{1,2})\s+(\d{1,2}):(\d{1,2})'
        match = re.search(short_pattern, s)
        if match:
            try:
                month, day, hour, minute = map(int, match.groups())
                if 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{default_year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
            except (ValueError, IndexError):
                pass
    
    # 3. 最终回退方案：从字符串中提取数字
    numbers = re.findall(r'\d+', str(raw_string))
    try:
        if len(numbers) >= 5: # Y, M, D, H, M
            year, month, day, hour, minute = map(int, numbers[:5])
            if 2020 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
        elif len(numbers) >= 4 and default_year: # M, D, H, M
            month, day, hour, minute = map(int, numbers[:4])
            if 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{default_year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
    except (ValueError, IndexError):
        pass

    print(f"警告: 无法解析时间字符串 '{raw_string}'")
    return None

def clean_and_split_datetimes(raw_string: str, default_year: int = None) -> tuple:
    """根据实际表格格式分割时间范围字符串, 支持无年份格式。"""
    if pd.isna(raw_string):
        return None, None

    s = str(raw_string).strip().replace('"', '').replace('：', ':').replace('；', ':')
    
    start_str, end_str = None, None
    split_patterns = ['/', ' / ', ' - ', '—', '－', ' 至 ', ' 到 ']
    
    # 尝试使用定义的分隔符进行分割
    for separator in split_patterns:
        if separator in s:
            parts = s.split(separator, 1)
            if len(parts) == 2:
                start_str, end_str = parts[0].strip(), parts[1].strip()
                break
    
    # 如果没有找到分隔符，则尝试根据年份分割
    if start_str is None:
        year_pattern = r'(?<!\d)(20\d{2})(?!\d)' # 匹配独立的四位数年份
        year_matches = list(re.finditer(year_pattern, s))
        if len(year_matches) >= 2:
            split_pos = year_matches[1].start()
            start_str, end_str = s[:split_pos].strip(), s[split_pos:].strip()

    if start_str is None or end_str is None:
        print(f"警告: 无法分割时间范围字符串 '{raw_string}'")
        return None, None
    
    # 解析开始时间
    start_dt = clean_and_format_datetime(start_str, default_year)
    
    # 从解析出的开始时间中提取年份，作为结束时间的默认年份，这更稳健
    year_from_start = default_year
    if start_dt:
        match = re.match(r'(\d{4})', start_dt)
        if match:
            year_from_start = int(match.group(1))
            
    # 解析结束时间
    end_dt = clean_and_format_datetime(end_str, year_from_start)
    
    return start_dt, end_dt

def calculate_time_difference_hours(start_time_str, end_time_str):
    """计算两个时间字符串之间的差值，单位为小时"""
    if pd.isna(start_time_str) or pd.isna(end_time_str):
        return None
    try:
        start_time = pd.to_datetime(start_time_str)
        end_time = pd.to_datetime(end_time_str)
        time_diff = end_time - start_time
        return round(time_diff.total_seconds() / 3600, 2)
    except Exception:
        return None

# ==============================================================================
#                                SCRIPT EXECUTION
# ==============================================================================

def main():
    """主执行函数"""
    try:
        df = read_csv_with_encoding("real_data.csv")
        
        print(f"数据形状: {df.shape}")
        print("可用的列名有:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")
        
        print("\n数据前3行预览:")
        print(df.head(3).to_string())
        
        # 自动识别时间相关列
        time_columns = []
        for col in df.columns:
            if any(keyword in str(col) for keyword in ['时间', '日期', 'time', 'date']) and not df[col].isna().all():
                time_columns.append(col)
        
        print(f"\n识别到的时间相关列: {time_columns}")
        
        if not time_columns:
            print("错误：未找到任何时间相关的列")
            return
        
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    print("\n--- 开始数据清洗 ---")

    # 处理所有识别到的时间列
    cleaned_time_cols = []
    
    for time_col in time_columns:
        print(f"\n处理时间列: '{time_col}'")
        
        # 检查是否包含时间范围（即一个单元格内有两个时间点）
        sample_values = df[time_col].dropna().head(5)
        has_range = False
        
        for val in sample_values:
            val_str = str(val)
            # 检查是否包含常见的时间范围分隔符
            if any(sep in val_str for sep in ['/', ' / ', ' - ', '—', '－', ' 至 ', ' 到 ']):
                has_range = True
                break
            # 检查是否包含多个年份（另一种时间范围的标志）
            year_matches = re.findall(r'20\d{2}', val_str)
            if len(year_matches) >= 2:
                has_range = True
                break
        
        if has_range:
            print(f"  → 检测到时间范围格式，将分割为开孔时间和浇筑结束时间")
            year_for_range = find_year_from_series(df[time_col], time_col)
            
            # 创建分割后的列名 - 使用具体的业务含义
            start_col_name = "开孔时间"
            end_col_name = "浇筑结束时间"
            
            df[[start_col_name, end_col_name]] = df[time_col].apply(
                lambda x: pd.Series(clean_and_split_datetimes(x, default_year=year_for_range))
            )
            
            cleaned_time_cols.extend([start_col_name, end_col_name])
            
            # 计算时间差
            duration_col_name = "施工持续时长_小时"
            df[duration_col_name] = df.apply(
                lambda r: calculate_time_difference_hours(r[start_col_name], r[end_col_name]), 
                axis=1
            )
            cleaned_time_cols.append(duration_col_name)
            
        else:
            print(f"  → 检测到单个时间格式")
            year_for_single = find_year_from_series(df[time_col], time_col)
            cleaned_col_name = f"{time_col}_已清洗"
            
            df[cleaned_col_name] = df[time_col].apply(
                clean_and_format_datetime, args=(year_for_single,)
            )
            cleaned_time_cols.append(cleaned_col_name)

    print("\n--- 计算时间间隔 ---")
    
    # 寻找开孔时间列和成孔时间列，计算它们之间的差值
    start_time_col = None  # 开孔时间列
    hole_completion_col = None  # 成孔时间列
    
    # 查找成孔时间清洗后的列
    hole_completion_col = None
    if '成孔时间_已清洗' in df.columns:
        hole_completion_col = '成孔时间_已清洗'
    elif '成孔时间' in df.columns:
        hole_completion_col = '成孔时间'

    # 查找开孔时间列
    start_time_col = None
    if '开孔时间' in df.columns:
        start_time_col = '开孔时间'

    # 计算成孔与开孔时间差
    if start_time_col and hole_completion_col:
        print(f"计算 '{hole_completion_col}' 与 '{start_time_col}' 之间的时间差")
        time_diff_col = "成孔与开孔时间差_小时"
        df[time_diff_col] = df.apply(
            lambda r: calculate_time_difference_hours(r[start_time_col], r[hole_completion_col]), 
            axis=1
        )
        cleaned_time_cols.append(time_diff_col)
        print(f"✓ 已创建列: '{time_diff_col}'")
    else:
        print("未找到合适的开孔时间和成孔时间列进行配对")
        if start_time_col:
            print(f"  找到开孔时间列: {start_time_col}")
        if hole_completion_col:
            print(f"  找到成孔时间列: {hole_completion_col}")

    # 构建展示列
    display_cols = []
    
    # 添加标识列
    id_cols = ['桩号', '孔号', '序号', 'ID', 'id']
    for col in id_cols:
        if col in df.columns:
            display_cols.append(col)
    
    # 添加原始时间列和清洗后的列
    for time_col in time_columns:
        if time_col in df.columns:
            display_cols.append(time_col)
    
    for cleaned_col in cleaned_time_cols:
        if cleaned_col in df.columns:
            display_cols.append(cleaned_col)

    # 限制显示列数，避免过宽
    if len(display_cols) > 8:
        display_cols = display_cols[:8]
        print(f"注意：为便于查看，只显示前8列")

    print("数据预览:")
    if display_cols:
        print(df[display_cols].head().to_markdown(index=False))
    else:
        print(df.head().to_markdown(index=False))
    
    print("\n处理结果统计:")
    total_count = len(df)
    
    for col in time_columns:
        if col in df.columns:
            valid_count = df[col].notna().sum()
            print(f"  - 原始列 '{col}': {valid_count}/{total_count} ({valid_count/total_count:.1%}) 有数据")
    
    for col in cleaned_time_cols:
        if col in df.columns:
            valid_count = df[col].notna().sum()
            print(f"  - 清洗后 '{col}': {valid_count}/{total_count} ({valid_count/total_count:.1%}) 有效")

    try:
        output_filename = "cleaned_data.xlsx"
        df.to_excel(output_filename, index=False)
        print(f"\n✓ 结果已保存到: {output_filename}")
    except Exception as e:
        print(f"\n保存Excel文件时出错: {e}")
        try:
            output_filename = "cleaned_data.csv"
            df.to_csv(output_filename, index=False, encoding='utf-8-sig')
            print(f"✓ 备用方案：结果已保存到: {output_filename}")
        except Exception as e2:
            print(f"保存CSV文件也失败: {e2}")

    print("\n处理完成！")

if __name__ == "__main__":
    main()