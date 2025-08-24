#!/bin/bash
# 演示新的测试结果格式

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

echo "🎨 演示新的测试结果格式"
echo "=========================================="

# 演示测试用例状态
show_test_case_status "TC01" "实时输入采集功能测试" "start"

# 演示测试步骤
show_test_step 1 "启动程序" "start"
sleep 1
show_test_step 1 "启动程序" "success"

show_test_step 2 "模拟鼠标移动" "start"
sleep 1
show_test_step 2 "模拟鼠标移动" "success"

show_test_step 3 "模拟鼠标点击" "start"
sleep 1
show_test_step 3 "模拟鼠标点击" "success"

# 演示结果表格
write_result_header "演示测试结果"
write_result_table_header

write_result_row 1 "启动程序" "进程启动成功" "PID=12345" "Pass"
write_result_row 2 "模拟鼠标移动" "鼠标移动被检测到" "移动成功" "Pass"
write_result_row 3 "模拟鼠标点击" "鼠标点击被检测到" "点击成功" "Pass"
write_result_row 4 "模拟滚动" "滚动事件被检测到" "滚动成功" "Pass"
write_result_row 5 "检查日志关键字" "包含事件类型关键字" "找到15个关键字" "Pass"
write_result_row 6 "退出程序" "优雅退出或被终止" "退出完成" "Pass"

write_result_footer

# 演示结果汇总
write_result_summary 6 6 0 0 0 0

# 演示性能指标
show_performance_metrics "TC01" "执行时间: 2.5秒
内存使用: 45MB
CPU使用: 12%
关键字匹配: 15个
日志大小: 2.3KB"

# 演示错误详情（模拟）
show_error_details "模拟错误信息" 1

echo ""
echo "🎯 新格式特点:"
echo "  ✅ 清晰的表格边框"
echo "  🎨 彩色状态标识"
echo "  📊 详细的步骤状态"
echo "  📈 完整的结果汇总"
echo "  🔍 详细的错误信息"
echo "  📁 清晰的测试产物位置"
