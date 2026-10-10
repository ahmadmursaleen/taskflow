"""Offline regression tests: all Git mutations are confined to temporary repos."""
import argparse
import copy
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agents
import quality
import setup_codex


class ProviderTests(unittest.TestCase):
    def test_plain_windows_import_does_not_restart_importer(self):
        p = subprocess.run([sys.executable, '-c', 'import agents; print("import completed")'],
                           cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
                           env={k: v for k, v in os.environ.items() if k != 'PYTHONUTF8'})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn('import completed', p.stdout)

    def test_selection_and_override(self):
        with patch.dict(os.environ, {}, clear=True):
            a = argparse.Namespace(provider=None, cmd=None, yolo=False)
            self.assertEqual(agents.provider_command(a), ('claude', agents.DEFAULT_CMD))
            a.provider = 'codex'
            self.assertEqual(agents.provider_command(a)[1], agents.CODEX_CMD)
            a.yolo = True
            self.assertEqual(agents.provider_command(a)[1], agents.CODEX_YOLO_CMD)
            a.cmd = 'python fake.py'
            self.assertEqual(agents.provider_command(a), ('codex', a.cmd))
            a.provider, a.cmd = 'custom', None
            with self.assertRaises(ValueError):
                agents.provider_command(a)

    def test_environment_selection(self):
        with patch.dict(os.environ, {'AGENT_PROVIDER': 'codex', 'AGENT_CMD': 'fake'}):
            a = argparse.Namespace(provider=None, cmd=None, yolo=False)
            self.assertEqual(agents.provider_command(a), ('codex', 'fake'))
            a.provider, a.cmd = 'claude', 'explicit'
            self.assertEqual(agents.provider_command(a), ('claude', 'explicit'))

    def test_codex_events(self):
        cases = [
            ({'type': 'turn.completed'}, ('finished: Codex turn', 'Codex turn completed')),
            ({'type': 'turn.failed', 'error': {'message': 'oops'}}, ('failed: oops', None)),
            ({'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'git status'}}, ('$ git status', None)),
            ({'type': 'item.updated', 'item': {'type': 'file_change', 'changes': [{'path': 'a.py'}]}}, ('editing a.py', None)),
            ({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'hello'}}, ('» hello', None)),
            ({'type': 'thread.started', 'thread_id': 'x'}, (None, None)),
            ([], (None, None)),
        ]
        for event, expected in cases:
            with self.subTest(event=event):
                self.assertEqual(agents.describe(json.dumps(event), '.'), expected)
        self.assertEqual(agents.describe('plain output', '.'), ('plain output', None))

    def test_limit_requires_error_event(self):
        self.assertIsNone(agents.codex_limit_info(json.dumps({'type': 'item.completed', 'item': {'type': 'command_execution', 'aggregated_output': '429 rate limit'}})))
        self.assertIsNotNone(agents.codex_limit_info(json.dumps({'type': 'error', 'message': 'rate limit reached|1900000000'})))

    def test_windows_npm_keeps_prompt_literal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            shim = root / 'codex.cmd'
            launcher = root / 'node_modules/@openai/codex/bin/codex.js'
            launcher.parent.mkdir(parents=True)
            launcher.write_text('fake')
            prompt = 'quotes " & echo BAD | $(secret) %PATH%\nnext'
            with patch.object(agents, 'WINDOWS', True), patch.object(agents.shutil, 'which', side_effect=lambda x: str(shim) if x == 'codex' else 'node.exe'):
                argv = agents.agent_argv('codex exec --json', prompt)
            self.assertEqual(argv, ['node.exe', str(launcher), 'exec', '--json', prompt])

    def test_windows_unknown_shim_refused(self):
        with patch.object(agents, 'WINDOWS', True), patch.object(agents.shutil, 'which', return_value='custom.cmd'):
            with self.assertRaises(ValueError):
                agents.agent_argv('custom', 'literal & prompt')


class InstallerTests(unittest.TestCase):
    def test_helper_configuration_names_and_role_instructions(self):
        root = Path(__file__).resolve().parents[1]
        reports = {'test-writer': 'tests.md', 'code-reviewer': 'review.md', 'fixer': 'fixes.md'}
        names = set()
        for filename, report in reports.items():
            with self.subTest(role=filename):
                config = tomllib.loads((root / 'templates/codex-agents' / (filename + '.toml')).read_text(encoding='utf-8'))
                self.assertRegex(config['name'], r'^[a-z0-9_]+$')
                self.assertEqual(config['name'], filename.replace('-', '_'))
                self.assertNotIn(config['name'], names)
                names.add(config['name'])
                self.assertGreater(len(config['description'].strip()), 40)
                instructions = config['developer_instructions']
                self.assertIn(f'.codex/taskflow/roles/{filename}.md', instructions)
                self.assertIn(f'reviews/<task-id>/{report}', instructions)
                self.assertIn('reviewed revision', instructions)
                self.assertIn('Do not manipulate Taskflow state', instructions)
                self.assertIn('commit, push, merge, rebase, change branches', instructions)
                self.assertIn('parent', instructions)

    def test_preserves_config_and_agents_idempotently(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / '.codex').mkdir()
            (root / '.codex/config.toml').write_text('user setting')
            (root / 'AGENTS.md').write_text('User instructions\n')
            setup_codex.install(root)
            self.assertEqual((root / '.codex/config.toml').read_text(), 'user setting')
            self.assertTrue((root / 'AGENTS.md').read_text().startswith('User instructions'))
            self.assertEqual(setup_codex.install(root), [])
            role = (root / '.codex/taskflow/roles/test-writer.md').read_text()
            self.assertIn('task coverage scope', role)
            self.assertFalse(role.startswith('---'))

    def test_conflict_is_atomic_and_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'agents.py').write_text('user code')
            with self.assertRaisesRegex(ValueError, 'existing files differ'):
                setup_codex.install(root)
            self.assertFalse((root / 'quality.py').exists())
            setup_codex.install(root, overwrite=True, dry_run=True)
            self.assertEqual((root / 'agents.py').read_text(), 'user code')
            self.assertFalse((root / 'quality.py').exists())

    def test_malformed_managed_markers_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'AGENTS.md').write_text(setup_codex.START + '\nuser text')
            with self.assertRaisesRegex(ValueError, 'malformed'):
                setup_codex.install(root)


class GitProject:
    def __init__(self, root):
        self.ROOT = root

    def git(self, *args, check=True):
        return subprocess.run(['git', *args], cwd=self.ROOT, capture_output=True, text=True, check=check, encoding='utf-8')

    def write(self, name, text):
        p = self.ROOT / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'fixture')


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = GitProject(Path(self.tmp.name))
        self.p.git('init', '-q')
        self.p.git('config', 'user.name', 'Fictional Tester')
        self.p.git('config', 'user.email', 'tester@example.invalid')
        self.p.write('.taskquality', 'required\n')
        self.p.write('production.py', 'print(1)\n')
        self.p.commit()
        self.rev = self.p.git('rev-parse', 'HEAD').stdout.strip()
        self.task = {'id': 'sample'}
        self.q = {'schema_version': 1, 'task_id': 'sample', 'reviewed_revision': self.rev,
                  'helpers': {'test-writer': {'status': 'completed', 'report': 'reviews/sample/tests.md'},
                              'code-reviewer': {'status': 'completed', 'report': 'reviews/sample/review.md'},
                              'fixer': {'status': 'not_required', 'reason': 'no findings'}},
                  'fixes_required': False, 'findings': [],
                  'validation': {'status': 'passed', 'command': 'python -m unittest'},
                  'coverage': {'status': 'unavailable', 'reason': 'no configured provider'}}

    def evidence(self, commit=True):
        self.p.write('reviews/sample/quality.json', json.dumps(self.q))
        for name in ('tests.md', 'review.md', 'fixes.md'):
            self.p.write('reviews/sample/' + name, f'Task sample reviewed revision {self.rev}\nConcrete validation evidence.\n')
        if commit:
            self.p.commit()

    def test_valid_and_bookkeeping_changes(self):
        self.evidence()
        self.assertIsNone(quality.validate(self.p, self.task))
        self.p.write('tasks/sample.md', 'bookkeeping')
        self.p.commit()
        self.assertIsNone(quality.validate(self.p, self.task))

    def test_missing_and_uncommitted_evidence(self):
        self.assertIn('commit reviews', quality.validate(self.p, self.task))
        self.evidence(commit=False)
        self.assertIn('commit reviews', quality.validate(self.p, self.task))

    def test_stale(self):
        self.evidence()
        self.p.write('production.py', 'print(2)\n')
        self.p.commit()
        self.assertIn('stale', quality.validate(self.p, self.task))

    def test_equivalent_rebase_preserves_fresh_evidence(self):
        # A rewritten implementation commit can have an identical project tree.
        tree = self.p.git('rev-parse', 'HEAD^{tree}').stdout.strip()
        rebased = self.p.git('commit-tree', tree, '-m', 'equivalent rewritten implementation').stdout.strip()
        self.assertNotEqual(rebased, self.rev)
        self.p.git('update-ref', 'HEAD', rebased)
        self.evidence()
        self.assertIsNone(quality.validate(self.p, self.task))

    def test_wrong_task(self):
        self.q['task_id'] = 'other'
        self.evidence()
        self.assertIn('task_id must match', quality.validate(self.p, self.task))

    def test_required_fixes(self):
        self.q['fixes_required'] = True
        self.evidence()
        self.assertIn('fixer must complete', quality.validate(self.p, self.task))
        self.q['helpers']['fixer'] = {'status': 'completed', 'report': 'reviews/sample/fixes.md'}
        self.evidence()
        self.assertIsNone(quality.validate(self.p, self.task))

    def test_blocking_findings_and_validation(self):
        self.q['findings'] = [{'id': 'R1', 'blocking': True, 'disposition': 'accepted'}]
        self.evidence()
        self.assertIn('unresolved', quality.validate(self.p, self.task))
        self.q['findings'][0]['disposition'] = 'resolved'
        self.q['validation']['status'] = 'failed'
        self.evidence()
        self.assertIn('passed command', quality.validate(self.p, self.task))

    def test_missing_committed_report(self):
        self.evidence()
        self.p.git('rm', 'reviews/sample/tests.md')
        self.p.commit()
        self.assertIn('must be committed', quality.validate(self.p, self.task))

    def test_placeholder_report(self):
        self.evidence()
        self.p.write('reviews/sample/tests.md', f'sample {self.rev}\nTODO\n')
        self.p.commit()
        self.assertIn('placeholder', quality.validate(self.p, self.task))

    def test_exemption_requires_reason(self):
        self.task['quality'] = 'exempt'
        self.assertIn('quality_reason', quality.validate(self.p, self.task))
        self.task['quality_reason'] = 'planning documentation only'
        self.assertIsNone(quality.validate(self.p, self.task))


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.remote = root / 'remote.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(self.remote)], check=True)
        clone = root / 'worker'
        clone.mkdir()
        self.p = GitProject(clone)
        self.p.git('init', '-q')
        self.p.git('checkout', '-qb', 'main')
        self.p.git('config', 'user.name', 'Fictional Worker')
        self.p.git('config', 'user.email', 'worker@example.invalid')
        for name in ('tasks.py', 'board.py', 'repos.py', 'quality.py'):
            shutil.copyfile(Path(__file__).resolve().parents[1] / name, clone / name)
        self.p.write('tasks/sample.md', '---\ntitle: Sample\nstatus: todo\nowner: \ndeps: []\n---\nTask\n')
        self.p.commit()
        self.p.git('remote', 'add', 'origin', str(self.remote))
        self.p.git('push', '-qu', 'origin', 'main')

    def cli(self, *args):
        env = dict(os.environ, TASK_OWNER='fictional-worker', TASKS_ROOT=str(self.p.ROOT), PYTHONUTF8='1')
        return subprocess.run([sys.executable, '-X', 'utf8', 'tasks.py', *args], cwd=self.p.ROOT,
                              env=env, capture_output=True, text=True, encoding='utf-8')

    def remote_file(self, path):
        return subprocess.run(['git', '--git-dir', str(self.remote), 'show', 'main:' + path], capture_output=True, text=True)

    def test_bookkeeping_does_not_publish_work_but_done_does(self):
        claimed = self.cli('claim', 'sample')
        self.assertEqual(claimed.returncode, 0, claimed.stdout + claimed.stderr)
        self.p.write('unfinished.py', 'print(1)')
        self.p.commit()
        assumed = self.cli('assume', 'sample', 'fictional assumption')
        self.assertEqual(assumed.returncode, 0, assumed.stdout + assumed.stderr)
        self.assertNotEqual(self.remote_file('unfinished.py').returncode, 0)
        self.assertIn('fictional assumption', self.remote_file('tasks/sample.md').stdout)
        done = self.cli('done', 'sample', '--skip-check')
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.remote_file('unfinished.py').returncode, 0)
        self.assertIn('status: done', self.remote_file('tasks/sample.md').stdout)

    def test_force_skip_cannot_bypass_quality_or_publish_work(self):
        self.p.write('.taskquality', 'required\n')
        self.p.commit()
        self.p.git('push', '-q')
        self.assertEqual(self.cli('claim', 'sample').returncode, 0)
        self.p.write('unfinished.py', 'print(1)')
        self.p.commit()
        done = self.cli('done', 'sample', '--force', '--skip-check')
        self.assertNotEqual(done.returncode, 0)
        self.assertIn('quality.json', done.stdout + done.stderr)
        self.assertIn('QUALITY REQUIRED', done.stdout + done.stderr)
        self.assertNotIn('no longer yours', done.stdout + done.stderr)
        self.assertNotEqual(self.remote_file('unfinished.py').returncode, 0)
        self.assertIn('status: in_progress', self.remote_file('tasks/sample.md').stdout)
        self.assertIn('owner: fictional-worker', self.remote_file('tasks/sample.md').stdout)

    def test_real_runner_fake_codex_claim_backup_release_complete(self):
        # The fake worker emits no CLAIMED output. Ownership must come from Git.
        script = self.p.ROOT.parent / 'fake_codex.py'
        phase = self.p.ROOT.parent / 'phase.txt'
        script.write_text('''import json, pathlib, subprocess, sys, time
phase = pathlib.Path(__file__).with_name('phase.txt')
n = int(phase.read_text()) if phase.exists() else 0
def run(*args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode:
        print(p.stdout + p.stderr, flush=True)
        sys.exit(p.returncode)
if n == 0:
    run(sys.executable, 'tasks.py', 'claim', 'sample')
    pathlib.Path('runner-work.py').write_text('print(123)')
    run('git', 'add', 'runner-work.py')
    run('git', 'commit', '-qm', 'fake implementation')
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'working'}}), flush=True)
    time.sleep(12)
elif n == 1:
    run('git', 'fetch', '-q', 'origin')
    run('git', 'cat-file', '-e', 'origin/wip/sample:runner-work.py')
    run(sys.executable, 'tasks.py', 'release', 'sample', '--note', 'offline handoff fixture')
else:
    run(sys.executable, 'tasks.py', 'claim', 'sample')
    run('git', 'fetch', '-q', 'origin')
    run('git', 'merge', '--no-edit', 'origin/wip/sample')
    run(sys.executable, 'tasks.py', 'done', 'sample', '--skip-check')
phase.write_text(str(n + 1))
print(json.dumps({'type':'turn.completed'}), end='', flush=True)
''', encoding='utf-8')
        (self.p.ROOT.parent / 'logs').mkdir()
        cmd = f'"{sys.executable}" -X utf8 "{script}"'
        runner = subprocess.run([sys.executable, '-X', 'utf8', str(Path(agents.__file__)),
                                 'run', 'fake', str(self.p.ROOT), '--owner', 'fictional-worker',
                                 '--provider', 'codex', '--cmd', cmd, '--lease', '40', '--timeout', '90'],
                                capture_output=True, text=True, encoding='utf-8', timeout=150)
        self.assertEqual(runner.returncode, 0, runner.stdout + runner.stderr)
        self.assertEqual(phase.read_text(), '3', runner.stdout + runner.stderr)
        self.assertIn('all tasks done', runner.stdout)
        self.assertIn('status: done', self.remote_file('tasks/sample.md').stdout)
        self.assertEqual(self.remote_file('runner-work.py').returncode, 0)
        status = json.loads((self.p.ROOT.parent / 'logs/fake.status.json').read_text())
        self.assertEqual(status['state'], 'finished')


if __name__ == '__main__':
    unittest.main()
