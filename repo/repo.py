from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import git
import os
import os.path as osp

from os import getcwd
from git import Repo
from git.exc import GitCommandError
from github_reviewboard_sync.exceptions import MissingRemoteException, MissingBranchExcpetion, PushFailedException


_LOG = logging.getLogger(__name__)



def create_git_repository():
    '''Create the git repository, or change into it if it exists'''
    datastore = 'bucketlist'
    if not os.path.isdir(datastore):
        os.makedirs(datastore)
        git.Repo.init(datastore)
    repo = git.Repo(datastore)
    os.chdir(datastore)
    return repo


def _get_repo(path=None):
    ''' Gets the repo object associated with path. I f the path is none it uses the current working directory '''
    path = path or getcwd()
    return  Repo(path)


def get_existing_branches():
    branches = git.Git.branch()
    branches = branches.replace(" ", "").replace("*", "")
    branchlist = branches.split('\n')
    return branchlist


def _push_repo(repo, branch, remote='origin', remote_branch=None):
    '''Pushes the repo up to the remote and sets the upstream to the remote branch '''
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


def _get_remote(repo, name):
    ''' Gets the remote object raises a MissingRemoteException when it doesn't exist'''

    try:
        return repo.remotes[name]
    except IndexError:  # I have no idea why they raise an IndexError instead of KeyError
        raise MissingRemoteException('The remote "{0}" does not exist.  '
                                     'Please select a different remote or'
                                     ' add it using "git remote add" command')

def _checkout_branch(repo, branch):
    """Checks out the branch specified locally"""
    branch = _get_branch(repo, branch)
    _LOG.info('Checking out branch "{0}"'.format(branch.name))
    branch.checkout()
    return branch


def _get_branch(repo, name):
    '''Gets a branch and raises a missing branch exception if doesn't exist'''
    try:
        return repo.branches[name]
    except:
        return MissingBranchExcpetion('The Branch "{}" does not seems to exist'.format(name))



def _clone_repo(cls, repo, url, path, name, **kwargs):
    """:return: Repo instance of newly cloned repository
    :param repo: our parent repository
    :param url: url to clone from
    :param path: repository-relative path to the submodule checkout location
    :param name: canonical of the submodule
    :param kwrags: additinoal arguments given to git.clone"""
    module_abspath = cls._module_abspath(repo, path, name)
    module_checkout_path = module_abspath
    if cls._need_gitfile_submodules(repo.git):
        kwargs['separate_git_dir'] = module_abspath
        module_abspath_dir = osp.dirname(module_abspath)
        if not osp.isdir(module_abspath_dir):
            os.makedirs(module_abspath_dir)
        module_checkout_path = osp.join(repo.working_tree_dir, path)
    # end

    clone = git.Repo.clone_from(url, module_checkout_path, **kwargs)
    if cls._need_gitfile_submodules(repo.git):
        cls._write_git_file_and_module_config(module_checkout_path, module_abspath)
    # end
    return clone

