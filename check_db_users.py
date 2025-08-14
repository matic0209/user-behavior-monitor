#!/usr/bin/env python3
"""
数据库快速自检脚本（Windows/Linux 通用）

功能:
- 检查 SQLite 数据库是否存在并可读
- 列出 `features` 表中的各用户样本数分布
- 可选: 排除指定用户后，检查是否存在用于训练的负样本（其他用户数据）

用法示例:
  python check_db_users.py --db data\\mouse_data.db --exclude-user HUAWEI_1755061580
  python check_db_users.py --db data/mouse_data.db --top 50
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

try:
    # 确保控制台可以安全打印中文/Unicode
    from src.utils.console_encoding import ensure_utf8_console
    ensure_utf8_console()
except Exception:
    pass


def validate_database_file(database_path: Path) -> bool:
    if not database_path.exists():
        print(f"[ERROR] 数据库文件不存在: {database_path}")
        return False
    if not database_path.is_file():
        print(f"[ERROR] 路径不是文件: {database_path}")
        return False
    return True


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        )
        return cursor.fetchone() is not None
    except Exception as error:
        print(f"[WARN] 无法检查数据表是否存在: {table_name}，错误: {error}")
        return False


def fetch_user_sample_counts(connection: sqlite3.Connection) -> list:
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT user_id, COUNT(*) AS cnt FROM features GROUP BY user_id ORDER BY cnt DESC"
        )
        return cursor.fetchall()
    except Exception as error:
        print(f"[ERROR] 查询用户样本分布失败: {error}")
        return []


def count_negative_samples(connection: sqlite3.Connection, exclude_user_id: str) -> int:
    try:
        cursor = connection.cursor()
        # 使用 TRIM 防止首尾空白导致的不匹配
        cursor.execute(
            "SELECT COUNT(*) FROM features WHERE TRIM(user_id) != TRIM(?)",
            (exclude_user_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as error:
        print(f"[WARN] 统计负样本数量失败: {error}")
        return 0


def fetch_recent_feature_vectors(
    connection: sqlite3.Connection, user_id: str, limit: int = 5
) -> list:
    cursor = connection.cursor()
    # 优先尝试按 timestamp 排序；若失败则退化为无排序
    try:
        cursor.execute(
            """
            SELECT feature_vector FROM features
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return cursor.fetchall()
    except Exception:
        try:
            cursor.execute(
                "SELECT feature_vector FROM features WHERE user_id = ? LIMIT ?",
                (user_id, limit),
            )
            return cursor.fetchall()
        except Exception:
            return []


def try_parse_feature_vector(sample_value: str) -> str:
    """尝试解析特征向量，返回简要信息字符串，不抛异常。"""
    if sample_value is None:
        return "<None>"
    text = str(sample_value).strip()
    # 常见两种格式：JSON 数组 或 逗号分隔
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return f"JSON list, length={len(parsed)}"
    except Exception:
        pass
    # 尝试逗号分隔
    try:
        length = len([p for p in text.split(',') if p.strip()])
        return f"CSV list, length={length}"
    except Exception:
        return "<unrecognized>"


def main() -> int:
    parser = argparse.ArgumentParser(description="SQLite 数据库快速自检")
    parser.add_argument(
        "--db",
        type=str,
        default=str(Path("data") / "mouse_data.db"),
        help="数据库文件路径 (默认: data/mouse_data.db)",
    )
    parser.add_argument(
        "--exclude-user",
        type=str,
        default=None,
        help="排除的用户ID（用于检测负样本是否存在）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="显示样本数最多的前 N 个用户 (默认: 20)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=3,
        help="示例性读取每个用户的最近特征向量条数 (默认: 3)",
    )

    args = parser.parse_args()
    database_path = Path(args.db)

    print("[INFO] 数据库路径:", database_path)

    if not validate_database_file(database_path):
        return 1

    try:
        connection = sqlite3.connect(str(database_path))
        print("[INFO] 数据库连接成功")
    except Exception as error:
        print(f"[ERROR] 数据库连接失败: {error}")
        return 1

    try:
        if not table_exists(connection, "features"):
            print("[ERROR] 缺少数据表: features")
            return 1

        user_counts = fetch_user_sample_counts(connection)
        total_rows = sum(int(row[1]) for row in user_counts) if user_counts else 0

        print("\n[SUMMARY] 样本分布:")
        print(f"  总样本数: {total_rows}")
        print(f"  用户数  : {len(user_counts)}")

        print(f"\n[TOP-{args.top}] 用户样本数 (按样本数降序):")
        for index, (user_id, count) in enumerate(user_counts[: args.top], start=1):
            print(f"  {index:2d}. {user_id} -> {count}")

        if args.exclude_user:
            negative_count = count_negative_samples(connection, args.exclude_user)
            print(
                f"\n[CHECK] 排除用户 '{args.exclude_user}' 后的负样本数量: {negative_count}"
            )
            if negative_count <= 0:
                print("[WARN] 未找到负样本，请导入其他用户数据或生成负样本后再训练")
            else:
                print("[OK] 已存在可用的负样本数据")

        # 对样本最多的前1-2个用户做特征向量抽样检查
        print("\n[CHECK] 特征向量示例 (解析格式/长度):")
        for user_id, _ in user_counts[:2]:
            rows = fetch_recent_feature_vectors(connection, user_id, limit=args.sample)
            if not rows:
                print(f"  用户 {user_id}: 无法读取样本或无数据")
                continue
            for idx, (raw_value,) in enumerate(rows, start=1):
                parsed_info = try_parse_feature_vector(raw_value)
                print(f"  用户 {user_id} 样本 {idx}: {parsed_info}")

        print("\n[DONE] 数据库检查完成")
        return 0

    finally:
        try:
            connection.close()
            print("[INFO] 数据库连接已关闭")
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())


