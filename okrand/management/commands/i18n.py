from django.core.management.base import BaseCommand

from okrand import update_po_files


class Command(BaseCommand):
    help = 'Okrand internationalization'

    # def add_arguments(self, parser):
    #     parser.add_argument('interactive', type=bool)

    def handle(self, *args, **options):
        update_po_files()

#
# def main_interactive():
#     # TODO: CLI interactive and non-interactive modes
#     # TODO: suggest best match: https://stackoverflow.com/questions/6690739/high-performance-fuzzy-string-comparison-in-python-use-levenshtein-or-difflib
#
#     from textual.app import (
#         App,
#         ComposeResult,
#     )
#     from textual.widgets import (
#         ListView,
#         ListItem,
#         Label,
#         Header,
#     )
#
#     result = update_po_files()
#
#     if not result.newly_obsolete_strings:
#         return
#
#     class Okrand(App):
#
#         # CSS_PATH = "list_view.css"
#
#         def compose(self) -> ComposeResult:
#             yield Header()
#             yield Label(f'{len(result.newly_obsolete_strings)} left')
#             yield Label('Select which string matches this string:')
#             yield Label(repr(result.newly_obsolete_strings[0]))
#             yield ListView(
#                 ListItem(Label('< none of these match >')),
#                 *[
#                     ListItem(Label(repr(x)))
#                     for x in result.new_strings
#                 ]
#             )
#
#         def on_ready(self):
#             self.screen.focus_next()
#
#     app = Okrand()
#     app.run()
#
#     # result = update_po_files()
#     # if not result.newly_obsolete_strings:
#     #     break
#     #
#     #
#     #
#     # print('new:')
#     # for i, x in enumerate(result.new_strings):
#     #     print('    ', repr(x))
#     #
#     # print()
#     #
#     # print('newly obsolete:')
#     # for x in result.newly_obsolete_strings:
#     #     print('    ', repr(x))
#
