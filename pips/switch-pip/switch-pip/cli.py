#!/usr/bin/env python3
"""
switch-pip CLI v1.0.0
Switch pip index-url (package source) with one command.

Commands:
    switch-pip                  Interactive mode (asks for URL)
    switch-pip <URL>            Set index-url directly
    switch-pip --default        Reset to PyPI (https://pypi.org/simple/)
    switch-pip --show           Show current index-url
    switch-pip --list           Show switch history
    switch-pip --test           Test connection to current index-url
    switch-pip --backup         Backup pip.conf
    switch-pip --restore        Restore pip.conf from backup
    switch-pip --help           Show help
    switch-pip --version        Show version
"""

import os
import sys
import configparser
import datetime
import json
import shutil


DEFAULT_INDEX = "https://pypi.org/simple/"
VERSION = "1.0.0"

POPULAR_MIRRORS = {
    "pypi": "https://pypi.org/simple/",
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "aliyun": "https://mirrors.aliyun.com/pypi/simple/",
    "alibaba": "https://mirrors.aliyun.com/pypi/simple/",
    "douban": "https://pypi.doubanio.com/simple/",
    "testpypi": "https://test.pypi.org/simple/",
}


def get_pip_conf_dir():
    """Get pip config directory for current platform."""
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "pip")

    home = os.path.expanduser("~")

    if sys.platform == "darwin":
        mac_path = os.path.join(home, "Library", "Application Support", "pip")
        if os.path.exists(mac_path):
            return mac_path
        return os.path.join(home, ".config", "pip")

    return os.path.join(home, ".config", "pip")


def get_pip_conf_path():
    """Get full path to pip.conf."""
    conf_dir = get_pip_conf_dir()
    if sys.platform == "win32":
        return os.path.join(conf_dir, "pip.ini")
    return os.path.join(conf_dir, "pip.conf")


def get_history_path():
    """Get path to switch history file."""
    return os.path.join(get_pip_conf_dir(), "switch-pip-history.json")


def read_pip_conf():
    """Read current pip.conf and return ConfigParser object."""
    conf_path = get_pip_conf_path()
    config = configparser.ConfigParser()
    if os.path.exists(conf_path):
        config.read(conf_path)
    return config


def write_pip_conf(config):
    """Write ConfigParser to pip.conf."""
    conf_path = get_pip_conf_path()
    conf_dir = os.path.dirname(conf_path)
    os.makedirs(conf_dir, exist_ok=True)
    with open(conf_path, "w") as f:
        config.write(f)


def get_current_index():
    """Get current index-url from pip.conf."""
    config = read_pip_conf()
    if config.has_section("global") and config.has_option("global", "index-url"):
        return config.get("global", "index-url")
    return DEFAULT_INDEX


def set_index_url(url, trust_host=True):
    """Set new index-url in pip.conf."""
    config = read_pip_conf()

    if not config.has_section("global"):
        config.add_section("global")

    config.set("global", "index-url", url)

    if trust_host and url != DEFAULT_INDEX:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname
            if host:
                config.set("global", "trusted-host", host)
        except Exception:
            pass
    elif url == DEFAULT_INDEX:
        if config.has_option("global", "trusted-host"):
            config.remove_option("global", "trusted-host")

    write_pip_conf(config)
    add_history(url)


def add_history(url):
    """Add entry to switch history."""
    history_path = get_history_path()
    history = []

    if os.path.exists(history_path):
        try:
            with open(history_path, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "is_default": url == DEFAULT_INDEX,
    }
    history.append(entry)

    if len(history) > 50:
        history = history[-50:]

    conf_dir = os.path.dirname(history_path)
    os.makedirs(conf_dir, exist_ok=True)

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def show_current():
    """Show current pip index-url configuration."""
    current = get_current_index()
    conf_path = get_pip_conf_path()

    print()
    if current == DEFAULT_INDEX:
        print("\033[36m\U0001f4e6 Current pip index-url:\033[0m")
        print(f"   \033[33m{current}\033[0m")
        print("   \033[90m(default PyPI)\033[0m")
    else:
        print("\033[36m\U0001f4e6 Current pip index-url:\033[0m")
        print(f"   \033[33m{current}\033[0m")
        print("   \033[90m(custom mirror)\033[0m")

    config = read_pip_conf()
    if config.has_section("global") and config.has_option("global", "trusted-host"):
        host = config.get("global", "trusted-host")
        print(f"   \033[90mtrusted-host: {host}\033[0m")

    print(f"   \033[90mConfig: {conf_path}\033[0m")
    exists = os.path.exists(conf_path)
    print(f"   \033[90mFile exists: {'yes' if exists else 'no'}\033[0m")
    print()


def show_history():
    """Show switch history."""
    history_path = get_history_path()

    if not os.path.exists(history_path):
        print()
        print("\033[90mNo switch history yet.\033[0m")
        print()
        return

    try:
        with open(history_path, "r") as f:
            history = json.load(f)
    except Exception:
        print("\033[31mError reading history.\033[0m")
        return

    if not history:
        print()
        print("\033[90mNo switch history yet.\033[0m")
        print()
        return

    print()
    print("\033[36m\U0001f4cb Switch history:\033[0m")
    print()
    for i, entry in enumerate(history, 1):
        ts = entry.get("timestamp", "?")
        url = entry.get("url", "?")
        is_def = entry.get("is_default", False)
        marker = " \033[32m(default)\033[0m" if is_def else ""
        print(f"   {i:>3}. \033[90m{ts}\033[0m \033[33m{url}\033[0m{marker}")
    print()


def test_connection():
    """Test connection to current index-url."""
    current = get_current_index()
    print()
    print(f"\033[36m\U0001f50d Testing connection to:\033[0m")
    print(f"   \033[33m{current}\033[0m")
    print()

    import time
    start = time.time()

    try:
        import urllib.request
        req = urllib.request.Request(current, method="HEAD")
        req.add_header("User-Agent", "switch-pip/1.0")
        response = urllib.request.urlopen(req, timeout=10)
        elapsed = time.time() - start
        code = response.getcode()
        print(f"   \033[32m\u2705 Available! (HTTP {code}, {elapsed:.2f}s)\033[0m")
    except Exception as e:
        elapsed = time.time() - start
        err_code = getattr(e, "code", None)
        if err_code and err_code in (403, 405):
            print(f"   \033[32m\u2705 Available! (HTTP {err_code}, {elapsed:.2f}s)\033[0m")
        else:
            print(f"   \033[31m\u274c Connection failed: {e} ({elapsed:.2f}s)\033[0m")

    print()


def backup_config():
    """Backup pip.conf."""
    conf_path = get_pip_conf_path()
    if not os.path.exists(conf_path):
        print()
        print("\033[33m\u26a0 No pip.conf found — nothing to backup.\033[0m")
        print()
        return

    backup_path = conf_path + ".backup"
    shutil.copy2(conf_path, backup_path)
    print()
    print(f"\033[32m\u2705 Backup created:\033[0m")
    print(f"   {backup_path}")
    print()


def restore_config():
    """Restore pip.conf from backup."""
    conf_path = get_pip_conf_path()
    backup_path = conf_path + ".backup"

    if not os.path.exists(backup_path):
        print()
        print(f"\033[31m\u274c No backup found at: {backup_path}\033[0m")
        print()
        return

    shutil.copy2(backup_path, conf_path)
    current = get_current_index()
    print()
    print(f"\033[32m\u2705 Config restored from backup!\033[0m")
    print(f"   Current index-url: \033[33m{current}\033[0m")
    print()


def set_default():
    """Reset to default PyPI."""
    set_index_url(DEFAULT_INDEX, trust_host=False)
    print()
    print(f"\033[32m\u2705 pip reset to default PyPI:\033[0m")
    print(f"   \033[33m{DEFAULT_INDEX}\033[0m")
    conf_path = get_pip_conf_path()
    print(f"   \033[90mConfig: {conf_path}\033[0m")
    print()


def interactive_set():
    """Interactive mode — ask user for URL."""
    print()
    print("\033[36m\U0001f517 Enter pip mirror URL (index-url):\033[0m")
    print()
    print("  Popular mirrors (type name or paste URL):")
    print("    \033[33mpypi\033[0m      — https://pypi.org/simple/")
    print("    \033[33mtsinghua\033[0m  — https://pypi.tuna.tsinghua.edu.cn/simple/")
    print("    \033[33maliyun\033[0m    — https://mirrors.aliyun.com/pypi/simple/")
    print("    \033[33mdouban\033[0m    — https://pypi.doubanio.com/simple/")
    print("    \033[33mtestpypi\033[0m  — https://test.pypi.org/simple/")
    print()

    try:
        url = input("\033[36m> \033[0m").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print("\033[90mCancelled.\033[0m")
        return

    if not url:
        print("\033[31mNo URL provided. Cancelled.\033[0m")
        return

    if url.lower() in POPULAR_MIRRORS:
        url = POPULAR_MIRRORS[url.lower()]

    if not url.startswith("http://") and not url.startswith("https://"):
        print("\033[31m\u274c URL must start with http:// or https://\033[0m")
        return

    if not url.endswith("/"):
        url += "/"

    old = get_current_index()
    set_index_url(url)

    print()
    print(f"\033[32m\u2705 pip index-url changed:\033[0m")
    print(f"   \033[90mOld: {old}\033[0m")
    print(f"   \033[33mNew: {url}\033[0m")
    conf_path = get_pip_conf_path()
    print(f"   \033[90mConfig: {conf_path}\033[0m")
    print()


def direct_set(url):
    """Set URL directly from argument."""
    if url.lower() in POPULAR_MIRRORS:
        url = POPULAR_MIRRORS[url.lower()]

    if not url.startswith("http://") and not url.startswith("https://"):
        print("\033[31m\u274c URL must start with http:// or https://\033[0m")
        sys.exit(1)

    if not url.endswith("/"):
        url += "/"

    old = get_current_index()
    set_index_url(url)

    print()
    print(f"\033[32m\u2705 pip index-url changed:\033[0m")
    print(f"   \033[90mOld: {old}\033[0m")
    print(f"   \033[33mNew: {url}\033[0m")
    conf_path = get_pip_conf_path()
    print(f"   \033[90mConfig: {conf_path}\033[0m")
    print()


def show_help():
    """Show help message."""
    print()
    print("\033[1mswitch-pip v1.0.0\033[0m — Switch pip package source easily")
    print()
    print("\033[1mUsage:\033[0m")
    print("  switch-pip                    Interactive mode")
    print("  switch-pip <URL>              Set index-url directly")
    print("  switch-pip <shortcut>         Use named mirror (pypi, tsinghua, aliyun...)")
    print("  switch-pip --default          Reset to https://pypi.org/simple/")
    print("  switch-pip --show             Show current index-url")
    print("  switch-pip --list             Show switch history")
    print("  switch-pip --test             Test connection to current mirror")
    print("  switch-pip --backup           Backup pip.conf")
    print("  switch-pip --restore          Restore pip.conf from backup")
    print("  switch-pip --help             Show this help")
    print("  switch-pip --version          Show version")
    print()
    print("\033[1mShortcuts:\033[0m")
    for name, url in POPULAR_MIRRORS.items():
        print(f"  {name:<12} {url}")
    print()
    print("\033[1mExamples:\033[0m")
    print("  switch-pip tsinghua")
    print("  switch-pip https://my-company.com/pypi/simple/")
    print("  switch-pip --default")
    print()


def main():
    args = sys.argv[1:]

    if not args:
        interactive_set()
        return

    arg = args[0]

    if arg in ("--help", "-h"):
        show_help()
    elif arg in ("--version", "-v"):
        print(f"switch-pip {VERSION}")
    elif arg in ("--default", "-d", "--reset"):
        set_default()
    elif arg in ("--show", "-s", "--current"):
        show_current()
    elif arg in ("--list", "-l", "--history"):
        show_history()
    elif arg in ("--test", "-t"):
        test_connection()
    elif arg in ("--backup", "-b"):
        backup_config()
    elif arg in ("--restore", "-r"):
        restore_config()
    elif arg.startswith("--"):
        print(f"\033[31mUnknown option: {arg}\033[0m")
        print("Use --help for usage info.")
        sys.exit(1)
    else:
        direct_set(arg)


if __name__ == "__main__":
    main()
