# UBM Test Results 2025-08-21T19:45:14.6484070+08:00
# TC01 Realtime Input Collection
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process starts successfully | PID=20032 | pass |
| 2 | Simulate mouse actions | Events are produced (see logs) | actions executed | N/A |
| 3 | Check log keywords | contains move/click/scroll | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191423.log; hits={"scroll":0,"move":0,"click":0} | review |
| 4 | Exit program | Graceful exit or terminated | done | pass |
# TC02 Feature extraction
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process started | PID=6180 | Pass |
| 2 | Trigger feature processing | Feature processing starts | send rrrr | N/A |
| 3 | Check feature logs | Contains processing/complete keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_194521.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_19-46-12\monitor_20250821_194521.log; hits={"processed":0,"feature":0,"features":0,"complete":0,"process_session_features":0} | Review |
| 4 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC06 Behavior fingerprint (import/export)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | 鍚姩 EXE | 杩涚▼鍚姩鎴愬姛 | PID=20188 | 閫氳繃 |
| 2 | Check fingerprint logs | import/export/fingerprint keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_194547.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_19-46-45\monitor_20250821_194547.log; hits={"fingerprint":0,"import":0,"export":0} | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC08 Feature count threshold (>=200)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE (feature) | Output feature stats | PID=1776 | Pass |
| 2 | Check feature count | >= 200 | no feature_count matched | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC09 Accuracy & F1 thresholds
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start evaluation | Output Accuracy / F1 | PID=1044 | Pass |
| 2 | Threshold check | Acc>=90%, F1>=85% | no Accuracy/F1 matched | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC10 Alert false positive rate (<=1%)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start online monitoring | Keep running, produce logs | PID=8348 | Pass |
| 2 | Compute from logs | FPR <= 1% | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_194654.log, total=4, alerts=0, rate=0% (limit: windows>=120 or <180 s) | Pass |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
