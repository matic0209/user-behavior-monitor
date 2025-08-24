#!/bin/bash
# 测试参数解析的简单脚本

echo "测试参数解析..."
echo "参数数量: $#"
echo "所有参数: $@"

# 参数处理
EXE_PATH=""
WORK_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -ExePath)
            EXE_PATH="$2"
            echo "找到 ExePath: $EXE_PATH"
            shift 2
            ;;
        -WorkDir)
            WORK_DIR="$2"
            echo "找到 WorkDir: $WORK_DIR"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            shift
            ;;
    esac
done

echo "最终 ExePath: $EXE_PATH"
echo "最终 WorkDir: $WORK_DIR"

if [[ -z "$EXE_PATH" ]] || [[ -z "$WORK_DIR" ]]; then
    echo "错误: 缺少必要参数"
    echo "用法: $0 -ExePath <exe_path> -WorkDir <work_dir>"
    exit 1
fi

echo "参数验证通过！"
