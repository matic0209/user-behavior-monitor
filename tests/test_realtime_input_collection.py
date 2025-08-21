import os
import sys
import time
import types
import sqlite3
import threading
import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch


class TestLinuxMouseCollectorRealtime(unittest.TestCase):
    def setUp(self):
        # 确保项目根目录在 sys.path
        project_root = Path(__file__).resolve().parents[1]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # 为每个测试创建独立的临时数据库
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "mouse_data_test.db"

        # 伪造 Controller 与 mouse.Listener
        class FakeController:
            def __init__(self):
                self._x = 0
                self._y = 0

            @property
            def position(self):
                # 每次访问都微调位置，模拟鼠标在移动
                self._x += 1
                self._y += 1
                return (self._x, self._y)

        class FakeMouseListener:
            def __init__(self, on_click=None, on_scroll=None, *args, **kwargs):
                self.on_click = on_click
                self.on_scroll = on_scroll
                self._running = False

            def start(self):
                self._running = True
                return self

            def stop(self):
                self._running = False

        # 动态导入模块后再打补丁
        import src.core.data_collector.linux_mouse_collector as lmc

        # Patch 配置加载，避免依赖实际 config.yaml
        def _fake_load_config(self):
            # 设置最小配置占位
            type(self)._config = {
                'paths': {},
                'data_collection': {
                    'collection_interval': 0.001,
                    'max_buffer_size': 1000,
                    'target_samples_per_session': 20,
                },
                'alert': {},
                'system': {},
            }

        self.cfg_load_patch = patch(
            'src.utils.config.config_loader.ConfigLoader.load_config',
            new=_fake_load_config
        )

        # Patch 配置，使用高频率与较小目标样本，确保测试快速完成
        self.cfg_paths_patch = patch(
            'src.utils.config.config_loader.ConfigLoader.get_paths',
            return_value={
                'models': str(Path(self.tmpdir.name) / 'models'),
                'data': str(Path(self.tmpdir.name) / 'data'),
                'logs': str(Path(self.tmpdir.name) / 'logs'),
                'results': str(Path(self.tmpdir.name) / 'results'),
                'test_data': str(Path(self.tmpdir.name) / 'data' / 'processed' / 'all_test_aggregation.pickle'),
                'train_data': str(Path(self.tmpdir.name) / 'data' / 'processed' / 'all_training_aggregation.pickle'),
                'database': str(self.db_path),
                'user_config': str(Path(self.tmpdir.name) / 'user_config.json'),
            }
        )
        self.cfg_dc_patch = patch(
            'src.utils.config.config_loader.ConfigLoader.get_data_collection_config',
            return_value={
                'collection_interval': 0.001,
                'max_buffer_size': 1000,
                'target_samples_per_session': 20,
            }
        )
        self.pynput_available_patch = patch.object(lmc, 'PYNPUT_AVAILABLE', True)
        self.controller_patch = patch.object(lmc, 'Controller', FakeController)
        # 构造一个假的 mouse 包含 Listener
        fake_mouse_mod = types.SimpleNamespace(Listener=FakeMouseListener)
        self.mouse_patch = patch.object(lmc, 'mouse', fake_mouse_mod)

        # 启动所有补丁
        self.cfg_load_patch.start()
        self.cfg_paths_patch.start()
        self.cfg_dc_patch.start()
        self.pynput_available_patch.start()
        self.controller_patch.start()
        self.mouse_patch.start()

        self.lmc_mod = lmc

    def tearDown(self):
        # 停止所有补丁
        self.mouse_patch.stop()
        self.controller_patch.stop()
        self.pynput_available_patch.stop()
        self.cfg_dc_patch.stop()
        self.cfg_paths_patch.stop()
        self.cfg_load_patch.stop()

        # 清理临时目录
        self.tmpdir.cleanup()

    def _count_events(self, user_id, session_id):
        if not self.db_path.exists():
            return 0
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute(
            'SELECT COUNT(*) FROM mouse_events WHERE user_id = ? AND session_id = ?',
            (user_id, session_id)
        )
        count = cur.fetchone()[0]
        conn.close()
        return count

    def test_realtime_mouse_collection_saves_to_db(self):
        # 实例化并启动采集
        collector = self.lmc_mod.LinuxMouseCollector(user_id='test_user')
        started = collector.start_collection()
        self.assertTrue(started, "采集应当成功启动")

        # 等待采集线程根据目标样本自动结束（设置超时防止死等）
        deadline = time.time() + 5  # 最长等待5秒
        while collector.is_collecting and time.time() < deadline:
            time.sleep(0.01)

        # 保底停止
        collector.stop_collection()

        # 校验数据库中写入的事件条目数
        session_id = collector.session_id
        self.assertIsNotNone(session_id)
        count = self._count_events('test_user', session_id)
        self.assertGreaterEqual(count, 20, f"应当至少保存 20 条事件，当前为 {count}")


class TestKeyboardListenerRealtime(unittest.TestCase):
    def setUp(self):
        # 确保项目根目录在 sys.path
        project_root = Path(__file__).resolve().parents[1]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # 构造假的 pynput.keyboard.Listener
        class FakeKey:
            def __init__(self, char):
                self.char = char

        class FakeKeyboardListener:
            def __init__(self, on_press=None, on_release=None, *args, **kwargs):
                self.on_press = on_press
                self.on_release = on_release
                self._thread = None
                self._running = False

            def _run(self):
                # 模拟快速连续按下 'a' 四次（小于1秒的窗口）
                for _ in range(4):
                    if not self._running:
                        return
                    if self.on_press:
                        self.on_press(FakeKey('a'))
                    time.sleep(0.05)

            def start(self):
                self._running = True
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()
                return self

            def stop(self):
                self._running = False
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=1)

        # 准备一个假的 pynput 模块注入 sys.modules
        fake_pynput_keyboard = types.SimpleNamespace(Listener=FakeKeyboardListener)
        fake_pynput = types.SimpleNamespace(keyboard=fake_pynput_keyboard)
        self.fake_pynput = fake_pynput

        # 打补丁：ConfigLoader.load_config 与 get_paths 使 user_config 存在
        self.tmpdir = tempfile.TemporaryDirectory()
        self.user_config_path = Path(self.tmpdir.name) / 'user_config.json'
        def _fake_load_config(self):
            type(self)._config = {
                'paths': {},
                'user': {},
            }
        self.cfg_load_patch = patch(
            'src.utils.config.config_loader.ConfigLoader.load_config',
            new=_fake_load_config
        )
        self.cfg_paths_patch = patch(
            'src.utils.config.config_loader.ConfigLoader.get_paths',
            return_value={
                'models': str(Path(self.tmpdir.name) / 'models'),
                'data': str(Path(self.tmpdir.name) / 'data'),
                'logs': str(Path(self.tmpdir.name) / 'logs'),
                'results': str(Path(self.tmpdir.name) / 'results'),
                'test_data': str(Path(self.tmpdir.name) / 'data' / 'processed' / 'all_test_aggregation.pickle'),
                'train_data': str(Path(self.tmpdir.name) / 'data' / 'processed' / 'all_training_aggregation.pickle'),
                'database': str(Path(self.tmpdir.name) / 'mouse_data.db'),
                'user_config': str(self.user_config_path),
            }
        )

        # 注入假的 pynput
        self.sys_modules_patch = patch.dict(sys.modules, { 'pynput': self.fake_pynput })

        self.cfg_load_patch.start()
        self.cfg_paths_patch.start()
        self.sys_modules_patch.start()

        # 导入 UserManager 模块后再做其余补丁
        import src.core.user_manager as um
        self.um_mod = um

        # 强制标记可用
        self.kb_available_patch = patch.object(self.um_mod, 'KEYBOARD_AVAILABLE', True)
        self.kb_available_patch.start()

    def tearDown(self):
        self.kb_available_patch.stop()
        self.sys_modules_patch.stop()
        self.cfg_paths_patch.stop()
        self.cfg_load_patch.stop()
        self.tmpdir.cleanup()

    def test_keyboard_sequence_triggers_callback(self):
        user_manager = self.um_mod.UserManager()

        # 用事件标记回调是否被触发
        triggered = threading.Event()

        def on_trigger_alert(user_id=None):
            triggered.set()

        user_manager.register_callback('trigger_alert', on_trigger_alert)

        # 启动键盘监听线程
        user_manager.start_keyboard_listener()

        # 等待回调触发（超时保护）
        self.assertTrue(triggered.wait(timeout=3), "应当在连续按下 'a' x4 后触发告警回调")

        # 停止监听
        user_manager.stop_keyboard_listener()


if __name__ == '__main__':
    unittest.main()


