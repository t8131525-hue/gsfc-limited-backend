import os
import shutil

def delete_pycache_dirs(root_dir):
    pycache_count = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Deleted: {pycache_path}")
                pycache_count += 1
            except Exception as e:
                print(f"Failed to delete {pycache_path}: {e}")
    
    print(f"\n✅ Done. Deleted {pycache_count} '__pycache__' folders.")

if __name__ == "__main__":
    # Set the root directory to the current working directory
    project_root = os.getcwd()
    print(f"Scanning for __pycache__ folders in: {project_root}")
    delete_pycache_dirs(project_root)
    
