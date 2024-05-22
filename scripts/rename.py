from pathlib import Path
import shutil

AUTHOR = "valory"
SKILL_NAME_SNAKE_CASE = "learning"
SKILL_NAME_CAMEL_CASE = "Learning"

PACKAGES_DIR = Path(".")

WORDS = [
    "demo_service",
    "demo_agent",
    "demo_abci",
    "/demo/",
    "DemoBaseBehaviour",
    "DemoBehaviour",
    "DemoRoundBehaviour",
    "DemoRound",
    "FinishedDemoRound",
    "DemoAbci",
    "DemoAbciApp",
    "DemoPayload",
    "DemoParams",
    "demo_chained_abci",
    "DemoChainedSkillAbci",
    "DemoChainedSkillAbciApp",
    "DemoChainedConsensusBehaviour",
    "service_id: demo",
    "demo skill",
    "demo agent",
    "Demo Agent",
    "demo service",
    "Demo Service",
    "demo_data",
    "participant_to_demo_round",
    "the demo ",
    "DemoChainedAbciApp",
    "demo.",
    "DemoEvent",
    "demo_tm_0"
]


def replace(word):
    if "demo" in word:
        word = word.replace("demo", SKILL_NAME_SNAKE_CASE)
    if "Demo" in word:
        word = word.replace("Demo", SKILL_NAME_CAMEL_CASE)
    return word


def process_file(file_path):

    print(f"Processing {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        data = file.read()

    for word in WORDS:
        new_word = replace(word)
        data = data.replace(word, new_word)

    data = data.replace("/author", f"/{AUTHOR}")
    data = data.replace("author/", f"{AUTHOR}/")
    data = data.replace("author: author", f"author: {AUTHOR}")
    data = data.replace("packages.author", f"packages.{AUTHOR}")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(data)



if __name__ == "__main__":

    for file_path in PACKAGES_DIR.rglob("*"):
        if not file_path.is_file():
            continue

        if "author" not in file_path.parts:
            continue

        if file_path.parts[0] in ["tests", ".tox", ".mypy_cache", "scripts"]:
            continue

        if file_path.suffix not in [
            ".py",
            ".yaml",
            ".json",
            ".md",
            ".sh",
            ".gitignore",
            ".gitleaksignore",
        ]:
            continue

        process_file(file_path)

    for file_path in [".gitignore", ".gitleaksignore", "Makefile", "README.md", "run_agent.sh", "run_service.sh", "packages/packages.json"]:
        process_file(file_path)

    shutil.move(
        Path("packages", "author", "agents", "demo_agent"),
        Path("packages", AUTHOR, "agents", f"{SKILL_NAME_SNAKE_CASE}_agent")
    )
    shutil.move(
        Path("packages", "author", "services", "demo_service"),
        Path("packages", AUTHOR, "services", f"{SKILL_NAME_SNAKE_CASE}_service")
    )
    shutil.move(
        Path("packages", "author", "skills", "demo_abci"),
        Path("packages", AUTHOR, "skills", f"{SKILL_NAME_SNAKE_CASE}_abci")
    )
    shutil.move(
        Path("packages", "author", "skills", "demo_chained_abci"),
        Path("packages", AUTHOR, "skills", f"{SKILL_NAME_SNAKE_CASE}_chained_abci")
    )
    shutil.rmtree(Path("packages", "author"))