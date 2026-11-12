"""Exercise the real installer shell with fake package/network commands; no downloads."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get('TEST_BASH') or shutil.which('bash')
SCRIPT = Path(os.environ.get('INSTALL_SCRIPT', ROOT/'scripts/install-dependencies.sh')).resolve()

def shell_path(path):
    value = str(path).replace('\\', '/')
    return '/' + value[0].lower() + value[2:] if len(value)>1 and value[1]==':' else value

class InstallerTests(unittest.TestCase):
    def run_installer(self, phase='', kind='transient'):
        with tempfile.TemporaryDirectory() as directory:
            work=Path(directory)
            (work/'python').write_text('''#!/usr/bin/env bash
case "$*" in
  *playwright*) phase=browser;;
  *requirements.txt*) phase=requirements;;
  *) phase=pip;;
esac
echo "$phase" >> "$STATE/trace"
count=$(grep -c "^$phase$" "$STATE/trace")
if [[ "$phase" == "$FAIL_PHASE" ]]; then
  if [[ "$FAIL_KIND" == permanent ]]; then echo 'ERROR: No matching distribution found'; exit 1; fi
  if [[ "$FAIL_KIND" == timeout && "$count" == 1 ]]; then exit 124; fi
  if [[ "$FAIL_KIND" == always || "$count" == 1 ]]; then
    echo "Temporary failure resolving 'security.ubuntu.com'"; exit 100
  fi
fi
echo "$phase completed"
''',encoding='utf-8',newline='\n')
            (work/'timeout').write_text('''#!/usr/bin/env bash
echo "$1 $2" >> "$STATE/timeouts"
shift 2
"$@"
''',encoding='utf-8',newline='\n')
            (work/'pip').write_text((work/'python').read_text(),encoding='utf-8',newline='\n')
            for p in (work/'python',work/'pip',work/'timeout'): p.chmod(0o755)
            env=dict(os.environ, STATE=shell_path(work), STUB_DIR=shell_path(work),
                INSTALL_SCRIPT=shell_path(SCRIPT), FAIL_PHASE=phase,FAIL_KIND=kind,
                INSTALL_RETRY_DELAY_SECONDS='0')
            # Exclude host package managers: every Python/pip invocation must hit a stub.
            result=subprocess.run([BASH,'-c','export PATH="$STUB_DIR:/usr/bin:/bin"; bash -e -o pipefail "$INSTALL_SCRIPT"'],
                env=env,capture_output=True,text=True,timeout=20)
            trace=(work/'trace').read_text().splitlines() if (work/'trace').exists() else []
            timers=(work/'timeouts').read_text().splitlines() if (work/'timeouts').exists() else []
            return result,trace,timers

    def test_dns_failure_recovers(self):
        r,trace,timers=self.run_installer('browser')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(trace,['pip','requirements','browser','browser'])
        self.assertEqual(timers,['--kill-after=10s 150s']*4)

    def test_pip_network_failure_recovers(self):
        r,trace,_=self.run_installer('requirements')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(trace,['pip','requirements','requirements','browser'])

    def test_persistent_dns_failure_stays_failed(self):
        r,trace,_=self.run_installer('browser','always')
        self.assertEqual(r.returncode,100)
        self.assertEqual(trace,['pip','requirements','browser','browser','browser'])

    def test_package_error_is_not_retried(self):
        r,trace,_=self.run_installer('requirements','permanent')
        self.assertEqual(r.returncode,1)
        self.assertEqual(trace,['pip','requirements'])

    def test_timeout_is_retried(self):
        r,trace,_=self.run_installer('browser','timeout')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(trace,['pip','requirements','browser','browser'])

    def test_success_runs_every_phase_once(self):
        r,trace,_=self.run_installer()
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(trace,['pip','requirements','browser'])

if __name__=='__main__': unittest.main()
