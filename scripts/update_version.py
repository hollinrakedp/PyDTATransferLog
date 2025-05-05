"""Extract and update version from version.txt file"""
import os
import re
import subprocess

def update_version():
    # Get the repository root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Read version.txt
    version_file_path = os.path.join(root_dir, 'version.txt')
    with open(version_file_path, 'r') as f:
        content = f.read()
    
    # Extract version components
    file_vers_match = re.search(r'filevers=\((\d+), (\d+), (\d+), (\d+)\)', content)
    if not file_vers_match:
        print("Failed to extract version information")
        return
        
    major, minor, build, revision = map(int, file_vers_match.groups())
    
    # Check if we need to increment the build number
    # Use git to determine if this is a new commit since last build
    try:
        # Get the current commit hash
        current_commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            universal_newlines=True
        ).strip()
        
        # Increment build number
        build += 1
        print(f"Incrementing build number to {build}")
        
        # Update version.txt with new build number
        new_content = content.replace(
            f'filevers=({major}, {minor}, {build-1}, {revision})', 
            f'filevers=({major}, {minor}, {build}, {revision})'
        )
        new_content = new_content.replace(
            f'prodvers=({major}, {minor}, {build-1}, {revision})', 
            f'prodvers=({major}, {minor}, {build}, {revision})'
        )
        new_content = new_content.replace(
            f"'FileVersion', '{major}.{minor}.{build-1}.{revision}'", 
            f"'FileVersion', '{major}.{minor}.{build}.{revision}'"
        )
        new_content = new_content.replace(
            f"'ProductVersion', '{major}.{minor}.{build-1}.{revision}'", 
            f"'ProductVersion', '{major}.{minor}.{build}.{revision}'"
        )
        
        # Write updated version.txt
        with open(version_file_path, 'w') as f:
            f.write(new_content)
            
        # Create version.py
        version_string = f"{major}.{minor}.{build}.{revision}"
        version_py_path = os.path.join(root_dir, 'src', 'version.py')
        with open(version_py_path, 'w') as f:
            f.write('"""Version information"""\n')
            f.write('# This file is automatically updated by the build process\n')
            f.write(f'VERSION = "{version_string}"\n')
            f.write(f'VERSION_TUPLE = ({major}, {minor}, {build}, {revision})\n')
            
        print(f"Updated version to {version_string}")
        
    except Exception as e:
        print(f"Error incrementing version: {e}")
        # Still create version.py with current version
        version_string = f"{major}.{minor}.{build}.{revision}"
        version_py_path = os.path.join(root_dir, 'src', 'version.py')
        with open(version_py_path, 'w') as f:
            f.write('"""Version information"""\n')
            f.write('# This file is automatically updated by the build process\n')
            f.write(f'VERSION = "{version_string}"\n')
            f.write(f'VERSION_TUPLE = ({major}, {minor}, {build}, {revision})\n')

if __name__ == "__main__":
    update_version()