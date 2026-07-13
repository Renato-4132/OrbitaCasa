#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import datetime

METODI_PAGAMENTO = [
    "Contanti", "RID/SDD", "Bonifico", "C.Credito", "C.Debito",
    "Contactless", "PayPal", "Bollettino", "Prepagata", "Assegno",
    "Revolut", "Apple Pay", "Google Pay", "Postepay", "Satispay",
    "Scalapay", "Amazon Pay", "Altro",
]

def campo(entry, nome, default=""):
    if isinstance(entry, SpesaEntry):
        return getattr(entry, nome, default)
    return default

class SpesaEntry:
    __slots__ = (
        "categoria", "descrizione", "importo", "tipo", "id_ricorrenza",
        "id_spesa", "conto", "ora", "hashtag", "metodo_pagamento",
    )

    def __init__(self, categoria, descrizione, importo, tipo,
                 id_ricorrenza=None, id_spesa=None, conto="", ora="",
                 hashtag=None, metodo_pagamento=""):
        self.categoria = categoria
        self.descrizione = descrizione
        self.importo = float(importo)
        self.tipo = tipo
        self.id_ricorrenza = id_ricorrenza
        self.id_spesa = id_spesa or uuid.uuid4().hex[:12]
        self.conto = conto or ""
        self.ora = ora or ""
        self.hashtag = list(hashtag) if hashtag else []
        self.metodo_pagamento = metodo_pagamento or ""
    def _tupla_legacy(self):
        base = (self.categoria, self.descrizione, self.importo, self.tipo)
        if self.id_ricorrenza is not None:
            return base + (self.id_ricorrenza,)
        return base
    def __iter__(self):
        return iter(self._tupla_legacy())
    def __len__(self):
        return len(self._tupla_legacy())
    def __getitem__(self, idx):
        return self._tupla_legacy()[idx]
    def __eq__(self, other):
        if isinstance(other, SpesaEntry):
            return self._tupla_legacy() == other._tupla_legacy()
        if isinstance(other, tuple):
            return self._tupla_legacy() == other
        return NotImplemented
    def __repr__(self):
        return (f"SpesaEntry(id={self.id_spesa!r}, cat={self.categoria!r}, "
                f"desc={self.descrizione!r}, importo={self.importo}, "
                f"tipo={self.tipo!r}, conto={self.conto!r}, ora={self.ora!r}, "
                f"metodo_pagamento={self.metodo_pagamento!r}, hashtag={self.hashtag!r})")

    @classmethod
    def da_dict(cls, e):
        return cls(
            categoria=e["categoria"],
            descrizione=e["descrizione"],
            importo=float(e["importo"]),
            tipo=e["tipo"],
            id_ricorrenza=e.get("id_ricorrenza"),
            id_spesa=e.get("id_spesa"),
            conto=e.get("conto", ""),
            ora=e.get("ora", ""),
            hashtag=e.get("hashtag", []),
            metodo_pagamento=e.get("metodo_pagamento", ""),
        )
    def a_dict(self):
        d = {
            "id_spesa": self.id_spesa,
            "categoria": self.categoria,
            "descrizione": self.descrizione,
            "importo": self.importo,
            "tipo": self.tipo,
        }
        if self.id_ricorrenza is not None:
            d["id_ricorrenza"] = self.id_ricorrenza
        if self.conto:
            d["conto"] = self.conto
        if self.ora:
            d["ora"] = self.ora
        if self.hashtag:
            d["hashtag"] = self.hashtag
        if self.metodo_pagamento:
            d["metodo_pagamento"] = self.metodo_pagamento
        return d

    @classmethod
    def nuova(cls, categoria, descrizione, importo, tipo, id_ricorrenza=None,
              conto="", metodo_pagamento="", hashtag=None, ora=None):
        if ora is None:
            ora = datetime.datetime.now().strftime("%H:%M")
        return cls(categoria, descrizione, importo, tipo,
                    id_ricorrenza=id_ricorrenza, conto=conto, ora=ora,
                    hashtag=hashtag, metodo_pagamento=metodo_pagamento)
