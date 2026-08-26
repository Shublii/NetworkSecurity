"The setup.py file is a crucial component of a Python project, as it defines the package metadata and dependencies required for installation. It typically includes information such as the package name, version, author, license, and a list of required packages. This file is used by tools like pip to install the package and its dependencies correctly."


from setuptools import find_packages, setup
from typing import List


def get_requirements() -> List[str]:
    """
    this function will return the list of requirements
    """
    requirement_lst:List[str] = []

    try:
        with open("requirements.txt" ,"r") as file:
            #read lines from the file
            lines=file.readlines()
            #process each line
            for line in lines:
                requirement=line.strip()
                ##ignore emty lines and -e .
                if requirement and requirement!= "-e .": ##-e . --it refers to setup.py file thats itt
                    requirement_lst.append(requirement)

    except FileNotFoundError:
        print("requirements.txt file not found")

    return requirement_lst

print(get_requirements())

##Metadata  --It is information that describes or gives context about some other data.

setup(
    name="NetworkSecurity",
    version="2.1",
    author="Shubham",
    author_email="pratapshuham511@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements(),

)




