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


def _get_repo(path):
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


def _commit_to_repo(repo, cloned_repo_directory, commiter_name, commiter_email, commit_message):
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
    return repoclone.create_commit('refs/heads/master', author, commiter, commit_message, tree,
                                  [repoclone.head.peel().hex])


def _push_to_repo(user_name, cloned_repo_directory):
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


def _get_current_working_branch(path_to_repo):
    """
    :param path_to_repo:
    :return: current working branch
    """
    repo = pygit2.Repository(path_to_repo)
    head = repo.lookup_reference('HEAD').resolve()
    head = repo.head
    branch_name = head.name
    print (branch_name)


def _git_checkout(path_to_repo, branch_name):
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


def _create_new_branch(repo, name):
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


def _rebasing(path_to_repo, branch_name, commiter_name, commiter_email, commit_message):
    """
    Rebasing one branch on master branch
    :param path_to_repo: path_to_repository
    :param branch_name: Branch name needs to be rebased on master branch
    :param commiter_name:
    :param commiter_email:
    :param commit_message:
    :return:
    """
    repo = pygit2.Repository(path_to_repo)

    author = pygit2.Signature("gshubh", "skg31297@gmail.com")
    commiter = pygit2.Signature(commiter_name, commiter_email)

    branch = repo.lookup_branch("remotes/origin/" + branch_name)
    master_branch = repo.lookup_branch("master")
    print (branch.target)

    base = repo.merge_base(master_branch.target, branch.target)
    tree_master = repo.get(master_branch.target).tree
    treec = repo.get(branch.target).tree
    base_tree = repo.get(base).tree

    repo.checkout(master_branch)
    index = repo.merge_trees(base_tree, tree_master, treec)
    tree_id = index.write_tree(repo)
    repo.create_commit(branch.name, author, commiter, commit_message, tree_id, [master_branch.target])


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
    ref = "heads/{0}".format(name)
    src = repo.get_git_ref(ref)
    try:
        src.delete()
    except IndexError:
        raise MissingBranchException('The branch "{0}" does not seem to exist'.format(name))

                                            ###   FILES   ###


def _create_new_file(repo, path, message, content,  branch):
    """
    To create new file inside the repository
    parameters
    path - string, (required), path of the file in the repository
    message - string, (required), commit message
    content - string, (required) actual data in the file
    """
    print (repo.create_file(path, message, content, branch))


def _update_a_file(repo, file_path, content, commit_message, ref, branch):
    """
    :param repo: repository
    :param file_path:  path of the inside the project folder like "projectgit/temp.py",
        if we want to add temp.py in the bucketlist folder
    :param content: Content which we want to add inside the file
    :param commit_message:
    :param ref: Branch name in string
    :param branch:  Branch in which we want to do this operation
    :return:
    """
    contents = repo.get_contents(file_path, ref)
    print (repo.update_file(contents.path, content, commit_message, contents.sha, branch))


def _delete_a_file(repo, file_path, commit_message, ref, branch):
    """
    To delete file inside the repository
    :param repo: repository
    :param file_path: path of the inside the project folder like "projectgit/temp.py",
        if we want to add temp.py in the bucketlist folder
    :param commit_message:
    :param ref: Branch name in string
    :param branch: Branch in which we want to do this operation
    :return:
    """
    contents = repo.get_contents(file_path, ref)
    print (repo.delete_file(contents.path, commit_message, contents.sha, branch))


def _commit_and_push_new_files(repo_dir, file_list, commit_message):
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


def _git_pull(path_to_repo, remote_name='origin', branch='master'):
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


def _get_username_and_password(username):
    password = get_github_password(username, refresh=False)
    g = Github(username, password)
    return g

#
# def test():
#     g = _get_username_and_password("gshubh")
#     repo = g.get_repo("gshubh/bucketlist")
#     # _clone_repo("https://github.com/gshubh/bucketlist.git", "/home/ubuntu-1804/Desktop/shubh")
#     # _commit_to_repo(repo, "/home/ubuntu-1804/Desktop/bucketlist", "gshubh", "skg31297@gmail.com", "New Commit")
#     # _push_to_repo("gshubh", "/home/ubuntu-1804/Desktop/bucketlist")
#     # print (git_checkout("/home/ubuntu-1804/Desktop/bucketlist", "master"))
#     # get_current_working_branch("/home/ubuntu-1804/Desktop/bucketlist")
#     # _delete_branch(repo, "neew_branch")
#     # create_new_branch(repo, "new_branch")
#     # rebasing("/home/ubuntu-1804/Desktop/bucketlist", "new_branch", "gshubh", "skg31297@gmail.com", "Rebasing of neew_branch into master branch")
#     # _git_pull("/home/ubuntu-1804/Desktop/bucketlist", remote_name="origin", branch="master")
#     # _get_branches_list(repo)
#     # _get_repo("/home/ubuntu-1804/Desktop/bucketlist")
#     # _merge_branch_to_master(repo, "new_branch")
#     _delete_a_file(repo, "temp1.py", "Remove temp3.py", "master", "master")


def main_menu():

    print("Select a Git operation which you want to perform")

    print("                     #######  COMMIT  #######      ")
    print("0. Get Head Commit")

    print("                     #######  REPOSITORY  #######      ")
    print("1. Clone Repository")
    print("2. Create Repository")
    print("3. Get Repository")
    print("4. Commit and Push to Repository")
    print("5. Push To Repository")

    print("                     #######  BRANCHES  #######      ")
    print("6. Get Current Working Branch")
    print("7. Get Branch")
    print("8. Get Branches List")
    print("9. Checkout Branch")
    print("10. Create New Branch")
    print("11. Merge Branch To Master")
    print("12. Rebasing")
    print("13. Delete Branch")

    print("                     #######  FILES  #######      ")
    print("14. Create New File")
    print("15. Update File")
    print("16. Delete File")
    print("17. Commit And Push New File")
    print("18. Git Pull")

    print("                     #######  ISSUES  #######      ")
    print("19. Get Issues")
    print("20. Create Issues")
    print("21. Create Issue With Body")
    print("22. Create Issue With Labels")
    print("23. Create Issue With Assignee")
    print("24. Create Issue With Milestone")
    print("25. Quit\n")


def getchoice():
    choice = int(input('Enter your choice : '))
    return choice


def replymenu():

    choice = getchoice()

    if choice == 0:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        branch_name = (raw_input('Enter the branch name: '))
        print (_get_head_commit(repo, branch_name))
        main()

    if choice == 1:
        url = (raw_input('Enter repository URL : '))
        to_path = (raw_input('Enter path to directory where you want to clone : '))
        _clone_repo(url, to_path)
        main()

    elif choice == 2:
        username = (raw_input('Enter your Github username: '))
        full_name = (raw_input('Enter the name which you want to give to the repository: '))
        g = _get_username_and_password(username)
        _create_repo(g, full_name)
        main()

    elif choice == 3:
        username = (raw_input('Enter your Github username: '))
        full_name = (raw_input('Enter the name which you want to give to the repository: '))
        g = _get_username_and_password(username)
        _create_repo(g, full_name)
        main()

    elif choice == 4:
        user_name = (raw_input('Enter your Github username: '))
        commiter_name = (raw_input('Enter Commiter name: '))
        commiter_email = (raw_input('Enter Commiter email_address: '))
        cloned_repo_directory = (raw_input('Enter the path/to/cloned_repo_directory: '))
        commit_message = (raw_input('Enter Commit message: '))
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        _commit_to_repo(repo, cloned_repo_directory, commiter_name, commiter_email, commit_message)
        _push_to_repo(user_name, cloned_repo_directory)
        main()

    elif choice == 5:
        user_name = (raw_input('Enter your Github username: '))
        cloned_repo_directory = (raw_input('Enter the path/to/cloned_repo_directory: '))
        _push_to_repo(user_name, cloned_repo_directory)
        main()

    elif choice == 6:
        path_to_repo = (raw_input('Enter the path/to/repository: '))
        _get_current_working_branch(path_to_repo)
        main()

    elif choice == 7:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        name = (raw_input('Enter the branch name: '))
        _get_branch(repo, name)
        main()

    elif choice == 8:
        path_to_repo = (raw_input('Enter the path/to/repository: '))
        _get_current_working_branch(path_to_repo)
        main()

    elif choice == 9:
        path_to_repo = (raw_input('Enter the path/to/repository: '))
        branch_name = (raw_input('Enter the branch name: '))
        _git_checkout(path_to_repo, branch_name)
        main()

    elif choice == 10:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        branch_name = (raw_input('Enter the branch name: '))
        _create_new_branch(repo, branch_name)
        main()

    elif choice == 11:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        branch_name = (raw_input('Enter the branch name: '))
        _merge_branch_to_master(repo, branch_name)
        main()

    elif choice == 12:
        path_to_repo = (raw_input('Enter the path/to/repository: '))
        branch_name = (raw_input('Enter the branch name which you want to rebase to master: '))
        commiter_name = (raw_input('Enter Commiter name: '))
        commiter_email = (raw_input('Enter Commiter email_address: '))
        commit_message = (raw_input('Enter Commit message: '))
        _rebasing(path_to_repo, branch_name, commiter_name, commiter_email, commit_message)
        main()

    elif choice == 13:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        name = (raw_input('Enter the branch name: '))
        _delete_branch(repo, name)
        main()

    elif choice == 14:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        file_path = (raw_input('Enter the file path inside the project directory: '))
        commit_message = (raw_input('Enter Commit message: '))
        content = (raw_input('Enter the content which you want to add to the file: '))
        branch = (raw_input('Enter the branch name: '))
        _create_new_file(repo, file_path, content, commit_message, branch)
        main()

    elif choice == 15:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        file_path = (raw_input('Enter the file path inside the project directory: '))
        commit_message = (raw_input('Enter Commit message: '))
        content = (raw_input('Enter the content which you want to add to the file: '))
        branch = (raw_input('Enter the branch name: '))
        ref = branch
        _update_a_file(repo, file_path, content, commit_message, ref, branch)
        main()

    elif choice == 16:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        file_path = (raw_input('Enter the file path inside the project directory: '))
        commit_message = (raw_input('Enter Commit message: '))
        branch = (raw_input('Enter the branch name: '))
        ref = branch
        _delete_a_file(repo, file_path, commit_message, ref, branch)
        main()

    elif choice == 17:
        repo_dir = (raw_input('Enter the path/to/repository: '))
        commit_message = (raw_input('Enter Commit message: '))
        file_list = input("Array of path of files which you want to add: ")
        _commit_and_push_new_files(repo_dir, file_list, commit_message)
        main()

    elif choice == 18:
        path_to_repo = (raw_input('Enter the path/to/repository: '))
        _git_pull(path_to_repo, remote_name='origin', branch='master')
        main()

    elif choice == 19:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        number = int(input('Enter the issue number: '))
        _get_issue(repo, number)
        main()

    elif choice == 20:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        title = (raw_input('Enter the issue title: '))
        _create_issue(repo, title)
        main()

    elif choice == 21:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        title = (raw_input('Enter the issue title: '))
        body = (raw_input('Enter the issue: '))
        _create_issue_with_body(repo, title, body)
        main()

    elif choice == 22:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        _create_issue_with_labels(repo)
        main()

    elif choice == 23:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        title = (raw_input('Enter the issue title: '))
        github_username = (raw_input('Enter your github username: '))
        _create_issue_with_body(repo, title, github_username)
        main()

    elif choice == 24:
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        _create_issue_with_milestone(repo)
        main()

    elif choice == 25:
        exit()

    else:
        print ("Invalid choice selection")
        main()


def main():
    main_menu()
    replymenu()


if __name__ == '__main__':
    main()
