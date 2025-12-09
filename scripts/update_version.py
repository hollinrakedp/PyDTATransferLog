"""Extract and update version from version.txt file"""
import os
import re
import subprocess
import sys
from datetime import datetime


def get_git_info():
    """Get git repository information safely."""
    try:
        # Check if we're in a git repository
        subprocess.check_output(['git', 'rev-parse', '--git-dir'], 
                               stderr=subprocess.DEVNULL, universal_newlines=True)
        
        # Get current commit hash
        current_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                               universal_newlines=True).strip()
        
        # Check if there are uncommitted changes
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                     capture_output=True, universal_newlines=True)
        has_changes = bool(status_result.stdout.strip())
        
        # Get commit count for this branch
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'], 
            universal_newlines=True
        ).strip()
        
        return {
            'commit': current_commit,
            'has_changes': has_changes,
            'commit_count': int(commit_count),
            'available': True
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {'available': False}


def update_version(increment_build=True, force=False):
    """
    Update version information in version.txt and create version.py
    
    Args:
        increment_build (bool): Whether to increment the build number
        force (bool): Force update even if no git changes detected
    """
    # Get the repository root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Read version.txt
    version_file_path = os.path.join(root_dir, 'version.txt')
    
    if not os.path.exists(version_file_path):
        print(f"ERROR: version.txt not found at {version_file_path}")
        sys.exit(1)
    
    try:
        with open(version_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Could not read version.txt: {e}")
        sys.exit(1)
    
    # Extract version components
    file_vers_match = re.search(r'filevers=\((\d+), (\d+), (\d+), (\d+)\)', content)
    if not file_vers_match:
        print("ERROR: Could not extract version information from version.txt")
        print("Expected format: filevers=(major, minor, build, revision)")
        sys.exit(1)
        
    major, minor, build, revision = map(int, file_vers_match.groups())
    original_build = build
    
    print(f"Current version: {major}.{minor}.{build}.{revision}")
    
    # Get git information
    git_info = get_git_info()
    
    # Determine if we should increment the build number
    should_increment = False
    
    if increment_build:
        if force:
            should_increment = True
            print("Force increment requested")
        elif not git_info['available']:
            print("WARNING: Git not available, incrementing build number anyway")
            should_increment = True
        else:
            # Check if this is a CI environment or if there are changes
            is_ci = os.getenv('CI') or os.getenv('GITHUB_ACTIONS')
            if is_ci:
                should_increment = True
                print("CI environment detected, incrementing build number")
            elif git_info['has_changes']:
                should_increment = True
                print("Uncommitted changes detected, incrementing build number")
            else:
                print("No changes detected, build number will not be incremented")
    
    if should_increment:
        build += 1
        print(f"Incrementing build number: {original_build} → {build}")
        
        # Update version.txt with new build number
        try:
            new_content = content.replace(
                f'filevers=({major}, {minor}, {original_build}, {revision})', 
                f'filevers=({major}, {minor}, {build}, {revision})'
            )
            new_content = new_content.replace(
                f'prodvers=({major}, {minor}, {original_build}, {revision})', 
                f'prodvers=({major}, {minor}, {build}, {revision})'
            )
            new_content = new_content.replace(
                f"'FileVersion', '{major}.{minor}.{original_build}.{revision}'", 
                f"'FileVersion', '{major}.{minor}.{build}.{revision}'"
            )
            new_content = new_content.replace(
                f"'ProductVersion', '{major}.{minor}.{original_build}.{revision}'", 
                f"'ProductVersion', '{major}.{minor}.{build}.{revision}'"
            )
            
            # Write updated version.txt
            with open(version_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"Updated version.txt with build number {build}")
            
        except Exception as e:
            print(f"ERROR: Could not update version.txt: {e}")
            sys.exit(1)
    
    # Create version.py
    version_string = f"{major}.{minor}.{build}.{revision}"
    version_py_path = os.path.join(root_dir, 'src', 'version.py')
    
    try:
        # Ensure src directory exists
        os.makedirs(os.path.dirname(version_py_path), exist_ok=True)
        
        # Build metadata
        build_time = datetime.utcnow().isoformat() + 'Z'
        
        version_py_content = f'''"""Version information"""
# This file is automatically updated by the build process
# DO NOT EDIT MANUALLY

VERSION = "{version_string}"
VERSION_TUPLE = ({major}, {minor}, {build}, {revision})
BUILD_TIME = "{build_time}"

# Version components
MAJOR = {major}
MINOR = {minor}
BUILD = {build}
REVISION = {revision}
'''
        
        # Add git information if available
        if git_info['available']:
            version_py_content += f'''
# Git information
GIT_COMMIT = "{git_info['commit'][:8]}"
GIT_COMMIT_FULL = "{git_info['commit']}"
GIT_COMMIT_COUNT = {git_info['commit_count']}
GIT_DIRTY = {git_info['has_changes']}
'''
        else:
            version_py_content += '''
# Git information (not available)
GIT_COMMIT = "unknown"
GIT_COMMIT_FULL = "unknown"
GIT_COMMIT_COUNT = 0
GIT_DIRTY = False
'''
        
        with open(version_py_path, 'w', encoding='utf-8') as f:
            f.write(version_py_content)
            
        print(f"Created version.py with version {version_string}")
        
        # Also create a simple version file for easy reading
        simple_version_path = os.path.join(root_dir, 'VERSION')
        with open(simple_version_path, 'w', encoding='utf-8') as f:
            f.write(f"{version_string}\n")
            
    except Exception as e:
        print(f"ERROR: Could not create version.py: {e}")
        sys.exit(1)
    
    print(f"Version update complete: {version_string}")
    return version_string


def main():
    """Main entry point with argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update version information for PyDTATransferLog'
    )
    parser.add_argument(
        '--no-increment', 
        action='store_true',
        help='Do not increment build number, just regenerate version.py'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force increment build number even if no changes detected'
    )
    parser.add_argument(
        '--check', 
        action='store_true',
        help='Just check current version without updating'
    )
    
    args = parser.parse_args()
    
    if args.check:
        # Just show current version
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        version_file_path = os.path.join(root_dir, 'version.txt')
        
        if os.path.exists(version_file_path):
            with open(version_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_vers_match = re.search(r'filevers=\((\d+), (\d+), (\d+), (\d+)\)', content)
            if file_vers_match:
                major, minor, build, revision = map(int, file_vers_match.groups())
                print(f"{major}.{minor}.{build}.{revision}")
            else:
                print("ERROR: Could not parse version from version.txt")
                sys.exit(1)
        else:
            print("ERROR: version.txt not found")
            sys.exit(1)
    else:
        # Update version
        increment = not args.no_increment
        update_version(increment_build=increment, force=args.force)


if __name__ == "__main__":
    main()