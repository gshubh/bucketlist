from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import logging
import pygit2
import re
import sys, os
sys.path.append(os.path.abspath(".."))

from os import getcwd
from git import Repo, Commit, Git
from git.exc import GitCommandError
from github import Github
from pygit2 import Repository
from projectgit.exceptions import *
from projectgit.credentials import *


_LOG = logging.getLogger(__name__)

                                            ###   COMMITS   ###

def _get_head_commit(repo, branch_name):
    """
    To get the latest commit of the given branch
    eg: Commit(sha="5e69ff00a3be0a76b13356c6ff42af79ff469ef3")
    :param Repo repo:
    :param unicode branch_name: The name of the branch
    :return commit object
    """
    branch = _get_branch(repo, branch_name)
    return branch.commit


def _get_commit(repo, sha):
    """
    :param sha:
    :return: unicode
    """
    return repo.get_commit(sha)


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


def _construct_summary(relevant_commits):
    """
    Returns an appropriate summary for the given
    commits
    :param list[Commit] relevant_commits:
    :rtype: unicode
    """
    if not relevant_commits or len(relevant_commits) == 0:
        return 'Autogenerated pull request'
    return relevant_commits[0].summary


def construct_message(repo, base, branch):
    """
    Constructs a message that contains all of the
    commits message that are unique to the given branch
    :param Repo repo:
    :param unicode base:
    :param unicode branch:
    :return: The latest commits summary and the combined messages
        of the commits as a tuple of unicode objects
    :rtype: unicode, unicode,
    """
    commit_shas = _get_relevant_commit_shas(repo, base, branch)
    _LOG.debug('Relevant shas: {0}'.format(commit_shas))
    commits = _get_relevant_commits(repo, commit_shas, branch)
    return _construct_summary(commits), _get_messages(commits)


def _get_messages(commits):
    """
    To get all the commit messages associated with the commits
    :param commits:
    :return:
    """
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


def _create_repo(g):
    user = g.get_user()
    repo = user.create_repo(full_name)

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


def commit_and_push_repo(repo, url, to_path, user_name):
    """
    clone repository, change files in it and then push it back to github
    :param repo: Repo
    :param url: Repository url
    :param to_path: /path/to/clone/to
    :param user_name: github_username
    """
    repoclone = _clone_repo(url, to_path)
    repoclone.remotes.set_url("origin", repo.clone_url)
    remote = repoclone.remotes["origin"]
    username = user_name
    password = get_github_password(username, refresh=False)
    credentials = pygit2.UserPass(username, password)
    remote.credentials = credentials
    callbacks = pygit2.RemoteCallbacks(credentials=credentials)
    try:
        remote.push(['refs/heads/master'], callbacks=callbacks)
    except GitCommandError as e:
        _LOG.error(str(e))
        raise PushFailedException('Uh oh, it seems like something went'
                                  ' wrong with the push. "{0}"'.format(str(e)))


def _clone_repo(url, to_path):
    """
    :param url: Repository url
    :param to_path: /path/to/clone/to
    :return:
    """
    try:
        return pygit2.clone_repository(url, to_path)
    except ValueError:  # I have no idea why they raise an IndexError instead of KeyError
        raise MissingRepoException('The remote repo does not exist. Please select a different repository')

# def _commit_repo():
#
# def _push_repo():


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
    Deletes the branch and raises a MissingRepoException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :return: The branch object
    :rtype: git.refs.head.Head
    :raises: MissingBranchException
    """
    try:
        repo.git.__del__()
        return repo.branches()
    except IndexError:
        raise MissingRepoException('The remote "{0}" does not exist. Please select a different repository'.format(name))


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
        return repo.get_branch(name)
    except IndexError:
        raise MissingBranchException('The branch "{0}" does not seem to exist'.format(name))

def _get_branches(repo):
    """
    Gets the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :return: The branch object
    :rtype: git.refs.head.Head
    """
    return repo.get_branches()


def get_current_working_branch(repo):
    """
    :param repo:
    :return: current working branch
    """

    head = repo.lookup_reference('HEAD').resolve()
    head = repo.head
    branch_name = head.name
    print (branch_name)


def create_new_branch(repo, name):
    """Gets the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :raises: ExistingBranchException
    """
    ref = "refs/heads/{0}".format(name)
    sha = repo.git.get_branch("master").commit.sha
    try:
        repo.create_git_ref(ref, sha)
    except IndexError:
        raise ExistingBranchException('Branch "{0}" already exist.'
                                        'To create new branch give some different name'.format(name))


def _checkout_branch(branch_name):
    """
    Checks out the branch specified locally
    :param Repo repo:
    :param unicode branch:
    :return: The branch object
    :rtype: git.refs.head.Head
    """
    repo = pygit2.Repository("gshubh/bucketlist")
    branch = repo.lookup_branch(branch_name)
    _LOG.info('Checking out branch "{0}"'.format(branch.name))
    ref = repo.lookup_reference(branch.name)
    return repo.checkout(ref)


def _merge_branch_to_master(repo, working_branch):
    """
    :param repo:
    :param working_branch: Branch which we want to merge to master
    :return: None
    """
    try:
        head = repo.get_branch(working_branch)
        merge_to_master = repo.merge("master", head.commit.sha, "merge to master")
        print (merge_to_master)
    except Exception as ex:
        print (ex)


def _delete_branch(repo,name):
    """
    Deletes the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :return: The branch object
    :rtype: git.refs.head.Head
    :raises: MissingBranchException
    """
    ref = "heads/{0}".format(name)
    src = repo.get_git_ref(ref)
    try:
        src.delete()
    except IndexError:
        raise MissingBranchException('The branch "{0}" does not seem to exist'.format(name))

                                            ###   FILES   ###


def create_new_file(repo, path, message, content,  branch):
    """
    To create new file inside the repository
    parameters
    path - string, (required), path of the file in the repository
    message - string, (required), commit message
    content - string, (required) actual data in the file
    """
    repo.create_file(path, message, content, branch=branch)


def update_a_file(repo, path, message, content, sha, branch):
    """
    Update a file in the repository
    parameters
        path - string, (required), path of the file in the repository
        message - string, (required), commit message
        content - string, (required) actual data in the file
        sha - string, (required), Th blob sha of file being replaced
        branch - string. The branch name. Default: The repository's branch name (usually master)
    """
    repo.update_file(path, message, content, sha, branch)


def delete_a_file(repo, path, sha, message, branch):
    """
    Update a file in the repository
    parameters
        :repo - repository
        :path - string, (required), path of the file in the repository
        :message - string, (required), commit message
        :sha - string, (required), Th blob sha of file being replaced
        :branch - string. The branch name. Default: The repository's branch name (usually master)
    """
    repo.delete_file(path, message, sha, branch)

                                        ###  ISSUES  ###


def _get_issue(repo, number):
    """
    Get issue with given number
    :param number:
    :return: github.Issue.Issue
    """
    try:
        return repo.get_issue(number=number)
    except IndexError:
        raise MissingNumberException('Issue number "{0}" does not seem to exist'.format(number))


def _create_issue(repo, title):
    """
    Creates a new issue
    :param repo:
    :param title:
    """
    repo.create_issue(title=title)


def _create_issue_with_body(repo, title, body):
    """
    Create an issue with body. A title and description describe what the issue is all about.
    """
    repo.create_issue(title=title, body=body)


def _create_issue_with_labels(repo):
    """
    Color-coded labels help you categorize and filter your issues (just like labels in email).
    :param repo: Repository
    :return:
    """
    label = repo.get_label("My Label")
    repo.create_issue(title="This is a new issue", labels=[label])


def _create_issue_with_assignee(repo, title, github_username):
    """
    One assignee is responsible for working on the issue at any given time.
    :param repo: Repository
    :param github_username:
    :return:
    """
    repo.create_issue(title=title , assignee=github_username)


def _create_issue_with_milestone(repo):
    """
    A milestone acts like a container for issues.
    This is useful for associating issues with specific features or project phases
    (e.g. Weekly Sprint 9/5-9/16 or Shipping 1.0).
    :param repo: Repository
    :return:
    """
    milestone = repo.create_milestone("New Issue Milestone")
    repo.create_issue(title="This is a new issue", milestone=milestone)


def main():
    username = "gshubh"
    password = get_github_password(username, refresh=False)
    g = Github(username, password)
    repo = g.get_repo("gshubh/bucketlist")
    # construct_message(repo, "new", "master")
    # _clone_repo("https://github.com/gshubh/bucketlist.git", "/home/ubuntu-1804/Desktop/new")

if __name__ == '__main__':
    main()