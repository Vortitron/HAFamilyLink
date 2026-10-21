"""Community tag consumption."""

import pytest

from kerb_core.tags import MAX_VISIBLE_TAGS, TAXONOMY, Profile, TagScore, TagSource

MC = "android:com.mojang.minecraftpe"


def test_taxonomy_matches_spec_section_7_1() -> None:
	assert len(TAXONOMY) == 26
	assert TAXONOMY["educational"] == "value"
	assert TAXONOMY["chat_with_strangers"] == "caution"


def test_positive_value_tags_show_and_negative_do_not() -> None:
	source = TagSource([TagScore(MC, "educational", 5), TagScore(MC, "creative", -2), TagScore(MC, "unknown_tag", 9)])
	assert source.tags_for(MC) == {"educational"}


def test_caution_tags_need_evidence_and_three_contributors() -> None:
	source = TagSource(
		[
			TagScore(MC, "chat_with_strangers", 4, contributors=2, evidence=True),
			TagScore(MC, "in_app_purchases", 4, contributors=3, evidence=False),
			TagScore(MC, "loot_boxes", 4, contributors=3, evidence=True),
		]
	)
	assert source.tags_for(MC) == {"loot_boxes"}


def test_visible_tags_capped_at_ten_by_score() -> None:
	value_tags = [tag for tag, polarity in TAXONOMY.items() if polarity != "caution"]
	scores = [TagScore(MC, tag, index + 1) for index, tag in enumerate(value_tags)]
	source = TagSource(scores)
	visible = source.crowd_tags(MC)
	assert len(visible) == MAX_VISIBLE_TAGS
	assert visible[0] == value_tags[-1]


def test_profile_overlay_replaces_crowd_and_local_beats_everything() -> None:
	source = TagSource([TagScore(MC, "educational", 5)])
	source.subscribe(Profile.from_dict({"name": "strict under 10", "tags": [{"app": MC, "tags": ["creative"]}]}))
	assert source.tags_for(MC) == {"creative"}
	source.set_local(MC, "educational", True)
	source.set_local(MC, "creative", False)
	assert source.tags_for(MC) == {"educational"}
	with pytest.raises(ValueError):
		source.set_local(MC, "not_a_tag", True)
	assert source.tags_for(None) == set()


def test_loads_jsonl_dump(tmp_path) -> None:
	path = tmp_path / "tags.jsonl"
	path.write_text(
		"# nightly dump\n"
		'{"app": "steam:252950", "tag": "educational", "score": 3, "contributors": 4}\n'
		"\n"
		'{"app": "steam:252950", "tag": "horror", "score": 2, "contributors": 1, "evidence": true}\n'
	)
	source = TagSource.from_jsonl(path)
	assert source.tags_for("steam:252950") == {"educational"}
