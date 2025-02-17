from LSP.plugin.core.protocol import DiagnosticSeverity
from LSP.plugin.core.protocol import DiagnosticTag
from LSP.plugin.core.protocol import PublishDiagnosticsParams
from LSP.plugin.core.typing import Generator
from LSP.plugin.core.url import filename_to_uri
from setup import TextDocumentTestCase
import sublime


class ServerNotifications(TextDocumentTestCase):

    def test_publish_diagnostics(self) -> Generator:
        self.insert_characters("a b c\n")
        params = {
            'uri': filename_to_uri(self.view.file_name() or ''),
            'diagnostics': [
                {
                    'message': "foo",
                    'severity': DiagnosticSeverity.Error,
                    'source': 'qux',
                    'range': {'end': {'character': 1, 'line': 0}, 'start': {'character': 0, 'line': 0}}
                },
                {
                    'message': 'bar',
                    'severity': DiagnosticSeverity.Warning,
                    'source': 'qux',
                    'range': {'end': {'character': 3, 'line': 0}, 'start': {'character': 2, 'line': 0}}
                },
                {
                    'message': "baz",
                    'severity': DiagnosticSeverity.Information,
                    'source': 'qux',
                    'range': {'end': {'character': 5, 'line': 0}, 'start': {'character': 4, 'line': 0}},
                    'tags': [DiagnosticTag.Unnecessary]
                }
            ]
        }  # type: PublishDiagnosticsParams
        yield from self.await_client_notification("textDocument/publishDiagnostics", params)
        yield lambda: len(self.view.get_regions("lspTESTds1")) > 0
        yield lambda: len(self.view.get_regions("lspTESTds2")) > 0
        yield lambda: len(self.view.get_regions("lspTESTds3")) > 0
        yield lambda: len(self.view.get_regions("lspTESTds3_tags")) == 0
        errors = self.view.get_regions("lspTESTds1")
        warnings = self.view.get_regions("lspTESTds2")
        info = self.view.get_regions("lspTESTds3")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], sublime.Region(0, 1))
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], sublime.Region(2, 3))
        self.assertEqual(len(info), 1)
        self.assertEqual(info[0], sublime.Region(4, 5))

        # Testing whether the cursor position moves along with lsp_next_diagnostic

        self.view.window().run_command("lsp_next_diagnostic")
        self.assertEqual(self.view.sel()[0].a, self.view.sel()[0].b)
        self.assertEqual(self.view.sel()[0].b, 0)

        self.view.window().run_command("lsp_next_diagnostic")
        self.assertEqual(self.view.sel()[0].a, self.view.sel()[0].b)
        self.assertEqual(self.view.sel()[0].b, 2)

        self.view.window().run_command("lsp_next_diagnostic")
        self.assertEqual(self.view.sel()[0].a, self.view.sel()[0].b)
        self.assertEqual(self.view.sel()[0].b, 4)

        # lsp_prev_diagnostic should work as well

        self.view.window().run_command("lsp_prev_diagnostic")
        self.assertEqual(self.view.sel()[0].a, self.view.sel()[0].b)
        self.assertEqual(self.view.sel()[0].b, 2)

        self.view.window().run_command("lsp_prev_diagnostic")
        self.assertEqual(self.view.sel()[0].a, self.view.sel()[0].b)
        self.assertEqual(self.view.sel()[0].b, 0)

        # Testing to wrap around if there are no more diagnostics in the direction

        self.view.window().run_command("lsp_prev_diagnostic")
        self.assertEqual(self.view.sel()[0].a, self.view.sel()[0].b)
        self.assertEqual(self.view.sel()[0].b, 4)
