from petforge import load_catalogue, load_actions

ORB_ANIMS = ["blink", "ear-wiggle", "tail-wag", "orb-pulse", "float-bob",
             "sparkle-trail", "yawn", "hop", "twirl", "nod"]


def test_catalogue_has_over_100_pets():
    assert len(load_catalogue()) >= 100


def test_every_pet_has_orb_face_spec():
    for pet in load_catalogue():
        assert pet.orb.get("palette"), pet.id
        assert pet.orb.get("face"), pet.id
        assert pet.orb.get("prompt"), pet.id
        assert pet.orb_prompt() == pet.orb["prompt"]


def test_every_pet_can_do_orb_animations():
    actions = load_actions()
    for anim in ORB_ANIMS:
        assert anim in actions
        assert actions[anim].animation  # every animation carries a motion prompt
    for pet in load_catalogue():
        for anim in ORB_ANIMS:
            assert pet.can(anim), f"{pet.id} missing {anim}"


def test_every_pet_has_signature_move_with_animation():
    for pet in load_catalogue():
        assert pet.signature_move is not None, pet.id
        assert pet.signature_move.animation, pet.id
