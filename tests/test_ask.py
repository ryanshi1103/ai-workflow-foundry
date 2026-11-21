import unittest
from pathlib import Path
from unittest.mock import patch

from flowfoundry.ask import _condense, ask_project
from flowfoundry.project_context import ContextSnippet, RetrievalResult


def result(*snippets, question='What did we decide about Grok?'):
    return RetrievalResult(question, snippets, ('state.md',), sum(len(s.content) for s in snippets), ())


def snippet(content, status='ACCEPTED', kind='CURRENT_STATE'):
    return ContextSnippet(kind, 'state.md', 'Context', content, status)


class AskTests(unittest.TestCase):
    def test_selects_whole_bullets_and_preserves_qualifiers(self):
        retrieved = result(snippet('# Core\n- Grok is optional, not authority,\n  and remains unverified without credentials.\n- Unrelated evaluator details.'))
        answer = _condense(retrieved)
        self.assertIn('Grok is optional, not authority, and remains unverified without credentials. [1; ACCEPTED]', answer)
        self.assertNotIn('Unrelated', answer)
        self.assertNotIn('# Core', answer)

    def test_status_conflicts_and_reference_indices_survive(self):
        retrieved = result(snippet('Grok is mandatory.', 'CANDIDATE', 'FACT'), snippet('Grok is optional.'))
        answer = _condense(retrieved)
        self.assertLess(answer.index('Grok is optional.'), answer.index('Grok is mandatory.'))
        self.assertIn('[2; ACCEPTED]', answer)
        self.assertIn('[1; CANDIDATE]', answer)
        self.assertIn('conflicts are not verified', answer)

    def test_deduplicates_without_collapsing_status(self):
        answer = _condense(result(snippet('Grok is optional.'), snippet('Grok is optional.'), snippet('Grok is optional.', 'CANDIDATE')))
        self.assertEqual(answer.count('Grok is optional.'), 2)

    def test_no_match_and_empty_are_honest(self):
        for retrieved in (result(), result(snippet('The evaluator is ready.'))):
            self.assertIn('No directly matching answer', _condense(retrieved))
        self.assertIn('No directly matching answer', _condense(result(snippet('The evaluator is ready.'), question='What is the project?')))

    def test_bounded_output_and_truncated_evidence(self):
        answer = _condense(result(snippet('\n'.join(f'- Grok detail {i}.' for i in range(20)))))
        self.assertEqual(answer.count('; ACCEPTED]'), 6)
        answer = _condense(result(snippet('x' * 1589 + '\n- Grok cut')))
        self.assertIn('[excerpt may be truncated]', answer)

    def test_api_keeps_raw_sources_and_zero_ai_calls(self):
        retrieved = result(snippet('Grok is optional.', 'CANDIDATE'))
        with patch('flowfoundry.ask.project_root', return_value=Path('.')), patch('flowfoundry.ask.retrieve_context', return_value=retrieved):
            value = ask_project(Path('.'), 'Grok?')
        self.assertEqual(value['sources'], [retrieved.snippets[0].to_dict()])
        self.assertEqual(value['ai_calls'], 0)
        self.assertEqual(value['executor'], 'local-retrieval')
        self.assertEqual(value['status'], 'PARTIAL')

    def test_long_matching_paragraph_keeps_qualifiers_and_raw_evidence(self):
        paragraph = (
            'Project ask retrieves bounded excerpts from current state, active decisions, '
            'canonical reports and durable task results. Answers select matching bullets '
            'and paragraphs with numbered source references and status labels, using zero '
            'AI calls; full retrieved excerpts remain in source evidence. Selection does '
            'not verify completeness or resolve conflicts. Explicit external handoffs '
            'remain labeled CANDIDATE; they do not override accepted state automatically.'
        )
        self.assertGreater(len(paragraph), 450)
        retrieved = result(snippet(paragraph + '\n\nUnrelated background.'), question='What can project ask do?')
        with patch('flowfoundry.ask.project_root', return_value=Path('.')), patch('flowfoundry.ask.retrieve_context', return_value=retrieved):
            value = ask_project(Path('.'), retrieved.question)
        self.assertIn(paragraph + ' [1; ACCEPTED]', value['answer'])
        self.assertNotIn('Unrelated background.', value['answer'])
        self.assertEqual(value['sources'], [retrieved.snippets[0].to_dict()])
        self.assertEqual(value['ai_calls'], 0)

    def test_question_helpers_do_not_select_unrelated_claims(self):
        for helper in ('can', 'could', 'would', 'should'):
            with self.subTest(helper=helper):
                answer = _condense(result(snippet(f'Checks {helper} mask failures.\n\nProject ask retrieves context.'), question=f'What {helper} project ask do?'))
                self.assertIn('Project ask retrieves context. [1; ACCEPTED]', answer)
                self.assertNotIn('mask failures', answer)

    def test_chinese_problem_question_selects_recorded_limitations(self):
        retrieved = result(
            snippet(
                '# Known limitations\n'
                '- Only Codex has a proven executor implementation.\n'
                '- The optional broker remains unverified without credentials.\n'
                '\nUnrelated product description.'
            ),
            question='这个项目当前最严重的问题是什么？',
        )
        answer = _condense(retrieved)
        self.assertIn('Only Codex has a proven executor implementation.', answer)
        self.assertIn('broker remains unverified', answer)
        self.assertNotIn('Unrelated product description.', answer)

    def test_oversize_paragraph_is_not_cut_or_allowed_to_exceed_budget(self):
        answer = _condense(result(snippet('Grok ' + 'detail ' * 180 + 'is unverified.')))
        self.assertIn('No directly matching answer', answer)
