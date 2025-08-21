# UBM Test Results 2025-08-21T19:10:21.5337873+08:00
# TC01 Realtime Input Collection
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process starts successfully | PID=11276 | pass |
| 2 | Simulate mouse actions | Events are produced (see logs) | actions executed | N/A |
| 3 | Check log keywords | contains move/click/scroll | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\debug_20250821_190556.log; hits={"scroll":0,"move":0,"click":0} | review |
| 4 | Exit program | Graceful exit or terminated | done | pass |
# TC02 Feature extraction
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process started | PID=12828 | Pass |
| 2 | Trigger feature processing | Feature processing starts | send rrrr | N/A |
| 3 | Check feature logs | Contains processing/complete keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_190556.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_19-11-18\monitor_20250821_190556.log; hits={"processed":0,"feature":0,"features":0,"complete":0,"process_session_features":0} | Review |
| 4 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC03 DL classification runnable
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Auto workflow enters | PID=5200 | Pass |
| 2 | Check classification logs | Predict/Prediction keywords present | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191055.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_19-11-52\monitor_20250821_191055.log; hits={"SimplePredictor":0,"prediction":0,"start_continuous_prediction":0,"predict":0} | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC04 Anomaly alert
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start monitoring | Monitoring state | PID=15652 | Pass |
| 2 | Inject anomaly sequence | Anomaly score triggers alert | Injected | N/A |
| 3 | Check log keywords | Alert/Anomaly keyword present | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191128.log; hits={"alert":0,"anomaly":0,"trigger":0} | Review |
| 4 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC05 Anomaly blocking
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start monitoring | Monitoring state | PID=20036 | Pass |
| 2 | Inject high-risk sequence | Reach blocking threshold | Injected | N/A |
| 3 | Check log keywords | Contains blocking/lock keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191201.log; hits={"lock screen":0,"block":0,"LockWorkStation":0,"alert triggered":0} | Review |
| 4 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC06 Behavior fingerprint (import/export)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | 鍚姩 EXE | 杩涚▼鍚姩鎴愬姛 | PID=23268 | 閫氳繃 |
| 2 | Check fingerprint logs | import/export/fingerprint keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191233.log; artifact=F:\user-behaviro\user-behavior-monitor\win_test_run\artifacts\2025-08-21_19-13-28\monitor_20250821_191233.log; hits={"fingerprint":0,"import":0,"export":0} | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC07 Collection coverage (move/click/scroll/keyboard)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE | Process started | PID=4196 | Pass |
| 2 | Simulate 4 types | Logs show 4 types | Injected | N/A |
| 3 | Check log keywords | Contains 4 event-type keywords | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191303.log; hits={"keyboard":0,"click":0,"hotkey":0,"move":0,"scroll":0,"released":0,"pressed":0} | Review |
| 4 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC08 Feature count threshold (>=200)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start EXE (feature) | Output feature stats | PID=18460 | Pass |
| 2 | Check feature count | >= 200 | no feature_count matched | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC09 Accuracy & F1 thresholds
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start evaluation | Output Accuracy / F1 | PID=22164 | Pass |
| 2 | Threshold check | Acc>=90%, F1>=85% | no Accuracy/F1 matched | Review |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
# TC10 Alert false positive rate (<=1%)
| Index | Action | Expectation | Actual | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | Start online monitoring | Keep running, produce logs | PID=5532 | Pass |
| 2 | Compute from logs | FPR <= 1% | log=F:\user-behaviro\user-behavior-monitor\win_test_run\logs\monitor_20250821_191403.log, total=4, alerts=0, rate=0% (limit: windows>=120 or <180 s) | Pass |
| 3 | Exit program | Graceful exit or terminated | Exit done | Pass |
