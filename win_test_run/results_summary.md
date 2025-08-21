# UBM Test Results 2025-08-21T20:07:08.0228903+08:00
# TC02 Feature extraction
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process started | PID=7364 | Pass |
| 2 | Trigger feature processing | Feature processing starts | send rrrr | N/A |
| 3 | Check feature logs | Contains processing/complete keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_200714.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_20-07-45\monitor_20250821_200714.log; hits={"feature":0,"澶勭悊瀹屾垚":0,"processed":0,"鐗瑰緛 澶勭悊 瀹屾垚":0,"features":0,"鐗瑰緛澶勭悊":0,"[SUCCESS] 鐗瑰緛澶勭悊瀹屾垚":0,"process_session_features":0,"complete":0} | Review |
| 4 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC06 Behavior fingerprint (import/export)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process started | PID=13020 | Pass |
| 2 | Check fingerprint logs | import/export/fingerprint keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_200714.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_20-08-18\monitor_20250821_200714.log; hits={"fingerprint":0,"import":0,"export":0} | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC08 Feature count threshold (>=200)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE (feature) | Output feature stats | PID=8268 | Pass |
| 2 | Check feature count | >= 200 | no feature_count matched | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC09 Accuracy & F1 thresholds
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start evaluation | Output Accuracy / F1 | PID=15796 | Pass |
| 2 | Threshold check | Acc>=90%, F1>=85% | no Accuracy/F1 matched | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC10 Alert false positive rate (<=1%)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start online monitoring | Keep running, produce logs | PID=8684 | Pass |
| 2 | Compute from logs | FPR <= 1% | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_200827.log, total=4, alerts=0, rate=0% (limit: windows>=120 or <180 s) | Pass |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
