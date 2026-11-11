"""Piezas de formulario compartidas por todas las apps (se definen una sola vez)."""
from django import forms


class CampoFecha(forms.DateField):
    """Campo de fecha con el selector de calendario del navegador (formato AAAA-MM-DD)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
        kwargs.setdefault('input_formats', ['%Y-%m-%d'])
        super().__init__(*args, **kwargs)
