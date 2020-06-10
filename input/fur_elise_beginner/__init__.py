import utils

score = utils.Score(
    channels=[
        utils.Channel(name="Left Hand", channel_score="""
    E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 G#4 B4
    C5-2 Rq E4 E5 D#5

    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 C5 B4
    A4-4 Rm E5 D#5
    E5 D#5 E5 B4 D5 C5

    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 G#4 B4
    C5-2 Rq E4 E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4

    B4-2 Rq E4 C5 B4
    A4-2 Rq B4 C5 D5
    E5-2 Rq G4 F5 E5
    D5-2 Rq F4 E5 D5
    C5-2 Rq E4 D5 C5

    B4-2 E4 E4 E5 E4
    E5 E5 E6 D#5 E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 G#4 B4

    C5-2 Rq E4 E5 D#5
    E5 D#5 E5 B4 D5 C5
    A4-2 Rq C4 E4 A4
    B4-2 Rq E4 C5 B4
    A4-2 Rm
    """),
        # right hand
        utils.Channel(name="right hand", channel_score="""
    Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm

    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    Rs Rm

    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    Rs Rm
    A2 E3 A3 Rq Rm

    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    C3 G3 C4 Rq Rm
    G2 G3 B3 Rq Rm
    A2 E3 A3 Rq Rm

    E2 E3 Rm Rm
    Rs Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm

    A2 E3 A3 Rq Rm
    Rs Rm
    A2 E3 A3 Rq Rm
    E2 E3 G#3 Rq Rm
    A2 E3 A3 Rq Rm
    """)
    ],
    time_signature=(3, 4),
    bpm=120,
)
