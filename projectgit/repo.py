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
    git_log = repo.log('{0}..{1}'.format(base, branch))
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


def _create_repo(g, full_name):
    """
    :param g: github(username, password)
    :param full_name: name of newly created repository
    :return:
    """
    user = g.get_user()
    repo = user.create_repo(full_name)
    return repo


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
    print (Repo(path))


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


def commit_to_repo(repo, cloned_repo_directory, commiter_name, commiter_email):
    """

    :param repo:
    :param cloned_repo_directory: path/to/repo_directory
    :param commiter_name:
    :param commiter_email:
    :return: commit value
    """
    repoclone = pygit2.Repository(cloned_repo_directory + "/.git/")
    repoclone.remotes.set_url("origin", repo.clone_url)
    index = repoclone.index
    index.add_all()
    index.write()
    author = pygit2.Signature("gshubh", "skg31297@gmail.com")
    commiter = pygit2.Signature(commiter_name, commiter_email)
    tree = index.write_tree()
    return repoclone.create_commit('refs/heads/master', author, commiter, "init commit", tree,
                                  [repoclone.head.peel().hex])


def push_to_repo(user_name, cloned_repo_directory):
    """

    :param user_name: github username
    :param cloned_repo_directory:  path/to/repo_directory
    :return:
    """

    repoclone = pygit2.Repository(cloned_repo_directory + "/.git/")
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


                                            ###   Branches   ###

def get_current_working_branch(path_to_repo):
    """
    :param repo:
    :return: current working branch
    """
    repo = pygit2.Repository(path_to_repo)
    head = repo.lookup_reference('HEAD').resolve()
    head = repo.head
    branch_name = head.name
    print (branch_name)


def git_checkout(path_to_repo, branch_name):
    """
    :param repo:
    :param branch_name: Name of the branch which we want ot switch to
    :return:
    """
    repo = pygit2.Repository(path_to_repo)
    branch = repo.lookup_branch(branch_name)
    repo.checkout(branch)


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


def _get_branches_list(repo):
    """
    Gets the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :return: The branch object
    :rtype: git.refs.head.Head
    """
    branch_list = []
    for branch in repo.get_branches():
        branch_list.append(branch)
    print (branch_list)
    exit()


def create_new_branch(repo, name):
    """Gets the branch and raises a MissingBranchException
    if it doesn't exist
    :param Repo repo:
    :param unicode name: The name of the branch
    :raises: ExistingBranchException
    """
    ref = "refs/heads/{0}".format(name)
    sha = repo.get_branch("master").commit.sha
    try:
        repo.create_git_ref(ref, sha)
    except IndexError:
        raise ExistingBranchException('Branch "{0}" already exist.'
                                        'To create new branch give some different name'.format(name))


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


def rebasing(path_to_repo, branch_name, commiter_name, commiter_email, commit_message):
    """
    Rebasing one branch on master branch
    :param repo: Repository
    :param branch_name: Branch name needs to be rebased on master branch
    :param commiter_name:
    :param commiter_email:
    :param commit_message:
    :return:
    """
    repo = pygit2.Repository(path_to_repo)

    author = pygit2.Signature("gshubh", "skg31297@gmail.com")
    commiter = pygit2.Signature(commiter_name, commiter_email)

    branch = repo.lookup_branch("remotes/origin/new_branch")
    master_branch = repo.lookup_branch("master")
    print (branch.target)

    # base = repo.merge_base(master_branch.target, branch.target)
    # tree_master = repo.get(master_branch.target).tree
    # treec = repo.get(branch.target).tree
    # base_tree = repo.get(base).tree
    #
    # repo.checkout(master_branch)
    # index = repo.merge_trees(base_tree, tree_master, treec)
    # tree_id = index.write_tree(repo)
    # repo.create_commit(branch.name, author, commiter, commit_message, tree_id, [master_branch.target])


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

def commit_and_push_new_files(repo_dir, file_list, commit_message):
    """

    :param repo_dir: path of repository directory
    :param file_list: list of path of all files which we want to add
    :param commit_message: commit message
    :return:
    """
    repo = Repo(repo_dir)
    repo.index.add(file_list)
    repo.index.commit(commit_message)
    origin = repo.remote('origin')
    origin.push()


def git_pull(path_to_repo, remote_name='origin', branch='master'):
    """
    :param repo:
    :param remote_name:
    :param branch:
    :return:
    """
    repo = pygit2.Repository(path_to_repo)
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch()
            remote_master_id = repo.lookup_reference('refs/remotes/origin/%s' % (branch)).target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return
            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_master_id))
                try:
                    master_ref = repo.lookup_reference('refs/heads/%s' % (branch))
                    master_ref.set_target(remote_master_id)
                except KeyError:
                    repo.create_branch(branch, repo.get(remote_master_id))
                repo.head.set_target(remote_master_id)
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                repo.merge(remote_master_id)

                if repo.index.conflicts is not None:
                    for conflict in repo.index.conflicts:
                        print ('Conflicts found in:', conflict[0].path)
                    raise AssertionError('Conflicts, ahhhhh!!')

                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD', user, user, "Merge!", tree, [repo.head.target, remote_master_id])
                # We need to do this or git CLI will think we are still merging.
                repo.state_cleanup()
            else:
                raise AssertionError('Unknown merge analysis result')


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
    # _clone_repo("https://github.com/gshubh/bucketlist.git", "/home/ubuntu-1804/Desktop/shubh")
    commit_to_repo(repo, "/home/ubuntu-1804/Desktop/bucketlist", "gshubh", "skg31297@gmail.com")
    push_to_repo("gshubh", "/home/ubuntu-1804/Desktop/bucketlist")
    # print (git_checkout("/home/ubuntu-1804/Desktop/bucketlist", "master"))
    # get_current_working_branch("/home/ubuntu-1804/Desktop/bucketlist")
    # _delete_branch(repo, "neew_branch")
    # create_new_branch(repo, "new_branch")
    # rebasing("/home/ubuntu-1804/Desktop/bucketlist", "new_branch", "gshubh", "skg31297@gmail.com", "Rebasing of neew_branch into master branch")
    # git_pull("/home/ubuntu-1804/Desktop/bucketlist", remote_name="origin", branch="master")
    # _get_branches_list(repo)

if __name__ == '__main__':
    main()
