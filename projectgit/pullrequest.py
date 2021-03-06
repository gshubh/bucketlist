from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from uuid import uuid4
from github import Github
from github.GithubException import GithubException, BadCredentialsException, TwoFactorException
from git import Repo
from giturlparse import parse

from projectgit.credentials import *
from projectgit.repo import construct_message, _get_repo
from projectgit.exceptions import AuthenticationException

_LOG = logging.getLogger(__name__)


def _get_org_and_name_from_remote(remote):
    """
    Gets the org name and the repo name
    for a github remote.
    :param git.Remote remote:
    :return: The owner and the repo name in that order
    :rtype: unicode, unicode
    """
    url = remote.config_reader.get('url')
    if not url.endswith('.git'):
        url = '{0}.git'.format(url)
    git_info = parse(url)
    _LOG.debug('Repo owner: "{0}"'.format(git_info.owner))
    _LOG.debug('Repo name: "{0}"'.format(git_info.repo))
    return git_info.owner, git_info.repo


def _get_current_repo(github, repo, remote='origin'):
    """
    Gets the github repo associated with the
    provided repo
    :param Github github:
    :param Repo repo:
    :param unicode remote:
    :return: The github repository assocated with
        the provided repo
    :rtype: github.Repository.Repository
    """
    owner, repo = _get_org_and_name_from_remote(repo.remotes[remote])
    return github.get_repo('{0}/{1}'.format(owner, repo))


def _create_pull_request_helper(repo, remote_repo, branch, base, auth=None):
    """
    Creates a pull request to merge the branch into the base.
    Ignores the error if there is already a pull request open
    for the given branch->base
    :param Repo repo:
    :param Repository remote_repo:
    :param unicode branch:
    :param unicode base:
    """
    title, message = construct_message(repo, base, branch)
    try:
        _LOG.info('Creating pull request')
        return remote_repo.create_pull(title=title, head=branch, base=base,
                                       body='Autogenerated: \n\n{0}'.format(message))
    except GithubException as exc:
        if 'errors' in exc.data and len(exc.data['errors']) == 1 and \
            exc.data['errors'][0].get('message', '').startswith('A pull request already exists for'):
            _LOG.warning('A pull request already exists for "{0}".  Continuing.'.format(branch))
            return _get_pull_request(remote_repo, branch, base)
        else:
            raise exc


def _get_pull_request(remote_repo, branch_name, base_name):
    """
    Gets the active pull request with the given branch and base
    :param Repository remote_repo:
    :param unicode branch_name:
    :param unicode base_name:
    :return:
    """
    all_active_pull_request = remote_repo.get_pulls(state='open')
    for pull_request in all_active_pull_request:
        if pull_request.base.ref == base_name and pull_request.head.ref == branch_name:
            return pull_request


def _instantiate_github(username):
    """
    Gets a github object that has been authenticated.
    If authentication fails it asks the user for their
    password agains
    :param unicode username:
    :rtype: Github
    """
    password = get_github_password(username)
    count = 0
    while True:
        count += 1
        github = Github(login_or_token=username, password=password)
        try:
            auth = github.get_user().create_authorization(
                scopes=['repo'],
                note='bucketlist {0}'.format(str(uuid4())))
            return github, auth
        except BadCredentialsException as exc:
            _LOG.error('The password was not valid for "{0}"'.format(username))
            if count == 3:
                raise AuthenticationException('Failed to authenticate three times. '
                                              'Is "{0}" the correct username?'.format(username))
            password = get_github_password(username, refresh=True)
        # except TwoFactorException as exc:
        #     user = github.get_user()
        #     onetime_password =input('Github 2-Factor code: ')
        #     authorization = user.create_authorization(
        #         scopes=['repo'],
        #         note='bucketlist {0}'.format(str(uuid4())),
        #         onetime_password=onetime_password)
        #     return Github(authorization.token), authorization


def create_pull_request(path, branch, base, username, remote):
    """
    Creates a pull request for branch to merge into base
    on the remote.
    :param unicode path: The path to the repository defaults to the current working directory
    :param unicode branch: The branch with the updates to merge
    :param unicode base: The branch to merge into
    :param unicode username: The github username
    :param unicode remote: The remote to create the pull request on
    :return: The pull request that was created or the existing one. Returns ``None`` if no pull request
        could be created and the pull request could not be found
    :rtype: PullRequest
    """
    github, auth = _instantiate_github(username)
    repo = _get_repo(path)
    remote_repo = _get_current_repo(github, repo, remote)
    return _create_pull_request_helper(repo, remote_repo, branch, base, auth=auth)


if __name__ == '__main__':
    create_pull_request("/home/ubuntu-1804/Desktop/bucketlist", "new", "master", "gshubh", "origin")