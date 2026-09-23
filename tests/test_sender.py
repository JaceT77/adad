import unittest

from bot.utils.sender import (
    clean_text_for_telegram,
    prepare_telegram_html,
    split_text_into_chunks,
)


class TestSenderUtils(unittest.TestCase):
    def test_clean_text_latex(self):
        text = "Formulalar: $R_0 = 3.5 \\text{ m}^2 \\cdot \\text{K/W}$ va narxi $500"
        cleaned = clean_text_for_telegram(text)
        self.assertNotIn("$", cleaned)
        self.assertNotIn("\\text", cleaned)
        self.assertIn("R_0 = 3.5", cleaned)
        self.assertIn("·", cleaned)

    def test_prepare_telegram_html(self):
        text = (
            "### Sarlavha\n"
            "**Qalin matn** va *kursiv matn*\n"
            "Formulalar: $R_0 = 3.5 \\text{ m}^2$\n"
            "Balandlik < 3.0m va eni > 1.2m & narxi $100\n"
            "<blockquote><b>SHNK 2.08.02-09</b>: me'yorlar</blockquote>"
        )
        html = prepare_telegram_html(text)
        self.assertIn("<b>Sarlavha</b>", html)
        self.assertIn("<b>Qalin matn</b>", html)
        self.assertIn("<i>kursiv matn</i>", html)
        self.assertIn("&lt; 3.0m", html)
        self.assertIn("&gt; 1.2m", html)
        self.assertIn("&amp;", html)
        self.assertIn("<blockquote><b>SHNK 2.08.02-09</b>: me'yorlar</blockquote>", html)

    def test_split_text_into_chunks_short(self):
        text = "Qisqa xabar"
        chunks = split_text_into_chunks(text, max_chunk_size=3800)
        self.assertEqual(chunks, ["Qisqa xabar"])

    def test_split_text_into_chunks_long_without_newlines(self):
        text = "X" * 7900
        chunks = split_text_into_chunks(text, max_chunk_size=3800)
        self.assertTrue(len(chunks) >= 2)
        for c in chunks:
            self.assertLessEqual(len(c), 3800)

    def test_split_text_into_chunks_paragraphs(self):
        p1 = "P1 " * 1000
        p2 = "P2 " * 1000
        text = f"{p1}\n\n{p2}"
        chunks = split_text_into_chunks(text, max_chunk_size=3800)
        self.assertEqual(len(chunks), 2)
        for c in chunks:
            self.assertLessEqual(len(c), 3800)


if __name__ == "__main__":
    unittest.main()
