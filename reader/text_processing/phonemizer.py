"""Optional G2P (grapheme-to-phoneme) preprocessing using misaki.

Converts text to IPA phonemes before passing to Kokoro for better pronunciation
of abbreviations, numbers, and homographs. Falls back gracefully if misaki
is not installed.

Install with: pip install audiobook-reader[g2p-en]
"""


# Language code to misaki module mapping
LANG_TO_MISAKI = {
    'en-us': ('en', False),   # (module_name, british)
    'en-gb': ('en', True),
    'ja': ('ja', None),
    'zh': ('zh', None),
}


class Phonemizer:
    """Lazy-loading G2P wrapper around misaki."""

    def __init__(self, debug=False):
        self._g2p_cache = {}  # lang_code -> g2p instance
        self._available = None
        self.debug = debug

    def is_available(self, lang_code='en-us'):
        """Check if misaki is installed for the given language."""
        module_name = LANG_TO_MISAKI.get(lang_code, (None, None))[0]
        if module_name is None:
            return False
        try:
            __import__(f'misaki.{module_name}')
            return True
        except ImportError:
            return False

    def phonemize(self, text, lang_code='en-us'):
        """Convert text to phonemes. Returns (phonemes, True) or (text, False).

        Returns the original text unchanged if misaki is not available
        for the given language. Unknown words (no lexicon entry) are passed
        through as original text for Kokoro's internal espeak to handle.
        """
        if lang_code not in LANG_TO_MISAKI:
            return text, False

        g2p = self._get_g2p(lang_code)
        if g2p is None:
            return text, False

        try:
            phonemes, tokens = g2p(text)
            if phonemes and phonemes.strip():
                if self.debug:
                    print(f"  [G2P] {lang_code}: {len(text)} chars → {len(phonemes)} phonemes")
                return phonemes, True
            return text, False
        except TypeError:
            # fallback=None leaves unknown words with phonemes=None,
            # causing a crash in misaki's join. Rebuild from tokens manually.
            return self._phonemize_safe(g2p, text, lang_code)
        except Exception as e:
            if self.debug:
                print(f"  [G2P] Failed for {lang_code}: {e}")
            return text, False

    def _phonemize_safe(self, g2p, text, lang_code):
        """Handle None phonemes from unknown words.

        Retries the lexicon, then the espeak fallback (if configured); only
        substitutes raw text as a last resort so we don't feed Kokoro's IPA-only
        vocab literal English/foreign letters (most get silently dropped or
        misread as unrelated phonemes by the model).
        """
        try:
            from misaki.en import G2P as EnG2P, TokenContext, replace

            text2, tokens, features = EnG2P.preprocess(text)
            tokens = g2p.tokenize(text2, tokens, features)
            tokens = g2p.fold_left(tokens)
            tokens = EnG2P.retokenize(tokens)

            def resolve(t, ctx):
                if t.phonemes is None:
                    t.phonemes, t.rating = g2p.lexicon(replace(t), ctx)
                if t.phonemes is None and g2p.fallback is not None:
                    t.phonemes, t.rating = g2p.fallback(replace(t))
                if t.phonemes is None:
                    t.phonemes = t.text

            ctx = TokenContext()
            flat = []
            for w in reversed(tokens):
                if not isinstance(w, list):
                    resolve(w, ctx)
                    ctx = EnG2P.token_context(ctx, w.phonemes, w)
                    flat.insert(0, w)
                else:
                    for t in w:
                        resolve(t, ctx)
                        flat.insert(0, t)

            result = ''.join(t.phonemes + t.whitespace for t in flat)
            if result and result.strip():
                if self.debug:
                    unk = sum(1 for t in flat if t.rating is None)
                    print(f"  [G2P] {lang_code}: {len(text)} chars → {len(result)} phonemes ({unk} unknown)")
                return result, True
            return text, False
        except Exception as e:
            if self.debug:
                print(f"  [G2P] Safe fallback failed for {lang_code}: {e}")
            return text, False

    def _get_g2p(self, lang_code):
        """Get or create G2P instance for language."""
        if lang_code in self._g2p_cache:
            return self._g2p_cache[lang_code]

        module_name, british = LANG_TO_MISAKI[lang_code]

        try:
            if module_name == 'en':
                from misaki import en
                g2p = en.G2P(trf=False, british=bool(british), fallback=self._make_espeak_fallback(bool(british)))

            elif module_name == 'ja':
                from misaki import ja
                g2p = ja.G2P()

            elif module_name == 'zh':
                from misaki import zh
                g2p = zh.G2P()

            else:
                self._g2p_cache[lang_code] = None
                return None

            self._g2p_cache[lang_code] = g2p
            if self.debug:
                print(f"  [G2P] Loaded misaki for {lang_code}")
            return g2p

        except ImportError:
            self._g2p_cache[lang_code] = None
            return None
        except Exception as e:
            # misaki is installed but failed to init (e.g. spaCy model download
            # failed) - warn even outside --debug, since the user otherwise has
            # no way to know G2P silently isn't running.
            print(f"⚠️  G2P (misaki) failed to initialize for {lang_code}, "
                  f"falling back to standard TTS pronunciation: {e}")
            self._g2p_cache[lang_code] = None
            return None

    @staticmethod
    def _make_espeak_fallback(british):
        """Build misaki's espeak-ng fallback for words its lexicon doesn't know
        (proper nouns, foreign loanwords, etc.) instead of leaving them
        unphonemized. Returns None if espeak-ng can't be located, in which case
        unknown words fall through to raw text (existing behavior).

        Points phonemizer's espeak backend at the espeakng_loader-bundled
        library (already a hard dependency via kokoro-onnx) before misaki's own
        espeak module runs its lookup - misaki's default lookup only checks a
        hardcoded Homebrew path, which doesn't work on Linux, Windows, or even
        non-Homebrew macOS installs.
        """
        try:
            from phonemizer.backend.espeak.wrapper import EspeakWrapper
            if not EspeakWrapper._ESPEAK_LIBRARY:
                import espeakng_loader
                EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
                EspeakWrapper.set_library(espeakng_loader.get_library_path())

            from misaki.espeak import EspeakFallback
            return EspeakFallback(british=british)
        except Exception:
            return None


_phonemizer = None


def get_phonemizer(debug=False):
    """Get singleton phonemizer instance."""
    global _phonemizer
    if _phonemizer is None:
        _phonemizer = Phonemizer(debug=debug)
    return _phonemizer
