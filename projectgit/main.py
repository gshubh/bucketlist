from projectgit.repo import *

def main_menu():

    print("Select an Git operation which you want to perform")

    print("                     #######  REPOSITORY  #######      ")
    print("1. Clone Repository")
    print("2. Create Repository")
    print("3. Get Repository")
    print("4. Commit Repository")
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
    print("16. Update File")
    print("17. Delete File")
    print("18. Commit And Push New File")
    print("19. Git Pull")

    print("                     #######  ISSUES  #######      ")
    print("20. Get Issues")
    print("21. Create Issues")
    print("22. Create Issue With Body")
    print("23. Create Issue With Labels")
    print("24. Create Issue With Assignee")
    print("25. Create Issue With Milestone")
    print("26. Quit\n")


def getchoice():
    choice = int(input('Enter your choice : '))
    return choice


def replymenu ():

    choice = getchoice()

    if choice == 1:
        url = str(input('Enter repository URL : '))
        to_path = str(input('Enter path to directory where you want to clone : '))
        _clone_repo(url, to_path)
        main_menu()

    elif choice == 2:
        username = str(input('Enter your Github username: '))
        full_name = str(input('Enter the name which you want to give to the repository:'))
        g = _get_username_and_password("gshubh")
        _create_repo(g, full_name)
        main_menu()

    elif choice == 3:
        username = str(input('Enter your Github username: '))
        full_name = str(input('Enter the name which you want to give to the repository:'))
        g = _get_username_and_password(username)
        _create_repo(g, full_name)
        main_menu()

    elif choice == 4:
        commiter_name = str(input('Enter Commiter name: '))
        commiter_email = str(input('Enter Commiter email_address: '))
        cloned_repo_directory = str(input('Enter the path/to/cloned_repo_directory:'))
        g = _get_username_and_password("gshubh")
        repo = g.get_repo("gshubh/bucketlist")
        _commit_to_repo(repo, cloned_repo_directory, commiter_name, commiter_email)
        main_menu()

    elif choice == 5:
        user_name = str(input('Enter your Github username: '))
        cloned_repo_directory = str(input('Enter the path/to/cloned_repo_directory:'))
        _push_to_repo(user_name, cloned_repo_directory)
        main_menu()

    elif choice == 6:
        path_to_repo = str(input('Enter the path/to/repository:'))
        _get_current_working_branch(path_to_repo)

    elif choice == 7:
        path_to_repo = str(input('Enter the path/to/repository:'))
        _get_branch(repo, name)

    elif choice == 8:
        path_to_repo = str(input('Enter the path/to/repository:'))
        _get_current_working_branch(path_to_repo)

