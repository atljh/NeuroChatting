from src.managers.file_manager import FileManager


def test_read_groups(tmp_path):
    file = tmp_path / "groups.txt"
    file.write_text("https://group1\nhttps://group2\nhttps://group3")

    groups = FileManager.read_groups(file)
    assert groups == ["group1", "group2", "group3"]


def test_read_prompts(tmp_path):
    file = tmp_path / "prompts.txt"
    file.write_text("prompt1\n# comment\nprompt2")

    prompts = FileManager.read_prompts(file)
    assert prompts == ["prompt1", "prompt2"]


def test_read_blacklist(tmp_path):
    file = tmp_path / "blacklist.txt"
    file.write_text("123456789:group1\n123456789:group2")

    blacklist = FileManager.read_blacklist(file)
    assert blacklist == {"123456789": ["group1", "group2"]}


def test_add_to_blacklist(tmp_path):
    file = tmp_path / "blacklist.txt"
    file.write_text("")

    FileManager.add_to_blacklist("123456789", "group1", file)

    with open(file, "r") as f:
        content = f.read().strip()
    assert content == "123456789:group1"
