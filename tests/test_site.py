"""Regresión estática para la web de La Escalera. Ejecutar: python -m unittest discover -s tests -v"""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')

class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.refs = []
        self.tiles = []
        self.videos = []
        self.hero = None
        self.headings = []
        self.in_title = False
        self.title_text = []
        self.p_depth = 0
        self.invalid_p_heading = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        for attr in ('src', 'href', 'poster', 'data-full'):
            value = a.get(attr, '')
            if value: self.refs.append((tag, attr, value))
        if 'gallery-tile' in a.get('class', '').split(): self.tiles.append(a)
        if tag == 'video': self.videos.append(a)
        if tag == 'img' and 'hero-image' in a.get('class', '').split(): self.hero = a
        if tag == 'h1': self.headings.append(a)
        if tag == 'p': self.p_depth += 1
        elif tag in ('h1','h2','h3') and self.p_depth: self.invalid_p_heading = True
    def handle_endtag(self, tag):
        if tag == 'p' and self.p_depth: self.p_depth -= 1

class SiteRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = SiteParser(); cls.parser.feed(HTML)
    def test_main_hero_is_original_and_prioritized(self):
        hero = self.parser.hero
        self.assertIsNotNone(hero)
        self.assertIn('Zahara%20de%20la%20Sierra%2C%20Spain.jpg', hero['src'])
        self.assertEqual(hero.get('loading'), 'eager')
        self.assertEqual(hero.get('fetchpriority'), 'high')
        self.assertEqual(hero.get('decoding'), 'async')
    def test_no_heading_inside_paragraph(self):
        self.assertFalse(self.parser.invalid_p_heading)
        self.assertEqual(len(self.parser.headings), 1, 'El hero debe tener un único H1')
    def test_gallery_cards_preserved(self):
        self.assertGreaterEqual(len(self.parser.tiles), 14)
        self.assertIn('Senderos de Zahara: Garganta Verde', HTML)
        self.assertIn('Permisos y estado del sendero', HTML)
    def test_local_assets_exist(self):
        missing = []
        for tag, attr, ref in self.parser.refs:
            if ref.startswith(('http://','https://','mailto:','tel:','data:')) or ref.startswith('#') or ref.startswith('javascript:'):
                continue
            path = ref.split('#', 1)[0].split('?', 1)[0]
            if not path or path.startswith('//'): continue
            if not (ROOT / path).is_file(): missing.append((tag, attr, ref))
        self.assertEqual(missing, [], f'Recursos locales ausentes: {missing}')
    def test_internal_anchors_exist(self):
        missing = []
        for tag, attr, ref in self.parser.refs:
            if attr == 'href' and ref.startswith('#') and ref[1:] not in self.parser.ids:
                missing.append(ref)
        self.assertEqual(missing, [], f'Anclas internas rotas: {missing}')
    def test_video_loading_is_deferred(self):
        self.assertEqual(len(self.parser.videos), 2)
        self.assertTrue(all(v.get('preload') == 'none' and 'playsinline' in v for v in self.parser.videos))
    def test_external_image_credits_exist(self):
        self.assertIn('Créditos y licencias de las fotografías del entorno', HTML)
        self.assertIn('CC BY-SA 4.0', HTML)
        self.assertIn('CC0', HTML)
    def test_responsive_css_breakpoints(self):
        css = (ROOT / 'css/styles.css').read_text(encoding='utf-8')
        for breakpoint in ('max-width: 1024px', 'max-width: 680px', 'max-width: 380px'):
            self.assertIn(breakpoint, css)
        self.assertIn('overflow-wrap: break-word', css)
        self.assertIn('prefers-reduced-motion: reduce', css)

if __name__ == '__main__': unittest.main(verbosity=2)
