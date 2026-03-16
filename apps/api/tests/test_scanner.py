"""Tests for the static code scanner."""

import pytest

from app.games.scanner import DenylistStrategy, scan_code


def test_clean_pygame_code_passes():
    """Standard pygame code with safe imports should pass."""
    code = '''
import pygame
import random
import math
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
'''
    result = scan_code(code)
    assert result.passed is True
    assert len(result.findings) == 0


def test_import_os_fails():
    """Importing os module should fail (critical)."""
    code = "import os\nos.system('ls')"
    result = scan_code(code)
    assert result.passed is False
    assert result.critical_count >= 1


def test_import_subprocess_fails():
    """Importing subprocess should fail (critical)."""
    code = "import subprocess\nsubprocess.run(['ls'])"
    result = scan_code(code)
    assert result.passed is False
    assert result.critical_count >= 1


def test_eval_fails():
    """Using eval() should fail (critical)."""
    code = "x = eval('1 + 2')"
    result = scan_code(code)
    assert result.passed is False


def test_exec_fails():
    """Using exec() should fail (critical)."""
    code = "exec('import os')"
    result = scan_code(code)
    assert result.passed is False


def test_open_fails():
    """Using open() should fail (high)."""
    code = "f = open('/etc/passwd', 'r')"
    result = scan_code(code)
    assert result.passed is False
    assert result.high_count >= 1


def test_socket_fails():
    """Importing socket should fail (critical)."""
    code = "import socket\ns = socket.socket()"
    result = scan_code(code)
    assert result.passed is False


def test_dunder_import_fails():
    """Using __import__() should fail (critical)."""
    code = "__import__('os').system('ls')"
    result = scan_code(code)
    assert result.passed is False


def test_comments_ignored():
    """Dangerous patterns in comments should not trigger findings."""
    code = "# import os  -- this is just a comment\nimport pygame"
    result = scan_code(code)
    assert result.passed is True


def test_medium_findings_pass():
    """Medium severity findings should not fail the scan."""
    code = "import pickle\ndata = pickle.loads(b'test')"
    result = scan_code(code)
    assert result.passed is True
    assert len(result.findings) > 0
    assert all(f.severity == "medium" for f in result.findings)


def test_multiple_findings():
    """Code with multiple issues should report all of them."""
    code = "import os\nimport subprocess\neval('x')\nexec('y')"
    result = scan_code(code)
    assert result.passed is False
    assert len(result.findings) >= 4


def test_from_import_detected():
    """from X import Y patterns should be detected."""
    code = "from os import path"
    result = scan_code(code)
    assert result.passed is False


def test_strategy_is_pluggable():
    """DenylistStrategy can be instantiated independently."""
    strategy = DenylistStrategy()
    result = strategy.scan("import pygame\nprint('hello')")
    assert result.passed is True
