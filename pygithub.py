from github import Github

# using username and password
USERNAME = ""
PASSWORD = ""
OWNER = ""
REPO_NAME = ""
g = Github("user", "password")
repo = g.get_repo("{owner}/{repo_name}".format(owner=OWNER, repo_name=REPO_NAME))


def get_current_user(g):
    user = g.get_user()
    return  user.login


def get_user_by_name(self):
    user= get_current_user(g)
    user = g.get_user(user)
    return user.name

def get_repository_by_name(full_name_or_id):
    """

    :rtype: oject
    """
    repo = g.get_repo(full_name_or_id)
    print (repo.name)

def get_repository_topics(full_name_or_id):
    # Give list of all topics

    repo = g.get_repo(full_name_or_id)
    repo = g.get_repo(full_name_or_id)
    list = repo.get_topics()
    return list

def get_list_of_open_issues(full_name_or_id):
    repo = g.get_repo(full_name_or_id)
    open_issues = repo.get_issues(state='open')
    for issue in open_issues:
        print(issue)

def get_repository_labels(full_name_or_id):
    # To get the all labels of the repository

    repo = g.get_repo(full_name_or_id)
    labels = repo.get_labels()
    for label in labels:
        print(label)

def root_directory_content(full_name_or_id):
    # To get all content of the root directory of the repository

    repo = g.get_repo(full_name_or_id)
    contents = repo.get_contents("")
    for content_file in contents:
        print(content_file)

def create_new_file(full_name_or_id, path, message, content, branch):
    # To create new file inside the repository
    '''parameters
    path - string, (required), path of the file in the repository
    message - string, (required), commit message
    content - string, (required) actual data in the file
    '''

    repo = g.get_repo(full_name_or_id)
    repo.create_file(path, message, content, branch=branch)

def update_a_file(full_name_or_id, path, ref, message, content, branch):
    # Update a file in the repository
    '''parameters
        path - string, (required), path of the file in the repository
        message - string, (required), commit message
        content - string, (required) actual data in the file
        sha - string, (required), Th blob sha of file being replaced
        branch - string. The branch name. Default: The repository's branch name (usually master)
    '''

    repo = g.get_repo(full_name_or_id)
    contents = repo.get_contents(path, ref)
    repo.update_file(contents.path, message, content, contents.sha, branch)


def delete_a_file(full_name_or_id, path, ref, message, content, branch):
    # Update a file in the repository
    '''parameters
        path - string, (required), path of the file in the repository
        message - string, (required), commit message
        content - string, (required) actual data in the file
        sha - string, (required), Th blob sha of file being replaced
        branch - string. The branch name. Default: The repository's branch name (usually master)
    '''

    repo = g.get_repo(full_name_or_id)
    contents = repo.get_contents(path, ref)
    repo.delete_file(contents.path, message, content, contents.sha, branch)

def main():
    get_repository_by_name('gshubh/bucketlist')

if __name__ == '__main__ ':
    main()


