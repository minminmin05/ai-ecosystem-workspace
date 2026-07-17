
from label_studio_sdk import LabelStudio


URL = "http://localhost:8080"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6ODA5MTQ3OTU4NSwiaWF0IjoxNzg0Mjc5NTg1LCJqdGkiOiIxZTM0NWE1YjY1MDA0ZWQxYWViZDJkZTI3ODJiYjc3ZSIsInVzZXJfaWQiOiIxIn0.50W6V_Dq9EnBGVO8NlUEmwZRvbertCIFBDMGtw-0Dus"


client = LabelStudio(
    base_url=URL,
    api_key=API_KEY
)


def list_projects():

    projects = list(client.projects.list())

    print("=== All Projects ===")

    for project in projects:
        print(
            f"ID: {project.id}, "
            f"Title: {project.title}"
        )

    return projects


def list_tasks(project_id):

    print("\n=== Tasks ===")

    tasks = client.tasks.list(
        project=project_id
    )

    for task in tasks:
        print(task)


if __name__ == "__main__":

    projects = list_projects()

    if projects:

        project_id = projects[0].id

        print(
            f"\nSelected Project ID: {project_id}"
        )

        list_tasks(project_id)