from git import Repo
import os
from datetime import datetime

def show_git_differences(local_path):
	
    try:
        repo = Repo(local_path)
        
        # get differences between working directory and last commit
        diff = repo.git.diff('HEAD', '--color')
        
        if diff:
            print("\nChanges in the following files:")
            print(diff)
            return True
        else:
            print("\nNo changes in tracked files.")
            
        # show files not in git
        untracked = repo.untracked_files
        if untracked:
            print("\nFiles not in git:")
            for file in untracked:
                print(f"+ {file}")
            return True
            
        return False
        
    except Exception as e:
        print(f"Error showing git differences: {str(e)}")
        return False

def push_to_github(local_path, repo_url, branch="main", commit_message=None):

    try:
        
        print("Printing git differences")
        show_git_differences(local_path)

        if not os.path.exists(os.path.join(local_path, '.git')):
            repo = Repo.init(local_path)
        else:
            repo = Repo(local_path)

        try:
            origin = repo.remote('origin')
            if origin.url != repo_url:
                repo.delete_remote('origin')
                repo.create_remote('origin', repo_url)
        except ValueError:
            repo.create_remote('origin', repo_url)

        repo.git.add(all=True)

        if not commit_message:
            commit_message = f"Auto-commit: Updated files {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        repo.index.commit(commit_message)

        origin = repo.remote('origin')
        origin.push(branch)

        return True

    except Exception as e:
        print(f"Error pushing to GitHub: {str(e)}")
        return False
