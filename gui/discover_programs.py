#!/usr/bin/env python3
"""
Introspects every videobeaux program module and emits a JSON map of
  { programId: { description, outputType, args: [ argSchema, … ] } }
to stdout.

Each argSchema:
  { name, label, type, required, help, default?, choices?, subtype? }
Types: 'text' | 'number' | 'select' | 'file' | 'checkbox'
Subtypes: 'dir'  (only on type='file', opens a folder-picker dialog)

Optional GUI_METADATA dict in any program module (highest priority):
  GUI_METADATA = {
      'output_type': 'video',   # 'video'|'audio'|'json'|'image'|'text'
      'args': {
          'arg_name': {
              'type':    'file',    # override inferred type
              'subtype': 'dir',     # override inferred subtype
              'label':   'My Label',
              'help':    '...',
          }
      }
  }
"""

import sys, io

# Force UTF-8 on stdout/stderr before any imports that might print emoji.
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os, re, json, importlib, argparse, contextlib

# ── Ensure the videobeaux package is importable ──────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VB_ROOT    = os.path.normpath(os.path.join(SCRIPT_DIR, '..'))
if VB_ROOT not in sys.path:
    sys.path.insert(0, VB_ROOT)

PROGRAMS_DIR = os.path.join(VB_ROOT, 'videobeaux', 'programs')

# ── Type heuristics ───────────────────────────────────────────────────────────
#
# Rule: split the long-flag name (--foo_bar_baz) by _ and - and look at the
# LAST word only.  This prevents false positives like:
#
#   --audio_mode    → last='mode'   → text  (NOT file)
#   --input_audio   → last='audio'  → file  ✓
#   --stt_model     → last='model'  → file  ✓
#   --watermark     → last='watermark' (whole name) → file  ✓
#   --norm_crf      → last='crf'    → text  ✓
#
# Matching on the last word also means the full arg name can be in the list
# (e.g. just "--lut" → last word is 'lut' → file).

# These last-words are strong indicators of a file path argument.
FILE_LAST_WORDS = frozenset({
    'file', 'path', 'image', 'lut', 'watermark', 'srt',
    'model', 'video', 'font', 'logo', 'mask', 'overlay', 'thumbnail',
})

# These last-words indicate a *directory* path (opens folder picker).
DIR_LAST_WORDS = frozenset({'dir', 'folder', 'directory'})


def guess_type(flags, kwargs):
    """
    Return (type_str, subtype_or_None) based on argparse kwargs and flag names.
    Only inspects --long-flag names; short flags (-x) are ignored for heuristics.
    """
    action  = kwargs.get('action', '')
    choices = kwargs.get('choices')
    py_type = kwargs.get('type')

    if action in ('store_true', 'store_false'):
        return 'checkbox', None

    if choices:
        return 'select', None

    if py_type in (int, float) or (
        callable(py_type) and getattr(py_type, '__name__', '') in ('int', 'float')
    ):
        return 'number', None

    # Only inspect long flags for file/dir detection
    long_flags = [f for f in flags if f.startswith('--')]
    if long_flags:
        name  = long_flags[0].lstrip('-').replace('-', '_').lower()
        parts = [p for p in name.split('_') if p]
        last  = parts[-1] if parts else ''

        if last in DIR_LAST_WORDS:
            return 'file', 'dir'

        if last in FILE_LAST_WORDS:
            return 'file', None

    return 'text', None


def safe_default(default):
    if default is None or default is argparse.SUPPRESS:
        return None
    if isinstance(default, (str, int, float, bool)):
        return default
    return None


# ── Capturing ArgumentParser ──────────────────────────────────────────────────

class CapturingParser(argparse.ArgumentParser):
    """
    Intercepts add_argument() calls, prefers --long-flag names, applies
    guess_type() heuristics, and collects results in self._captured.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(add_help=False)
        self._captured   = []
        self.description = ''

    def add_argument(self, *flags, **kwargs):
        long_flags  = [f for f in flags if f.startswith('--')]
        short_flags = [f for f in flags if f.startswith('-') and not f.startswith('--')]

        # Prefer --long-flag so the user sees 'stt_model' not 'M'
        flag = long_flags[0] if long_flags else (short_flags[0] if short_flags else None)
        if flag is None:
            return  # positional — skip

        name     = flag.lstrip('-')
        arg_type, subtype = guess_type(flags, kwargs)

        schema = {
            'name':     name,
            'label':    name.replace('-', ' ').replace('_', ' ').title(),
            'type':     arg_type,
            'required': bool(kwargs.get('required', False)),
            'help':     (kwargs.get('help') or '')
                            .replace('%(default)s', str(kwargs.get('default', '')))
                            .strip(),
        }

        if subtype:
            schema['subtype'] = subtype

        default = safe_default(kwargs.get('default'))
        if default is not None:
            schema['default'] = default

        if kwargs.get('choices') is not None:
            schema['choices'] = [str(c) for c in kwargs['choices']]

        self._captured.append(schema)

    def set_defaults(self, **kwargs):
        pass


# ── Silence context ───────────────────────────────────────────────────────────

@contextlib.contextmanager
def silence():
    saved_out, saved_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved_out, saved_err


# ── Discovery loop ────────────────────────────────────────────────────────────

program_names = sorted([
    f[:-3] for f in os.listdir(PROGRAMS_DIR)
    if f.endswith('.py') and not f.startswith('_')
])

result = {}

for prog_name in program_names:
    try:
        with silence():
            mod    = importlib.import_module(f'videobeaux.programs.{prog_name}')
            parser = CapturingParser()
            mod.register_arguments(parser)

        gui_meta    = getattr(mod, 'GUI_METADATA', {}) or {}
        output_type = gui_meta.get('output_type', 'video')
        meta_args   = gui_meta.get('args', {}) or {}

        for schema in parser._captured:
            if schema['name'] in meta_args:
                for key in ('type', 'subtype', 'label', 'help', 'default', 'choices', 'min', 'max'):
                    if key in meta_args[schema['name']]:
                        schema[key] = meta_args[schema['name']][key]

        result[prog_name] = {
            'description': (parser.description or '').strip(),
            'outputType':  output_type,
            'args':        parser._captured,
        }
    except Exception as exc:
        result[prog_name] = {
            'description': '',
            'outputType':  'video',
            'args':        [],
            'error':       str(exc),
        }

sys.stdout.write(json.dumps(result, ensure_ascii=False) + '\n')
sys.stdout.flush()
