from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
from typing import Dict, Set, Tuple

from codev1.src.rag import loadRAG, embed_for_created_files, embed_for_updated_files, embed_for_deleted_files

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)
        # Initialize directory structure cache
        self.dir_cache: Dict[str, Set[str]] = {}
        self._init_dir_cache(self.base_path)
        self.reset_changes()
        loadRAG()
        
    def _init_dir_cache(self, path: str):
        """Initialize cache of directory structure"""
        for root, _, files in os.walk(path):
            abs_root = os.path.abspath(root)
            self.dir_cache[abs_root] = set(
                os.path.join(abs_root, f) for f in files
            )
    
    def _update_dir_cache(self, dir_path: str):
        """Update cache for a specific directory"""
        abs_path = os.path.abspath(dir_path)
        if os.path.exists(abs_path):
            self.dir_cache[abs_path] = set(
                os.path.join(abs_path, f) 
                for f in os.listdir(abs_path) 
                if os.path.isfile(os.path.join(abs_path, f))
            )
        elif abs_path in self.dir_cache:
            del self.dir_cache[abs_path]
            
    def reset_changes(self):
        """Reset all tracked changes"""
        self.created_files: Set[str] = set()
        self.modified_files: Set[str] = set()
        self.deleted_files: Set[str] = set()
    
    def on_created(self, event):
        if event.is_directory:
            self._update_dir_cache(event.src_path)
        else:
            self.created_files.add(event.src_path)
            dir_path = os.path.dirname(event.src_path)
            self._update_dir_cache(dir_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.modified_files.add(event.src_path)
    
    def on_deleted(self, event):
        if event.is_directory:
            # Get all files that were in this directory and its subdirectories
            deleted_prefix = os.path.abspath(event.src_path)
            for dir_path, files in list(self.dir_cache.items()):
                if dir_path.startswith(deleted_prefix):
                    self.deleted_files.update(files)
                    del self.dir_cache[dir_path]
        else:
            self.deleted_files.add(event.src_path)
            dir_path = os.path.dirname(event.src_path)
            self._update_dir_cache(dir_path)
    
    def on_moved(self, event):
        """Handle moved (renamed) files and directories"""
        if event.is_directory:
            # Handle all files in moved directory
            old_prefix = os.path.abspath(event.src_path)
            new_prefix = os.path.abspath(event.dest_path)
            
            # Track moves in cache
            for old_dir_path, files in list(self.dir_cache.items()):
                if old_dir_path.startswith(old_prefix):
                    # Calculate new path
                    rel_path = os.path.relpath(old_dir_path, old_prefix)
                    new_dir_path = os.path.join(new_prefix, rel_path)
                    
                    # Update cache with new paths
                    self.dir_cache[new_dir_path] = {
                        os.path.join(new_dir_path, os.path.basename(f))
                        for f in files
                    }
                    del self.dir_cache[old_dir_path]
                    
                    # Track file movements
                    self.deleted_files.update(files)
                    self.created_files.update(self.dir_cache[new_dir_path])
        else:
            self.deleted_files.add(event.src_path)
            self.created_files.add(event.dest_path)
            # Update cache for both old and new directories
            self._update_dir_cache(os.path.dirname(event.src_path))
            self._update_dir_cache(os.path.dirname(event.dest_path))
    
    def get_changes(self) -> Tuple[Set[str], Set[str], Set[str]]:
        """Return current changes and reset the tracking"""
        # Convert absolute paths to relative paths
        rel_created = {os.path.relpath(p, self.base_path) for p in self.created_files}
        rel_modified = {os.path.relpath(p, self.base_path) for p in self.modified_files}
        rel_deleted = {os.path.relpath(p, self.base_path) for p in self.deleted_files}
        
        self.reset_changes()
        return rel_created, rel_modified, rel_deleted

def monitor_directory(path: str, interval: float = 1.0):
    """
    Monitor a directory recursively for file changes.
    
    Args:
        path: Directory path to monitor
        interval: How often to check for changes (in seconds)
    
    Yields:
        Tuple of sets containing (created_files, modified_files, deleted_files)
        All paths are relative to the monitored directory
    """
    path = os.path.abspath(path)
    event_handler = FileChangeHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(interval)
            changes = event_handler.get_changes()
            if any(changes):  # Only yield if there are any changes
                yield changes
                
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

# Example usage
if __name__ == "__main__":
    directory_to_watch = "/Users/saravanan/base/code-assist/codev1/codev1/src"  # Current directory
    
    print(f"Monitoring directory: {os.path.abspath(directory_to_watch)}")
    print("Press Ctrl+C to stop monitoring")
    
    for created, modified, deleted in monitor_directory(directory_to_watch):
        print("\nChanges detected:")
        
        if created:
            print("\nCreated files:")
            for file in sorted(created):
                print(f"  + {file}")
                embed_for_created_files(directory_to_watch + "/" + file)
                
        if modified:
            print("\nModified files:")
            for file in sorted(modified):
                print(f"  ~ {file}")
                embed_for_updated_files(directory_to_watch + "/" + file)
                
        if deleted:
            print("\nDeleted files:")
            for file in sorted(deleted):
                print(f"  - {file}")
                embed_for_deleted_files(directory_to_watch + "/" + file)