#!/usr/bin/env python3
"""
GitHub Actions Runner Environment Validation Script

This script validates that a self-hosted runner environment is properly configured
for building PyDTATransferLog executables.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


class Colors:
    """Terminal color codes for output formatting."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []
        self.warnings_list = []
    
    def add_pass(self, message):
        """Add a passing validation."""
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
        self.passed += 1
    
    def add_fail(self, message, error=None):
        """Add a failing validation."""
        print(f"{Colors.RED}✗{Colors.END} {message}")
        self.failed += 1
        if error:
            self.errors.append(f"{message}: {error}")
        else:
            self.errors.append(message)
    
    def add_warning(self, message):
        """Add a warning."""
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
        self.warnings += 1
        self.warnings_list.append(message)
    
    def add_info(self, message):
        """Add informational message."""
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")
    
    def summary(self):
        """Print validation summary."""
        print(f"\n{Colors.BOLD}=== Validation Summary ==={Colors.END}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")
        
        if self.failed > 0:
            print(f"\n{Colors.RED}Errors that must be fixed:{Colors.END}")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings > 0:
            print(f"\n{Colors.YELLOW}Warnings (recommended to fix):{Colors.END}")
            for warning in self.warnings_list:
                print(f"  - {warning}")
        
        return self.failed == 0


def run_command(command, capture_output=True):
    """Run a command and return the result."""
    try:
        if isinstance(command, str):
            command = command.split()
        
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    except Exception:
        return None


def check_system_info(result: ValidationResult):
    """Check basic system information."""
    print(f"\n{Colors.BOLD}=== System Information ==={Colors.END}")
    
    # Platform info
    system = platform.system()
    release = platform.release()
    machine = platform.machine()
    
    result.add_info(f"Platform: {system} {release} ({machine})")
    
    # Check if this is RHEL9
    if system == "Linux":
        try:
            with open("/etc/redhat-release", "r") as f:
                rhel_info = f.read().strip()
                result.add_info(f"RHEL Info: {rhel_info}")
                if "release 9" in rhel_info.lower():
                    result.add_pass("RHEL9 detected")
                else:
                    result.add_warning("Not RHEL9 - ensure Python 3.11+ is available")
        except FileNotFoundError:
            result.add_info("Not a RHEL system")
    
    # Check available disk space
    try:
        stat = os.statvfs('.')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        if free_gb >= 10:
            result.add_pass(f"Sufficient disk space: {free_gb:.1f} GB free")
        elif free_gb >= 5:
            result.add_warning(f"Low disk space: {free_gb:.1f} GB free (10GB+ recommended)")
        else:
            result.add_fail(f"Insufficient disk space: {free_gb:.1f} GB free (minimum 5GB required)")
    except Exception as e:
        result.add_warning(f"Could not check disk space: {e}")


def check_python_installation(result: ValidationResult):
    """Check Python 3.11 installation and configuration."""
    print(f"\n{Colors.BOLD}=== Python Installation ==={Colors.END}")
    
    # List of Python commands to try
    python_commands = ['python3.11', 'python3', 'python']
    python_cmd = None
    python_version = None
    
    for cmd in python_commands:
        cmd_result = run_command([cmd, '--version'])
        if cmd_result and cmd_result.returncode == 0:
            version_output = cmd_result.stdout.strip()
            if "Python 3.11" in version_output or "Python 3.1" in version_output:
                python_cmd = cmd
                python_version = version_output
                break
    
    if python_cmd:
        result.add_pass(f"Python found: {python_version} (command: {python_cmd})")
        
        # Check Python version compatibility
        version_check = run_command([
            python_cmd, '-c',
            'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"); sys.exit(0 if sys.version_info >= (3, 11) else 1)'
        ])
        
        if version_check and version_check.returncode == 0:
            version = version_check.stdout.strip()
            result.add_pass(f"Python version compatible: {version}")
        else:
            result.add_fail("Python version is less than 3.11")
        
        # Check pip
        pip_result = run_command([python_cmd, '-m', 'pip', '--version'])
        if pip_result and pip_result.returncode == 0:
            result.add_pass(f"Pip available: {pip_result.stdout.strip()}")
        else:
            result.add_fail("Pip not available or not working")
        
        # Check if we can import key modules
        modules_to_check = ['sys', 'os', 'subprocess', 'pathlib', 'zipfile', 'tarfile']
        for module in modules_to_check:
            import_result = run_command([python_cmd, '-c', f'import {module}'])
            if import_result and import_result.returncode == 0:
                result.add_pass(f"Can import {module}")
            else:
                result.add_fail(f"Cannot import {module}")
    
    else:
        result.add_fail("Python 3.11+ not found. Please install Python 3.11 or later.")
    
    return python_cmd


def check_build_dependencies(result: ValidationResult, python_cmd):
    """Check build dependencies and tools."""
    print(f"\n{Colors.BOLD}=== Build Dependencies ==={Colors.END}")
    
    if not python_cmd:
        result.add_fail("Cannot check build dependencies without Python")
        return
    
    # Check PyInstaller
    pyinstaller_result = run_command([python_cmd, '-m', 'PyInstaller', '--version'])
    if pyinstaller_result and pyinstaller_result.returncode == 0:
        version = pyinstaller_result.stdout.strip()
        result.add_pass(f"PyInstaller available: {version}")
    else:
        result.add_warning("PyInstaller not installed - will be installed during build")
    
    # Check Git
    git_result = run_command(['git', '--version'])
    if git_result and git_result.returncode == 0:
        result.add_pass(f"Git available: {git_result.stdout.strip()}")
    else:
        result.add_fail("Git not found - required for version control")
    
    # Check archive tools
    tools = ['tar', 'gzip', 'zip', 'unzip']
    for tool in tools:
        if shutil.which(tool):
            result.add_pass(f"{tool} available")
        else:
            result.add_warning(f"{tool} not found - may be needed for packaging")


def check_project_structure(result: ValidationResult):
    """Check if we're in a valid project directory."""
    print(f"\n{Colors.BOLD}=== Project Structure ==={Colors.END}")
    
    required_files = [
        'main.spec',
        'requirements.txt',
        'src/main.py',
        'src/config.ini',
        'scripts/update_version.py'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            result.add_pass(f"Found: {file_path}")
        else:
            result.add_fail(f"Missing: {file_path}")
    
    # Check source structure
    src_files = [
        'src/models/log_model.py',
        'src/utils/config_manager.py',
        'src/ui/app_window.py'
    ]
    
    for file_path in src_files:
        if Path(file_path).exists():
            result.add_pass(f"Found: {file_path}")
        else:
            result.add_warning(f"Missing: {file_path}")


def check_runner_environment(result: ValidationResult):
    """Check GitHub Actions runner specific environment."""
    print(f"\n{Colors.BOLD}=== Runner Environment ==={Colors.END}")
    
    # Check if we're in a GitHub Actions environment
    if os.getenv('GITHUB_ACTIONS'):
        result.add_info("Running in GitHub Actions environment")
        
        # Check GitHub specific environment variables
        github_vars = [
            'GITHUB_WORKSPACE',
            'GITHUB_REPOSITORY',
            'GITHUB_SHA',
            'RUNNER_OS'
        ]
        
        for var in github_vars:
            value = os.getenv(var)
            if value:
                result.add_pass(f"{var}: {value}")
            else:
                result.add_warning(f"{var} not set")
    else:
        result.add_info("Not running in GitHub Actions (manual validation)")
    
    # Check if we can write to the current directory
    try:
        test_file = Path('.github_runner_test')
        test_file.write_text('test')
        test_file.unlink()
        result.add_pass("Write permissions verified")
    except Exception as e:
        result.add_fail(f"Cannot write to current directory: {e}")


def check_network_connectivity(result: ValidationResult):
    """Check network connectivity to required services."""
    print(f"\n{Colors.BOLD}=== Network Connectivity ==={Colors.END}")
    
    # Check GitHub connectivity
    github_result = run_command(['curl', '-s', '-I', 'https://github.com'])
    if github_result and github_result.returncode == 0:
        result.add_pass("GitHub connectivity verified")
    else:
        result.add_warning("Cannot verify GitHub connectivity (curl not available or network issues)")
    
    # Check PyPI connectivity
    pypi_result = run_command(['curl', '-s', '-I', 'https://pypi.org'])
    if pypi_result and pypi_result.returncode == 0:
        result.add_pass("PyPI connectivity verified")
    else:
        result.add_warning("Cannot verify PyPI connectivity (curl not available or network issues)")


def main():
    """Main validation function."""
    print(f"{Colors.BOLD}GitHub Actions Runner Environment Validation{Colors.END}")
    print(f"PyDTATransferLog Build Environment Checker\n")
    
    result = ValidationResult()
    
    # Run all validation checks
    check_system_info(result)
    python_cmd = check_python_installation(result)
    check_build_dependencies(result, python_cmd)
    check_project_structure(result)
    check_runner_environment(result)
    check_network_connectivity(result)
    
    # Print summary and exit with appropriate code
    success = result.summary()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Environment validation passed!{Colors.END}")
        print("The runner environment is ready for building PyDTATransferLog.")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Environment validation failed!{Colors.END}")
        print("Please fix the errors above before running builds.")
        sys.exit(1)


if __name__ == '__main__':
    main()