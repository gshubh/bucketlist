import os
import subprocess
from git import Repo
from github import Github


def execute_shell_command(cmd, work_dir):
    """Executes a shell command in a subprocess, waiting until it has completed.

    :param cmd: Command to execute.
    :param work_dir: Working directory path.
    """
    pipe = subprocess.Popen(cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, error) = pipe.communicate()
    print (out, error)
    pipe.wait()


def create_new_repository(reponame):
    """This function will create new repository"""
    cmd = "git init"
    subprocess.call(cmd, shell=True)
    cmd = "git remote add origin git@github.com:gshubh/<" + reponame + ">.git"
    subprocess.call(cmd, shell=True)
    cmd = "git push -u origin master"
    subprocess.call(cmd, shell=True)


def git_user(name, email, repo_dir):
    """Configure the author name and email address to be used with your commits.
       Note that Git strips some characters (for example trailing periods) from user.name.
    :param name: Name of user.
    :param email: user email address.
    """
    cmd1  = 'git config --global user.name "' + name + '"'
    execute_shell_command(cmd1, repo_dir)
    cmd2  = 'git config --global user.email ' + email
    execute_shell_command(cmd2, repo_dir)


def git_add(file_path, repo_dir):
    """Adds the file at supplied path to the Git index.
    File will not be copied to the repository directory.
    No control is performed to ensure that the file is located in the repository directory.

    :param file_path: Path to file to add to Git index.
    :param repo_dir: Repository directory.
    """
    cmd = 'git add ' + file_path
    execute_shell_command(cmd, repo_dir)


def git_commit(commit_message, repo_dir):
    """Commits the Git repository located in supplied repository directory with the supplied commit message.

    :param commit_message: Commit message.
    :param repo_dir: Directory containing Git repository to commit.
    """
    cmd = 'git commit -am "%s"' % commit_message
    execute_shell_command(cmd, repo_dir)


def git_pull(repo_dir):
    """Pull the changes from upstream.

    :param repo_dir: Directory containing git repository to pull.
    """
    cmd = 'git pull '
    execute_shell_command(cmd, repo_dir)


def git_clone(repo_url, repo_dir):
    """Clones the remote Git repository at supplied URL into the local directory at supplied path.
    The local directory to which the repository is to be clone is assumed to be empty.

    :param repo_url: URL of remote git repository.
    :param repo_dir: Directory which to clone the remote repository into.
    """
    cmd = 'git clone ' + repo_url + ' ' + repo_dir
    execute_shell_command(cmd, repo_dir)


                                                #Branches

def create_new_branch(branch_name, repo_dir):
    """ Creates new branch inside the repository.

    :param branch_name: name of newly created branch.
    :param repo_dir: URL of remote git repository.
    """
    cmd = 'git checkout -b <' + branch_name + '>'
    execute_shell_command(cmd, repo_dir)


def branch_switch(branch_name, repo_dir):
    """Switch from one branch to another.

    :param branch_name: name of newly created branch.
    :param repo_dir: URL of remote git repository
    """
    cmd = 'git checkout <' + branch_name + '>'
    execute_shell_command(cmd, repo_dir)

def get_branch(repo_dir):
    """List all the branches in your repo, and also tell you what branch you're currently in.

    :param repo_dir: URL of remote git repository
    """
    cmd = 'git branch'
    execute_shell_command(cmd, repo_dir)


def push_branch(repo_dir, branch_name):
    """Push the branch to your remote repository, so others can use it.

    :param repo_dir: URL of remote git repository
    """
    cmd = 'git push origin <' + branch_name + '> '
    execute_shell_command(cmd, repo_dir)


def push_all_branch(repo_dir):
    """Push all branches to your remote repository.

    :param repo_dir: URL of remote git repository
    """
    cmd = 'git push --all origin'
    execute_shell_command(cmd, repo_dir)


def delete_branch(repo_dir, branch_name):
    """Delete a branch on your remote repository.

    :param repo_dir: URL of remote git repository
    :param repo_dir: URL of remote git repository
    """
    cmd = 'git push origin: <' + branch_name + '> '
    execute_shell_command(cmd, repo_dir)



def main():
    # Step 1: Create a Github instance:
    #g = Github("gshubh", "passwd")
    create_new_repository("bucketlist")
    #repo_dir =test
    git_pull('/home/ubuntu-1804/Desktop/bucketlist')
    git_add('/home/ubuntu-1804/Desktop/bucketlist/repo.py', '/home/ubuntu-1804/Desktop/bucketlist')
    git_commit("New Commit", '/home/ubuntu-1804/Desktop/bucketlist')
    #push_branch('/home/ubuntu-1804/Desktop/bucketlist', 'master')
    #push_all_branch('/home/ubuntu-1804/Desktop/bucketlist')


if __name__ == '__main__':
    main()






