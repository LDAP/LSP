from .types import diff
from .typing import Any, Dict, List, Union
from .url import filename_to_uri
import sublime
import os


def is_subpath_of(file_path: str, potential_subpath: str) -> bool:
    try:
        file_path = os.path.realpath(file_path)
        potential_subpath = os.path.realpath(potential_subpath)
        return not os.path.relpath(file_path, potential_subpath).startswith("..")
    except ValueError:
        return False


class WorkspaceFolder:

    __slots__ = ('name', 'path')

    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = path

    @classmethod
    def from_path(cls, path: str) -> 'WorkspaceFolder':
        return cls(os.path.basename(path) or path, path)

    def __hash__(self) -> int:
        return hash((self.name, self.path))

    def __repr__(self) -> str:
        return "{}('{}', '{}')".format(self.__class__.__name__, self.name, self.path)

    def __str__(self) -> str:
        return self.path

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WorkspaceFolder):
            return self.name == other.name and self.path == other.path
        return False

    def to_lsp(self) -> Dict[str, str]:
        return {"name": self.name, "uri": self.uri()}

    def uri(self) -> str:
        return filename_to_uri(self.path)

    def includes_uri(self, uri: str) -> bool:
        return uri.startswith(self.uri())


class ProjectFolders(object):

    def __init__(self, window: sublime.Window) -> None:
        self._window = window
        self.folders = self._window.folders()  # type: List[str]

    def update(self) -> bool:
        new_folders = self._window.folders()
        added, removed = diff(self.folders, new_folders)
        if added or removed:
            self.folders = new_folders
            return True
        return False

    def includes_path(self, file_path: str) -> bool:
        if self.folders:
            return any(is_subpath_of(file_path, folder) for folder in self.folders)
        else:
            return True

    def contains(self, view_or_file_name: Union[str, sublime.View]) -> bool:
        file_path = view_or_file_name.file_name() if isinstance(view_or_file_name, sublime.View) else view_or_file_name
        return self.includes_path(file_path) if file_path else False

    def get_workspace_folders(self) -> List[WorkspaceFolder]:
        return [WorkspaceFolder.from_path(f) for f in self.folders]


def sorted_workspace_folders(folders: List[str], file_path: str) -> List[WorkspaceFolder]:
    matching_paths = []  # type: List[str]
    other_paths = []  # type: List[str]

    for folder in folders:
        is_subpath = is_subpath_of(file_path, folder)
        if is_subpath:
            if matching_paths and len(folder) > len(matching_paths[0]):
                matching_paths.insert(0, folder)
            else:
                matching_paths.append(folder)
        else:
            other_paths.append(folder)

    return [WorkspaceFolder.from_path(path) for path in matching_paths + other_paths]


def enable_in_project(window: sublime.Window, config_name: str) -> None:
    project_data = window.project_data()
    if isinstance(project_data, dict):
        project_settings = project_data.setdefault('settings', dict())
        project_lsp_settings = project_settings.setdefault('LSP', dict())
        project_client_settings = project_lsp_settings.setdefault(config_name, dict())
        project_client_settings['enabled'] = True
        window.set_project_data(project_data)
    else:
        sublime.message_dialog(
            "Can't enable {} in the current workspace. Ensure that the project is saved first.".format(config_name))


def disable_in_project(window: sublime.Window, config_name: str) -> None:
    project_data = window.project_data()
    if isinstance(project_data, dict):
        project_settings = project_data.setdefault('settings', dict())
        project_lsp_settings = project_settings.setdefault('LSP', dict())
        project_client_settings = project_lsp_settings.setdefault(config_name, dict())
        project_client_settings['enabled'] = False
        window.set_project_data(project_data)
    else:
        sublime.message_dialog(
            "Can't disable {} in the current workspace. Ensure that the project is saved first.".format(config_name))
