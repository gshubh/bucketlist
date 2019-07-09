from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from os import getcwd
from git import  Repo
from git.exc import GitCommandError
from project_git.exceptions import MissingRemoteException, MissingBranchExcpetion, \
    PushFailedException, MissingRepoException


import logging
import re
import os, sys

_LOG = logging.getLogger(__name__)

                                            ###   COMMITS   ###


def _get_relevant_commit_shas(repo, base, branch):
    """
    Parses the git log to get all commit shas that
    are on the branch but not the base
    :param Repo repo:
    :param unicode base:
    :param unicode branch:
    :return: list[unicode]
    """
    # regex for parsing the commit sha from the git log
    # ignores merges
    regex = re.compile(r'commit ([a-z0-9]{40})\n(?!Merge)')
    git_log = repo.git.log('{0}..{1}'.format(base, branch))
    return re.findall(regex, git_log)


def _get_relevant_commits(repo, commit_shas, branch):
    """
    Gets all commits on the repo with the given shas
    :param Repo repo:
    :param list[unicode] commit_shas:
    :param unicode branch:
    :return: list[Commit]
    """
    remaining_shas = set(commit_shas)
    commits = list()
    for commit in repo.iter_commits(branch):
        if commit.hexsha in remaining_shas:
            commits.append(commit)
            remaining_shas.remove(commit.hexsha)
    return commits


def _get_messages(commits):
    ''' To get all the commit messages associated with the commits'''
    if not commits:
        return ''
    return '\n\n'.join([commit.message for commit in commits])


                                            ###   REPOSITORY   ###
def init(repo):
    """
    Create a directory for the repo and initialize .git directory
    :param Repo repo:
    """
    os.mkdir(os.path.join(repo, '.git'))
    for name in ['objects', 'refs', 'refs/heads']:
        os.mkdir(os.path.join(repo, '.git', name))
    print('initialized empty repository: {}'.format(repo))


def _get_repo(path=None):
    """
    Gets the Repo object associated with
    the path.  If the path is `None` or empty
    it uses the current working directory
    :param unicode path:
    :return: The repo object
    :rtype: git.repo.base.Repo
    """
    path = path or getcwd()
    return Repo(path)


def push_repo(repo, branch, remote='origin', remote_branch=None):
    """
    Pushes the repo up to the remote.  It will set
    the upstream to the remote branch.
    :param Repo repo: The repo you wish to push
    :param unicode branch: The branch being pushed
    :param unicode remote: The remote to use (e.g. ``'origin'``
    :param unicode remote_branch: The remote branch.  Defaults
        to the `branch` parameter
    :return: None
    :raises: PushFailedException
    """
    remote_branch = remote_branch or branch
    _checkout_branch(repo, branch)
    _LOG.info("Pushing all commits to remote '{0}'".format(remote))
    remote = _get_remote(repo, remote)
    try:
        remote.push(remote_branch, set_upstream=True)
    except GitCommandError as e:
        _LOG.error(str(e))
        raise PushFailedException('Uh oh, it seems like something went'
                                  ' wrong with the push. "{0}"'.format(str(e)))


def _clone_repository(repo, url, to_path, ):
    """
    To clone the repository
    :param unicode path:
    :return: The repo object
    :rtype: git.repo.base.Repo
    """

    try:
        repo.clone_from(url, to_path)
    except IndexError:  # I have no idea why they raise an IndexError instead of KeyError
        raise MissingRepoException('The remote "{0}" does not exist.  '
                                     'Please select a different repository')


def _get_remote(repo, name):
    """
    Gets the remote object raising a MissingRemoteException
    when it does not exist
    :param Repo repo:
    :param unicode name: The remote name
    :return: The remote object
    :rtype: git.remote.Remote
    :raises: MissingRemoteException
    """
    try:
        return repo.remotes[name]
    except IndexError:  # I have no idea why they raise an IndexError instead of KeyError
        raise MissingRemoteException('The remote "{0}" does not exist.  '
                                     'Please select a different remote or'
                                     ' add it using "git remote add" command')


def _delete_repo(repo, name):
    """
    Deletes the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :return: The branch object
    :rtype: git.refs.head.Head
    :raises: MissingBranchException
    """
    try:
        repo.__del__()
        return repo.branches()
    except IndexError:
        raise MissingRepoException('The remote "{0}" does not exist.  '
                                     'Please select a different repository'.format(name))


                                            ###   Branches   ###

def _get_branch(repo, name):
    """
    Gets the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :return: The branch object
    :rtype: git.refs.head.Head
    :raises: MissingBranchException
    """
    try:
        return repo.branches(name)
    except IndexError:
        raise MissingBranchExcpetion('The branch "{0}" does not seem to exist'.format(name))


def _checkout_branch(repo, branch):
    """
    Checks out the branch specified locally
    :param Repo repo:
    :param unicode branch:
    :return: The branch object
    :rtype: git.refs.head.Head
    """
    branch = _get_branch(repo, branch)
    _LOG.info('Checking out branch "{0}"'.format(branch.name))
    branch.checkout()
    return branch


def _merge_base_into_repo(repo, branch_name, base_name):
    """
    Merge the branch with the ``base_name`` into the ``branch_name``
    :param Repo repo:
    :param unicode branch_name:
    :param unicode base_name:
    """
    _checkout_branch(repo, branch_name)
    # ensure the branches exist
    base = _get_branch(repo, base_name)
    branch = _get_branch(repo, branch_name)

    # When the log is empty that means there are no
    # commits on the base that are not on the branch
    if not repo.git.log('{0}..{1}'.format(branch_name, base_name)):
        return
    _LOG.info('Merging "{0}" into "{1}"'.format(base_name, branch_name))
    repo.git.merge(base_name, commit=True)


def merge_base_into_branch_and_push(branch_name,
                                    base_name='master',
                                    remote_name='origin',
                                    remote_branch_name=None,
                                    path=None):
    """
    Merges the branch with the ``base_name`` into the
    branch ``branch_name`` from the repo at the ``path``
    or the current working directory.  Finally, pushes
    the resulting commit up to the specified remote branch
    :param unicode path: The path of the repo to operate on
    :param unicode branch_name: The branch to be updated
    :param unicode base_name: The branch that will be merged
        into the ``branch_name``
    :param unicode remote_name: The name of the remote (e.g. ``'origin'``)
    :param unicode remote_branch_name: The name of the remote
        branch.  Defaults to the branch_name parameter
    """
    path = path or getcwd()
    repo = _get_repo(path)
    _checkout_branch(repo, branch_name)
    _merge_base_into_repo(repo, branch_name, base_name)
    push_repo(repo, branch_name, remote_name, remote_branch=remote_branch_name)




def _delete_branch(repo, name):
    """
    Deletes the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :return: The branch object
    :rtype: git.refs.head.Head
    :raises: MissingBranchException
    """
    try:
        repo.branches(name).__del__()
        return repo.branches()
    except IndexError:
        raise MissingBranchExcpetion('The branch "{0}" does not seem to exist'.format(name))

                                            ###   FILES   ###


def create_new_file(repo, path, message, branch):
    # To create new file inside the repository
    '''parameters
    path - string, (required), path of the file in the repository
    message - string, (required), commit message
    content - string, (required) actual data in the file
    '''

    repo.create_file(path, message, branch=branch)

def update_a_file(repo, path, ref, message, content, branch):
    # Update a file in the repository
    '''parameters
        path - string, (required), path of the file in the repository
        message - string, (required), commit message
        content - string, (required) actual data in the file
        sha - string, (required), Th blob sha of file being replaced
        branch - string. The branch name. Default: The repository's branch name (usually master)
    '''

    contents = repo.get_contents(path, ref)
    repo.update_file(contents.path, message, content, contents.sha, branch)


def delete_a_file(repo, path, ref, message, content, branch):
    # Update a file in the repository
    '''parameters
        path - string, (required), path of the file in the repository
        message - string, (required), commit message
        content - string, (required) actual data in the file
        sha - string, (required), Th blob sha of file being replaced
        branch - string. The branch name. Default: The repository's branch name (usually master)
    '''

    contents = repo.get_contents(path, ref)
    repo.delete_file(contents.path, message, content, contents.sha, branch)



def main():
    _get_relevant_commit_shas("https://github.com/gshubh/bucketlist.git" , "" , "master")


if __name__ == '__main__':
    main()