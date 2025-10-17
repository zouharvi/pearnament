from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
os.makedirs("data", exist_ok=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAKE_DATA = [
    {
        "src_id": "fakesrc_1",
        "src": [
            'Another view to the origin of the name is also related to the Czech word práh (with the meaning of a threshold) and a legendary etymology connects the name of the city with princess Libuše, prophetess and a wife of the mythical founder of the Přemyslid dynasty. She is said to have ordered the city "to be built where a man hews a threshold of his house".',
            'The Czech práh might thus be understood to refer to rapids or fords in the river, the edge of which could have acted as a means of fording the river, thus providing a "threshold" to the castle.',
            'Another derivation of the name Praha is suggested from na prazě, the original term for the shale hillside rock upon which the original castle was built.',
            'At that time, the castle was surrounded by forests, covering the nine hills of the future city – the Old Town on the opposite side of the river, as well as the Lesser Town beneath the existing castle, appeared only later.'
        ],
        "sys_a": "Online-B",
        "out_a": [
            '<span class="difference">Eine andere Ansicht</span> zum Ursprung des Namens <span class="difference">steht ebenfalls im Zusammenhang mit</span> dem tschechischen Wort práh (<span class="difference">mit der Bedeutung einer Schwelle</span>), und eine <span class="difference">legendäre</span> Etymologie verbindet den Namen der Stadt mit Prinzessin Libuše, Prophetin und <span class="difference">Ehefrau</span> des mythischen Gründers der Přemysliden-Dynastie. <span class="difference">Sie soll befohlen haben</span>, die Stadt <span class="difference">dort zu errichten</span>, „wo ein Mann die Schwelle seines Hauses <span class="difference">behaut</span>“.',
            'Das tschechische práh <span class="difference">könnte daher so verstanden werden, dass es sich auf</span> Stromschnellen oder Furten im Fluss bezieht, deren <span class="difference">Rand</span> als <span class="difference">Mittel zur Durchquerung</span> des Flusses <span class="difference">gedient haben könnte</span> und somit eine „Schwelle“ zur Burg <span class="difference">bot</span>.',
            '<span class="difference">Eine weitere Ableitung</span> des Namens Praha <span class="difference">wird von</span> na prazě <span class="difference">vorgeschlagen</span>, <span class="difference">dem ursprünglichen Begriff</span> für den <span class="difference">Schieferfelsen am Hang</span>, auf dem die <span class="difference">ursprüngliche</span> Burg erbaut wurde.',
            '<span class="difference">Zu dieser Zeit</span> war die Burg von Wäldern <span class="difference">umgeben</span>, die die neun Hügel der <span class="difference">zukünftigen</span> Stadt bedeckten – die Altstadt <span class="difference">auf der gegenüberliegenden Seite des Flusses</span> sowie die Kleinseite unterhalb der <span class="difference">bestehenden</span> Burg entstanden erst später.',
        ],
        "sys_b": "GPT4.1",
        "out_b": [
            '<span class="difference">Ein anderer Ansatz</span> zum Ursprung des Namens <span class="difference">bezieht sich ebenfalls auf</span> das tschechische Wort práh (<span class="difference">was „Schwelle“ bedeutet</span>), und eine <span class="difference">sagenhafte</span> Etymologie <span class="difference">stellt eine Verbindung zwischen dem Namen der Stadt und</span> Prinzessin Libuše her, einer Prophetin und der <span class="difference">Gemahlin</span> des mythischen Gründers der Přemysliden-Dynastie. <span class="difference">Ihr wird nachgesagt, sie habe den Bau der Stadt</span> befohlen, „wo ein Mann die Schwelle seines Hauses <span class="difference">zimmert</span>“.',
            'Das tschechische Wort práh <span class="difference">könnte sich somit auf</span> Stromschnellen oder Furten im Fluss beziehen, deren <span class="difference">Kante</span> als <span class="difference">Möglichkeit zur Überquerung</span> des Flusses <span class="difference">dienen konnte</span> und so eine „Schwelle“ zur Burg <span class="difference">darstellte</span>.',
            '<span class="difference">Eine andere Herleitung</span> des Namens Praha <span class="difference">geht auf</span> na prazě <span class="difference">zurück</span>, <span class="difference">die ursprüngliche Bezeichnung</span> für den <span class="difference">schieferhaltigen Felsen</span>, auf dem die <span class="difference">erste</span> Burg errichtet wurde.',
            '<span class="difference">Damals</span> war die Burg von Wäldern <span class="difference">umschlossen</span>, welche die neun Hügel der <span class="difference">künftigen</span> Stadt bedeckten – die Altstadt <span class="difference">auf der anderen Flussseite und auch</span> die Kleinseite unterhalb der <span class="difference">damaligen</span> Burg entstanden erst später.',
        ],
    },
    {
        "src_id": "fakesrc_2",
        "src": [
            "The Sun is the star at the center of the Solar System.",
            "It is a nearly perfect ball of hot plasma, heated to incandescence by nuclear fusion reactions in its core.",
            "The Sun radiates this energy mainly as light, ultraviolet, and infrared radiation, and is the most important source of energy for life on Earth."
        ],
        "sys_a": "System-Alpha",
        "out_a": [
            "Die Sonne ist der Stern im <span class=\"difference\">Zentrum</span> des <span class=\"difference\">Sonnensystems</span>.",
            "Sie ist eine <span class=\"difference\">fast perfekte</span> Kugel aus heißem Plasma, die durch Kernfusionsreaktionen in ihrem <span class=\"difference\">Inneren</span> zum Glühen <span class=\"difference\">gebracht wird</span>.",
            "Die Sonne <span class=\"difference\">strahlt</span> diese Energie <span class=\"difference\">hauptsächlich</span> als Licht, Ultraviolett- und Infrarotstrahlung ab und ist die <span class=\"difference\">wichtigste</span> Energiequelle für das Leben auf der Erde."
        ],
        "sys_b": "Translator-2025",
        "out_b": [
            "Die Sonne ist der Stern im <span class=\"difference\">Mittelpunkt</span> des <span class=\"difference\">Sonnensystems</span>.",
            "Sie ist eine <span class=\"difference\">nahezu perfekte</span> Kugel aus heißem Plasma, die durch Kernfusionsreaktionen in ihrem <span class=\"difference\">Kern</span> zum Glühen <span class=\"difference\">erhitzt wird</span>.",
            "Die Sonne <span class=\"difference\">gibt</span> diese Energie <span class=\"difference\">vorwiegend</span> als Licht, Ultraviolett- und Infrarotstrahlung ab und ist die <span class=\"difference\">bedeutendste</span> Energiequelle für das Leben auf der Erde."
        ]
    },
    {
        "src_id": "fakesrc_3",
        "src": [
            "Coffee is a brewed drink prepared from roasted coffee beans, the seeds of berries from certain flowering plants in the Coffea species.",
            "From the coffee fruit, the seeds are separated to produce a stable, raw product: unroasted green coffee.",
            "The seeds are then roasted, a process which transforms them into a consumable product: roasted coffee, which is ground into fine particles that are typically steeped in hot water before being filtered out, producing a cup of coffee."
        ],
        "sys_a": "Pro-Translate",
        "out_a": [
            "Kaffee ist ein <span class=\"difference\">gebrühtes Getränk</span>, das aus gerösteten Kaffeebohnen, den Samen von Beeren <span class=\"difference\">bestimmter</span> Blütenpflanzen der Gattung Coffea, <span class=\"difference\">zubereitet wird</span>.",
            "Aus der Kaffeefrucht werden die Samen <span class=\"difference\">getrennt</span>, um ein <span class=\"difference\">stabiles Rohprodukt</span> zu <span class=\"difference\">erzeugen</span>: ungerösteten Rohkaffee.",
            "Anschließend werden die Samen geröstet, ein Prozess, der sie in ein <span class=\"difference\">konsumierbares Produkt</span> verwandelt: Röstkaffee, der zu feinen Partikeln gemahlen wird, die <span class=\"difference\">üblicherweise</span> in heißem Wasser <span class=\"difference\">aufgegossen</span> werden, bevor sie <span class=\"difference\">herausgefiltert</span> werden, um eine Tasse Kaffee <span class=\"difference\">zu erhalten</span>."
        ],
        "sys_b": "Lingua-Max",
        "out_b": [
            "Kaffee ist ein <span class=\"difference\">Brühgetränk</span>, das aus gerösteten Kaffeebohnen, den Samen von Beeren <span class=\"difference\">gewisser</span> Blütenpflanzen der Gattung Coffea, <span class=\"difference\">hergestellt wird</span>.",
            "Aus der Kaffeefrucht werden die Samen <span class=\"difference\">separiert</span>, um ein <span class=\"difference\">haltbares Rohprodukt</span> zu <span class=\"difference\">gewinnen</span>: ungerösteten Rohkaffee.",
            "Die Samen werden dann geröstet, ein Vorgang, der sie in ein <span class=\"difference\">verzehrfertiges Produkt</span> umwandelt: Röstkaffee, der zu feinen Partikeln gemahlen und <span class=\"difference\">typischerweise</span> in heißem Wasser <span class=\"difference\">gezogen</span>, bevor er <span class=\"difference\">gefiltert</span> wird, was eine Tasse Kaffee <span class=\"difference\">ergibt</span>."
        ]
    },
    {
        "src_id": "fakesrc_4",
        "src": [
            "The Great Wall of China is a series of fortifications that were built across the historical northern borders of ancient Chinese states and Imperial China as protection against various nomadic groups from the Eurasian Steppe.",
            "Several walls were built from as early as the 7th century BC, with selective stretches later joined together by Qin Shi Huang (220–206 BC), the first emperor of China.",
            "Later on, many successive dynasties have built and maintained multiple stretches of border walls."
        ],
        "sys_a": "DeepL",
        "out_a": [
            "Die Chinesische Mauer ist eine Reihe von <span class=\"difference\">Befestigungsanlagen</span>, die entlang der <span class=\"difference\">historischen</span> Nordgrenzen <span class=\"difference\">antiker chinesischer Staaten</span> und des kaiserlichen Chinas zum Schutz vor <span class=\"difference\">verschiedenen</span> Nomadengruppen aus der eurasischen Steppe errichtet wurden.",
            "Mehrere Mauern wurden bereits im 7. Jahrhundert v. Chr. errichtet, wobei <span class=\"difference\">einzelne Abschnitte</span> später von Qin Shi Huang (220–206 v. Chr.), dem ersten Kaiser Chinas, <span class=\"difference\">miteinander verbunden wurden</span>.",
            "<span class=\"difference\">Später</span> haben viele <span class=\"difference\">aufeinanderfolgende</span> Dynastien <span class=\"difference\">mehrere Abschnitte</span> von Grenzmauern gebaut und <span class=\"difference\">instand gehalten</span>."
        ],
        "sys_b": "Google Translate",
        "out_b": [
            "Die Chinesische Mauer ist eine Reihe von <span class=\"difference\">Befestigungen</span>, die zum Schutz vor <span class=\"difference\">verschiedenartigen</span> Nomadengruppen aus der eurasischen Steppe über die <span class=\"difference\">geschichtlichen</span> Nordgrenzen <span class=\"difference\">der alten chinesischen Staaten</span> und des kaiserlichen China hinweg gebaut wurden.",
            "Bereits im 7. Jahrhundert v. Chr. wurden mehrere Mauern gebaut, wobei <span class=\"difference\">ausgewählte Abschnitte</span> später von Qin Shi Huang (220–206 v. Chr.), dem ersten Kaiser Chinas, <span class=\"difference\">zusammengefügt wurden</span>.",
            "<span class=\"difference\">Danach</span> haben viele <span class=\"difference\">nachfolgende</span> Dynastien <span class=\"difference\">mehrfache Strecken</span> von Grenzmauern gebaut und <span class=\"difference\">gewartet</span>."
        ]
    }
]


class UIDRequest(BaseModel):
    uid: str

@app.post("/get-next")
async def get_next(request: UIDRequest):
    print(request.uid)
    global FAKE_DATA
    FAKE_DATA = FAKE_DATA + [FAKE_DATA.pop(0)]
    return JSONResponse(content=FAKE_DATA[0])


async def log_message(message: str):
    with open("data/log.jsonl", "a") as log_file:
        log_file.write(message + "\n")